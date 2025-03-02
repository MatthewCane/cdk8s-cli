from cdk8s import App
from charts.application import ApplicationChart
from charts.redis import RedisChart
from config import ApplicationConfig, RedisConfig

from cdk8s_cli.cdk8s_cli import cdk8s_cli


def main():
    redis = App()
    redis_config = RedisConfig()
    RedisChart(redis, "redis-demo", config=redis_config)

    dev = App()
    ApplicationChart(dev, "dev", config=ApplicationConfig())

    prod = App()
    ApplicationChart(prod, "prod", config=ApplicationConfig(replicas=3))

    cdk8s_cli(redis, name="redis")
    cdk8s_cli(dev, name="dev")
    cdk8s_cli(prod, name="prod")


if __name__ == "__main__":
    main()
