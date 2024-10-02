from charts.application import ApplicationChart
from charts.redis import RedisChart
from config import ApplicationConfig, RedisConfig
from cdk8s_cli.cdk8s_cli import CLIHandler, App


def main():
    redis = App(name="redis")
    redis_config = RedisConfig()
    RedisChart(redis, config=redis_config)

    dev = App(name="dev")
    dev_config = ApplicationConfig()
    ApplicationChart(dev, "dev", config=dev_config)

    prod = App(name="prod")
    prod_config = ApplicationConfig(replicas=3)
    ApplicationChart(prod, "prod", config=prod_config)

    CLIHandler()


if __name__ == "__main__":
    main()
