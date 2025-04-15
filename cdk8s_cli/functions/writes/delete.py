from argparse import Namespace
from kubernetes import client
from pathlib import Path
from typing import Optional
from cdk8s import App
from cdk8s_cli.functions.internals.get_client import get_api_client
from cdk8s_cli.functions.internals.synth import _synth_app


def _delete(
    app: App,
    name: Optional[str],
    output_dir: Path,
    k8s_client: Optional[client.ApiClient],
    args: Namespace,
):
    raise NotImplementedError("Deleting is not implemented yet")

    k8s_client = get_api_client(k8s_client, args)

    _synth_app(app, name, output_dir)
