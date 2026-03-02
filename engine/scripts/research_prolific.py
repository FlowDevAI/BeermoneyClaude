"""
Script de investigacion para Prolific.
Abre el browser en modo VISIBLE (headless=False) para documentar:
- Flujo de login
- Estructura del dashboard de studies
- Selectores CSS reales
- Flujo de aceptacion de study

INSTRUCCIONES:
1. Ejecutar: python scripts/research_prolific.py
2. El browser se abre visible
3. Haz login manualmente en el browser
4. El script detecta automaticamente cuando la URL cambia (login OK)
5. Toma screenshots y documenta selectores
"""

import asyncio
import sys
import io
from playwright.async_api import async_playwright
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCREENSHOTS_DIR = Path("data/screenshots/prolific_research")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# File to write all findings
REPORT_PATH = SCREENSHOTS_DIR / "research_report.txt"


def log(msg: str):
    """Print and write to report."""
    print(msg)
    with open(str(REPORT_PATH), "a", encoding="utf-8") as f:
        f.write(msg + "\n")


async def research():
    # Clear report
    with open(str(REPORT_PATH), "w", encoding="utf-8") as f:
        f.write("=== PROLIFIC RESEARCH REPORT ===\n\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/Madrid",
        )
        page = await context.new_page()

        # 1. Ir al login
        log("\n[>] Navigating to Prolific login...")
        await page.goto("https://app.prolific.com/login", wait_until="networkidle")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_login_page.png"))
        log("[SCREENSHOT] 01_login_page.png")

        # 2. Inspeccionar selectores del login
        log("\n--- LOGIN FORM SELECTORS ---")
        selectors_to_check = [
            'input[type="email"]',
            'input[name="email"]',
            '#email',
            'input[id*="email"]',
            'input[placeholder*="email" i]',
            'input[data-testid*="email"]',
            'input[type="password"]',
            'input[name="password"]',
            '#password',
            'input[data-testid*="password"]',
            'button[type="submit"]',
            'button[data-testid*="login"]',
            'button[data-testid*="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            'button:has-text("Continue")',
            'button:has-text("Google")',
            'a[href*="google"]',
            '[data-provider="google"]',
        ]

        for sel in selectors_to_check:
            try:
                el = await page.query_selector(sel)
                if el:
                    tag = await el.evaluate("e => e.tagName")
                    text = await el.evaluate("e => e.textContent?.trim() || ''")
                    attrs = await el.evaluate("""e => {
                        const a = {};
                        for (const attr of e.attributes) a[attr.name] = attr.value;
                        return a;
                    }""")
                    log(f"  [OK] {sel}")
                    log(f"       Tag: {tag}, Text: '{text[:50]}'")
                    log(f"       Attrs: {attrs}")
            except Exception:
                pass

        # 3. Esperar a que haga login manualmente (detectar cambio de URL)
        log("\n" + "=" * 60)
        log("[WAITING] Haz login MANUALMENTE en el browser abierto.")
        log("  El script detectara automaticamente cuando estes logueado.")
        log("  Tienes 5 minutos...")
        log("=" * 60)

        try:
            # Wait until URL is no longer the login page (max 5 min)
            await page.wait_for_url(
                lambda url: "/login" not in url and "auth0" not in url,
                timeout=300_000,
            )
            # Give the page time to fully load after redirect
            await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            log(f"[TIMEOUT] Login wait timed out or error: {e}")
            log("[INFO] Continuing with whatever page is loaded...")

        current_url = page.url
        log(f"\n[URL] After login: {current_url}")

        # 4. Screenshot del dashboard
        await page.screenshot(
            path=str(SCREENSHOTS_DIR / "02_after_login.png"), full_page=True
        )
        log("[SCREENSHOT] 02_after_login.png")

        # 5. Inspeccionar estructura del dashboard
        log("\n--- DASHBOARD SELECTORS ---")
        dashboard_selectors = [
            # Study list containers
            '[data-testid*="study"]',
            '[data-testid*="task"]',
            '[class*="study"]',
            '[class*="Study"]',
            '[class*="task"]',
            "article",
            ".card",
            '[role="listitem"]',
            '[role="list"]',
            # Study details
            '[data-testid*="reward"]',
            '[data-testid*="time"]',
            '[data-testid*="places"]',
            '[class*="reward"]',
            '[class*="Reward"]',
            # Accept/Reserve button
            'button:has-text("Take part")',
            'button:has-text("Reserve")',
            'button:has-text("Start")',
            'button:has-text("Accept")',
            'a:has-text("Take part")',
            # Navigation
            "nav",
            '[data-testid*="nav"]',
            '[role="navigation"]',
            # User/profile indicators
            '[data-testid*="user"]',
            '[data-testid*="avatar"]',
            '[data-testid*="profile"]',
            '[class*="avatar"]',
            '[class*="Avatar"]',
            'img[alt*="avatar" i]',
            # Balance
            '[data-testid*="balance"]',
            '[class*="balance"]',
            '[class*="Balance"]',
            # Empty state
            '[data-testid*="empty"]',
            '[class*="empty"]',
            '[class*="Empty"]',
            ':text("no studies")',
            ':text("No studies")',
            ':text("check back")',
            ':text("Check back")',
            # Prolific-specific
            '[class*="Prolific"]',
            '[data-testid*="study-list"]',
            '[data-testid*="studies"]',
        ]

        for sel in dashboard_selectors:
            try:
                elements = await page.query_selector_all(sel)
                if elements:
                    log(f"\n  [OK] FOUND {len(elements)}x: {sel}")
                    for i, el in enumerate(elements[:3]):
                        tag = await el.evaluate("e => e.tagName")
                        text = await el.evaluate(
                            "e => e.textContent?.trim()?.substring(0, 100) || ''"
                        )
                        classes = await el.evaluate("e => e.className || ''")
                        test_id = await el.evaluate(
                            "e => e.getAttribute('data-testid') || ''"
                        )
                        log(
                            f"       [{i}] Tag: {tag}, data-testid: '{test_id}', "
                            f"Class: '{str(classes)[:80]}', Text: '{text[:60]}'"
                        )
            except Exception:
                pass

        # 6. Extraer HTML de la zona principal
        log("\n--- MAIN HTML STRUCTURE ---")
        try:
            main_html = await page.evaluate(
                """() => {
                const main = document.querySelector('main')
                    || document.querySelector('[role="main"]')
                    || document.querySelector('#root > div')
                    || document.body;
                const clone = main.cloneNode(true);
                clone.querySelectorAll('script, style, svg').forEach(e => e.remove());
                return clone.innerHTML.substring(0, 8000);
            }"""
            )
            with open(
                str(SCREENSHOTS_DIR / "dashboard_structure.html"), "w", encoding="utf-8"
            ) as f:
                f.write(main_html)
            log("  [SAVED] dashboard_structure.html")
        except Exception as e:
            log(f"  [ERROR] extracting HTML: {e}")

        # 7. Extraer todos los data-testid del DOM
        log("\n--- ALL data-testid ATTRIBUTES ---")
        try:
            test_ids = await page.evaluate(
                """() => {
                const els = document.querySelectorAll('[data-testid]');
                return [...els].map(e => ({
                    testid: e.getAttribute('data-testid'),
                    tag: e.tagName,
                    text: (e.textContent || '').trim().substring(0, 60)
                }));
            }"""
            )
            for item in test_ids:
                log(f"  data-testid=\"{item['testid']}\" <{item['tag']}> '{item['text'][:50]}'")
        except Exception as e:
            log(f"  [ERROR] {e}")

        # 8. Extraer todas las clases unicas relevantes
        log("\n--- RELEVANT CSS CLASSES ---")
        try:
            classes = await page.evaluate(
                """() => {
                const els = document.querySelectorAll('*');
                const classSet = new Set();
                els.forEach(e => {
                    if (e.className && typeof e.className === 'string') {
                        e.className.split(/\\s+/).forEach(c => {
                            if (c.match(/study|task|reward|place|time|part|accept|reserve|card|balance|empty|avatar|profile|nav/i)) {
                                classSet.add(c);
                            }
                        });
                    }
                });
                return [...classSet].sort();
            }"""
            )
            for cls in classes:
                log(f"  .{cls}")
        except Exception as e:
            log(f"  [ERROR] {e}")

        # 9. Intentar navegar a paginas de studies
        log(f"\n--- STUDY PAGE NAVIGATION ---")
        study_urls = [
            "https://app.prolific.com/studies",
            "https://app.prolific.com/participant/studies",
            "https://app.prolific.com/studies/active",
        ]

        for url in study_urls:
            try:
                log(f"\n[NAV] Trying: {url}")
                await page.goto(url, wait_until="networkidle", timeout=15000)
                final_url = page.url
                log(f"  Redirected to: {final_url}")
                screenshot_name = f"03_studies_{url.split('/')[-1]}.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / screenshot_name))
                log(f"  [SCREENSHOT] {screenshot_name}")

                # Check for studies on this page too
                study_els = await page.query_selector_all('[data-testid*="study"], article, .card, [role="listitem"]')
                log(f"  Potential study elements found: {len(study_els)}")
            except Exception as e:
                log(f"  [ERROR] {e}")

        # 10. Resumen final
        log("\n" + "=" * 60)
        log("[DONE] RESEARCH COMPLETE")
        log(f"Screenshots saved to: {SCREENSHOTS_DIR}")
        log(f"Full report: {REPORT_PATH}")
        log("\nFiles generated:")
        for f in sorted(SCREENSHOTS_DIR.iterdir()):
            log(f"  - {f.name}")
        log("=" * 60)

        # Mantener browser abierto 60 segundos mas para inspeccion
        log("\n[INFO] Browser stays open 60s for manual inspection (F12 for DevTools).")
        await asyncio.sleep(60)

        await browser.close()
        log("[INFO] Browser closed.")


asyncio.run(research())
