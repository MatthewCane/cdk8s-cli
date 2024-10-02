import cdk8s_plus_30 as kplus
from cdk8s import Chart, Helm
from constructs import Construct
from examples.complex.config import RedisConfig


class RedisChart(Chart):
    def __init__(self, scope: Construct, config: RedisConfig) -> None:
        id = "demo-redis"
        super().__init__(scope, id)

        namespace = kplus.Namespace(
            self,
            id,
        )

        Helm(
            self,
            "helm",
            chart="oci://registry-1.docker.io/bitnamicharts/redis",
            release_name="redis",
            namespace=namespace.name,
            values=config.values,
        )
