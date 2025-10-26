"""
CLI interface for iterata
"""

import click
from pathlib import Path
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


@click.group()
@click.version_option()
def cli():
    """iterata - Learn from human corrections to improve ML models"""
    pass


@cli.command()
@click.option("--path", default="./corrections", help="Base path for corrections")
@click.option("--name", default="my-project", help="Project name")
@click.option("--skill-path", default=None, help="Path for skill generation (optional)")
def init(path, name, skill_path):
    """Initialize a new iterata project"""
    from .loop import CorrectionLoop

    base_path = Path(path)
    base_path.mkdir(parents=True, exist_ok=True)

    # Initialize CorrectionLoop to create directory structure
    loop = CorrectionLoop(base_path=str(base_path), skill_path=skill_path)

    if RICH_AVAILABLE:
        console.print(f"\n[green]✓[/green] Initialized iterata project: [bold]{name}[/bold]")
        console.print(f"[dim]Location:[/dim] {base_path.absolute()}")
        if skill_path:
            console.print(f"[dim]Skill path:[/dim] {skill_path}")
    else:
        print(f"\n✓ Initialized iterata project: {name}")
        print(f"Location: {base_path.absolute()}")
        if skill_path:
            print(f"Skill path: {skill_path}")

    # Create a sample config file
    config_file = base_path / "iterata.yaml"
    if not config_file.exists():
        sample_config = f"""# iterata configuration
base_path: {path}
skill_path: {skill_path if skill_path else './my-skill'}
auto_explain: false
min_corrections_for_skill: 25

# Optional: Configure backend for auto-explanation
# backend:
#   provider: anthropic
#   api_key: ${{ANTHROPIC_API_KEY}}
#   model: claude-sonnet-4-5-20250929
"""
        with open(config_file, "w") as f:
            f.write(sample_config)

        if RICH_AVAILABLE:
            console.print(f"\n[green]✓[/green] Created config file: [dim]iterata.yaml[/dim]")
        else:
            print(f"\n✓ Created config file: iterata.yaml")


@cli.command()
@click.option(
    "--config",
    default="iterata.yaml",
    help="Config file",
    type=click.Path(exists=True),
)
@click.option("--detailed", is_flag=True, help="Show detailed statistics")
def stats(config, detailed):
    """Show statistics about corrections"""
    from .loop import CorrectionLoop

    try:
        loop = CorrectionLoop.from_config(config)
    except FileNotFoundError:
        if RICH_AVAILABLE:
            console.print(
                f"[red]Error:[/red] Config file not found: {config}", file=sys.stderr
            )
        else:
            print(f"Error: Config file not found: {config}", file=sys.stderr)
        sys.exit(1)

    if detailed:
        stats_data = loop.get_detailed_stats()
    else:
        stats_data = loop.get_stats()

    if RICH_AVAILABLE:
        _display_stats_rich(stats_data, detailed)
    else:
        _display_stats_plain(stats_data, detailed)


def _display_stats_rich(stats: dict, detailed: bool):
    """Display statistics using rich formatting"""
    # Main statistics table
    table = Table(title="Correction Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Corrections", str(stats["total_corrections"]))
    table.add_row("Explained", str(stats["corrections_explained"]))
    table.add_row("Pending", str(stats["corrections_pending"]))
    table.add_row("Patterns Detected", str(stats["patterns_count"]))
    table.add_row("Explanation Rate", f"{stats['correction_rate']:.1%}")

    console.print(table)

    # Categories
    if stats.get("categories"):
        console.print("\n[bold]Top Categories:[/bold]")
        for category, count in sorted(
            stats["categories"].items(), key=lambda x: x[1], reverse=True
        ):
            console.print(f"  • {category}: [bold]{count}[/bold]")

    # Top fields
    if stats.get("top_fields"):
        console.print("\n[bold]Top Fields with Corrections:[/bold]")
        for field, count in list(stats["top_fields"].items())[:5]:
            console.print(f"  • {field}: [bold]{count}[/bold]")

    # Detailed stats
    if detailed and stats.get("pattern_summary"):
        summary = stats["pattern_summary"]
        console.print("\n[bold]Pattern Summary:[/bold]")
        console.print(f"  High impact patterns: [bold]{summary['high_impact_count']}[/bold]")
        console.print(f"  Automatable patterns: [bold]{summary['highly_automatable_count']}[/bold]")

    # Recommendations
    if detailed and stats.get("recommendations"):
        recs = loop.get_recommendations() if 'loop' in locals() else []
        if recs:
            console.print("\n[bold]Recommendations:[/bold]")
            for i, rec in enumerate(recs[:3], 1):
                priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(
                    rec["priority"], "white"
                )
                console.print(
                    f"  {i}. [{priority_color}]{rec['priority'].upper()}[/{priority_color}] {rec['title']}"
                )


