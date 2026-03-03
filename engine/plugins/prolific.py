"""
Prolific Plugin -- Tier 1 (Highest Priority)

Prolific is an academic research platform where studies fill up
in minutes. Speed of acceptance is CRITICAL.

IMPORTANT: This plugin prioritizes SPEED over stealth when accepting.
The scan phase uses normal humanized delays, but acceptance is turbo.

Login: Auth0 hosted page at auth.prolific.com
Frontend: Vue.js SPA
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import TYPE_CHECKING

from playwright.async_api import TimeoutError as PlaywrightTimeout

from plugins.base import (
    PlatformPlugin,
    LoginResult,
    DetectedTask,
    AcceptResult,
    TaskResult,
    TaskDifficulty,
    TaskUrgency,
)
from core.browser import BrowserManager, ElementNotFoundError
from core.logger import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Page

log = get_logger("prolific")

# GBP to EUR approximate conversion
GBP_TO_EUR = 1.16


class ProlificPlugin(PlatformPlugin):
    name = "prolific"
    display_name = "Prolific"
    url = "https://www.prolific.com"
    login_url = "https://app.prolific.com/login"
    dashboard_url = "https://app.prolific.com/studies"  # TODO: VERIFY URL after profile completion
    tier = 1
    category = "research"
    check_interval = 900  # 15 minutes
    currency = "GBP"

    # === SELECTORS (from research 2026-03-02) ===
    SELECTORS = {
        # --- Login (Auth0 hosted at auth.prolific.com) ---
        # Auth0 multi-step: first email, then password
        "login_email": 'input[name="username"]',  # TODO: VERIFY SELECTOR (Auth0 standard)
        "login_email_alt": 'input[type="email"]',  # fallback
        "login_password": '#password',  # VERIFIED
        "login_password_alt": 'input[type="password"]',  # VERIFIED (fallback)
        "login_submit": 'button[type="submit"]',  # VERIFIED (text: "Continue")
        "login_google": '[data-provider="google"]',  # VERIFIED

        # --- Logged in verification ---
        "user_indicator": '[data-testid*="user"]',  # TODO: VERIFY SELECTOR
        "user_indicator_alt": '[data-testid*="avatar"]',  # TODO: VERIFY SELECTOR
        "balance_indicator": '[data-testid*="balance"]',  # TODO: VERIFY SELECTOR

        # --- Waitlist / profile completion detection ---
        "waitlist_indicator": '[data-testid="progress-bar"]',  # VERIFIED (profile form)

        # --- Studies dashboard ---
        "study_card": '[data-testid*="study-card"]',  # TODO: VERIFY SELECTOR
        "study_card_alt": 'article',  # fallback
        "study_card_alt2": '[role="listitem"]',  # fallback
        "study_title": '[data-testid*="study-title"]',  # TODO: VERIFY SELECTOR
        "study_title_alt": 'h2, h3',  # fallback within card
        "study_reward": '[data-testid*="reward"]',  # TODO: VERIFY SELECTOR
        "study_time": '[data-testid*="time"]',  # TODO: VERIFY SELECTOR
        "study_places": '[data-testid*="places"]',  # TODO: VERIFY SELECTOR
        "take_part_button": 'button:has-text("Take part")',  # TODO: VERIFY SELECTOR
        "take_part_alt": 'a:has-text("Take part")',  # fallback
        "take_part_alt2": 'button:has-text("Reserve")',  # fallback

        # --- States ---
        "no_studies": ':text("No studies")',  # TODO: VERIFY SELECTOR
        "no_studies_alt": ':text("check back")',  # TODO: VERIFY SELECTOR
        "study_full": ':text("full")',  # TODO: VERIFY SELECTOR

        # --- Cookie consent (Orejime) ---
        "cookie_accept": 'button.orejime-Banner-saveButton',

        # --- CAPTCHA ---
        "captcha_recaptcha": 'iframe[src*="recaptcha"]',
        "captcha_cloudflare": '#cf-challenge-running',
    }

    def __init__(self, browser: BrowserManager | None = None) -> None:
        self.browser = browser

    # ================================================================
    # LOGIN
    # ================================================================

    async def login(self, page: Page) -> LoginResult:
        """Login to Prolific via Auth0."""
        log.info("Starting login flow...")

        try:
            # Navigate to login
            await page.goto(self.login_url, wait_until="networkidle", timeout=30000)
            screenshot_dir = "data/screenshots/prolific"
            log.info(f"Login page loaded: {page.url}")

            # Dismiss cookie consent if present
            await self._dismiss_cookies(page)

            # Check for CAPTCHA
            captcha = await self._detect_captcha(page)
            if captcha:
                log.warning(f"CAPTCHA detected on login: {captcha}")
                return LoginResult(
                    success=False,
                    needs_captcha=True,
                    error=f"CAPTCHA detected: {captcha}",
                )

            # Auth0 login: try email field
            email_filled = await self._try_fill_selector(
                page,
                [self.SELECTORS["login_email"], self.SELECTORS["login_email_alt"]],
                "",  # Will be filled from config
                field_name="email",
            )

            if not email_filled:
                log.error("Could not find email field on login page")
                return LoginResult(
                    success=False,
                    error="Email field not found. Login page may have changed.",
                )

            # Click continue (Auth0 may show password on next step)
            try:
                await page.click(self.SELECTORS["login_submit"], timeout=5000)
                await asyncio.sleep(2)
            except PlaywrightTimeout:
                log.debug("No submit button found after email, password may be on same page")

            # Fill password
            password_filled = await self._try_fill_selector(
                page,
                [self.SELECTORS["login_password"], self.SELECTORS["login_password_alt"]],
                "",  # Will be filled from config
                field_name="password",
            )

            if not password_filled:
                log.error("Could not find password field")
                return LoginResult(
                    success=False,
                    error="Password field not found.",
                )

            # Submit login
            try:
                await page.click(self.SELECTORS["login_submit"], timeout=5000)
            except PlaywrightTimeout:
                log.error("Submit button not found after password")
                return LoginResult(success=False, error="Submit button not found")

            # Wait for redirect (login success or error)
            log.info("Waiting for login redirect...")
            try:
                await page.wait_for_url(
                    lambda url: "auth.prolific.com" not in url and "/login" not in url,
                    timeout=30000,
                )
            except PlaywrightTimeout:
                log.error("Login redirect timed out")
                return LoginResult(
                    success=False,
                    error="Login redirect timed out. Check credentials or 2FA.",
                )

            await page.wait_for_load_state("networkidle")
            final_url = page.url
            log.info(f"Login redirect completed: {final_url}")

            # Check if landed on waitlist/profile page
            if "waitlist" in final_url or "register" in final_url:
                log.warning("Account is in waitlist/registration mode")
                return LoginResult(
                    success=True,
                    error="Account in waitlist - profile completion required",
                )

            return LoginResult(success=True)

        except Exception as e:
            log.error(f"Login failed with exception: {e}")
            return LoginResult(success=False, error=str(e))

    # ================================================================
    # IS LOGGED IN
    # ================================================================

    async def is_logged_in(self, page: Page) -> bool:
        """Check if logged into Prolific."""
        current_url = page.url

        # If on auth page, not logged in
        if "auth.prolific.com" in current_url or "/login" in current_url:
            return False

        # If on any app.prolific.com page that's not login, likely logged in
        if "app.prolific.com" in current_url:
            # Try to find user indicators
            for sel in [
                self.SELECTORS["user_indicator"],
                self.SELECTORS["user_indicator_alt"],
                self.SELECTORS["balance_indicator"],
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        log.debug(f"Logged in indicator found: {sel}")
                        return True
                except Exception:
                    continue

            # Waitlist page also means logged in (just not fully onboarded)
            if "waitlist" in current_url or "register" in current_url:
                log.debug("Logged in but in waitlist/registration")
                return True

            # If we're on app.prolific.com and didn't get redirected to login,
            # we're likely logged in even without finding specific indicators
            log.debug("On app.prolific.com, assuming logged in")
            return True

        return False

    # ================================================================
    # SCAN AVAILABLE TASKS
    # ================================================================

    async def scan_available_tasks(self, page: Page) -> list[DetectedTask]:
        """Scan for available studies on Prolific dashboard."""
        log.info("Scanning for available studies...")
        studies: list[DetectedTask] = []

        try:
            # Navigate to studies dashboard
            current_url = page.url
            if self.dashboard_url not in current_url:
                await page.goto(
                    self.dashboard_url, wait_until="domcontentloaded", timeout=30000
                )
                # Vue.js SPA needs extra time to hydrate and render studies
                await page.wait_for_timeout(5000)

            final_url = page.url
            log.info(f"Studies page URL: {final_url}")

            # Check if redirected to login
            if "auth.prolific.com" in final_url or "/login" in final_url:
                log.warning("Not logged in, redirected to login page")
                return []

            # Check if on waitlist
            if "waitlist" in final_url or "register" in final_url:
                log.warning("Account in waitlist, cannot scan studies")
                return []

            # Dismiss cookie consent if present
            await self._dismiss_cookies(page)

            # Check for empty state
            is_empty = await self._check_empty_state(page)
            if is_empty:
                log.info("No studies available (empty state detected)")
                return []

            # Find study cards
            cards = await self._find_study_cards(page)
            if not cards:
                log.info("No study cards found on page")
                return []

            log.info(f"Found {len(cards)} study card(s)")

            # Extract details from each card
            for i, card in enumerate(cards):
                try:
                    study = await self._extract_study_details(page, card, i)
                    if study:
                        studies.append(study)
                        log.info(
                            f"  Study {i+1}: '{study.title}' - "
                            f"{study.currency} {study.estimated_pay:.2f} - "
                            f"{study.estimated_minutes}min - "
                            f"Urgency: {study.urgency.value}"
                        )
                except Exception as e:
                    log.warning(f"  Error extracting study {i+1}: {e}")

        except Exception as e:
            log.error(f"Error scanning studies: {e}")

        log.info(f"Scan complete: {len(studies)} studies found")
        return studies

    # ================================================================
    # ACCEPT TASK (TURBO MODE)
    # ================================================================

    async def accept_task(self, page: Page, task: DetectedTask) -> AcceptResult:
        """
        Accept a study -- TURBO MODE.
        Minimal delays, speed is critical on Prolific.
        """
        log.info(f"TURBO ACCEPT: '{task.title}' ({task.currency} {task.estimated_pay})")

        try:
            # If we have a direct URL, navigate there
            if task.url:
                await page.goto(task.url, wait_until="networkidle", timeout=15000)
            else:
                # Navigate to dashboard and find the study
                await page.goto(
                    self.dashboard_url, wait_until="networkidle", timeout=15000
                )

            # Try to click "Take part" button - NO humanized delays
            take_part_clicked = False
            for sel in [
                self.SELECTORS["take_part_button"],
                self.SELECTORS["take_part_alt"],
                self.SELECTORS["take_part_alt2"],
            ]:
                try:
                    button = await page.wait_for_selector(sel, timeout=3000)
                    if button:
                        await button.click()
                        take_part_clicked = True
                        log.info(f"Clicked Take Part button: {sel}")
                        break
                except PlaywrightTimeout:
                    continue

            if not take_part_clicked:
                # Check if study is full
                is_full = await self._check_study_full(page)
                if is_full:
                    log.warning("Study is full")
                    return AcceptResult(
                        success=False,
                        error="Study is full - all places taken",
                    )

                log.error("Take Part button not found")
                return AcceptResult(
                    success=False,
                    error="Take Part button not found on page",
                )

            # Wait for redirect to external study or confirmation
            await asyncio.sleep(2)
            final_url = page.url
            log.info(f"After accept, URL: {final_url}")

            # Prolific studies redirect to external sites (Qualtrics, etc.)
            # The study is accepted when we leave Prolific
            is_external = "prolific.com" not in final_url

            return AcceptResult(
                success=True,
                needs_human=True,
                human_reason="External study requires human completion",
                human_instructions=(
                    f"Study '{task.title}' accepted and opened.\n"
                    f"URL: {final_url}\n"
                    f"Pay: {task.currency} {task.estimated_pay:.2f}\n"
                    f"Time: {task.estimated_minutes} minutes\n"
                    f"{'Redirected to external survey.' if is_external else 'Still on Prolific.'}"
                ),
            )

        except Exception as e:
            log.error(f"Error accepting study: {e}")
            return AcceptResult(success=False, error=str(e))

    # ================================================================
    # CLASSIFY TASK
    # ================================================================

    async def classify_task(self, task: DetectedTask) -> TaskDifficulty:
        """Almost all Prolific studies are HUMAN (external surveys)."""
        # Check for indicators of auto-completable tasks
        title_lower = task.title.lower()

        # Screeners might be semi-auto
        if any(kw in title_lower for kw in ["screener", "screening", "pre-screen"]):
            return TaskDifficulty.SEMI_AUTO

        # Everything else is human
        return TaskDifficulty.HUMAN

    # ================================================================
    # GET BALANCE
    # ================================================================

    async def get_balance(self, page: Page) -> float | None:
        """Fetch current Prolific balance."""
        try:
            for sel in [
                self.SELECTORS["balance_indicator"],
                '[class*="balance"]',
                '[class*="Balance"]',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        amount = self._parse_reward(text)
                        if amount > 0:
                            log.debug(f"Balance found: GBP {amount}")
                            return amount
                except Exception:
                    continue
        except Exception as e:
            log.debug(f"Could not fetch balance: {e}")
        return None

    # ================================================================
    # HELPERS
    # ================================================================

    async def _dismiss_cookies(self, page: Page) -> None:
        """Dismiss cookie consent banner if present."""
        try:
            cookie_btn = await page.query_selector(self.SELECTORS["cookie_accept"])
            if cookie_btn:
                await cookie_btn.click()
                log.debug("Cookie consent dismissed")
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def _detect_captcha(self, page: Page) -> str | None:
        """Check for CAPTCHA on current page."""
        for name, sel in [
            ("recaptcha", self.SELECTORS["captcha_recaptcha"]),
            ("cloudflare", self.SELECTORS["captcha_cloudflare"]),
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    return name
            except Exception:
                continue
        return None

    async def _try_fill_selector(
        self,
        page: Page,
        selectors: list[str],
        value: str,
        field_name: str = "",
    ) -> bool:
        """Try multiple selectors to fill a field. Returns True if successful."""
        for sel in selectors:
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el:
                    await el.fill(value)
                    log.debug(f"Filled {field_name}: {sel}")
                    return True
            except PlaywrightTimeout:
                continue
            except Exception as e:
                log.debug(f"Error filling {sel}: {e}")
                continue
        return False

    async def _check_empty_state(self, page: Page) -> bool:
        """Check if dashboard shows no-studies state."""
        for sel in [
            self.SELECTORS["no_studies"],
            self.SELECTORS["no_studies_alt"],
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    return True
            except Exception:
                continue
        return False

    async def _find_study_cards(self, page: Page) -> list:
        """Find study card elements using fallback selectors."""
        for sel in [
            self.SELECTORS["study_card"],
            self.SELECTORS["study_card_alt"],
            self.SELECTORS["study_card_alt2"],
        ]:
            try:
                cards = await page.query_selector_all(sel)
                if cards:
                    log.debug(f"Study cards found with: {sel} ({len(cards)} cards)")
                    return cards
            except Exception:
                continue
        return []

    async def _extract_study_details(
        self, page: Page, card, index: int
    ) -> DetectedTask | None:
        """Extract study details from a card element."""
        try:
            # Title
            title = ""
            for sel in [self.SELECTORS["study_title"], self.SELECTORS["study_title_alt"]]:
                try:
                    title_el = await card.query_selector(sel)
                    if title_el:
                        title = (await title_el.inner_text()).strip()
                        break
                except Exception:
                    continue

            if not title:
                # Fallback: get all text from card
                title = (await card.inner_text()).strip()[:100]

            # Reward
            reward = 0.0
            try:
                reward_el = await card.query_selector(self.SELECTORS["study_reward"])
                if reward_el:
                    reward_text = await reward_el.inner_text()
                    reward = self._parse_reward(reward_text)
            except Exception:
                pass

            # If no reward found, try to extract from card text
            if reward == 0.0:
                card_text = await card.inner_text()
                reward = self._parse_reward(card_text)

            # Time
            minutes = 0
            try:
                time_el = await card.query_selector(self.SELECTORS["study_time"])
                if time_el:
                    time_text = await time_el.inner_text()
                    minutes = self._parse_minutes(time_text)
            except Exception:
                pass

            if minutes == 0:
                card_text = await card.inner_text()
                minutes = self._parse_minutes(card_text)

            # Places remaining
            places = -1
            try:
                places_el = await card.query_selector(self.SELECTORS["study_places"])
                if places_el:
                    places_text = await places_el.inner_text()
                    places = self._parse_places(places_text)
            except Exception:
                pass

            # Determine urgency based on places
            urgency = TaskUrgency.CRITICAL  # Prolific is always critical (Tier 1)
            if places > 0 and places <= 5:
                urgency = TaskUrgency.CRITICAL
            elif places > 50:
                urgency = TaskUrgency.HIGH

            # External ID (try data attributes or link)
            external_id = None
            try:
                external_id = await card.get_attribute("data-study-id")
            except Exception:
                pass
            if not external_id:
                try:
                    link = await card.query_selector("a[href]")
                    if link:
                        href = await link.get_attribute("href")
                        if href and "/studies/" in href:
                            external_id = href.split("/studies/")[-1].split("/")[0].split("?")[0]
                except Exception:
                    pass

            # Study URL
            study_url = ""
            try:
                link = await card.query_selector("a[href]")
                if link:
                    study_url = await link.get_attribute("href") or ""
                    if study_url and not study_url.startswith("http"):
                        study_url = f"https://app.prolific.com{study_url}"
            except Exception:
                pass

            return DetectedTask(
                platform=self.name,
                external_id=external_id,
                title=title,
                estimated_pay=reward,
                currency=self.currency,
                estimated_minutes=minutes,
                difficulty=TaskDifficulty.HUMAN,
                urgency=urgency,
                url=study_url,
                details={
                    "places_remaining": places,
                    "reward_eur": self._gbp_to_eur(reward),
                },
            )

        except Exception as e:
            log.warning(f"Error extracting study details from card {index}: {e}")
            return None

    async def _check_study_full(self, page: Page) -> bool:
        """Check if current study page shows 'full' message."""
        try:
            el = await page.query_selector(self.SELECTORS["study_full"])
            return el is not None
        except Exception:
            return False

    # ================================================================
    # PARSERS
    # ================================================================

    def _parse_reward(self, text: str) -> float:
        """Parse reward text like 'GBP 8.50' or '8.50' to float."""
        match = re.search(r'[£$€]?\s*([\d]+\.[\d]{1,2})', text)
        if match:
            return float(match.group(1))
        # Try integer amounts
        match = re.search(r'[£$€]\s*(\d+)', text)
        if match:
            return float(match.group(1))
        return 0.0

    def _parse_minutes(self, text: str) -> int:
        """Parse time text like '15 minutes' or '15 mins' to int."""
        match = re.search(r'(\d+)\s*min', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Try hours
        match = re.search(r'(\d+)\s*hour', text, re.IGNORECASE)
        if match:
            return int(match.group(1)) * 60
        return 0

    def _parse_places(self, text: str) -> int:
        """Parse places text like '3 places remaining' to int."""
        match = re.search(r'(\d+)\s*place', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return -1

    def _gbp_to_eur(self, gbp: float) -> float:
        """Convert GBP to EUR estimate."""
        return round(gbp * GBP_TO_EUR, 2)


# Alias for scheduler auto-discovery
Plugin = ProlificPlugin
