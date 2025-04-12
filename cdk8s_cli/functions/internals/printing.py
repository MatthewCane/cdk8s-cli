from kubernetes.dynamic import ResourceInstance
from rich.console import Console


def get_console():
    return Console()


def get_padding(resources: list[ResourceInstance]) -> int:
    """
    Get the padding required to align the resource names in the Rich console.
    """
    return max(
        [len(f"{resource.metadata.name} ({resource.kind})") for resource in resources]
    )


def print_applied_resources(
    resources: list[ResourceInstance],
    args,
) -> None:
    """
    Prints the resources that were applied to the Kubernetes cluster using the Rich console.
    """
    console = get_console()
    padding = get_padding(resources)
    for resource in resources:
        ns = resource.metadata.namespace
        console.print(
            f"Resource [purple]{f'{resource.metadata.name} ({resource.kind})':<{padding}}[/purple] applied{str(' in namespace [purple]' + ns + '[/purple]') if ns else ''}."
        )
        if args.verbose:
            console.print("[bold]Verbose resource details:[/]\n", resource)


def print_resources_ready(
    resources: list[ResourceInstance],
    args,
) -> None:
    """
    Prints the resources that were applied to the Kubernetes cluster using the Rich console.
    """
    console = get_console()
    padding = get_padding(resources)
    for resource in resources:
        console.print(
            f"Resource [purple]{f'{resource.metadata.name} ({resource.kind})':<{padding}}[/purple] is [green]ready[/]."
        )
        if args.verbose:
            console.print("[bold]Verbose resource details:[/]\n", resource)
