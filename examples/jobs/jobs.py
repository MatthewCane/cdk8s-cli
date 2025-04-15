from pathlib import Path

from cdk8s import App


from cdk8s_cli.cdk8s_cli import cdk8s_cli
from examples.jobs.job_specs import BasicJobSpec, PythonJobs


def main():
    namespace = "example-jobs"
    app = App()

    BasicJobSpec(app, "hello", namespace=namespace, command=["echo", "hello, world"])

    # Load all Python scripts from the examples/jobs/scripts directory
    # into a dictionary
    scripts = {
        script.stem: script.read_text()
        for script in Path("examples/jobs/scripts").resolve().iterdir()
        if script.is_file() and script.suffix == ".py"
    }

    # Pass scripts to the PythonJobs chart which will create a Job for each
    # script. The script code will be stored in a ConfigMap and mounted as a
    # volume in each Job's container. This will then be run using uv and takes
    # advantage of inline script metadata for dependency management.
    PythonJobs(
        app,
        "python-jobs",
        namespace=namespace,
        scripts=scripts,
    )

    cdk8s_cli(app, name="jobs")


if __name__ == "__main__":
    main()
