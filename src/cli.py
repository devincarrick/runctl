from typing import Optional
import typer
from typing_extensions import Annotated

app = typer.Typer(
    name="runctl",
    help="Command line tool for running analytics and workout tracking",
    add_completion=False,
)

@app.command()
def analyze(
    workout_file: Annotated[str, typer.Argument()],
    format: Annotated[str, typer.Option("--format", "-f")] = "stryd",
) -> None:
    """Analyze a workout file and display metrics."""
    typer.echo(f"Analyzing {workout_file} in {format} format...")

@app.command()
def zones(
    critical_power: Annotated[Optional[int], typer.Option("--critical-power", "-c")] = None,
) -> None:
    """Calculate and display training zones."""
    typer.echo("Calculating training zones...")

def main() -> None:
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()