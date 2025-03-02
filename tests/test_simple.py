from pathlib import Path

import yaml
from kubernetes import client

from examples.simple.simple import main as simple_example


def test_simple_synth(capsys, monkeypatch):
    monkeypatch.setenv("TEST_ARGS_OVERRIDE", "synth")
    simple_example()
    out, err = capsys.readouterr()
    assert err == ""
    assert out == f"Resources synthed to {Path.cwd() / 'dist'}\n"

    output = Path(Path.cwd(), "dist", "simple-cdk8s-chart.k8s.yaml").resolve()
    assert output.exists()
    assert yaml.safe_load_all(output.open("r"))


def test_simple_list(capsys, monkeypatch):
    monkeypatch.setenv("TEST_ARGS_OVERRIDE", "list")
    simple_example()
    out, err = capsys.readouterr()
    assert err == ""
    assert out.startswith("Resources for app:")
    assert "Kind: Namespace" in out
    assert "Kind: Deployment" in out
    assert "Kind: Service" in out


def test_simple_apply(capsys, monkeypatch):
    monkeypatch.setenv("TEST_ARGS_OVERRIDE", "apply --unattended")
    simple_example()
    out, err = capsys.readouterr()
    assert err == ""
    assert out.startswith(f"Resources synthed to {Path.cwd() / 'dist'}\n")
    assert out.endswith("Apply complete\n")
    namespaces = client.CoreV1Api().list_namespace()
    # This test needs to be improved to check the namespace was created
    # and that the resources were created in the namespace, not just that
    # the namespace exists as it could already exist after being created by
    # a previous test run.
    assert "simple-cdk8s-chart" in str(
        [namespace.metadata.name for namespace in namespaces.items]
    )
