from cdk8s import App
from pathlib import Path
from kubernetes import client, config
from kubernetes.dynamic import ResourceInstance, DynamicClient
from kubernetes.utils import create_from_directory, FailToCreateError
from json import loads
from rich.console import Console
from more_itertools import collapse
from typing import Optional
from argparse import ArgumentParser, Namespace
from time import sleep


class cdk8s_cli:
    def __init__(
        self,
        app: App,
        name: Optional[str] = None,
        kube_context: str = "minikube",
        kube_config_file: Optional[str] = None,
        k8s_client: Optional[client.ApiClient] = None,
        verbose: bool = False,
    ):
        self.args = self._parse_args()

        # Override argument values if CLI values are supplied
        self.args.verbose = self.args.verbose or verbose
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

        if self.args.action == "apply":
            self._apply(app, name, output_dir)

    def _apply(self, app, name, output_dir, k8s_client=None):
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
                exit(body["code"])

        self._print_resources_applied(resources)

        self.console.print("[green]Apply complete[/green]")
        # return
        # The following status check code requires more work to be functional
        dynamic_client = DynamicClient(k8s_client)
        readiness = self._get_resource_ready_status(resources, dynamic_client)
        with self.console.status(
            status="Waiting for reasources to report ready...\n"
            + "\n".join(
                [
                    f"[purple]{k}[/]: {'[green]Ready[/]' if v else "[red]Not Ready[/]"}"
                    for k, v in readiness.items()
                ]
            )
        ):
            while not all(readiness.values()):
                readiness = self._get_resource_ready_status(resources, dynamic_client)
                sleep(1)

    def _parse_args(self) -> Namespace:
        """
        Parse the CLI arguments using argparse.
        """
        parser = ArgumentParser(description="A CLI for deploying CDK8s apps.")
        parser.add_argument(
            "action",
            choices=["synth", "apply"],
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
        return parser.parse_args()

    def _del_dir(self, path: Path):
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
                exit(1)

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
