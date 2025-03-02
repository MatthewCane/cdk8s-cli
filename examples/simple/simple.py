from cdk8s_cli.cdk8s_cli import cdk8s_cli
import cdk8s_plus_31 as kplus
from cdk8s import App, Chart, ApiObjectMetadata
from constructs import Construct


class ApplicationChart(Chart):
    def __init__(
        self,
        scope: Construct,
        id: str,
    ) -> None:
        super().__init__(scope, id)

        namespace = kplus.Namespace(self, id)

        deployment = kplus.Deployment(
            self,
            "deployment",
            replicas=1,
            metadata=ApiObjectMetadata(namespace=namespace.name),
        )

        deployment.add_container(
            image="nginx",
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False, read_only_root_filesystem=False
            ),
            port_number=80,
        )

        deployment.expose_via_service(
            service_type=kplus.ServiceType.LOAD_BALANCER,
        )


def main():
    app = App()
    ApplicationChart(app, "simple-cdk8s-chart")

    cdk8s_cli(app)


if __name__ == "__main__":
    main()
