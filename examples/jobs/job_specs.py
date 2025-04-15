import cdk8s_plus_31 as kplus
from cdk8s import Chart, Duration, Size
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
        super().__init__(scope, id, namespace=namespace)

        job = kplus.Job(
            self,
            "job",
            ttl_after_finished=Duration.seconds(10),
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
        super().__init__(scope, id, namespace=namespace)

        config_map = kplus.ConfigMap(
            self,
            "config-map",
            data={f"{name}.py": script for name, script in scripts.items()},
        )
        volume = kplus.Volume.from_config_map(self, "volume", config_map)

        for name in scripts.keys():
            job = kplus.Job(
                self,
                name,
                ttl_after_finished=Duration.seconds(30),
            )

            job.add_container(
                image="ghcr.io/astral-sh/uv:debian",
                command=[
                    "uv",
                    "run",
                    f"/scripts/{name}.py",
                ],
                resources=kplus.ContainerResources(
                    cpu=kplus.CpuResources(limit=kplus.Cpu.millis(250)),
                    memory=kplus.MemoryResources(limit=Size.mebibytes(256)),
                ),
                security_context=kplus.ContainerSecurityContextProps(
                    ensure_non_root=False, read_only_root_filesystem=False
                ),
                volume_mounts=[
                    kplus.VolumeMount(volume=volume, path="/scripts", read_only=True),
                ],
                env_variables={"PYTHONUNBUFFERED": kplus.EnvValue.from_value("1")},
            )
