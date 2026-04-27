"""
PHANTOM MAILER — Beautiful CLI Interface
Rich terminal UI with live dashboard, progress tracking, and style.
"""

import sys
import time
import yaml
import random
import click
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.markdown import Markdown
from rich import box

from engine import PhantomEngine, SendResult
from templates import template_summary, get_template_names, get_all_categories, TEMPLATES
from renderer import MessageRenderer
from temp_mail import TempMailManager

console = Console()

# ═══════════════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════════════

BANNER = """
[bold red]
 ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ █████╗ ██████╗ ████████╗██╗  ██╗
██╔════╝ ██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██║  ██║
██║  ███╗███████║███████║██╔██╗ ██║   ██║   ███████║██████╔╝   ██║   ███████║
██║   ██║██╔══██║██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██╗   ██║   ██╔══██║
╚██████╔╝██║  ██║██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║   ██║   ██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
[/bold red]
[dim]                     ✦  Email Spam Framework  ✦  v2.0  ✦[/dim]
"""

SMALL_BANNER = "[bold red]♨ PHANTOM MAILER[/bold red] [dim]v2.0[/dim]"


# ═══════════════════════════════════════════════════════════════
#  CLI COMMANDS
# ═══════════════════════════════════════════════════════════════

@click.group()
@click.option("--config", "-c", default="config.yaml", help="Config file path")
@click.pass_context
def cli(ctx, config):
    """♨ PHANTOM MAILER — Email Spam Framework"""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    console.print(BANNER)


