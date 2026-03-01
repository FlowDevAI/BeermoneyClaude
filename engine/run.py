"""
BeermoneyClaude — Entry Point

Usage:
    python run.py                  # Interactive menu
    python run.py --night          # Start night agent
    python run.py --test-browser   # Test browser setup
    python run.py --scan [platform]  # Force scan one/all platforms
    python run.py --status         # Show system status
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from core.browser import BrowserManager
from core.config import settings
from core.db import Database
from core.logger import get_logger
from core.scheduler import NightAgent

log = get_logger("cli")
console = Console()


async def test_browser() -> None:
    """Test that the browser works correctly."""
    console.print(Panel("Testing Browser Setup", style="blue"))

    browser = BrowserManager()
    try:
        await browser.init()
        page = await browser.get_page("test")
        await browser.safe_navigate(page, "https://www.google.com")

        title = await page.title()
        console.print(f"  Page title: {title}")

        screenshot = await browser.take_screenshot(page, "test", "browser_test")
        console.print(f"  Screenshot saved: {screenshot}")
        console.print("[green]  Browser working![/green]")
    except Exception as e:
        console.print(f"[red]  Browser test failed: {e}[/red]")
        log.error(f"Browser test failed: {e}")
    finally:
        await browser.close()


async def show_status() -> None:
    """Show system status overview."""
    console.print(Panel("System Status", style="cyan"))

    platforms_path = settings.DATA_DIR / "platforms.json"
    if not platforms_path.exists():
        console.print("[yellow]  platforms.json not found[/yellow]")
        return

    data = json.loads(platforms_path.read_text(encoding="utf-8"))
    platforms = data.get("platforms", [])

    table = Table(title="Platforms")
    table.add_column("#", style="dim", width=3)
    table.add_column("Platform", style="cyan")
    table.add_column("Tier", justify="center")
    table.add_column("Category", style="dim")
    table.add_column("Pay/h", justify="right")
    table.add_column("Plugin", justify="center")
    table.add_column("Active", justify="center")

    tier_colors = {1: "green", 2: "blue", 3: "yellow", 4: "dim"}

    for i, p in enumerate(platforms, 1):
        tier = p.get("tier", 4)
        color = tier_colors.get(tier, "dim")
        active = "[green]ON[/green]" if p.get("active") else "[dim]off[/dim]"
        plugin = p.get("plugin_status", "planned")
        pay = f"{p.get('avg_pay_min', '?')}-{p.get('avg_pay_max', '?')}"

        table.add_row(
            str(i),
            f"[{color}]{p['name']}[/{color}]",
            f"[{color}]{tier}[/{color}]",
            p.get("category", ""),
            pay,
            plugin,
            active,
        )

    console.print(table)

    # Queue status
    db = Database()
    pending = await db.get_pending_queue()
    console.print(f"\n  Pending human tasks: {len(pending)}")


async def run_night_agent() -> None:
    """Start the night agent."""
    console.print(
        Panel(
            "[bold]Night Agent Mode[/bold]\n"
            f"[dim]Active hours: {settings.NIGHT_START_HOUR}:00 - {settings.NIGHT_END_HOUR}:00[/dim]",
            style="magenta",
        )
    )
    agent = NightAgent()
    await agent.start()


async def interactive_menu() -> None:
    """Show interactive menu."""
    while True:
        console.print("\n[bold]What do you want to do?[/bold]\n")
        console.print("  1. Start Night Agent")
        console.print("  2. Test Browser")
        console.print("  3. Force Scan")
        console.print("  4. Status")
        console.print("  5. Exit\n")

        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            await run_night_agent()
        elif choice == "2":
            await test_browser()
        elif choice == "3":
            console.print("[yellow]  Force scan not yet implemented[/yellow]")
        elif choice == "4":
            await show_status()
        elif choice == "5":
            console.print("[dim]Goodbye![/dim]")
            break


async def main() -> None:
    parser = argparse.ArgumentParser(description="BeermoneyClaude Agent")
    parser.add_argument("--night", action="store_true", help="Start night agent")
    parser.add_argument("--test-browser", action="store_true", help="Test browser")
    parser.add_argument("--scan", nargs="?", const="all", help="Force scan")
    parser.add_argument("--status", action="store_true", help="Show status")
    args = parser.parse_args()

    # Banner
    console.print(
        Panel.fit(
            "[bold cyan]BeermoneyClaude[/bold cyan]\n"
            "[dim]Autonomous Beermoney Agent[/dim]",
            border_style="cyan",
        )
    )

    if args.test_browser:
        await test_browser()
    elif args.night:
        await run_night_agent()
    elif args.scan:
        console.print(f"[yellow]Force scan ({args.scan}) not yet implemented[/yellow]")
    elif args.status:
        await show_status()
    else:
        await interactive_menu()


if __name__ == "__main__":
    asyncio.run(main())
