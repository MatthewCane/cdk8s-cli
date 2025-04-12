from argparse import ArgumentParser, Namespace
from os import environ


def _parse_args() -> Namespace:
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
    parser.add_argument("--verbose", action="store_true", help="enable verbose output")
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
    if args := environ.get("TEST_ARGS_OVERRIDE"):
        # Used to pass arguments to the CLI when running tests
        return parser.parse_args(args.split(" "))
    return parser.parse_args()
