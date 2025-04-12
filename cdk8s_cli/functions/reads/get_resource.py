from kubernetes.dynamic import DynamicClient


def get_resource(client: DynamicClient, resource):
    resource_type = client.resources.get(
        api_version=resource.api_version,
        kind=resource.kind,
    )
    return resource_type.get(
        name=resource.metadata.name,
        namespace=resource.metadata.namespace,
    )
