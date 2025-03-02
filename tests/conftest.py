from kubernetes import client, config
from pytest import fixture


@fixture(scope="session", autouse=True)
def check_kubernetes_connection():
    """
    Verify that the test suite can connect to the Kubernetes cluster
    and that minikube is the current context.
    """
    config.load_kube_config()
    k8s_client = client.ApiClient()
    assert k8s_client.configuration.host.startswith("https://127.0.0.1:")
    assert "minikube" in k8s_client.configuration.cert_file
    try:
        client.CoreV1Api().list_pod_for_all_namespaces()
    except Exception as e:
        raise Exception(f"Failed to connect to cluster: {e}")
