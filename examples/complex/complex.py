from cdk8s import App
from charts.application import ApplicationChart
from config import ApplicationConfig

from cdk8s_cli.cdk8s_cli import cdk8s_cli


def main():
    dev = App()
    ApplicationChart(dev, "complex-example-dev", config=ApplicationConfig())

    prod = App()
    ApplicationChart(prod, "complex-example-prod", config=ApplicationConfig(replicas=3))

    cdk8s_cli(dev, name="dev")
    cdk8s_cli(prod, name="prod")


if __name__ == "__main__":
    main()
