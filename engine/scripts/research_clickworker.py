"""
Script de investigacion para Clickworker.
Abre el browser en modo VISIBLE (headless=False) para documentar:
- Flujo de login
- Estructura del workplace (dashboard de tareas)
- Selectores CSS reales
- Seccion UHRS
- Tipos de tareas disponibles

INSTRUCCIONES:
1. Ejecutar: PYTHONPATH=. python scripts/research_clickworker.py
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

SCREENSHOTS_DIR = Path("data/screenshots/clickworker_research")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = SCREENSHOTS_DIR / "research_report.txt"


def log(msg: str):
    """Print and write to report."""
    print(msg)
    with open(str(REPORT_PATH), "a", encoding="utf-8") as f:
        f.write(msg + "\n")


async def research():
    # Clear report
    with open(str(REPORT_PATH), "w", encoding="utf-8") as f:
        f.write("=== CLICKWORKER RESEARCH REPORT ===\n\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Europe/Madrid",
        )
        page = await context.new_page()

        # ============================================================
        # PHASE 1: Marketing site login page
        # ============================================================
        log("\n[PHASE 1] Navigating to Clickworker login...")

        # Try the main login page first
        login_urls = [
            "https://www.clickworker.com/en/clickworker?login=1",
            "https://workplace.clickworker.com/en/account/login",
            "https://www.clickworker.com/login",
        ]

        login_url_used = None
        for url in login_urls:
            log(f"  Trying: {url}")
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=15000)
                final_url = page.url
                log(f"  -> Landed on: {final_url} (status: {response.status if response else '?'})")
                if response and response.status < 400:
                    login_url_used = final_url
                    break
            except Exception as e:
                log(f"  -> Error: {e}")

        if not login_url_used:
            log("[WARN] None of the login URLs worked. Trying workplace directly...")
            await page.goto("https://workplace.clickworker.com/", wait_until="networkidle", timeout=15000)
            login_url_used = page.url

        log(f"\n[LOGIN PAGE] Final URL: {login_url_used}")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_login_page.png"))
        log("[SCREENSHOT] 01_login_page.png")

        # ============================================================
        # PHASE 2: Inspect login form selectors
        # ============================================================
        log("\n--- LOGIN FORM SELECTORS ---")
        login_selectors = [
            # Email/username fields
            'input[type="email"]',
            'input[name="email"]',
            'input[name="user[email]"]',
            'input[name="username"]',
            'input[name="user[login]"]',
            '#user_email',
            '#user_login',
            '#email',
            'input[id*="email"]',
            'input[id*="login"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="mail" i]',
            'input[autocomplete="email"]',
            'input[autocomplete="username"]',
            # Password fields
            'input[type="password"]',
            'input[name="password"]',
            'input[name="user[password]"]',
            '#user_password',
            '#password',
            'input[id*="password"]',
            # Submit buttons
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Anmelden")',
            'input[value*="Log" i]',
            'input[value*="Sign" i]',
            # OAuth
            'a[href*="google"]',
            'button:has-text("Google")',
            'a[href*="facebook"]',
            'a[href*="oauth"]',
            # Remember me
            'input[type="checkbox"]',
            'input[name*="remember"]',
            # Forgot password
            'a[href*="forgot"]',
            'a[href*="reset"]',
            'a:has-text("Forgot")',
        ]

        for sel in login_selectors:
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
                    log(f"  [FOUND] {sel}")
                    log(f"          Tag: {tag}, Text: '{text[:50]}'")
                    log(f"          Attrs: {attrs}")
            except Exception:
                pass

        # Extract all form elements
        log("\n--- ALL FORM ELEMENTS ---")
        try:
            form_els = await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input, button[type="submit"], select, textarea');
                return [...inputs].map(e => ({
                    tag: e.tagName,
                    type: e.type || '',
                    name: e.name || '',
                    id: e.id || '',
                    placeholder: e.placeholder || '',
                    value: e.value || '',
                    className: (typeof e.className === 'string' ? e.className : '').substring(0, 80),
                }));
            }""")
            for el in form_els:
                log(f"  <{el['tag']} type='{el['type']}' name='{el['name']}' "
                    f"id='{el['id']}' placeholder='{el['placeholder']}' "
                    f"class='{el['className'][:60]}'>")
        except Exception as e:
            log(f"  [ERROR] {e}")

        # ============================================================
        # PHASE 3: Wait for manual login
        # ============================================================
        log("\n" + "=" * 60)
        log("[WAITING] Haz login MANUALMENTE en el browser abierto.")
        log("  El script detectara cuando estes en el workplace/dashboard.")
        log("  Tienes 5 minutos...")
        log("=" * 60)

        try:
            await page.wait_for_url(
                lambda url: "workplace.clickworker.com" in url and "/login" not in url,
                timeout=300_000,
            )
            await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle")
            log(f"[OK] Login detected! URL: {page.url}")
        except Exception as e:
            log(f"[TIMEOUT] Login wait: {e}")
            log(f"[INFO] Current URL: {page.url}")
            log("[INFO] Continuing with current page...")

        current_url = page.url
        log(f"\n[URL] After login: {current_url}")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "02_after_login.png"), full_page=True)
        log("[SCREENSHOT] 02_after_login.png")

        # ============================================================
        # PHASE 4: Inspect workplace dashboard
        # ============================================================
        log("\n--- DASHBOARD / WORKPLACE SELECTORS ---")
        dashboard_selectors = [
            # Job/task containers
            '[class*="job"]',
            '[class*="Job"]',
            '[class*="task"]',
            '[class*="Task"]',
            '[id*="job"]',
            '[id*="task"]',
            '[data-testid*="job"]',
            '[data-testid*="task"]',
            'table',
            'table tbody tr',
            '.table',
            'article',
            '.card',
            '[role="listitem"]',
            '[role="list"]',
            '[role="row"]',
            # Specific workplace elements
            '[class*="workplace"]',
            '[class*="Workplace"]',
            '[class*="hitapp"]',
            '[class*="HitApp"]',
            '[class*="uhrs"]',
            '[class*="UHRS"]',
            # Navigation
            'nav',
            '[role="navigation"]',
            'nav a',
            '.sidebar',
            '[class*="sidebar"]',
            '[class*="Sidebar"]',
            '[class*="menu"]',
            '[class*="Menu"]',
            # User info
            '[class*="user"]',
            '[class*="User"]',
            '[class*="profile"]',
            '[class*="Profile"]',
            '[class*="avatar"]',
            '[class*="Avatar"]',
            # Balance/earnings
            '[class*="balance"]',
            '[class*="Balance"]',
            '[class*="earning"]',
            '[class*="Earning"]',
            '[class*="payment"]',
            '[class*="Payment"]',
            '[class*="account"]',
            # Status/empty state
            '[class*="empty"]',
            '[class*="Empty"]',
            '[class*="no-"]',
            ':text("no jobs")',
            ':text("No jobs")',
            ':text("no tasks")',
            ':text("No tasks")',
            ':text("currently no")',
            ':text("available")',
        ]

        for sel in dashboard_selectors:
            try:
                elements = await page.query_selector_all(sel)
                if elements:
                    log(f"\n  [FOUND] {len(elements)}x: {sel}")
                    for i, el in enumerate(elements[:5]):
                        tag = await el.evaluate("e => e.tagName")
                        text = await el.evaluate(
                            "e => e.textContent?.trim()?.substring(0, 100) || ''"
                        )
                        classes = await el.evaluate("e => e.className || ''")
                        el_id = await el.evaluate("e => e.id || ''")
                        log(f"       [{i}] <{tag}> id='{el_id}' "
                            f"class='{str(classes)[:80]}' "
                            f"text='{text[:60]}'")
            except Exception:
                pass

        # ============================================================
        # PHASE 5: Navigate to key workplace pages
        # ============================================================
        log("\n--- WORKPLACE PAGE NAVIGATION ---")
        workplace_urls = [
            ("jobs", "https://workplace.clickworker.com/en/jobs"),
            ("assessments", "https://workplace.clickworker.com/en/assessments"),
            ("account", "https://workplace.clickworker.com/en/account"),
            ("payments", "https://workplace.clickworker.com/en/payments"),
            ("dashboard", "https://workplace.clickworker.com/en/dashboard"),
            ("clickworker_profile", "https://www.clickworker.com/en/clickworker"),
        ]

        for name, url in workplace_urls:
            try:
                log(f"\n[NAV] {name}: {url}")
                await page.goto(url, wait_until="networkidle", timeout=15000)
                final_url = page.url
                log(f"  -> Landed on: {final_url}")

                screenshot_name = f"03_{name}.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / screenshot_name), full_page=True)
                log(f"  [SCREENSHOT] {screenshot_name}")

                # Count potential job elements on this page
                for sel in ['table tbody tr', 'article', '.card', '[role="listitem"]',
                            '[class*="job"]', '[class*="task"]', '[class*="hitapp"]']:
                    try:
                        els = await page.query_selector_all(sel)
                        if els:
                            log(f"  Found {len(els)}x '{sel}'")
                    except Exception:
                        pass

            except Exception as e:
                log(f"  [ERROR] {e}")

        # ============================================================
        # PHASE 6: Deep inspect the jobs page
        # ============================================================
        log("\n--- DEEP INSPECT: JOBS PAGE ---")
        try:
            await page.goto("https://workplace.clickworker.com/en/jobs",
                            wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)

            # Extract HTML structure of main content
            main_html = await page.evaluate("""() => {
                const main = document.querySelector('main')
                    || document.querySelector('[role="main"]')
                    || document.querySelector('#content')
                    || document.querySelector('.content')
                    || document.querySelector('#app')
                    || document.body;
                const clone = main.cloneNode(true);
                clone.querySelectorAll('script, style, svg, noscript').forEach(e => e.remove());
                return clone.innerHTML.substring(0, 15000);
            }""")
            with open(str(SCREENSHOTS_DIR / "jobs_page_structure.html"), "w", encoding="utf-8") as f:
                f.write(main_html)
            log("  [SAVED] jobs_page_structure.html")

            # Extract all links on the page
            log("\n  --- Links on jobs page ---")
            links = await page.evaluate("""() => {
                return [...document.querySelectorAll('a[href]')].map(a => ({
                    href: a.href,
                    text: (a.textContent || '').trim().substring(0, 60),
                    classes: (typeof a.className === 'string' ? a.className : '').substring(0, 60),
                }));
            }""")
            for link in links:
                if 'clickworker' in link['href'] or 'uhrs' in link['href'].lower():
                    log(f"  <a href='{link['href']}' class='{link['classes']}'>{link['text']}</a>")

            # Extract all buttons
            log("\n  --- Buttons on jobs page ---")
            buttons = await page.evaluate("""() => {
                return [...document.querySelectorAll('button, input[type="submit"], a.btn, [role="button"]')].map(b => ({
                    tag: b.tagName,
                    text: (b.textContent || '').trim().substring(0, 60),
                    type: b.type || '',
                    classes: (typeof b.className === 'string' ? b.className : '').substring(0, 80),
                    href: b.href || '',
                }));
            }""")
            for btn in buttons:
                log(f"  <{btn['tag']} type='{btn['type']}' class='{btn['classes']}'>{btn['text']}</a>")

        except Exception as e:
            log(f"  [ERROR] {e}")

        # ============================================================
        # PHASE 7: Look for UHRS section
        # ============================================================
        log("\n--- UHRS DETECTION ---")
        try:
            uhrs_selectors = [
                'a[href*="uhrs"]',
                'a[href*="UHRS"]',
                ':text("UHRS")',
                ':text("uhrs")',
                '[class*="uhrs"]',
                '[class*="UHRS"]',
                'a:has-text("UHRS")',
                'a:has-text("Microsoft")',
                ':text("Microsoft")',
            ]
            for sel in uhrs_selectors:
                try:
                    els = await page.query_selector_all(sel)
                    if els:
                        log(f"  [FOUND] {len(els)}x: {sel}")
                        for i, el in enumerate(els[:3]):
                            text = await el.evaluate("e => e.textContent?.trim()?.substring(0, 100) || ''")
                            href = await el.evaluate("e => e.href || e.getAttribute('href') || ''")
                            log(f"       [{i}] text='{text[:60]}' href='{href}'")
                except Exception:
                    pass
        except Exception as e:
            log(f"  [ERROR] {e}")

        # ============================================================
        # PHASE 8: Extract all data-testid and IDs
        # ============================================================
        log("\n--- ALL data-testid ATTRIBUTES ---")
        try:
            test_ids = await page.evaluate("""() => {
                const els = document.querySelectorAll('[data-testid]');
                return [...els].map(e => ({
                    testid: e.getAttribute('data-testid'),
                    tag: e.tagName,
                    text: (e.textContent || '').trim().substring(0, 60)
                }));
            }""")
            if test_ids:
                for item in test_ids:
                    log(f"  data-testid=\"{item['testid']}\" <{item['tag']}> '{item['text'][:50]}'")
            else:
                log("  (none found)")
        except Exception as e:
            log(f"  [ERROR] {e}")

        log("\n--- ALL IDs ---")
        try:
            ids = await page.evaluate("""() => {
                const els = document.querySelectorAll('[id]');
                return [...els].slice(0, 50).map(e => ({
                    id: e.id,
                    tag: e.tagName,
                    classes: (typeof e.className === 'string' ? e.className : '').substring(0, 60),
                }));
            }""")
            for item in ids:
                log(f"  #{item['id']} <{item['tag']}> class='{item['classes'][:50]}'")
        except Exception as e:
            log(f"  [ERROR] {e}")

        # ============================================================
        # PHASE 9: Relevant CSS classes
        # ============================================================
        log("\n--- RELEVANT CSS CLASSES ---")
        try:
            classes = await page.evaluate("""() => {
                const els = document.querySelectorAll('*');
                const classSet = new Set();
                els.forEach(e => {
                    if (e.className && typeof e.className === 'string') {
                        e.className.split(/\\s+/).forEach(c => {
                            if (c.match(/job|task|work|hit|uhrs|reward|pay|earn|balance|start|accept|begin|assess|qualif|avail|empty|card|table|list/i)) {
                                classSet.add(c);
                            }
                        });
                    }
                });
                return [...classSet].sort();
            }""")
            for cls in classes:
                log(f"  .{cls}")
        except Exception as e:
            log(f"  [ERROR] {e}")

        # ============================================================
        # PHASE 10: Summary
        # ============================================================
        log("\n" + "=" * 60)
        log("[DONE] CLICKWORKER RESEARCH COMPLETE")
        log(f"Screenshots saved to: {SCREENSHOTS_DIR}")
        log(f"Full report: {REPORT_PATH}")
        log("\nFiles generated:")
        for f in sorted(SCREENSHOTS_DIR.iterdir()):
            log(f"  - {f.name}")
        log("=" * 60)

        # Keep browser open for manual inspection
        log("\n[INFO] Browser stays open 120s for manual inspection (F12 for DevTools).")
        log("[INFO] Use this time to explore the workplace and check UHRS.")
        await asyncio.sleep(120)

        await browser.close()
        log("[INFO] Browser closed.")


asyncio.run(research())
