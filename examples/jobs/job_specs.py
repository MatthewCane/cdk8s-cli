import cdk8s_plus_31 as kplus
from cdk8s import Chart, ApiObjectMetadata, Duration
from constructs import Construct


class BasicJobSpec(Chart):
    def __init__(
        self,
        scope: Construct,
        id: str,
        command: list[str],
        image: str = "busybox",
        namespace: str = "default",
    ):
        super().__init__(scope, id)

        job = kplus.Job(
            self,
            "job",
            ttl_after_finished=Duration.seconds(10),
            metadata=ApiObjectMetadata(namespace=namespace),
        )

        job.add_container(
            image=image,
            command=command,
            security_context=kplus.ContainerSecurityContextProps(ensure_non_root=False),
        )


class PythonJobs(Chart):
    def __init__(
        self,
        scope: Construct,
        id: str,
        scripts: dict[str, str],
        namespace: str = "default",
    ):
        super().__init__(scope, id)

        config_map = kplus.ConfigMap(
            self,
            "config-map",
            data={f"{name}.py": script for name, script in scripts.items()},
            metadata=ApiObjectMetadata(namespace=namespace),
        )
        volume = kplus.Volume.from_config_map(self, "volume", config_map)

        for name in scripts.keys():
            job = kplus.Job(
                self,
                name,
                ttl_after_finished=Duration.seconds(10),
                metadata=ApiObjectMetadata(namespace=namespace),
            )

            job.add_container(
                image="ghcr.io/astral-sh/uv:debian",
                command=[
                    "uv",
                    "run",
                    f"/scripts/{name}.py",
                ],
                security_context=kplus.ContainerSecurityContextProps(
                    ensure_non_root=False, read_only_root_filesystem=False
                ),
                volume_mounts=[
                    kplus.VolumeMount(volume=volume, path="/scripts", read_only=True),
                ],
                env_variables={"PYTHONUNBUFFERED": kplus.EnvValue.from_value("1")},
            )
