import cdk8s_plus_31 as kplus
from cdk8s import ApiObjectMetadata, Chart
from constructs import Construct

from examples.complex.config import ApplicationConfig


class ApplicationChart(Chart):
    def __init__(
        self,
        scope: Construct,
        stage: str,
        config: ApplicationConfig,
    ) -> None:
        id = "demo-app-" + stage
        super().__init__(scope, id)

        namespace = kplus.Namespace(self, id)

        deployment = kplus.Deployment(
            self,
            "deployment",
            replicas=config.replicas,
            metadata=ApiObjectMetadata(namespace=namespace.name),
        )

        deployment.add_container(
            image="nginx",
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False, read_only_root_filesystem=False
            ),
            port_number=80,
        )

        deployment.expose_via_service(service_type=kplus.ServiceType.NODE_PORT)
