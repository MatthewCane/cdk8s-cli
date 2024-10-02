# CDK8S CLI

**A CLI extension to cdk8s.**

This is a work-in-progress project with no promise of continued support or development. This is not sutable for production applications.

## Features

This provides extensions to standard cdk8s object to facilitate application deployments to a cluster without any external tooling using a simple CLI.

## Usage

WIP

## Development

This project is built using Poetry as the package manager.

## Examples

Examples can be run using `poetry run python3 examples/<example>/main.py synth --all`

### [Simple Example](examples/simple)
A very basic example containing a chart with a few simple resources in a single file deployed as a single stage.

### [Complex Example](examples/complex)
A more complex example with multiple charts and multiple stages.
