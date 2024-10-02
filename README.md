# CDK8S CLI

**A CLI extension to cdk8s.**

This is a work-in-progress project with no promise of continued support or development. This is not sutable for production applications.

## Features

This provides extensions to standard cdk8s object to facilitate application deployments to a cluster without any external tooling using a simple CLI.

## Usage

### Example CLI Usage

#### Synth all apps

```bash
python3 main.py synth --all
```

#### Synth selected apps

```bash
python3 main.py synth --apps dev prod
```

### Options

```text
positional arguments:
  {deploy,synth}        The action to perform.

options:
  -h, --help            show this help message and exit
  --apps APPS [APPS ...]
                        the apps to deploy in a space seperated list
  --all                 deploy all apps
  --context CONTEXT     The Kubernetes context to use. Defaults to minikube
  --kube-config-file KUBE_CONFIG_FILE
                        the path to a kubeconfig file
  --verbose             enable verbose output
```

## Development

This project is built using Poetry as the package manager.

## Examples

Examples can be run using `poetry run python3 examples/<example>/main.py synth --all`

### [Simple Example](examples/simple)
A very basic example containing a chart with a few simple resources in a single file deployed as a single stage.

### [Complex Example](examples/complex)
A more complex example with multiple charts and multiple stages.
