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

@app.command()
def analyze(
    workout_file: Annotated[str, typer.Argument()],
    format: Annotated[str, typer.Option("--format", "-f")] = "stryd",
) -> None:
    """Analyze a workout file and display metrics."""
    file_path = Path(workout_file)
    
    if format == "stryd":
        config = LocalStackConfig()
        storage = S3Storage(bucket_name="runctl-raw-data", endpoint_url=config.endpoint_url)
        validator = StrydDataValidator()
        service = StrydDataIngestionService(storage, validator)
        
        try:
            workouts = service.process_file(file_path)
            typer.echo(f"Successfully processed {len(workouts)} workouts")
        except Exception as e:
            typer.echo(f"Error processing file: {str(e)}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(f"Format {format} not supported yet")

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