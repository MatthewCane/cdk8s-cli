# CDK8S CLI

**A CLI helper for cdk8s.**

This is a work-in-progress project with no promise of continued support or development. This is not sutable for production applications.

## Features

This project provides a simple CLI to help with applying cdk8s charts.

## Usage

```python
# Import the dependencies
from cdk8s_cli.cdk8s_cli import cdk8s_cli
from cdk8s import App, Chart

# Construct your Apps and charts as you normally would:
app = App()
ApplicationChart(app, "simple-cdk8s-chart")

# Then call the CLI with:
cdk8s_cli(app)
```

That's it! You can now run your application with the desired flags

### Example CLI Usage

#### Synth all apps

```bash
python3 main.py synth
```

#### Deploy all apps

```bash
python3 main.py deploy
```

#### Deploy selected apps

```bash
python3 main.py deploy --apps dev prod
```

### Options

```text
usage: complex.py [-h] [--apps APPS [APPS ...]] [--context CONTEXT] [--verbose] [--unattended] {synth,apply}

A CLI for deploying CDK8s apps.

positional arguments:
  {synth,apply}         the action to perform. synth will synth the resources to the output directory. apply will apply the resources to the Kubernetes cluster

options:
  -h, --help            show this help message and exit
  --apps APPS [APPS ...]
                        the apps to apply. If supplied, unnamed apps will always be skipped
  --context CONTEXT     the Kubernetes context to use. Defaults to minikube
  --verbose             enable verbose output
  --unattended          enable unattended mode. This will not prompt for confirmation before applying
```

## Development

This project is built using:

- Poetry as the package manager
- Ruff for formatting and linting

### Features to be implemented

- [ ] Unit tests
- [ ] End-to-end tests
- [ ] Complete documentation
- [ ] Improve customisation
- [ ] Diff functionality

## Examples

Examples can be run using `poetry run python3 examples/<example>/<example>.py synth`

### Simple Example

[Link](examples/simple)

A very basic example containing a chart with a few simple resources in a single file deployed as a single stage.

### Complex Example

[Link](examples/complex)

A more complex example with multiple charts and multiple stages.
