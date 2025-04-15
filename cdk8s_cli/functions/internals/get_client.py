from typing import Optional
from kubernetes import client, config
from argparse import Namespace


def get_api_client(
    k8s_client: Optional[client.ApiClient], args: Namespace
) -> client.ApiClient:
    if not k8s_client:
        config.load_kube_config(
            config_file=args.kube_config_file, context=args.kube_context
        )
        k8s_client = client.ApiClient()
    return k8s_client
