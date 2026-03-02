"""
BeermoneyClaude — User Profile Data
Pydantic model for user demographics + encrypted storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from core.config import settings
from core.logger import get_logger

log = get_logger("profiler")


class UserProfile(BaseModel):
    """All demographic fields commonly asked by beermoney platforms."""

    # Personal
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    age: int = 0
    date_of_birth: str = ""
    gender: str = ""  # male | female | non-binary | prefer_not_to_say
    country: str = ""
    city: str = ""
    zip_code: str = ""
    language: str = ""
    timezone: str = ""

    # Demographics
    education: str = ""  # high_school | bachelors | masters | phd | other
    employment_status: str = ""  # employed_ft | employed_pt | freelance | unemployed | student | retired
    job_title: str = ""
    industry: str = ""
    income_range: str = ""  # e.g. "25000-50000"
    household_size: int = 0
    marital_status: str = ""  # single | married | divorced | widowed
    children: int = 0
    ethnicity: str = ""

    # Tech
    devices: list[str] = Field(default_factory=list)  # desktop | laptop | tablet | smartphone
    operating_systems: list[str] = Field(default_factory=list)  # windows | macos | linux | ios | android
    browsers: list[str] = Field(default_factory=list)  # chrome | firefox | safari | edge
    internet_speed: str = ""  # slow | moderate | fast | very_fast
    social_media: list[str] = Field(default_factory=list)

    # Interests
    interests: list[str] = Field(default_factory=list)
    shopping_habits: list[str] = Field(default_factory=list)

    # Health
    wears_glasses: bool | None = None
    has_disabilities: bool | None = None

    def get_field(self, field_name: str) -> Any:
        """Get a profile field value by name."""
        return getattr(self, field_name, None)


class ProfileManager:
    """Load, save, and query user profile with optional Fernet encryption."""

    PROFILE_FILE = "profile.json"
    PROFILE_ENCRYPTED_FILE = "profile.encrypted.json"

    def __init__(self) -> None:
        self.profile: UserProfile = UserProfile()
        self._data_dir: Path = settings.DATA_DIR

    def load(self) -> UserProfile:
        """Load profile from encrypted file (preferred) or plaintext fallback."""
        encrypted_path = self._data_dir / self.PROFILE_ENCRYPTED_FILE
        plain_path = self._data_dir / self.PROFILE_FILE

        if encrypted_path.exists() and settings.ENCRYPTION_KEY:
            try:
                from cryptography.fernet import Fernet

                fernet = Fernet(settings.ENCRYPTION_KEY.encode())
                encrypted_data = encrypted_path.read_bytes()
                decrypted = fernet.decrypt(encrypted_data)
                data = json.loads(decrypted)
                self.profile = UserProfile(**data)
                log.info("Profile loaded (encrypted)")
                return self.profile
            except Exception as e:
                log.error(f"Failed to decrypt profile: {e}")

        if plain_path.exists():
            data = json.loads(plain_path.read_text(encoding="utf-8"))
            self.profile = UserProfile(**data)
            log.info("Profile loaded (plaintext)")
            return self.profile

        log.warning("No profile found — using empty profile")
        return self.profile

    def save(self, encrypt: bool = True) -> None:
        """Save profile. Encrypts if key is available and encrypt=True."""
        data = self.profile.model_dump()

        if encrypt and settings.ENCRYPTION_KEY:
            try:
                from cryptography.fernet import Fernet

                fernet = Fernet(settings.ENCRYPTION_KEY.encode())
                encrypted = fernet.encrypt(json.dumps(data).encode())
                path = self._data_dir / self.PROFILE_ENCRYPTED_FILE
                path.write_bytes(encrypted)
                log.info("Profile saved (encrypted)")
                return
            except Exception as e:
                log.error(f"Encryption failed, saving plaintext: {e}")

        path = self._data_dir / self.PROFILE_FILE
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info("Profile saved (plaintext)")

    def get_field(self, field_name: str) -> Any:
        """Get a single profile field value."""
        return self.profile.get_field(field_name)

    def match_screener(self, question: str, options: list[str]) -> str | None:
        """Match a screener question to the best truthful answer from profile data.

        Returns the best matching option or None if uncertain.
        """
        q = question.lower()

        # Age-related questions
        if any(kw in q for kw in ["age", "old are you", "birth", "edad"]):
            if self.profile.age > 0:
                return self._match_age_range(self.profile.age, options)

        # Gender questions
        if any(kw in q for kw in ["gender", "sex", "genero"]):
            if self.profile.gender:
                return self._match_option(self.profile.gender, options)

        # Employment questions
        if any(kw in q for kw in ["employ", "work", "job", "occupation", "empleo", "trabajo"]):
            if self.profile.employment_status:
                return self._match_option(self.profile.employment_status, options)

        # Education
        if any(kw in q for kw in ["education", "degree", "school", "university", "estudios"]):
            if self.profile.education:
                return self._match_option(self.profile.education, options)

        # Income
        if any(kw in q for kw in ["income", "salary", "earn", "ingresos"]):
            if self.profile.income_range:
                return self._match_income_range(self.profile.income_range, options)

        # Country
        if any(kw in q for kw in ["country", "where do you live", "location", "pais"]):
            if self.profile.country:
                return self._match_option(self.profile.country, options)

        # Devices
        if any(kw in q for kw in ["device", "computer", "phone", "tablet", "dispositivo"]):
            if self.profile.devices:
                for device in self.profile.devices:
                    match = self._match_option(device, options)
                    if match:
                        return match

        # OS
        if any(kw in q for kw in ["operating system", "os ", "windows", "mac"]):
            if self.profile.operating_systems:
                for os_name in self.profile.operating_systems:
                    match = self._match_option(os_name, options)
                    if match:
                        return match

        # Browser
        if any(kw in q for kw in ["browser", "navegador"]):
            if self.profile.browsers:
                for browser in self.profile.browsers:
                    match = self._match_option(browser, options)
                    if match:
                        return match

        # Marital status
        if any(kw in q for kw in ["marital", "married", "relationship", "estado civil"]):
            if self.profile.marital_status:
                return self._match_option(self.profile.marital_status, options)

        # Children
        if any(kw in q for kw in ["children", "kids", "hijos"]):
            return self._match_number(self.profile.children, options)

        # Household
        if any(kw in q for kw in ["household", "people in your home", "hogar"]):
            if self.profile.household_size > 0:
                return self._match_number(self.profile.household_size, options)

        # Industry
        if any(kw in q for kw in ["industry", "sector", "field of work", "industria"]):
            if self.profile.industry:
                return self._match_option(self.profile.industry, options)

        return None

    @staticmethod
    def _match_option(value: str, options: list[str]) -> str | None:
        """Find the best matching option for a value."""
        value_lower = value.lower().replace("_", " ")
        for opt in options:
            if value_lower in opt.lower() or opt.lower() in value_lower:
                return opt
        return None

    @staticmethod
    def _match_age_range(age: int, options: list[str]) -> str | None:
        """Match age to an age range option like '25-34'."""
        for opt in options:
            # Try to parse ranges like "25-34", "25 - 34", "25 to 34"
            cleaned = opt.replace(" ", "").replace("to", "-")
            parts = cleaned.split("-")
            if len(parts) == 2:
                try:
                    low, high = int(parts[0]), int(parts[1])
                    if low <= age <= high:
                        return opt
                except ValueError:
                    continue
            # Check for "X+" format
            if opt.strip().endswith("+"):
                try:
                    threshold = int(opt.strip().rstrip("+"))
                    if age >= threshold:
                        return opt
                except ValueError:
                    continue
        return None

    @staticmethod
    def _match_income_range(income_range: str, options: list[str]) -> str | None:
        """Match income range to options."""
        try:
            parts = income_range.split("-")
            if len(parts) == 2:
                mid = (int(parts[0]) + int(parts[1])) / 2
                best_opt = None
                best_dist = float("inf")
                for opt in options:
                    cleaned = opt.replace("$", "").replace(",", "").replace(" ", "").replace("to", "-")
                    opt_parts = cleaned.split("-")
                    if len(opt_parts) == 2:
                        try:
                            opt_mid = (int(opt_parts[0]) + int(opt_parts[1])) / 2
                            dist = abs(opt_mid - mid)
                            if dist < best_dist:
                                best_dist = dist
                                best_opt = opt
                        except ValueError:
                            continue
                return best_opt
        except (ValueError, IndexError):
            pass
        return None

    @staticmethod
    def _match_number(value: int, options: list[str]) -> str | None:
        """Match a numeric value to options."""
        value_str = str(value)
        for opt in options:
            if value_str == opt.strip():
                return opt
            if value == 0 and any(kw in opt.lower() for kw in ["none", "no", "0"]):
                return opt
        return None
