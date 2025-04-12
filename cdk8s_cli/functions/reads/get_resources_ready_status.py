from kubernetes.dynamic import DynamicClient, ResourceInstance
from cdk8s_cli.functions.reads.get_resource import get_resource


def get_resources_ready_status(
    resources: list[ResourceInstance],
    client: DynamicClient,
) -> dict[str, bool]:
    """
    Returns a dictionary of resources and their readiness status in the form of {resource_name: is_ready}.

    Does not handle fetching the resources from the cluster,
    just takes in a list of resource objects and validates their readiness status
    using the resource_is_healthy function.
    """
    # ToDo: Refactor to use a list of resource objects so the resource type and namespace
    # can be printed in the console to make it easier to see what resources are being checked
    # and where they can be found in the cluster.
    readiness: dict[str, bool] = {
        resource.metadata.name: False for resource in resources
    }
    for resource in resources:
        healthy = resource_is_healthy(get_resource(client, resource))
        if healthy:
            if not readiness[resource.metadata.name]:
                readiness[resource.metadata.name] = True
    return readiness


def resource_is_healthy(resource: ResourceInstance) -> bool:
    """
    Returns True if the resource is healthy, False otherwise.

    Does not handle fetching the resources from the cluster,
    just validates individual resources for their readiness status.
    """
    status = resource.status

    # No status is good status?
    if not status:
        return True

    # StatefulSet is ready if the number of ready replicas is equal to the number of replicas
    if resource.kind == "StatefulSet":
        return status.ready_replicas == status.replicas

    # If there are no conditions, the resource is ready
    if not status.conditions:
        return True

    good_conditions = ["Ready", "Succeeded", "Available"]
    for condition in status.conditions:
        if condition.type in good_conditions and condition.status == "True":
            return True

    return False
