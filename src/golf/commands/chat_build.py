"""Interactive build command for GolfMCP."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from golf.core.config import load_settings, find_project_root
from golf.commands.build import build_project

console = Console()


def chat_build(output_dir: Optional[str] = None) -> None:
    """Interactively gather settings and build the project.

    Args:
        output_dir: Directory to output the built project (defaults to ./dist)
    """
    project_root, _ = find_project_root()
    if not project_root:
        console.print(
            "[bold red]Error: No GolfMCP project found in the current directory or any parent directory.[/bold red]"
        )
        console.print("Run 'golf init <project_name>' to create a new project.")
        raise typer.Exit(code=1)

    settings = load_settings(project_root)

    console.print("[bold green]Interactive build configuration[/bold green]")

    name = typer.prompt("Project name", default=settings.name)
    description = typer.prompt("Description", default=settings.description or "")
    host = typer.prompt("Server host", default=settings.host)
    port = typer.prompt("Server port", default=str(settings.port))
    build_env = typer.prompt("Build environment (dev/prod)", default="prod")
    copy_env = typer.confirm(
        "Copy environment variables into build?", default=(build_env == "dev")
    )

    if output_dir is None:
        output_path = project_root / "dist"
    else:
        output_path = Path(output_dir)

    # Update settings with answers
    settings.name = name
    settings.description = description
    settings.host = host
    try:
        settings.port = int(port)
    except ValueError:
        console.print("[yellow]Invalid port; using existing value.[/yellow]")

    build_project(project_root, settings, output_path, build_env=build_env, copy_env=copy_env)
    console.print("[bold green]Build complete.[/bold green]")