def _display_stats_plain(stats: dict, detailed: bool):
    """Display statistics in plain text"""
    print("\n=== Correction Statistics ===\n")
    print(f"Total Corrections: {stats['total_corrections']}")
    print(f"Explained: {stats['corrections_explained']}")
    print(f"Pending: {stats['corrections_pending']}")
    print(f"Patterns Detected: {stats['patterns_count']}")
    print(f"Explanation Rate: {stats['correction_rate']:.1%}")

    if stats.get("categories"):
        print("\nTop Categories:")
        for category, count in sorted(
            stats["categories"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  - {category}: {count}")

    if stats.get("top_fields"):
        print("\nTop Fields with Corrections:")
        for field, count in list(stats["top_fields"].items())[:5]:
            print(f"  - {field}: {count}")


@cli.command()
@click.option(
    "--config",
    default="iterata.yaml",
    help="Config file",
    type=click.Path(exists=True),
)
@click.option("--force", is_flag=True, help="Force update even if not enough corrections")
@click.option("--name", default=None, help="Custom skill name")
def update_skill(config, force, name):
    """Update the skill from corrections"""
    from .loop import CorrectionLoop

    try:
        loop = CorrectionLoop.from_config(config)
    except FileNotFoundError:
        if RICH_AVAILABLE:
            console.print(
                f"[red]Error:[/red] Config file not found: {config}", file=sys.stderr
            )
        else:
            print(f"Error: Config file not found: {config}", file=sys.stderr)
        sys.exit(1)

    # Check readiness
    readiness = loop.check_skill_readiness()

    if not readiness["ready"] and not force:
        if RICH_AVAILABLE:
            console.print(
                f"\n[yellow]⚠[/yellow]  Not ready to generate skill: {readiness['reason']}"
            )
            console.print(
                f"[dim]Use --force to generate anyway, or add more corrections.[/dim]"
            )
        else:
            print(f"\n⚠  Not ready to generate skill: {readiness['reason']}")
            print("Use --force to generate anyway, or add more corrections.")
        sys.exit(1)

    # Update skill
    if RICH_AVAILABLE:
        with Progress() as progress:
            task = progress.add_task("[cyan]Generating skill...", total=None)
            result = loop.update_skill(force=force, skill_name=name)
            progress.update(task, completed=True)
    else:
        print("Generating skill...")
        result = loop.update_skill(force=force, skill_name=name)

    if result["updated"]:
        if RICH_AVAILABLE:
            console.print("\n[green]✓[/green] Skill updated successfully")
            console.print(f"[dim]Skill file:[/dim] {result['skill_file']}")
            console.print(f"[dim]Total corrections:[/dim] {result['total_corrections']}")
            console.print(f"[dim]Patterns detected:[/dim] {result['patterns_detected']}")
        else:
            print("\n✓ Skill updated successfully")
            print(f"Skill file: {result['skill_file']}")
            print(f"Total corrections: {result['total_corrections']}")
            print(f"Patterns detected: {result['patterns_detected']}")
    else:
        if RICH_AVAILABLE:
            console.print(f"\n[yellow]✗[/yellow] {result['reason']}")
        else:
            print(f"\n✗ {result['reason']}")


@cli.command()
@click.option(
    "--config",
    default="iterata.yaml",
    help="Config file",
    type=click.Path(exists=True),
)
def check(config):
    """Check readiness for skill generation"""
    from .loop import CorrectionLoop

    try:
        loop = CorrectionLoop.from_config(config)
    except FileNotFoundError:
        if RICH_AVAILABLE:
            console.print(
                f"[red]Error:[/red] Config file not found: {config}", file=sys.stderr
            )
        else:
            print(f"Error: Config file not found: {config}", file=sys.stderr)
        sys.exit(1)

    readiness = loop.check_skill_readiness()

    if RICH_AVAILABLE:
        if readiness["ready"]:
            console.print("\n[green]✓ Ready to generate skill![/green]")
        else:
            console.print(f"\n[yellow]⚠ {readiness['reason']}[/yellow]")

        console.print(f"\n[dim]Corrections:[/dim] {readiness['corrections_count']}")
        console.print(f"[dim]Patterns:[/dim] {readiness['patterns_count']}")
        console.print(f"[dim]Minimum required:[/dim] {readiness['min_required']}")
    else:
        if readiness["ready"]:
            print("\n✓ Ready to generate skill!")
        else:
            print(f"\n⚠ {readiness['reason']}")

        print(f"\nCorrections: {readiness['corrections_count']}")
        print(f"Patterns: {readiness['patterns_count']}")
        print(f"Minimum required: {readiness['min_required']}")


if __name__ == "__main__":
    cli()
