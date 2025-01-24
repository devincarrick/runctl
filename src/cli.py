from typing import Optional
import typer

app = typer.Typer(
    name="runctl",
    help="Command line tool for running analytics and workout tracking",
    add_completion=False,
)

@app.command()
def analyze(
    workout_file: str = typer.Argument(..., help="Path to workout data file"),
    format: str = typer.Option("stryd", help="Data format (stryd, garmin, etc.)"),
) -> None:
    """Analyze a workout file and display metrics."""
    typer.echo(f"Analyzing {workout_file} in {format} format...")

@app.command()
def zones(
    critical_power: Optional[int] = typer.Option(None, help="Critical Power in watts"),
) -> None:
    """Calculate and display training zones."""
    typer.echo("Calculating training zones...")

if __name__ == "__main__":
    app()
