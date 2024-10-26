from argparse import ArgumentParser, Namespace
from json import loads
from pathlib import Path
from time import sleep, time
from typing import Optional

from cdk8s import App, Duration
from kubernetes import client, config
from kubernetes.config import KUBE_CONFIG_DEFAULT_LOCATION
from kubernetes.dynamic import DynamicClient, ResourceInstance
from kubernetes.utils import FailToCreateError, create_from_directory
from more_itertools import collapse
from rich.console import Console
from yaml import SafeLoader, load_all


class FailToSynthError(Exception):
    pass


class cdk8s_cli:
    def __init__(
        self,
        app: App,
        name: Optional[str] = None,
        kube_context: Optional[str] = "minikube",
        kube_config_file: Optional[str] = KUBE_CONFIG_DEFAULT_LOCATION,
        k8s_client: Optional[client.ApiClient] = None,
        verbose: Optional[bool] = False,
    ) -> None:
        """Triggers the CLI for the supplied CDK8s app.

        Many of these values can be overridden using the CLI arguments.
        You can run the CLI with `--help` to see the available options.

        Args:
            app (App): The CDK8s app to apply.
            name (Optional[str]): The name of the app. Defaults to None.
            kube_context (Optional[str]): The Kubernetes context to use. Defaults to "minikube".
            kube_config_file (Optional[str]): The path to a kubeconfig file. Defaults to using the default kube config location OR use the KUBECONFIG environment variable.
            k8s_client (Optional[client.ApiClient]): A Kubernetes client to use. If not supplied, one will be created using the kube_config_file and context arguments.
            verbose (Optional[bool]): Enable verbose output. Defaults to False.

        Returns:
            None

        Raises:
            FailToCreateError: If there is an error creating the resources.
            FailToSynthError: If there is an error synthing the resources.
        """
        self.args = self._parse_args()

        # Override argument values if CLI values are supplied
        self.args.verbose = self.args.verbose or verbose or self.args.debug
        self.args.kube_context = self.args.kube_context or kube_context

        self.console = Console()

        # If the user has supplied a list of apps to apply, skip unnamed apps
        if self.args.apps and name not in self.args.apps:
            self.console.print(
                f"[yellow]Skipping {'app '+name if name else 'unnamed app'}.[/]"
            )
            return

        # Resolve the full output directory path
        output_dir = Path(Path.cwd(), app.outdir).resolve()

        if self.args.action == "synth":
            self._synth_app(app, name, output_dir)

        if self.args.action == "list":
            self._list(app, name)

        if self.args.action == "diff":
            self._diff(app, name)

        if self.args.action == "apply":
            self.resources = self._apply(app, name, output_dir, k8s_client)

    def _list(self, app: App, name: Optional[str]):
        # This is a very basic implementation and will need to be improved
        manifests = list(load_all(app.synth_yaml(), Loader=SafeLoader))
        self.console.print(
            f"Resources for app{' [purple]' + name + '[/purple]' if name else ''}:"
        )
        if self.args.debug:
            self.console.log("Manifests:", manifests)
        manifest_count = len(manifests)

        for n, manifest in enumerate(manifests):
            connector = "├──" if n < manifest_count - 1 else "└──"
            pipe = "│" if n < manifest_count - 1 else " "
            ns = manifest.get("metadata", {}).get("namespace", None)

            self.console.print(f"{connector} [purple]{manifest['metadata']['name']}[/]")
            self.console.print(f"{pipe}   ├── Kind: {manifest['kind']}")

            if ns:
                self.console.print(f"{pipe}   ├── Namespace: {ns}")

            if manifest["kind"] in ["Deployment", "StatefulSet"]:
                self.console.print(
                    f"{pipe}   ├── Replicas: {manifest['spec']['replicas']}"
                )

            if manifest["kind"] in ["Service"]:
                self.console.print(f"{pipe}   ├── Type: {manifest['spec']['type']}")
                self.console.print(
                    f"{pipe}   ├── Ports: {', '.join([str(port['port']) for port in manifest['spec']['ports']])}"
                )

            # Leave this to last so the pipes match up without having to use
            # a conditional for the last item
            self.console.print(f"{pipe}   └── API Version: {manifest['apiVersion']}")

    def _diff(self, app: App, name: Optional[str]):
        raise NotImplementedError

    def _apply(
        self,
        app: App,
        name: Optional[str],
        output_dir: str,
        k8s_client: Optional[client.ApiClient],
    ):
        self._del_dir(output_dir)
        self._synth_app(app, name, output_dir)

        if not self.args.unattended:
            if self.console.input(
                f"Deploy resources{' for app [purple]' + name + '[/purple]' if name else '' }? [bold]\\[y/N][/]: "
            ).lower() not in ["y", "yes"]:
                self.console.print("[yellow]Skipping.[/]")
                return

        # If a k8s client is not supplied, load the kubeconfig file
        if not k8s_client:
            config.load_kube_config(
                config_file=self.args.kube_config_file, context=self.args.kube_context
            )
            k8s_client = client.ApiClient()

        resources = list()
        try:
            with self.console.status("Applying resources..."):
                response = create_from_directory(
                    k8s_client=k8s_client,
                    yaml_dir=output_dir,
                    apply=True,
                    namespace=None,
                )
                resources: list[ResourceInstance] = list(
                    collapse(response, base_type=ResourceInstance)
                )

        except FailToCreateError as e:
            for error in e.api_exceptions:
                body = loads(error.body)
                self.console.print("[red]ERROR DEPLOYING RESOURCES[/red]:", body)
            raise e

        self._print_resources_applied(resources)

        if self.args.validate:
            # The status check code is buggy and may not work with all resources
            self.console.print("[yellow]Warning: Validation mode is experimental.[/]")
            dynamic_client = DynamicClient(k8s_client)
            sleep
            readiness = self._get_resource_ready_status(resources, dynamic_client)
            TIMEOUT = Duration.minutes(self.args.validate_timeout_minutes)
            if self.args.debug:
                self.console.log("Timeout:", TIMEOUT.to_human_string())
            start_time = time()
            padding = self._get_padding(resources)
            # The whole proceeding status check context is very hard to read, needs to be refactored.
            with self.console.status(
                status="Waiting for reasources to report ready...\n  "
                + "\n  ".join(
                    [
                        f"[purple]{k+'[/]':{'.'}<{padding}}{'[green]Ready[/]' if v else "[red]Not Ready[/]"}"
                        for k, v in readiness.items()
                    ]
                )
            ):
                while not all(readiness.values()):
                    sleep(1)
                    readiness = self._get_resource_ready_status(
                        resources, dynamic_client
                    )
                    if time() - start_time > TIMEOUT.to_seconds():
                        self.console.print(
                            "[red]Timeout reached. Not all resources are ready.[/]"
                        )
                        if self.args.verbose:
                            self.console.print(
                                "Timed out after waiting for", TIMEOUT.to_human_string()
                            )
                        return resources

                self.console.print("[green]All resources are ready.[/]")

        self.console.print("[green]Apply complete[/green]")
        return resources

    def _parse_args(self) -> Namespace:
        """
        Parse the CLI arguments using argparse.
        """
        parser = ArgumentParser(description="A CLI for deploying CDK8s apps.")
        parser.add_argument(
            "action",
            choices=["synth", "apply", "list"],
            help="the action to perform. synth will synth the resources to the output directory. apply will apply the resources to the Kubernetes cluster",
        )
        parser.add_argument(
            "--apps",
            nargs="+",
            help="the apps to apply. If supplied, unnamed apps will always be skipped",
        )
        parser.add_argument(
            "--kube-context",
            default="minikube",
            type=str,
            help="the Kubernetes context to use. Defaults to minikube",
        )
        parser.add_argument(
            "--kube-config-file",
            default=None,
            type=str,
            help="the path to a kubeconfig file",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="enable verbose output"
        )
        parser.add_argument(
            "--unattended",
            action="store_true",
            help="enable unattended mode. This will not prompt for confirmation before applying",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="enable debug mode. This will print debug information",
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            help="experimental feature. Will enable validation mode. This will wait for resources to report ready before exiting",
        )
        parser.add_argument(
            "--validate-timeout-minutes",
            type=int,
            default=3,
            help="the number of minutes to wait for resources to report ready before timing out. Needs --validate to be set",
        )
        return parser.parse_args()

    def _del_dir(self, path: Path) -> None:
        """
        Empty a directory by deleting all files and directories within it.
        """
        for p in path.iterdir():
            if p.is_dir():
                self._del_dir(p)
                p.rmdir()
            else:
                p.unlink()

    def _get_resource(self, client: DynamicClient, resource):
        if self.args.debug:
            details = {
                "name": resource.metadata.name,
                "kind": resource.kind,
                "namespace": resource.metadata.namespace,
            }
            self.console.log(f"Getting resource: {details}")
        resource_type = client.resources.get(
            api_version=resource.api_version,
            kind=resource.kind,
        )
        return resource_type.get(
            name=resource.metadata.name,
            namespace=resource.metadata.namespace,
        )

    def _synth_app(self, app: App, name: Optional[str], output_dir: Path) -> None:
        with self.console.status(
            f"Synthing app{' for app [purple]' + name + '[/purple]' if name else '' }..."
        ):
            try:
                app.synth()
                self.console.print(
                    f"Resources{' for app [purple]' + name + '[/purple]' if name else '' } synthed to {output_dir}"
                )
            except Exception as e:
                self.console.print("[red]ERROR SYNTHING RESOURCES[/red]", e)
                raise FailToSynthError(e)

    def _get_padding(self, resources: list[ResourceInstance]) -> int:
        """
        Get the padding required to align the resource names in the Rich console.
        """
        return max(
            [
                len(f"{resource.metadata.name} ({resource.kind})")
                for resource in resources
            ]
        )

    def _print_resources_applied(
        self,
        resources: list[ResourceInstance],
    ) -> None:
        """
        Prints the resources that were applied to the Kubernetes cluster using the Rich console.
        """
        padding = self._get_padding(resources)
        for resource in resources:
            ns = resource.metadata.namespace
            self.console.print(
                f"Resource [purple]{f"{resource.metadata.name} ({resource.kind})":<{padding}}[/purple] applied{ str(' in namespace [purple]'+ns+'[/purple]') if ns else ''}."
            )
            if self.args.verbose:
                self.console.print("[bold]Verbose resource details:[/]\n", resource)

    def _print_resources_ready(
        self,
        resources: list[ResourceInstance],
    ) -> None:
        """
        Prints the resources that were applied to the Kubernetes cluster using the Rich console.
        """
        padding = self._get_padding(resources)
        for resource in resources:
            self.console.print(
                f"Resource [purple]{f"{resource.metadata.name} ({resource.kind})":<{padding}}[/purple] is [green]ready[/]."
            )
            if self.args.verbose:
                self.console.print("[bold]Verbose resource details:[/]\n", resource)

    def _resource_is_healthy(self, resource: ResourceInstance) -> bool:
        status = resource.status
        if self.args.debug:
            self.console.log(f"Resource {resource.metadata.name} status: {status}")

        # No status is good status
        if not status:
            return True

        if not status.conditions:
            return True
        good_conditions = ["Ready", "Succeeded", "Available"]
        for condition in status.conditions:
            if condition.type in good_conditions and condition.status == "True":
                return True

        return False

    def _get_resource_ready_status(
        self,
        resources: list[ResourceInstance],
        client: DynamicClient,
    ) -> dict[str, bool]:
        """
        Returns a dictionary of resources and their readiness status in the form of {resource_name: is_ready}.
        """
        # ToDo: Refactor to use a list of resource objects so the resource type and namespace
        # can be printed in the console to make it easier to see what resources are being checked
        # and where they can be found in the cluster.
        readiness: dict[str, bool] = {
            resource.metadata.name: False for resource in resources
        }
        for resource in resources:
            resource = self._get_resource(client, resource)
            healthy = self._resource_is_healthy(resource)
            if self.args.debug:
                self.console.log(f"Resource {resource.metadata.name} health: {healthy}")
            if healthy:
                if not readiness[resource.metadata.name]:
                    readiness[resource.metadata.name] = True
                    # self._print_resources_ready([resource])
        return readiness
