import cdk8s_plus_31 as kplus
from cdk8s import App, Chart
from constructs import Construct
from cdk8s_cli.cdk8s_cli import cdk8s_cli
from cdk8s import Size, Duration


class ApplicationChart(Chart):
    def __init__(
        self,
        scope: Construct,
        id: str,
    ) -> None:
        super().__init__(scope, id, namespace=id)

        # Create a service account
        service_account = kplus.ServiceAccount(
            self,
            "service-account",
            automount_token=True,
        )

        # Create a role
        role = kplus.ClusterRole(
            self,
            "role",
        )

        # Allow the role to read deployments
        role.allow_read(
            kplus.ApiResource.PODS,
        )

        # Bind the role to the service account
        role.bind(service_account)

        # Define the deployment with the service account and automount token enabled
        deployment = kplus.Deployment(
            self,
            "deployment",
            replicas=1,
            service_account=service_account,
            automount_service_account_token=True,
        )

        # Define the readiness and liveness probes
        ready_liveness_probe = kplus.Probe.from_command(
            command=[
                "kubectl",
                "get",
                "pods",
            ],
            initial_delay_seconds=Duration.seconds(1),
        )

        # Define the container running kubectl using the service account
        # token to access the cluster API
        deployment.add_container(
            image="bitnami/kubectl",
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False, read_only_root_filesystem=False
            ),
            resources=kplus.ContainerResources(
                cpu=kplus.CpuResources(limit=kplus.Cpu.millis(250)),
                memory=kplus.MemoryResources(limit=Size.mebibytes(256)),
            ),
            command=["kubectl", "get", "pods", "--all-namespaces", "-w"],
            readiness=ready_liveness_probe,
            startup=ready_liveness_probe,
        )


def main():
    app = App()
    ApplicationChart(app, "service-account-cdk8s-chart")

    cdk8s_cli(app, name="service-account")


if __name__ == "__main__":
    main()
