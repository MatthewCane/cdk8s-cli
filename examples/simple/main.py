from cdk8s_cli.cdk8s_cli import CLIHandler, App
import cdk8s_plus_30 as kplus
from cdk8s import Chart, ApiObjectMetadata
from constructs import Construct


class ApplicationChart(Chart):
    def __init__(
        self,
        scope: Construct,
        id: str,
    ) -> None:
        super().__init__(scope, id)

        namespace = kplus.Namespace(
            self,
            id,
        )

        deployment = kplus.Deployment(
            self,
            "deployment",
            metadata=ApiObjectMetadata(namespace=namespace.name),
            replicas=1,
        )

        deployment.add_container(
            image="nginx",
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False, read_only_root_filesystem=False
            ),
            port_number=80,
        )

        deployment.expose_via_service(service_type=kplus.ServiceType.NODE_PORT)


def main():
    app = App(name="example")
    ApplicationChart(app, "chart")

    CLIHandler()


if __name__ == "__main__":
    main()
