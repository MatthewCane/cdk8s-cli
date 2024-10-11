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


def _parse_args() -> Namespace:
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
        "--context",
        default="minikube",
        type=str,
        help="the Kubernetes context to use. Defaults to minikube",
    )
    # parser.add_argument(
    #     "--kube-config-file",
    #     default=None,
    #     type=str,
    #     help="the path to a kubeconfig file",
    # )
    parser.add_argument("--verbose", action="store_true", help="enable verbose output")
    parser.add_argument(
        "--unattended",
        action="store_true",
        help="enable unattended mode. This will not prompt for confirmation before applying",
    )

    return parser.parse_args()


def _del_dir(path: Path):
    for p in path.iterdir():
        if p.is_dir():
            _del_dir(p)
            p.rmdir()
        else:
            p.unlink()


def _get_resource(client: DynamicClient, resource):
    resource_type = client.resources.get(
        api_version=resource.api_version,
        kind=resource.kind,
    )
    return resource_type.get(
        name=resource.metadata.name,
        namespace=resource.metadata.namespace,
    )


def _synth_app(app: App, console: Console, name: str, output_dir: Path):
    try:
        app.synth()
        console.print(
            f"Resources{' for app [purple]' + name + '[/purple]' if name else '' } synthed to {output_dir}"
        )
    except Exception as e:
        console.print("[red]ERROR SYNTHING RESOURCES[/red]", e)
        exit(1)


def _print_resources(resources: list[ResourceInstance], console: Console):
    pad = max([len(resource.metadata.name) for resource in resources])
    for resource in resources:
        ns = resource.metadata.namespace
        console.print(
            f"Resource [purple]{resource.metadata.name:<{pad}}[/purple] applied{ str(' in namespace [purple]'+ns+'[/purple]') if ns else ''}."
        )


def cdk8s_cli(
    app: App,
    name: Optional[str] = None,
    kube_context: str = "minikube",
    k8s_client: Optional[client.ApiClient] = None,
    verbose: bool = False,
):
    args = _parse_args()
    console = Console()
    if args.apps and name not in args.apps:
        console.print(f"[yellow]Skipping {'app '+name if name else 'unnamed app'}.[/]")
        return
    output_dir = Path(Path.cwd(), app.outdir).resolve()

    if args.action == "synth":
        _synth_app(app, console, name, output_dir)

    if args.action == "apply":
        _del_dir(output_dir)
        _synth_app(app, console, name, output_dir)

        if not args.unattended:
            if console.input(
                f"Deploy resources{' for app [purple]' + name + '[/purple]' if name else '' }? [bold]\\[y/N][/]: "
            ).lower() not in ["y", "yes"]:
                console.print("[yellow]Skipping.[/]")
                return

        if not k8s_client:
            config.load_kube_config(context=kube_context)
            k8s_client = client.ApiClient()

        resources = list()
        try:
            response = create_from_directory(
                k8s_client=k8s_client,
                yaml_dir=output_dir,
                verbose=args.verbose or verbose,
                namespace=None,
                apply=True,
            )
            resources: list[ResourceInstance] = list(
                collapse(response, base_type=ResourceInstance)
            )

        except FailToCreateError as e:
            for error in e.api_exceptions:
                body = loads(error.body)
                console.print("[red]ERROR DEPLOYING RESOURCES[/red]:", body)
                exit(body["code"])

        _print_resources(resources, console)

        # dynamic_client = DynamicClient(k8s_client)
        # with console.status(
        #     "Waiting for successful deployment...",
        #     spinner="dots",
        # ):
        #     for resource in resources:
        #         while status := _get_resource(dynamic_client, resource)["status"][
        #             "succeeded"
        #         ]:
        #             print(status)
        #             sleep(1)
        #         console.print(
        #             f"Resource [purple]{resource.metadata.name}[/purple] is ready."
        #         )
        console.print("[green]Apply complete[/green]")
