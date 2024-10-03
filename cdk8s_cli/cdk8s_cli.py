import inspect
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any
from cdk8s import App, IResolver, YamlOutputType
from kubernetes.utils import create_from_yaml
import kubernetes
from tempfile import NamedTemporaryFile
from typing import Sequence
from rich import print


class CLIHandler:
    def __init__(self) -> None:
        """
        Initializes the KubernetesCLIHandler, parses command-line arguments,
        and triggers the appropriate action (synth or deploy) on the apps
        instantiated in the parent module.
        """
        args = self._parse_args()
        parent_locals = inspect.currentframe().f_back.f_locals

        # Collect list of app objects
        all_apps = self._get_all_apps(parent_locals)
        if not all_apps:
            print("No apps found")
            exit(1)

        # Filter list of apps. This could do with a refactor.
        if args.all:
            apps = all_apps
        else:
            apps = [app for app in all_apps if app.name in args.apps]
            for app in args.apps:
                if app not in [app.name for app in all_apps]:
                    print(f"App {app} not found.")
                    exit(1)

        k8s_client = kubernetes.config.new_client_from_config(
            config_file=args.kube_config_file, context=args.context
        )

        if args.action == "synth":
            self._synth_apps(apps)

        if args.action == "deploy":
            self._deploy_apps(k8s_client, args, apps)

    def _synth_apps(self, apps: list[App]) -> None:
        for app in apps:
            app.synth()
        print(
            f"Manifest for [blue]{"[/blue], [blue]".join([app.name for app in apps])}[/blue] synthed to {Path(apps[0].outdir).resolve()}"
        )

    def _deploy_apps(
        self, k8s_client: kubernetes.client.ApiClient, args: Namespace, apps: list[App]
    ) -> None:
        if not args.unattended:
            print(
                f"Deploying the following apps: [blue]{"[/blue], [blue]".join([app.name for app in apps])}[/blue]. Continue? [y/n]",
                end=" ",
            )
            response = input()
            if response.lower() != "y":
                print("Aborted")
                exit(1)
        for app in apps:
            print(f"Deploying app {app.name}...")
            app.deploy(client=k8s_client, verbose=args.verbose)
            print("Done")

    def _parse_args(self) -> Namespace:
        parser = ArgumentParser()
        parser.add_argument(
            "action",
            choices=["deploy", "synth"],
            help="The action to perform.",
        )

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--apps",
            nargs="+",
            type=str,
            help="the apps to deploy in a space seperated list",
        )
        group.add_argument("--all", action="store_true", help="deploy all apps")

        parser.add_argument(
            "--context",
            default="minikube",
            type=str,
            help="The Kubernetes context to use. Defaults to minikube",
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
            help="enable unattended mode. This will not prompt for confirmation before deploying.",
        )

        return parser.parse_args()

    def _get_all_apps(self, locals: dict[str, Any]) -> list[App]:
        """
        Returns a list of all App instances in the locals dictionary.
        """
        return [locals[app] for app in locals if isinstance(locals[app], App)]


class App(App):
    """
    Inherit from the cdk8s.App class to add a deploy method that writes the
    synthesized YAML to a temporary file and deploys it to the Kubernetes cluster.
    """

    def __init__(
        self,
        *,
        name: str,
        outdir: str | None = None,
        output_file_extension: str | None = None,
        record_construct_metadata: bool | None = None,
        resolvers: Sequence[IResolver] | None = None,
        yaml_output_type: YamlOutputType | None = None,
    ) -> App:
        super().__init__(
            outdir=outdir,
            output_file_extension=output_file_extension,
            record_construct_metadata=record_construct_metadata,
            resolvers=resolvers,
            yaml_output_type=yaml_output_type,
        )
        self.name = name

    def deploy(
        self, client: kubernetes.client.ApiClient, verbose: bool = False
    ) -> list:
        """
        Deploys Kubernetes resources defined in the apps charts to the cluster.

        Args:
            client (kubernetes.client.ApiClient): The Kubernetes API client to use for deployment.
            verbose (bool, optional): If True, enables verbose output during deployment. Defaults to False.

        Returns:
            list: A list of created Kubernetes API objects.

        Notes:
            The create_from_yaml function will fail with AlreadyExists if the resources already exist in the cluster.
            This is unavoidable until https://github.com/kubernetes-client/python/pull/2252 is available in a release.
            Once it is, apply=True can be passed to create_from_yaml to trigger a server-side apply.
        """
        with NamedTemporaryFile("w+", suffix=self.output_file_extension) as f:
            f.write(self.synth_yaml())
            f.seek(0)
            resources = create_from_yaml(
                k8s_client=client, yaml_file=f.name, verbose=verbose, apply=True
            )
        return resources
