"""
Clickworker Plugin -- Tier 3 (Microtasks)

Clickworker offers daily microtasks including UHRS (Microsoft) tasks.
Some tasks are auto-completable (simple categorization),
others need human judgment.

Key features:
- Daily availability (not sporadic like Prolific)
- Mix of AUTO and HUMAN tasks
- UHRS integration for search evaluation tasks
- Assessments required for some task types

Login: Rails/Devise at workplace.clickworker.com
Frontend: Server-rendered HTML + Bootstrap
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
from core.browser import BrowserManager
from core.logger import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Page

log = get_logger("clickworker")


class ClickworkerPlugin(PlatformPlugin):
    name = "clickworker"
    display_name = "Clickworker"
    url = "https://www.clickworker.com"
    login_url = "https://workplace.clickworker.com/en/users/sign_in"  # TODO: VERIFY URL
    dashboard_url = "https://workplace.clickworker.com/en/workplace/jobs"
    tier = 3
    category = "microtasks"
    check_interval = 3600  # 60 minutes
    currency = "EUR"

    # === SELECTORS ===
    # Most selectors need verification after account registration.
    # Clickworker uses Rails/Devise (no data-testid attributes, classic CSS).
    SELECTORS = {
        # --- Login (Rails/Devise pattern) ---
        "login_email": 'input#user_email',  # TODO: VERIFY SELECTOR
        "login_email_alt": 'input[name="user[email]"]',  # TODO: VERIFY SELECTOR
        "login_email_alt2": 'input[type="email"]',  # fallback
        "login_password": 'input#user_password',  # TODO: VERIFY SELECTOR
        "login_password_alt": 'input[name="user[password]"]',  # TODO: VERIFY SELECTOR
        "login_password_alt2": 'input[type="password"]',  # fallback
        "login_submit": 'input[type="submit"]',  # TODO: VERIFY SELECTOR
        "login_submit_alt": 'button[type="submit"]',  # fallback
        "login_remember": 'input#user_remember_me',  # TODO: VERIFY SELECTOR

        # --- Logged in verification ---
        "user_indicator": 'nav.side-navbar:not(.register-login-menu)',  # TODO: VERIFY SELECTOR
        "user_indicator_alt": '[class*="user-info"]',  # TODO: VERIFY SELECTOR
        "user_indicator_alt2": 'a[href*="sign_out"]',  # TODO: VERIFY SELECTOR
        "dashboard_body": 'body:not(#http_404)',  # pages that aren't 404

        # --- Jobs / Workplace ---
        "job_list": 'table.jobs-table',  # TODO: VERIFY SELECTOR
        "job_list_alt": '[class*="job-list"]',  # TODO: VERIFY SELECTOR
        "job_list_alt2": 'table tbody',  # fallback
        "job_row": 'table.jobs-table tbody tr',  # TODO: VERIFY SELECTOR
        "job_row_alt": '[class*="job-item"]',  # TODO: VERIFY SELECTOR
        "job_row_alt2": 'table tbody tr',  # fallback
        "job_title": 'td.job-title',  # TODO: VERIFY SELECTOR
        "job_title_alt": 'td:first-child a',  # TODO: VERIFY SELECTOR
        "job_pay": 'td.job-pay',  # TODO: VERIFY SELECTOR
        "job_pay_alt": '[class*="pay"]',  # TODO: VERIFY SELECTOR
        "job_type": 'td.job-type',  # TODO: VERIFY SELECTOR
        "job_start_button": 'a.btn:has-text("Start")',  # TODO: VERIFY SELECTOR
        "job_start_alt": 'a:has-text("Start working")',  # TODO: VERIFY SELECTOR
        "job_start_alt2": 'a.btn-primary',  # TODO: VERIFY SELECTOR

        # --- Assessments ---
        "assessment_required": ':text("assessment")',  # TODO: VERIFY SELECTOR
        "assessment_link": 'a[href*="assessment"]',  # TODO: VERIFY SELECTOR

        # --- UHRS ---
        "uhrs_link": 'a[href*="uhrs"]',  # TODO: VERIFY SELECTOR
        "uhrs_link_alt": 'a:has-text("UHRS")',  # TODO: VERIFY SELECTOR
        "uhrs_section": '[class*="uhrs"]',  # TODO: VERIFY SELECTOR

        # --- Balance ---
        "balance": '[class*="balance"]',  # TODO: VERIFY SELECTOR
        "balance_alt": '[class*="earning"]',  # TODO: VERIFY SELECTOR
        "balance_alt2": '[class*="account-balance"]',  # TODO: VERIFY SELECTOR

        # --- States ---
        "no_jobs": ':text("no jobs available")',  # TODO: VERIFY SELECTOR
        "no_jobs_alt": ':text("currently no")',  # TODO: VERIFY SELECTOR
        "no_jobs_alt2": ':text("No jobs")',  # TODO: VERIFY SELECTOR
        "error_404": 'body#http_404',  # VERIFIED (from research)

        # --- Cookie consent ---
        "cookie_accept": 'button:has-text("Accept")',  # TODO: VERIFY SELECTOR
        "cookie_accept_alt": '.moove-gdpr-infobar-allow-all',  # TODO: VERIFY SELECTOR

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
        """Login to Clickworker via Devise (email/password)."""
        log.info("Starting login flow...")

        try:
            await page.goto(self.login_url, wait_until="networkidle", timeout=30000)
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

            # Check if already logged in (redirected away from login)
            if "sign_in" not in page.url and "login" not in page.url:
                log.info("Already logged in (redirected from login)")
                return LoginResult(success=True)

            # Fill email
            email_filled = await self._try_fill_selector(
                page,
                [
                    self.SELECTORS["login_email"],
                    self.SELECTORS["login_email_alt"],
                    self.SELECTORS["login_email_alt2"],
                ],
                "",  # from config
                field_name="email",
            )

            if not email_filled:
                log.error("Could not find email field on login page")
                return LoginResult(
                    success=False,
                    error="Email field not found. Login page may have changed.",
                )

            # Fill password
            password_filled = await self._try_fill_selector(
                page,
                [
                    self.SELECTORS["login_password"],
                    self.SELECTORS["login_password_alt"],
                    self.SELECTORS["login_password_alt2"],
                ],
                "",  # from config
                field_name="password",
            )

            if not password_filled:
                log.error("Could not find password field")
                return LoginResult(
                    success=False,
                    error="Password field not found.",
                )

            # Check "remember me" if available
            try:
                remember = await page.query_selector(self.SELECTORS["login_remember"])
                if remember:
                    is_checked = await remember.is_checked()
                    if not is_checked:
                        await remember.click()
                        log.debug("Checked 'remember me'")
            except Exception:
                pass

            # Submit login
            submit_clicked = False
            for sel in [self.SELECTORS["login_submit"], self.SELECTORS["login_submit_alt"]]:
                try:
                    await page.click(sel, timeout=5000)
                    submit_clicked = True
                    log.debug(f"Clicked submit: {sel}")
                    break
                except PlaywrightTimeout:
                    continue

            if not submit_clicked:
                log.error("Submit button not found")
                return LoginResult(success=False, error="Submit button not found")

            # Wait for redirect
            log.info("Waiting for login redirect...")
            try:
                await page.wait_for_url(
                    lambda url: "sign_in" not in url and "/login" not in url,
                    timeout=30000,
                )
            except PlaywrightTimeout:
                log.error("Login redirect timed out")
                return LoginResult(
                    success=False,
                    error="Login redirect timed out. Check credentials.",
                )

            await page.wait_for_load_state("networkidle")
            final_url = page.url
            log.info(f"Login redirect completed: {final_url}")

            # Check for 404 (account issue)
            is_404 = await page.query_selector(self.SELECTORS["error_404"])
            if is_404:
                log.warning("Landed on 404 page after login")
                return LoginResult(
                    success=True,
                    error="Account may need activation - workplace shows 404",
                )

            return LoginResult(success=True)

        except Exception as e:
            log.error(f"Login failed: {e}")
            return LoginResult(success=False, error=str(e))

    # ================================================================
    # IS LOGGED IN
    # ================================================================

    async def is_logged_in(self, page: Page) -> bool:
        """Check if logged into Clickworker workplace."""
        current_url = page.url

        # If on login/sign_in page, not logged in
        if "sign_in" in current_url or "/login" in current_url:
            return False

        # If on registration page, not logged in
        if "users/new" in current_url:
            return False

        # If on workplace, check for user indicators
        if "workplace.clickworker.com" in current_url:
            # Check for 404 (might be logged in but account not activated)
            is_404 = await page.query_selector(self.SELECTORS["error_404"])
            if is_404:
                log.debug("On workplace but got 404 - account may not be activated")
                return False

            # Try to find user indicators
            for sel in [
                self.SELECTORS["user_indicator"],
                self.SELECTORS["user_indicator_alt"],
                self.SELECTORS["user_indicator_alt2"],
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        log.debug(f"Logged in indicator found: {sel}")
                        return True
                except Exception:
                    continue

            # If we're on workplace and not on login, likely logged in
            log.debug("On workplace.clickworker.com, assuming logged in")
            return True

        return False

    # ================================================================
    # SCAN AVAILABLE TASKS
    # ================================================================

    async def scan_available_tasks(self, page: Page) -> list[DetectedTask]:
        """Scan for available jobs on Clickworker workplace."""
        log.info("Scanning for available jobs...")
        jobs: list[DetectedTask] = []

        try:
            # Navigate to jobs/dashboard page
            current_url = page.url
            if self.dashboard_url not in current_url:
                await page.goto(
                    self.dashboard_url, wait_until="domcontentloaded", timeout=30000
                )
                await page.wait_for_timeout(3000)

            final_url = page.url
            log.info(f"Jobs page URL: {final_url}")

            # Check for login redirect
            if "sign_in" in final_url or "/login" in final_url:
                log.warning("Not logged in, redirected to login page")
                return []

            # Check for 404
            is_404 = await page.query_selector(self.SELECTORS["error_404"])
            if is_404:
                log.warning("Jobs page returns 404 - account may not be activated")
                return []

            # Dismiss cookies
            await self._dismiss_cookies(page)

            # Check for empty state
            is_empty = await self._check_empty_state(page)
            if is_empty:
                log.info("No jobs available (empty state detected)")
                return []

            # Find job rows
            rows = await self._find_job_rows(page)
            if not rows:
                log.info("No job rows found on page")
                return []

            log.info(f"Found {len(rows)} job row(s)")

            # Extract details from each row
            for i, row in enumerate(rows):
                try:
                    job = await self._extract_job_details(page, row, i)
                    if job:
                        jobs.append(job)
                        log.info(
                            f"  Job {i+1}: '{job.title}' - "
                            f"{job.currency} {job.estimated_pay:.2f} - "
                            f"Difficulty: {job.difficulty.value}"
                        )
                except Exception as e:
                    log.warning(f"  Error extracting job {i+1}: {e}")

            # Also check for UHRS
            uhrs_jobs = await self._check_uhrs(page)
            jobs.extend(uhrs_jobs)

        except Exception as e:
            log.error(f"Error scanning jobs: {e}")

        log.info(f"Scan complete: {len(jobs)} jobs found")
        return jobs

    # ================================================================
    # ACCEPT TASK
    # ================================================================

    async def accept_task(self, page: Page, task: DetectedTask) -> AcceptResult:
        """Accept/start a job on Clickworker."""
        log.info(f"Accepting job: '{task.title}' ({task.currency} {task.estimated_pay})")

        try:
            # Navigate to job URL if available
            if task.url:
                await page.goto(task.url, wait_until="networkidle", timeout=15000)
            else:
                await page.goto(
                    self.dashboard_url, wait_until="networkidle", timeout=15000
                )

            # Check for assessment requirement
            needs_assessment = await self._check_needs_assessment(page)
            if needs_assessment:
                log.info("Job requires assessment first")
                return AcceptResult(
                    success=True,
                    needs_human=True,
                    human_reason="Assessment required before starting job",
                    human_instructions=(
                        f"Job '{task.title}' requires completing an assessment first.\n"
                        f"URL: {page.url}\n"
                        f"Pay: {task.currency} {task.estimated_pay:.2f}\n"
                        f"Complete the assessment to unlock this job type."
                    ),
                )

            # Try to click start/accept button
            start_clicked = False
            for sel in [
                self.SELECTORS["job_start_button"],
                self.SELECTORS["job_start_alt"],
                self.SELECTORS["job_start_alt2"],
            ]:
                try:
                    button = await page.wait_for_selector(sel, timeout=3000)
                    if button:
                        await button.click()
                        start_clicked = True
                        log.info(f"Clicked start button: {sel}")
                        break
                except PlaywrightTimeout:
                    continue

            if not start_clicked:
                log.error("Start button not found")
                return AcceptResult(
                    success=False,
                    error="Start button not found on page",
                )

            await asyncio.sleep(2)
            final_url = page.url
            log.info(f"After accept, URL: {final_url}")

            # Determine if task needs human completion
            difficulty = await self.classify_task(task)

            return AcceptResult(
                success=True,
                needs_human=difficulty != TaskDifficulty.AUTO,
                human_reason=f"Task type: {difficulty.value}",
                human_instructions=(
                    f"Job '{task.title}' started on Clickworker.\n"
                    f"URL: {final_url}\n"
                    f"Pay: {task.currency} {task.estimated_pay:.2f}\n"
                    f"Type: {task.details.get('job_type', 'unknown')}"
                ),
            )

        except Exception as e:
            log.error(f"Error accepting job: {e}")
            return AcceptResult(success=False, error=str(e))

    # ================================================================
    # CLASSIFY TASK
    # ================================================================

    async def classify_task(self, task: DetectedTask) -> TaskDifficulty:
        """Classify task difficulty based on type and title."""
        title_lower = task.title.lower()
        job_type = task.details.get("job_type", "").lower()

        # AUTO: simple categorization, tagging, labeling
        auto_keywords = [
            "categoriz", "categori", "classify", "classif",
            "tag", "label", "sort", "match",
            "verify", "validat", "check",
        ]
        if any(kw in title_lower or kw in job_type for kw in auto_keywords):
            return TaskDifficulty.AUTO

        # SEMI_AUTO: transcription, UHRS, simple data entry
        semi_keywords = [
            "transcri", "uhrs", "data entry", "copy",
            "search evaluat", "relevance", "rating",
        ]
        if any(kw in title_lower or kw in job_type for kw in semi_keywords):
            return TaskDifficulty.SEMI_AUTO

        # HUMAN: surveys, writing, creative, complex evaluation
        human_keywords = [
            "survey", "writing", "creative", "essay",
            "opinion", "review", "feedback", "interview",
        ]
        if any(kw in title_lower or kw in job_type for kw in human_keywords):
            return TaskDifficulty.HUMAN

        # Default to SEMI_AUTO for Clickworker (most tasks are doable with guidance)
        return TaskDifficulty.SEMI_AUTO

    # ================================================================
    # GET BALANCE
    # ================================================================

    async def get_balance(self, page: Page) -> float | None:
        """Fetch current Clickworker balance."""
        try:
            for sel in [
                self.SELECTORS["balance"],
                self.SELECTORS["balance_alt"],
                self.SELECTORS["balance_alt2"],
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        amount = self._parse_amount(text)
                        if amount > 0:
                            log.debug(f"Balance found: EUR {amount}")
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
        for sel in [self.SELECTORS["cookie_accept"], self.SELECTORS["cookie_accept_alt"]]:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    log.debug("Cookie consent dismissed")
                    await asyncio.sleep(0.5)
                    return
            except Exception:
                continue

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
        """Try multiple selectors to fill a field."""
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
        """Check if workplace shows no-jobs state."""
        for sel in [
            self.SELECTORS["no_jobs"],
            self.SELECTORS["no_jobs_alt"],
            self.SELECTORS["no_jobs_alt2"],
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    return True
            except Exception:
                continue
        return False

    async def _find_job_rows(self, page: Page) -> list:
        """Find job row elements using fallback selectors."""
        for sel in [
            self.SELECTORS["job_row"],
            self.SELECTORS["job_row_alt"],
            self.SELECTORS["job_row_alt2"],
        ]:
            try:
                rows = await page.query_selector_all(sel)
                if rows:
                    log.debug(f"Job rows found with: {sel} ({len(rows)} rows)")
                    return rows
            except Exception:
                continue
        return []

    async def _extract_job_details(
        self, page: Page, row, index: int
    ) -> DetectedTask | None:
        """Extract job details from a row/card element."""
        try:
            # Title
            title = ""
            for sel in [self.SELECTORS["job_title"], self.SELECTORS["job_title_alt"]]:
                try:
                    title_el = await row.query_selector(sel)
                    if title_el:
                        title = (await title_el.inner_text()).strip()
                        break
                except Exception:
                    continue

            if not title:
                title = (await row.inner_text()).strip()[:100]

            # Pay
            pay = 0.0
            try:
                pay_el = await row.query_selector(self.SELECTORS["job_pay"])
                if not pay_el:
                    pay_el = await row.query_selector(self.SELECTORS["job_pay_alt"])
                if pay_el:
                    pay_text = await pay_el.inner_text()
                    pay = self._parse_amount(pay_text)
            except Exception:
                pass

            if pay == 0.0:
                row_text = await row.inner_text()
                pay = self._parse_amount(row_text)

            # Job type (native, UHRS, etc.)
            job_type = "native"
            row_text = await row.inner_text()
            if "uhrs" in row_text.lower():
                job_type = "uhrs"

            # Check for assessment requirement
            needs_assessment = "assessment" in row_text.lower()

            # Job URL
            job_url = ""
            try:
                link = await row.query_selector("a[href]")
                if link:
                    job_url = await link.get_attribute("href") or ""
                    if job_url and not job_url.startswith("http"):
                        job_url = f"https://workplace.clickworker.com{job_url}"
            except Exception:
                pass

            # Determine urgency (Clickworker jobs are generally not as urgent as Prolific)
            urgency = TaskUrgency.MEDIUM
            if pay > 0 and pay >= 1.0:
                urgency = TaskUrgency.HIGH

            return DetectedTask(
                platform=self.name,
                title=title,
                estimated_pay=pay,
                currency=self.currency,
                estimated_minutes=self._estimate_minutes(title, pay),
                difficulty=TaskDifficulty.SEMI_AUTO,
                urgency=urgency,
                url=job_url,
                details={
                    "job_type": job_type,
                    "needs_assessment": needs_assessment,
                },
            )

        except Exception as e:
            log.warning(f"Error extracting job details from row {index}: {e}")
            return None

    async def _check_uhrs(self, page: Page) -> list[DetectedTask]:
        """Check for UHRS tasks availability."""
        uhrs_tasks: list[DetectedTask] = []

        for sel in [
            self.SELECTORS["uhrs_link"],
            self.SELECTORS["uhrs_link_alt"],
            self.SELECTORS["uhrs_section"],
        ]:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    log.info(f"UHRS section detected: {sel} ({len(els)} elements)")
                    # UHRS is a separate interface — mark as human task
                    uhrs_tasks.append(
                        DetectedTask(
                            platform=self.name,
                            title="UHRS Tasks Available",
                            estimated_pay=0.0,
                            currency=self.currency,
                            estimated_minutes=0,
                            difficulty=TaskDifficulty.SEMI_AUTO,
                            urgency=TaskUrgency.MEDIUM,
                            url="",
                            details={"job_type": "uhrs", "is_uhrs_portal": True},
                        )
                    )
                    break
            except Exception:
                continue

        return uhrs_tasks

    async def _check_needs_assessment(self, page: Page) -> bool:
        """Check if current job requires an assessment."""
        for sel in [
            self.SELECTORS["assessment_required"],
            self.SELECTORS["assessment_link"],
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    return True
            except Exception:
                continue
        return False

    async def _check_study_full(self, page: Page) -> bool:
        """Check if job is no longer available."""
        return await self._check_empty_state(page)

    # ================================================================
    # PARSERS
    # ================================================================

    def _parse_amount(self, text: str) -> float:
        """Parse amount text like 'EUR 0.50' or '0.50 EUR' to float."""
        match = re.search(r'[€$£]?\s*([\d]+\.[\d]{1,2})', text)
        if match:
            return float(match.group(1))
        match = re.search(r'([\d]+),(\d{1,2})\s*[€$£]?', text)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
        match = re.search(r'[€$£]\s*(\d+)', text)
        if match:
            return float(match.group(1))
        return 0.0

    def _estimate_minutes(self, title: str, pay: float) -> int:
        """Estimate task duration based on title and pay."""
        title_lower = title.lower()
        if "quick" in title_lower or "fast" in title_lower:
            return 5
        if "survey" in title_lower:
            return 15
        if "writing" in title_lower or "essay" in title_lower:
            return 30
        # Estimate from pay (assume ~EUR 8/h average)
        if pay > 0:
            return max(1, int((pay / 8.0) * 60))
        return 10


# Alias for scheduler auto-discovery
Plugin = ClickworkerPlugin
