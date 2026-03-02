"""
Test script for Clickworker plugin.
Runs in VISIBLE mode for manual verification.

Usage:
    python scripts/test_clickworker.py              # Full test
    python scripts/test_clickworker.py --login-only  # Just test login
    python scripts/test_clickworker.py --scan-only   # Just test scanning
"""

import asyncio
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright
from plugins.clickworker import ClickworkerPlugin


async def test_clickworker(mode: str = "full"):
    plugin = ClickworkerPlugin()
    print(f"\n{'='*60}")
    print(f"  CLICKWORKER PLUGIN TEST  (mode: {mode})")
    print(f"{'='*60}")
    print(f"  Plugin: {plugin}")
    print(f"  Login URL: {plugin.login_url}")
    print(f"  Dashboard URL: {plugin.dashboard_url}")
    print(f"{'='*60}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Europe/Madrid",
        )
        page = await context.new_page()

        # --- LOGIN TEST ---
        if mode in ("full", "login-only"):
            print("[TEST] Login flow...")
            print("  Navigating to Clickworker login page...")
            await page.goto(plugin.login_url, wait_until="networkidle", timeout=30000)
            print(f"  URL: {page.url}")

            # Check if already logged in
            is_logged = await plugin.is_logged_in(page)
            if is_logged:
                print("  [OK] Already logged in!")
            else:
                print("  Not logged in. Please log in manually in the browser.")
                print("  Waiting up to 5 minutes for login...")

                try:
                    await page.wait_for_url(
                        lambda url: (
                            "workplace.clickworker.com" in url
                            and "sign_in" not in url
                            and "/login" not in url
                            and "users/new" not in url
                        ),
                        timeout=300_000,
                    )
                    await asyncio.sleep(3)
                    await page.wait_for_load_state("networkidle")
                    print(f"  [OK] Login detected! URL: {page.url}")
                except Exception as e:
                    print(f"  [WARN] Login wait ended: {e}")
                    print(f"  Current URL: {page.url}")

            # Verify logged in state
            is_logged = await plugin.is_logged_in(page)
            print(f"  is_logged_in() = {is_logged}")

            # Try to get balance
            balance = await plugin.get_balance(page)
            print(f"  get_balance() = {balance}")

            if mode == "login-only":
                print("\n[LOGIN TEST COMPLETE]")
                print("  Browser stays open 60s for inspection.")
                await asyncio.sleep(60)
                await browser.close()
                return

        # --- SCAN TEST ---
        if mode in ("full", "scan-only"):
            if mode == "scan-only":
                print("[TEST] Navigating to Clickworker...")
                await page.goto(plugin.login_url, wait_until="networkidle", timeout=30000)

                is_logged = await plugin.is_logged_in(page)
                if not is_logged:
                    print("  Not logged in. Please log in manually.")
                    print("  Waiting up to 5 minutes...")
                    try:
                        await page.wait_for_url(
                            lambda url: (
                                "workplace.clickworker.com" in url
                                and "sign_in" not in url
                                and "/login" not in url
                                and "users/new" not in url
                            ),
                            timeout=300_000,
                        )
                        await asyncio.sleep(3)
                        await page.wait_for_load_state("networkidle")
                    except Exception:
                        pass

            print("\n[TEST] Scanning for jobs...")
            jobs = await plugin.scan_available_tasks(page)

            if not jobs:
                print("  No jobs found.")
                print("  (Check if account is activated and workplace is accessible)")
            else:
                print(f"\n  Found {len(jobs)} job(s):\n")
                print(f"  {'Title':<40} {'Pay':>8} {'Type':<10} {'Difficulty':<10}")
                print(f"  {'-'*40} {'-'*8} {'-'*10} {'-'*10}")
                for j in jobs:
                    job_type = j.details.get("job_type", "?")
                    print(
                        f"  {j.title[:40]:<40} "
                        f"EUR {j.estimated_pay:>5.2f} "
                        f"{job_type:<10} "
                        f"{j.difficulty.value:<10}"
                    )
                    if j.details.get("needs_assessment"):
                        print(f"    -> Requires assessment")

            if mode == "scan-only":
                print("\n[SCAN TEST COMPLETE]")
                print("  Browser stays open 60s for inspection.")
                await asyncio.sleep(60)
                await browser.close()
                return

        # --- FULL TEST ---
        if mode == "full" and jobs:
            print(f"\n[TEST] First job details:")
            print(f"  Title: '{jobs[0].title}'")
            print(f"  Pay: {jobs[0].currency} {jobs[0].estimated_pay}")
            print(f"  Type: {jobs[0].details.get('job_type', '?')}")
            print(f"  (Not starting automatically in test mode)")

        print(f"\n{'='*60}")
        print(f"  TEST COMPLETE")
        print(f"{'='*60}")
        print("  Browser stays open 60s for inspection.")
        await asyncio.sleep(60)
        await browser.close()


if __name__ == "__main__":
    mode = "full"
    if "--login-only" in sys.argv:
        mode = "login-only"
    elif "--scan-only" in sys.argv:
        mode = "scan-only"

    asyncio.run(test_clickworker(mode))
