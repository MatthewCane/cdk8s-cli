from time import sleep, time
from cdk8s import Duration
from kubernetes.dynamic import DynamicClient, ResourceInstance
from kubernetes import client
from argparse import Namespace
from cdk8s_cli.functions.reads.get_resources_ready_status import (
    get_resources_ready_status,
)
from cdk8s_cli.functions.internals.printing import (
    get_console,
    get_padding,
)


def validate(
    resources: list[ResourceInstance],
    k8s_client: client.ApiClient,
    args: Namespace,
):
    console = get_console()
    # The status check code is not feature complete and may not work with all resources
    console.print("[yellow]Warning: Validation mode is experimental.[/]")
    dynamic_client = DynamicClient(k8s_client)
    # Sleep for 1 second to allow the resources to be created
    sleep(1)
    readiness = get_resources_ready_status(resources, dynamic_client)
    TIMEOUT = Duration.minutes(args.validate_timeout_minutes)
    if args.debug:
        console.log("Timeout:", TIMEOUT.to_human_string())
    start_time = time()
    padding = get_padding(resources)
    # The whole proceeding status check context is very hard to read, needs to be refactored.
    with console.status(
        status="Waiting for reasources to report ready...\n  "
        + "\n  ".join(
            [
                f"[purple]{k + '[/]':{'.'}<{padding}}{'[green]Ready[/]' if v else '[red]Not Ready[/]'}"
                for k, v in readiness.items()
            ]
        )
    ):
        while not all(readiness.values()):
            sleep(1)
            readiness = get_resources_ready_status(resources, dynamic_client)
            if time() - start_time > TIMEOUT.to_seconds():
                console.print("[red]Timeout reached. Not all resources are ready.[/]")
                if args.verbose:
                    console.print(
                        "Timed out after waiting for", TIMEOUT.to_human_string()
                    )
                exit(1)

        console.print("[green]All resources are ready.[/]")
