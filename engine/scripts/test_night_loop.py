"""
Test the Night Agent loop with a short cycle.
Runs a quick scan with all active plugins.

Usage:
    python scripts/test_night_loop.py              # 5 min test
    python scripts/test_night_loop.py --duration 1  # 1 min test
"""

import asyncio
import argparse
import sys
import io
import time
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.config import settings
from core.scheduler import NightAgent
from core.logger import get_logger

log = get_logger("test_night")
console = Console()


class TestNightAgent(NightAgent):
    """Night agent with overrides for testing."""

    def __init__(self, duration_minutes: int = 5):
        super().__init__()
        self.duration_minutes = duration_minutes
        self.test_start: float = 0
        self.scan_results: dict[str, list] = {}
        self.scan_errors: dict[str, str] = {}
        self.login_results: dict[str, bool] = {}

    def _is_active_time(self) -> bool:
        """Override: run for the specified duration regardless of time."""
        elapsed = time.time() - self.test_start
        remaining = (self.duration_minutes * 60) - elapsed
        if remaining <= 0:
            return False
        if int(remaining) % 30 == 0:
            log.info(f"Test time remaining: {int(remaining)}s")
        return True

    async def start(self) -> None:
        """Override start with test-specific behavior."""
        self.test_start = time.time()

        console.print(Panel(
            f"[bold]Night Agent Test[/bold]\n"
            f"Duration: {self.duration_minutes} min | "
            f"Headless: {settings.HEADLESS} | "
            f"Session: {self.session_id}",
            style="magenta",
        ))

        try:
            # Use visible browser for testing
            self.browser.headless = False

            await self.browser.init()
            self.plugins = self._load_active_plugins()

            if not self.plugins:
                console.print("[yellow]No active plugins found! Check platforms.json[/yellow]")
                await self.browser.close()
                return

            # Show loaded plugins
            table = Table(title="Loaded Plugins")
            table.add_column("Plugin", style="cyan")
            table.add_column("Tier", justify="center")
            table.add_column("Category")
            table.add_column("Check Interval")
            for p in self.plugins:
                table.add_row(
                    p.display_name,
                    str(p.tier),
                    p.category,
                    f"{p.check_interval}s",
                )
            console.print(table)

            # Login phase
            console.print("\n[bold]Phase 1: Login[/bold]")
            for plugin in self.plugins:
                try:
                    page = await self.browser.get_page(plugin.name)
                    console.print(f"  Logging into {plugin.display_name}...")
                    console.print(f"    URL: {plugin.login_url}")

                    await page.goto(plugin.login_url, wait_until="networkidle", timeout=30000)

                    is_logged = await plugin.is_logged_in(page)
                    if is_logged:
                        console.print(f"  [green]  {plugin.display_name}: Already logged in[/green]")
                        self.login_results[plugin.name] = True
                    else:
                        console.print(f"  [yellow]  {plugin.display_name}: Not logged in. Login manually![/yellow]")
                        console.print(f"    Waiting up to 3 minutes...")

                        try:
                            # Generic wait: URL changes from login page
                            await page.wait_for_url(
                                lambda url, p=plugin: (
                                    "/login" not in url
                                    and "sign_in" not in url
                                    and "auth0" not in url
                                    and "auth.prolific" not in url
                                    and "users/new" not in url
                                    and "accounts.google.com" not in url
                                ),
                                timeout=180_000,
                            )
                            await asyncio.sleep(2)
                            await page.wait_for_load_state("networkidle")
                            is_logged = await plugin.is_logged_in(page)
                            self.login_results[plugin.name] = is_logged
                            if is_logged:
                                console.print(f"    [green]Login successful![/green]")
                            else:
                                console.print(f"    [yellow]URL changed but login not confirmed[/yellow]")
                        except Exception as e:
                            console.print(f"    [red]Login timeout: {e}[/red]")
                            self.login_results[plugin.name] = False

                except Exception as e:
                    console.print(f"  [red]  {plugin.display_name}: Error: {e}[/red]")
                    self.login_results[plugin.name] = False

            # Scan phase
            console.print("\n[bold]Phase 2: Scan[/bold]")
            self.running = True

            for plugin in self.plugins:
                if not self.login_results.get(plugin.name, False):
                    console.print(f"  [dim]Skipping {plugin.display_name} (not logged in)[/dim]")
                    continue

                try:
                    page = await self.browser.get_page(plugin.name)
                    console.print(f"  Scanning {plugin.display_name}...")

                    tasks = await plugin.scan_available_tasks(page)
                    self.scan_results[plugin.name] = tasks

                    if tasks:
                        console.print(f"    [green]Found {len(tasks)} task(s)[/green]")
                        for t in tasks:
                            console.print(
                                f"      - {t.title[:50]} | "
                                f"{t.currency} {t.estimated_pay:.2f} | "
                                f"{t.difficulty.value}"
                            )
                    else:
                        console.print(f"    [dim]No tasks found[/dim]")

                except Exception as e:
                    console.print(f"    [red]Scan error: {e}[/red]")
                    self.scan_errors[plugin.name] = str(e)

            # Generate mini report
            self._print_report()

        except KeyboardInterrupt:
            console.print("\n[yellow]Test interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Test failed: {e}[/red]")
            log.error(f"Test failed: {e}")
        finally:
            await self.browser.close()

    def _print_report(self) -> None:
        """Print a summary report of the test."""
        elapsed = time.time() - self.test_start

        console.print(f"\n{'='*60}")
        console.print(Panel("[bold]Test Summary[/bold]", style="cyan"))

        # Login results
        table = Table(title="Login Results")
        table.add_column("Plugin", style="cyan")
        table.add_column("Status", justify="center")
        for name, success in self.login_results.items():
            status = "[green]OK[/green]" if success else "[red]FAILED[/red]"
            table.add_row(name, status)
        console.print(table)

        # Scan results
        total_tasks = sum(len(t) for t in self.scan_results.values())
        table = Table(title=f"Scan Results ({total_tasks} total tasks)")
        table.add_column("Plugin", style="cyan")
        table.add_column("Tasks Found", justify="center")
        table.add_column("Error", style="red")
        for plugin in self.plugins:
            tasks = self.scan_results.get(plugin.name, [])
            error = self.scan_errors.get(plugin.name, "")
            table.add_row(
                plugin.display_name,
                str(len(tasks)),
                error[:40] if error else "",
            )
        console.print(table)

        # Task details
        if total_tasks > 0:
            table = Table(title="Detected Tasks")
            table.add_column("Platform", style="cyan")
            table.add_column("Title")
            table.add_column("Pay", justify="right")
            table.add_column("Difficulty", justify="center")
            table.add_column("Urgency", justify="center")

            for name, tasks in self.scan_results.items():
                for t in tasks:
                    table.add_row(
                        name,
                        t.title[:40],
                        f"{t.currency} {t.estimated_pay:.2f}",
                        t.difficulty.value,
                        t.urgency.value,
                    )
            console.print(table)

        console.print(f"\n  Duration: {elapsed:.1f}s")
        console.print(f"  Plugins loaded: {len(self.plugins)}")
        console.print(f"  Logins successful: {sum(1 for v in self.login_results.values() if v)}/{len(self.login_results)}")
        console.print(f"  Total tasks found: {total_tasks}")
        console.print(f"  Scan errors: {len(self.scan_errors)}")
        console.print(f"{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Test Night Agent Loop")
    parser.add_argument("--duration", type=int, default=5, help="Test duration in minutes")
    args = parser.parse_args()

    agent = TestNightAgent(duration_minutes=args.duration)
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
