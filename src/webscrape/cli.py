"""CLI entry point: scrape, validate, list-configs with rich output."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from webscrape.config import ConfigError, load_config
from webscrape.scraper import scrape

console = Console()


@click.group()
@click.version_option(package_name="webscrape")
def cli() -> None:
    """webscrape — async web scraper with rich CLI output."""


@cli.command()
@click.argument("config_path", type=click.Path(exists=True))
def run(config_path: str) -> None:
    """Run a scrape job from a YAML config file."""
    try:
        config = load_config(config_path)
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        sys.exit(1)

    console.print(f"[bold blue]Running scrape:[/bold blue] {config.name}")
    console.print(f"  Base URL: {config.base_url}")
    console.print(f"  URLs: {len(config.urls)}")
    console.print(f"  Parser: {config.selectors.parser}")
    console.print(f"  Export: {config.export.format} → {config.export.output}")
    console.print()

    with console.status("[bold green]Scraping...[/bold green]"):
        result = asyncio.run(scrape(config))

    table = Table(title="Scrape Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("URLs Scraped", str(result.urls_scraped))
    table.add_row("Items Found", str(result.items_found))
    table.add_row("Errors", str(result.errors))
    table.add_row("Duration", f"{result.duration:.2f}s")
    console.print(table)

    if result.errors > 0:
        console.print(f"[yellow]Completed with {result.errors} error(s)[/yellow]")
    else:
        console.print("[green]Completed successfully![/green]")


@cli.command()
@click.argument("config_path", type=click.Path(exists=True))
def validate(config_path: str) -> None:
    """Validate a scrape config without running it."""
    try:
        config = load_config(config_path)
    except ConfigError as e:
        console.print(f"[red]Invalid config:[/red] {e}")
        sys.exit(1)

    table = Table(title=f"Config: {config.name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Name", config.name)
    table.add_row("Base URL", config.base_url)
    table.add_row("URLs", str(len(config.urls)))
    table.add_row("Parser", config.selectors.parser)
    table.add_row("Items Selector", config.selectors.items)
    table.add_row("Fields", str(len(config.selectors.fields)))
    table.add_row("Pagination", str(config.pagination.enabled))
    table.add_row("Rate Limit", f"{config.rate_limit.requests_per_second} req/s")
    table.add_row("Max Retries", str(config.retry.max_attempts))
    table.add_row("Export Format", config.export.format)
    table.add_row("Output", config.export.output)
    console.print(table)
    console.print("[green]Config is valid![/green]")


@cli.command("list-configs")
@click.option("--dir", "config_dir", default="./configs", help="Directory containing config files.")
def list_configs(config_dir: str) -> None:
    """List available scrape configs in a directory."""
    config_path = Path(config_dir)
    if not config_path.is_dir():
        console.print(f"[red]Directory not found:[/red] {config_dir}")
        sys.exit(1)

    yaml_files = sorted(config_path.glob("*.yaml")) + sorted(config_path.glob("*.yml"))
    if not yaml_files:
        console.print(f"[yellow]No config files found in {config_dir}[/yellow]")
        return

    table = Table(title="Available Configs")
    table.add_column("File", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Base URL", style="blue")
    table.add_column("Format", style="magenta")

    for yaml_file in yaml_files:
        try:
            config = load_config(yaml_file)
            table.add_row(yaml_file.name, config.name, config.base_url, config.export.format)
        except ConfigError:
            table.add_row(yaml_file.name, "[red]INVALID[/red]", "", "")

    console.print(table)


if __name__ == "__main__":
    cli()
