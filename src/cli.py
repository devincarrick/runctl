from typing import Optional
import typer
from typing_extensions import Annotated
from pathlib import Path

from src.services.stryd import (
    StrydDataIngestionService,
    StrydDataValidator,
    S3Storage
)
from src.infra.localstack.config import LocalStackConfig

app = typer.Typer(
    name="runctl",
    help="Command line tool for running analytics and workout tracking",
    add_completion=False,
)

def validate_weight(value: Optional[float]) -> Optional[float]:
    """Validate weight parameter."""
    if value is None:
        return None
    if value <= 0:
        raise typer.BadParameter("Weight must be greater than 0")
    return value

def validate_critical_power(value: Optional[int]) -> Optional[int]:
    """Validate critical power parameter."""
    if value is None:
        return None
    if value <= 0:
        raise typer.BadParameter("Critical power must be greater than 0")
    return value

@app.command()
def analyze(
    workout_file: Annotated[str, typer.Argument()],
    format: Annotated[str, typer.Option("--format", "-f")] = "stryd",
    weight: Annotated[Optional[float], typer.Option("--weight", "-w", callback=validate_weight)] = None,
) -> None:
    """Analyze a workout file and display metrics."""
    file_path = Path(workout_file)
    
    if format != "stryd":
        typer.echo(f"Format {format} not supported yet")
        return
        
    if not file_path.exists():
        typer.echo(f"Error processing file: File {workout_file} does not exist", err=True)
        raise typer.Exit(1)
        
    # Prompt for weight if not provided
    while weight is None:
        try:
            input_weight = typer.prompt(
                "Enter athlete weight in kg",
                type=float,
                default=70.0
            )
            weight = validate_weight(input_weight)
            if weight is None:
                typer.echo("Weight must be greater than 0. Please try again.", err=True)
        except typer.BadParameter:
            typer.echo("Weight must be greater than 0. Please try again.", err=True)
            continue
    
    config = LocalStackConfig()
    storage = S3Storage(bucket_name="runctl-raw-data", endpoint_url=config.endpoint_url)
    validator = StrydDataValidator()
    service = StrydDataIngestionService(storage, validator, athlete_weight=weight)
    
    try:
        workouts = service.process_file(file_path)
        typer.echo(f"\nProcessed {len(workouts)} workouts")
        for workout in workouts:
            typer.echo(
                f"Average Power: {workout.average_power:.1f}W "
                f"({workout.average_power/weight:.1f} W/kg)"
            )
    except Exception as e:
        typer.echo(f"Error processing file: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def zones(
    critical_power: Annotated[Optional[int], typer.Option("--critical-power", "-c", callback=validate_critical_power)] = None,
) -> None:
    """Calculate and display training zones."""
    typer.echo("Calculating training zones...")

def main() -> None:
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()