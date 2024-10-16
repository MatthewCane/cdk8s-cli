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

class ApplicationChart(Chart):
  # Define cdk8s chart here
  ...

# Construct your Apps and charts as you normally would:
app = App()
ApplicationChart(app, "chart-name")

# Then call the CLI with:
cdk8s_cli(app)
```

That's it! You can now run your application with the desired flags

```bash
> python3 my-app.py apply
Resources synthed to /Users/exampleuser/project/my-project/dist
Deploy resources? [y/N]: y
Resource simple-cdk8s-chart-c81aeaa7                    applied.
Resource simple-cdk8s-chart-deployment-c83ea641         applied in namespace simple-cdk8s-chart-c81aeaa7.
Resource simple-cdk8s-chart-deployment-service-c8f17013 applied in namespace simple-cdk8s-chart-c81aeaa7.
Apply complete
```

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
positional arguments:
  {synth,apply}         the action to perform. synth will synth the resources to the output directory. apply will apply the resources to the Kubernetes cluster

options:
  -h, --help            show this help message and exit
  --apps APPS [APPS ...]
                        the apps to apply. If supplied, unnamed apps will always be skipped
  --kube-context KUBE_CONTEXT
                        the Kubernetes context to use. Defaults to minikube
  --kube-config-file KUBE_CONFIG_FILE
                        the path to a kubeconfig file
  --verbose             enable verbose output
  --unattended          enable unattended mode. This will not prompt for confirmation before applying
  --debug               enable debug mode. This will print debug information
  --validate            experimental feature. Will enable validation mode. This will wait for resources to report ready before exiting
  --validate-timeout-minutes VALIDATE_TIMEOUT_MINUTES
                        the number of minutes to wait for resources to report ready before timing out. Needs --validate to be set
```

## Development

This project is built using:

- Poetry as the package manager
- Ruff for formatting and linting

### Features to be implemented

- [ ] Unit tests
- [ ] End-to-end tests
  - Use the example projects for this
- [ ] Complete documentation
- [ ] Improve customisation
  - More inputs, more flexability
- [ ] Diff functionality
  - Similar to `kubectl diff`
- [ ] Destroy functionality
  - Similar to `kubectl delete`
- [x] List functionality
  - List all resources in an app
  - Useful, hierarchical view

## Examples

Examples can be run using `poetry run python3 examples/<example>/<example>.py synth`

### Simple Example

[Link](examples/simple)

A very basic example containing a chart with a few simple resources in a single file deployed as a single stage.

### Complex Example

[Link](examples/complex)

A more complex example with multiple charts and multiple stages.

### Jobs Example

[Link](examples/jobs)

An example job runner that executes Python scripts from a directory of scripts as jobs.
