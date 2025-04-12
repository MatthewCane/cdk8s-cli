from argparse import Namespace
from pathlib import Path
from typing import Optional
from cdk8s import App
from kubernetes import config, client
from kubernetes.dynamic import ResourceInstance
from kubernetes.utils import FailToCreateError, create_from_directory
from more_itertools import collapse
from json import loads
from cdk8s_cli.functions.internals.synth import _synth_app
from cdk8s_cli.functions.internals.printing import (
    get_console,
    print_applied_resources,
)
from cdk8s_cli.functions.reads.validate import validate


def _apply(
    app: App,
    name: Optional[str],
    output_dir: Path,
    k8s_client: Optional[client.ApiClient],
    args: Namespace,
) -> None:
    """Applies the resources for the given app.

    Args:
        app (App): The app to apply.
        name (Optional[str]): The name of the app.
        output_dir (Path): The output directory.
        k8s_client (Optional[client.ApiClient]): The Kubernetes client.
        args (Namespace): The arguments passed to the CLI.
    """
    console = get_console()
    _synth_app(app, name, output_dir)

    if not args.unattended:
        if console.input(
            f"Deploy resources{' for app [purple]' + name + '[/purple]' if name else ''}? [bold]\\[y/N][/]: "
        ).lower() not in ["y", "yes"]:
            console.print("[yellow]Skipping.[/]")
            return

    # If a k8s client is not supplied, load the kubeconfig file
    if not k8s_client:
        config.load_kube_config(
            config_file=args.kube_config_file, context=args.kube_context
        )
        k8s_client = client.ApiClient()

    resources: list[ResourceInstance] = list()
    try:
        with console.status("Applying resources..."):
            response = create_from_directory(
                k8s_client=k8s_client,
                yaml_dir=output_dir,
                apply=True,
                namespace=None,
            )
            resources = list(collapse(response, base_type=ResourceInstance))

    except FailToCreateError as e:
        for error in e.api_exceptions:
            body = loads(error.body)
            console.print("[red]ERROR DEPLOYING RESOURCES[/red]:", body)
        raise e

    print_applied_resources(resources, args)

    if args.validate:
        validate(resources, k8s_client, args)

    console.print("[green]Apply complete[/green]")
