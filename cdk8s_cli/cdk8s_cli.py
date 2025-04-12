from pathlib import Path

from typing import Optional

from cdk8s import App
from kubernetes import client
from kubernetes.config import KUBE_CONFIG_DEFAULT_LOCATION

from cdk8s_cli.functions.reads.list import _list
from cdk8s_cli.functions.reads.diff import _diff
from cdk8s_cli.functions.writes.apply import _apply
from cdk8s_cli.functions.internals.parse_args import _parse_args
from cdk8s_cli.functions.internals.synth import _synth_app


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
        args = _parse_args()

        # Override argument values if CLI values are supplied
        args.verbose = args.verbose or verbose or args.debug
        args.kube_context = args.kube_context or kube_context

        # If the user has supplied a list of apps to apply, skip unnamed apps
        if args.apps and name not in args.apps:
            self.console.print(
                f"[yellow]Skipping {'app ' + name if name else 'unnamed app'}.[/]"
            )
            return

        # Resolve the full output directory path
        output_dir = Path(Path.cwd(), app.outdir).resolve()

        if args.action == "synth":
            _synth_app(app, name, output_dir)

        if args.action == "list":
            _list(app, name, args)

        # Not implemented yet
        if args.action == "diff":
            _diff(app, name, args)

        if args.action == "apply":
            _apply(app, name, output_dir, k8s_client, args)
