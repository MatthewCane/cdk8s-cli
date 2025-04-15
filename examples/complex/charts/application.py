import cdk8s_plus_31 as kplus
from cdk8s import Chart, Size, Helm, Duration
from constructs import Construct

from examples.complex.config import ApplicationConfig


class ApplicationChart(Chart):
    def __init__(
        self,
        scope: Construct,
        id: str,
        config: ApplicationConfig,
    ) -> None:
        super().__init__(scope, id, namespace=id)

        VALKEY_SERVICE_NAME = "valkey-primary"

        # Create a secret for the valkey auth. The key must be REDISCLI_AUTH
        # for the redis-cli to pick up the password automatically.
        valkey_secret_value = "demo-app-secret"
        valkey_secret_key = "REDISCLI_AUTH"
        valkey_secret = kplus.Secret(
            self,
            "valkey-secret",
            string_data={valkey_secret_key: valkey_secret_value},
        )

        # Create a deployment for the application
        deployment = kplus.Deployment(
            self,
            "valkey-cli",
            replicas=config.replicas,
        )

        probe = kplus.Probe.from_command(
            command=["valkey-cli", "-h", VALKEY_SERVICE_NAME, "ping"],
            initial_delay_seconds=Duration.seconds(10),
        )

        # Create a container for valkey-cli. This is a simple container that
        # connects to the valkey instance and monitors the application.
        deployment.add_container(
            image="valkey/valkey",
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False, read_only_root_filesystem=False
            ),
            resources=kplus.ContainerResources(
                cpu=kplus.CpuResources(limit=kplus.Cpu.millis(250)),
                memory=kplus.MemoryResources(limit=Size.mebibytes(256)),
            ),
            env_from=[kplus.EnvFrom(sec=valkey_secret)],
            command=["valkey-cli", "-h", VALKEY_SERVICE_NAME, "monitor"],
            liveness=probe,
            readiness=probe,
        )

        # Create a helm chart for the valkey cluster
        Helm(
            self,
            "helm",
            chart="oci://registry-1.docker.io/bitnamicharts/valkey",
            release_name="valkey",
            namespace=id,
            values={
                "auth": {
                    "enabled": True,
                    "existingSecret": valkey_secret.name,
                    "existingSecretPasswordKey": valkey_secret_key,
                },
                "architecture": "standalone",
                "persistence": {
                    "enabled": False,
                },
            },
        )
