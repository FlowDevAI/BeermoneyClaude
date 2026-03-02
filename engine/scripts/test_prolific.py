"""
Test script for Prolific plugin.
Runs in VISIBLE mode for manual verification.

Usage:
    python scripts/test_prolific.py              # Full test
    python scripts/test_prolific.py --login-only  # Just test login
    python scripts/test_prolific.py --scan-only   # Just test scanning
"""

import asyncio
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright
from plugins.prolific import ProlificPlugin


async def test_prolific(mode: str = "full"):
    plugin = ProlificPlugin()
    print(f"\n{'='*60}")
    print(f"  PROLIFIC PLUGIN TEST  (mode: {mode})")
    print(f"{'='*60}")
    print(f"  Plugin: {plugin}")
    print(f"  Login URL: {plugin.login_url}")
    print(f"  Dashboard URL: {plugin.dashboard_url}")
    print(f"{'='*60}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/Madrid",
        )
        page = await context.new_page()

        # --- LOGIN TEST ---
        if mode in ("full", "login-only"):
            print("[TEST] Login flow...")
            print("  Navigating to Prolific login page...")
            await page.goto(plugin.login_url, wait_until="networkidle", timeout=30000)
            print(f"  URL: {page.url}")

            # Check if already logged in (persistent session)
            is_logged = await plugin.is_logged_in(page)
            if is_logged:
                print("  [OK] Already logged in!")
            else:
                print("  Not logged in. Please log in manually in the browser.")
                print("  Waiting up to 5 minutes for login...")

                try:
                    await page.wait_for_url(
                        lambda url: "/login" not in url and "auth0" not in url and "auth.prolific" not in url,
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

            if mode == "login-only":
                print("\n[LOGIN TEST COMPLETE]")
                print("  Browser stays open 30s for inspection.")
                await asyncio.sleep(30)
                await browser.close()
                return

        # --- SCAN TEST ---
        if mode in ("full", "scan-only"):
            if mode == "scan-only":
                print("[TEST] Navigating to Prolific...")
                await page.goto(plugin.login_url, wait_until="networkidle", timeout=30000)

                is_logged = await plugin.is_logged_in(page)
                if not is_logged:
                    print("  Not logged in. Please log in manually.")
                    print("  Waiting up to 5 minutes...")
                    try:
                        await page.wait_for_url(
                            lambda url: "/login" not in url and "auth0" not in url and "auth.prolific" not in url,
                            timeout=300_000,
                        )
                        await asyncio.sleep(3)
                        await page.wait_for_load_state("networkidle")
                    except Exception:
                        pass

            print("\n[TEST] Scanning for studies...")
            studies = await plugin.scan_available_tasks(page)

            if not studies:
                print("  No studies found.")
                print("  (This is normal if there are no active studies right now)")
            else:
                print(f"\n  Found {len(studies)} study(ies):\n")
                print(f"  {'Title':<40} {'Pay':>8} {'Time':>6} {'Urgency':<10}")
                print(f"  {'-'*40} {'-'*8} {'-'*6} {'-'*10}")
                for s in studies:
                    print(
                        f"  {s.title[:40]:<40} "
                        f"{s.currency} {s.estimated_pay:>5.2f} "
                        f"{s.estimated_minutes:>4}m "
                        f"{s.urgency.value:<10}"
                    )
                    if s.details.get("places_remaining", -1) > 0:
                        print(f"    -> {s.details['places_remaining']} places remaining")

            if mode == "scan-only":
                print("\n[SCAN TEST COMPLETE]")
                print("  Browser stays open 30s for inspection.")
                await asyncio.sleep(30)
                await browser.close()
                return

        # --- FULL TEST: accept ---
        if mode == "full" and studies:
            print(f"\n[TEST] Would you like to accept the first study?")
            print(f"  Study: '{studies[0].title}'")
            print(f"  Pay: {studies[0].currency} {studies[0].estimated_pay}")
            print(f"  (Not accepting automatically in test mode)")

        print(f"\n{'='*60}")
        print(f"  TEST COMPLETE")
        print(f"{'='*60}")
        print("  Browser stays open 30s for inspection.")
        await asyncio.sleep(30)
        await browser.close()


if __name__ == "__main__":
    mode = "full"
    if "--login-only" in sys.argv:
        mode = "login-only"
    elif "--scan-only" in sys.argv:
        mode = "scan-only"

    asyncio.run(test_prolific(mode))
