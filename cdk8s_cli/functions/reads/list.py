from argparse import Namespace
from typing import Optional
from cdk8s import App
from yaml import SafeLoader, load_all
from cdk8s_cli.functions.internals.printing import get_console


def _list(app: App, name: Optional[str], args: Namespace):
    console = get_console()
    # This is a very basic implementation and will need to be improved
    manifests = list(load_all(app.synth_yaml(), Loader=SafeLoader))
    console.print(
        f"Resources for app{' [purple]' + name + '[/purple]' if name else ''}:"
    )
    if args.debug:
        console.log("Manifests:", manifests)
    manifest_count = len(manifests)

    for n, manifest in enumerate(manifests):
        connector = "├──" if n < manifest_count - 1 else "└──"
        pipe = "│" if n < manifest_count - 1 else " "
        ns = manifest.get("metadata", {}).get("namespace", None)

        console.print(f"{connector} [purple]{manifest['metadata']['name']}[/]")
        console.print(f"{pipe}   ├── Kind: {manifest['kind']}")

        if ns:
            console.print(f"{pipe}   ├── Namespace: {ns}")

        if manifest["kind"] in ["Deployment", "StatefulSet"]:
            console.print(f"{pipe}   ├── Replicas: {manifest['spec']['replicas']}")

        if manifest["kind"] in ["Service"]:
            console.print(f"{pipe}   ├── Type: {manifest['spec']['type']}")
            console.print(
                f"{pipe}   ├── Ports: {', '.join([str(port['port']) for port in manifest['spec']['ports']])}"
            )

        # Leave this to last so the pipes match up without having to use
        # a conditional for the last item
        console.print(f"{pipe}   └── API Version: {manifest['apiVersion']}")
