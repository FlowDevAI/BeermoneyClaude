"""
BeermoneyClaude — Auto Form Filler
Detects form fields and fills them from user profile with human-like behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.logger import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Page

    from core.browser import BrowserManager

    from .profile_data import ProfileManager

log = get_logger("form_filler")

# Maps common field identifiers (label text, name attributes, placeholders) to profile fields
FIELD_MAP: dict[str, str] = {
    # Personal
    "first name": "first_name",
    "first_name": "first_name",
    "firstname": "first_name",
    "nombre": "first_name",
    "last name": "last_name",
    "last_name": "last_name",
    "lastname": "last_name",
    "apellido": "last_name",
    "surname": "last_name",
    "email": "email",
    "e-mail": "email",
    "correo": "email",
    "age": "age",
    "edad": "age",
    "gender": "gender",
    "genero": "gender",
    "country": "country",
    "pais": "country",
    "city": "city",
    "ciudad": "city",
    "zip": "zip_code",
    "zip code": "zip_code",
    "postal": "zip_code",
    "codigo postal": "zip_code",
    # Demographics
    "education": "education",
    "educacion": "education",
    "degree": "education",
    "employment": "employment_status",
    "employment status": "employment_status",
    "job title": "job_title",
    "job_title": "job_title",
    "occupation": "job_title",
    "puesto": "job_title",
    "industry": "industry",
    "industria": "industry",
    "sector": "industry",
    "income": "income_range",
    "ingresos": "income_range",
    "household size": "household_size",
    "household": "household_size",
    # Tech
    "device": "devices",
    "dispositivo": "devices",
    "operating system": "operating_systems",
    "browser": "browsers",
    "navegador": "browsers",
}


class FormFiller:
    """Auto-fills form fields using profile data and humanized browser interactions."""

    def __init__(self, browser: BrowserManager, profile_manager: ProfileManager) -> None:
        self.browser = browser
        self.profile = profile_manager

    def _detect_field(self, field_hint: str) -> str | None:
        """Detect which profile field matches a given hint (label/name/placeholder)."""
        hint_lower = field_hint.lower().strip()
        # Direct match
        if hint_lower in FIELD_MAP:
            return FIELD_MAP[hint_lower]
        # Partial match
        for key, profile_field in FIELD_MAP.items():
            if key in hint_lower or hint_lower in key:
                return profile_field
        return None

    async def fill_field(self, page: Page, selector: str, field_hint: str) -> bool:
        """Detect a field type from hint and fill it from the profile.

        Returns True if the field was filled, False if no matching profile data.
        """
        profile_field = self._detect_field(field_hint)
        if not profile_field:
            log.debug(f"No profile match for hint: {field_hint}")
            return False

        value = self.profile.get_field(profile_field)
        if not value:
            log.debug(f"Profile field '{profile_field}' is empty")
            return False

        # Convert lists to first item for single-value fields
        if isinstance(value, list):
            value = value[0] if value else ""

        await self.browser.safe_fill(page, selector, str(value))
        log.info(f"Filled '{field_hint}' → {profile_field}")
        return True

    async def fill_form(self, page: Page, field_map: dict[str, str]) -> dict[str, bool]:
        """Fill multiple form fields. field_map: {css_selector: field_hint}.

        Returns dict of {selector: was_filled}.
        """
        results: dict[str, bool] = {}
        for selector, hint in field_map.items():
            try:
                filled = await self.fill_field(page, selector, hint)
                results[selector] = filled
            except Exception as e:
                log.warning(f"Failed to fill {selector}: {e}")
                results[selector] = False
        return results

    async def fill_demographics(self, page: Page, selectors: dict[str, dict]) -> None:
        """Fill a platform-specific demographics form.

        selectors format:
        {
            "field_name": {
                "selector": "#css-selector",
                "type": "text" | "select" | "radio" | "checkbox",
                "options_map": {"profile_value": "option_value"}  # for selects/radios
            }
        }
        """
        for field_name, config in selectors.items():
            sel = config["selector"]
            field_type = config.get("type", "text")
            value = self.profile.get_field(field_name)

            if not value:
                log.debug(f"No profile data for {field_name}")
                continue

            try:
                if field_type == "text":
                    text_value = value[0] if isinstance(value, list) else str(value)
                    await self.browser.safe_fill(page, sel, text_value)

                elif field_type == "select":
                    options_map = config.get("options_map", {})
                    select_value = str(value)
                    if isinstance(value, list):
                        select_value = value[0]
                    # Map profile value to platform's option value
                    mapped = options_map.get(select_value, select_value)
                    await self.browser.safe_select(page, sel, mapped)

                elif field_type == "radio":
                    options_map = config.get("options_map", {})
                    radio_value = str(value)
                    mapped = options_map.get(radio_value, radio_value)
                    # Selector should target the specific radio by value
                    radio_sel = f"{sel}[value='{mapped}']"
                    await self.browser.safe_click(page, radio_sel)

                elif field_type == "checkbox":
                    # For list fields, click each matching checkbox
                    values = value if isinstance(value, list) else [value]
                    options_map = config.get("options_map", {})
                    for v in values:
                        mapped = options_map.get(str(v), str(v))
                        checkbox_sel = f"{sel}[value='{mapped}']"
                        await self.browser.safe_click(page, checkbox_sel)

                log.info(f"Demographics filled: {field_name} ({field_type})")

            except Exception as e:
                log.warning(f"Failed to fill demographic {field_name}: {e}")
