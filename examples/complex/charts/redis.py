from cdk8s import Chart, Helm
import cdk8s_plus_31 as kplus
from constructs import Construct
from examples.complex.config import RedisConfig


class RedisChart(Chart):
    def __init__(self, scope: Construct, id: str, config: RedisConfig) -> None:
        super().__init__(scope, id)

        namespace = kplus.Namespace(self, id)

        Helm(
            self,
            "helm",
            chart="oci://registry-1.docker.io/bitnamicharts/redis",
            release_name="redis",
            namespace=namespace.name,
            values=config.values,
        )