@cli.command()
@click.option("--count", "-n", default=None, type=int, help="Number of emails to send")
@click.option("--target", "-t", default=None, multiple=True, help="Target email(s)")
@click.option("--dry-run", "-d", is_flag=True, help="Dry run mode (no actual sends)")
@click.option("--workers", "-w", default=None, type=int, help="Number of parallel workers")
@click.option("--template", "-tpl", default=None, help="Specific template name")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def send(ctx, count, target, dry_run, workers, template, verbose):
    """🚀 Launch a spam campaign"""

    # Load config
    config = _load_config(ctx.obj["config_path"])

    # Override with CLI args
    if count:
        config["core"]["send_count"] = count
    if target:
        config["core"]["targets"] = list(target)
    if dry_run:
        config["core"]["dry_run"] = True
    if workers:
        config["core"]["max_workers"] = workers
    if template and template != "random":
        config["message"]["template_mode"] = template

    # Display campaign summary
    _show_campaign_summary(config)

    if not click.confirm("\n  Launch campaign?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    # Create and run engine
    engine = PhantomEngine(config)

    # Set up callbacks
    sent_count = [0]
    fail_count = [0]
    dry_count = [0]
    total = config["core"].get("send_count", 50)

    def on_send(result: SendResult):
        if result.status == "sent":
            sent_count[0] += 1
        elif result.status == "failed":
            fail_count[0] += 1
        elif result.status == "dry_run":
            dry_count[0] += 1

    def on_progress(current, total_n):
        pass  # Handled by Live display

    def on_status(msg):
        console.print(f"  {msg}")

    engine.on_send = on_send
    engine.on_progress = on_progress
    engine.on_status = on_status

    # Run with live dashboard
    is_dry = config["core"].get("dry_run", False)
    mode_str = "[yellow]DRY RUN[/yellow]" if is_dry else "[bold red]LIVE[/bold red]"

    with Live(_build_dashboard(engine, sent_count[0], fail_count[0], dry_count[0], total, mode_str),
              refresh_per_second=2, console=console) as live:

        def update_dashboard(result: SendResult):
            if result.status == "sent":
                sent_count[0] += 1
            elif result.status == "failed":
                fail_count[0] += 1
            elif result.status == "dry_run":
                dry_count[0] += 1
            live.update(_build_dashboard(engine, sent_count[0], fail_count[0], dry_count[0], total, mode_str))

        engine.on_send = update_dashboard
        engine.on_status = None  # Suppress text output during Live

        try:
            state = engine.run()
        except KeyboardInterrupt:
            engine.stop()
            console.print("\n[yellow]⚠ Campaign stopped by user[/yellow]")

    # Final summary
    _show_final_summary(engine, config)


@cli.command()
@click.pass_context
def templates(ctx):
    """📋 List all available scam templates"""
    console.print()
    console.print(Rule("[bold]Available Scam Templates[/bold]"))

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Name", style="cyan", width=22)
    table.add_column("Category", style="green", width=12)
    table.add_column("Urgency", width=12)
    table.add_column("Subjects", justify="right", width=8)
    table.add_column("Has Link", justify="center", width=8)

    for t in TEMPLATES:
        urgency_bar = "🔥" * t.urgency_level + "  " * (5 - t.urgency_level)
        table.add_row(
            t.name,
            t.category,
            urgency_bar,
            str(len(t.subject_pool)),
            "✓" if t.requires_link else "✗",
        )

    console.print(table)
    console.print(f"\n  [dim]Total: {len(TEMPLATES)} templates across {len(get_all_categories())} categories[/dim]")
    console.print(f"  [dim]Categories: {', '.join(get_all_categories())}[/dim]")
    console.print()


@cli.command()
@click.option("--template", "-t", default=None, help="Preview a specific template")
@click.option("--target", "-tgt", default="victim@example.com", help="Target email for preview")
@click.pass_context
def preview(ctx, template, target):
    """👁 Preview rendered email templates"""
    renderer = MessageRenderer()

    if template:
        from templates import get_template as gt
        tmpl = gt(name=template)
        templates_to_show = [tmpl]
    else:
        # Show 3 random templates
        templates_to_show = random.sample(TEMPLATES, min(3, len(TEMPLATES)))

    for tmpl in templates_to_show:
        subject, body_html, sender_email = renderer.render(
            tmpl, target,
            phishing_link="https://example.com/preview-link"
        )

        console.print()
        console.print(Rule(f"[bold cyan]{tmpl.name}[/bold cyan] ({tmpl.category})"))

        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column("Key", style="dim")
        info_table.add_column("Value", style="bold")
        info_table.add_row("From", sender_email)
        info_table.add_row("To", target)
        info_table.add_row("Subject", subject)
        info_table.add_row("Urgency", "🔥" * tmpl.urgency_level)
        console.print(info_table)

        # Show body (strip HTML for preview)
        import re
        clean = re.sub(r'<[^>]+>', '', body_html)
        clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        console.print(Panel(clean[:800] + ("..." if len(clean) > 800 else ""),
                          title="Body Preview", border_style="dim"))


@cli.command()
@click.option("--count", "-n", default=5, type=int, help="Number of accounts to generate")
@click.option("--provider", "-p", default="all", help="Provider to use")
@click.pass_context
def warmup(ctx, count, provider):
    """🔥 Warm up temp mail account pool"""
    console.print()
    console.print(Rule("[bold]Warming Up Temp Mail Pool[/bold]"))

    manager = TempMailManager(provider=provider)

    with console.status("[bold green]Generating accounts...[/bold green]") as status:
        accounts = manager.warm_up(count)

    # Display results
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Email", style="green", width=35)
    table.add_column("Provider", style="yellow", width=12)
    table.add_column("Max Sends", justify="right", width=10)
    table.add_column("Status", width=8)

    for i, acc in enumerate(accounts, 1):
        status_icon = "✅" if acc.alive else "❌"
        table.add_row(
            str(i), acc.email, acc.provider,
            str(acc.max_sends), status_icon,
        )

    console.print(table)
    console.print(f"\n  {manager.pool_status()}")


@cli.command()
@click.pass_context
def config_show(ctx):
    """⚙ Display current configuration"""
    config = _load_config(ctx.obj["config_path"])

    console.print()
    console.print(Rule("[bold]Current Configuration[/bold]"))

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    console.print(Panel(yaml_str, border_style="cyan", title="config.yaml"))


@cli.command()
@click.option("--campaign", "-c", default=None, help="Campaign name to resume")
@click.pass_context
def resume(ctx, campaign):
    """▶ Resume an interrupted campaign"""
    if campaign:
        state_file = Path.home() / ".phantom_mailer" / "campaigns" / f"{campaign}.json"
    else:
        # List available campaigns
        campaigns_dir = Path.home() / ".phantom_mailer" / "campaigns"
        if not campaigns_dir.exists():
            console.print("[yellow]No saved campaigns found.[/yellow]")
            return

        files = list(campaigns_dir.glob("*.json"))
        if not files:
            console.print("[yellow]No saved campaigns found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Campaign", style="green")
        table.add_column("Sent", justify="right")
        table.add_column("Failed", justify="right")
        table.add_column("Last Index", justify="right")
        table.add_column("Completed", justify="center")

        for f in files:
            try:
                import json
                with open(f) as fh:
                    data = json.load(fh)
                table.add_row(
                    data.get("name", f.stem),
                    str(data.get("sent", 0)),
                    str(data.get("failed", 0)),
                    str(data.get("last_index", -1)),
                    "✓" if data.get("completed") else "✗",
                )
            except Exception:
                pass

        console.print(table)
        console.print("\n  [dim]Use --campaign NAME to resume a specific campaign[/dim]")
        return

    if not state_file.exists():
        console.print(f"[red]Campaign file not found: {state_file}[/red]")
        return

    # Load config from saved state
    import json
    with open(state_file) as f:
        state_data = json.load(f)

    config = state_data.get("config", {})
    config["campaign"]["resume_file"] = str(state_file)

    console.print(f"[green]Resuming campaign: {campaign}[/green]")
    console.print(f"  Last sent index: {state_data.get('last_index', -1)}")

    engine = PhantomEngine(config)
    engine.run()


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _load_config(path: str) -> dict:
    """Load YAML config file."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        console.print(f"[yellow]Config not found at {path}, using defaults[/yellow]")
        return _default_config()
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        return _default_config()


def _default_config() -> dict:
    """Return minimal default config."""
    return {
        "core": {"send_count": 10, "targets": ["target@example.com"], "max_workers": 3, "dry_run": True},
        "timing": {"min_delay": 2.0, "max_delay": 5.0, "jitter": 0.3, "coffee_break_interval": 15, "coffee_break_min": 30, "coffee_break_max": 120},
        "temp_mail": {"provider": "all", "pre_generate": 5, "rotate_every": 3},
        "smtp": {"enabled": False, "servers": [], "rotate": True},
        "proxy": {"enabled": False, "list": [], "rotate_every": 5, "file": ""},
        "message": {"template_mode": "random", "locale": "en_US", "add_typo": True, "add_signature": True, "add_disclaimer": True, "add_urgency": True},
        "subject": {"mutate": True, "add_prefix": True, "add_emoji": True, "emoji_probability": 0.3},
        "campaign": {"auto_save_interval": 10, "resume_file": "", "name": "phantom_campaign"},
        "analytics": {"enabled": True, "live_dashboard": True, "save_report": True, "report_format": "json"},
        "logging": {"level": "INFO", "save_to_file": True, "log_file": "phantom.log"},
    }


def _show_campaign_summary(config: dict):
    """Display a beautiful campaign summary before launch."""
    core = config.get("core", {})
    timing = config.get("timing", {})
    mail = config.get("temp_mail", {})

    is_dry = core.get("dry_run", False)
    mode = "[yellow]DRY RUN[/yellow]" if is_dry else "[bold red]LIVE[/bold red]"

    summary = Table(show_header=False, box=box.ROUNDED, padding=(0, 2), border_style="cyan")
    summary.add_column("Key", style="dim", width=18)
    summary.add_column("Value", style="bold")

    summary.add_row("Mode", mode)
    summary.add_row("Emails", str(core.get("send_count", 50)))
    summary.add_row("Targets", ", ".join(core.get("targets", [])))
    summary.add_row("Workers", str(core.get("max_workers", 5)))
    summary.add_row("Template", config.get("message", {}).get("template_mode", "random"))
    summary.add_row("Temp Mail", mail.get("provider", "all"))
    summary.add_row("Delay Range", f"{timing.get('min_delay', 2)}s — {timing.get('max_delay', 8)}s")
    summary.add_row("Proxy", "✓" if config.get("proxy", {}).get("enabled") else "✗")
    summary.add_row("SMTP", "✓" if config.get("smtp", {}).get("enabled") else "✗ (simulate)")

    console.print()
    console.print(Rule("[bold]Campaign Summary[/bold]"))
    console.print(summary)


def _build_dashboard(engine: PhantomEngine, sent: int, failed: int, dry: int,
                      total: int, mode_str: str) -> Panel:
    """Build the live dashboard display."""
    progress_pct = ((sent + failed + dry) / max(1, total)) * 100

    # Progress bar (manual since we're in Live)
    bar_width = 30
    filled = int(bar_width * progress_pct / 100)
    bar = f"[bold green]{'█' * filled}[/bold green][dim]{'░' * (bar_width - filled)}[/dim]"

    # Stats table
    stats = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    stats.add_column("Label", style="dim", width=14)
    stats.add_column("Value", style="bold")

    stats.add_row("Mode", mode_str)
    stats.add_row("Progress", f"{bar} {progress_pct:.1f}%")
    stats.add_row("Sent", f"[green]{sent}[/green]")
    stats.add_row("Failed", f"[red]{failed}[/red]")
    if dry > 0:
        stats.add_row("Dry Run", f"[yellow]{dry}[/yellow]")
    stats.add_row("Total", str(total))

    pool = engine.temp_manager.pool_status()
    stats.add_row("Pool Alive", f"{pool.get('alive', 0)}/{pool.get('total', 0)}")

    return Panel(
        stats,
        title=f"[bold red]♨ PHANTOM MAILER[/bold red]",
        border_style="red",
        padding=(1, 2),
    )


def _show_final_summary(engine: PhantomEngine, config: dict):
    """Display final campaign results."""
    stats = engine.get_stats()

    console.print()
    console.print(Rule("[bold]Campaign Complete[/bold]"))

    table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2), border_style="green")
    table.add_column("Metric", style="dim", width=16)
    table.add_column("Value", style="bold")

    table.add_row("Total Processed", str(stats["total"]))
    table.add_row("Sent", f"[green]{stats['sent']}[/green]")
    table.add_row("Failed", f"[red]{stats['failed']}[/red]")
    table.add_row("Dry Run", f"[yellow]{stats['dry_run']}[/yellow]")
    table.add_row("Success Rate", str(stats["success_rate"]))
    table.add_row("Avg Duration", str(stats["avg_duration"]))

    pool = stats.get("pool", {})
    table.add_row("Pool Used", f"{pool.get('alive', 0)} alive / {pool.get('total', 0)} total")

    console.print(table)

    # Template distribution
    if engine.results:
        tmpl_counts = {}
        for r in engine.results:
            tmpl_counts[r.template] = tmpl_counts.get(r.template, 0) + 1

        tmpl_table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        tmpl_table.add_column("Template", style="green")
        tmpl_table.add_column("Count", justify="right", style="bold")

        for name, count in sorted(tmpl_counts.items(), key=lambda x: -x[1]):
            tmpl_table.add_row(name, str(count))

        console.print()
        console.print(Panel(tmpl_table, title="Template Distribution", border_style="cyan"))

    console.print(f"\n  [dim]Report saved to reports/ directory[/dim]")


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cli()
