from pathlib import Path
import shutil
from typing import Optional
from cdk8s import App
from cdk8s_cli.functions.internals.errors import FailToSynthError
from cdk8s_cli.functions.internals.printing import get_console


def _synth_app(app: App, name: Optional[str], output_dir: Path) -> None:
    console = get_console()
    # Clean up the output directory
    shutil.rmtree(output_dir)

    with console.status(
        f"Synthing app{' for app [purple]' + name + '[/purple]' if name else ''}..."
    ):
        try:
            app.synth()
            console.print(
                f"Resources{' for app [purple]' + name + '[/purple]' if name else ''} synthed to {output_dir}"
            )
        except Exception as e:
            console.print("[red]ERROR SYNTHING RESOURCES[/red]", e)
            raise FailToSynthError(e)
