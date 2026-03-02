"""
BeermoneyClaude — Screener Bot
Answers screener/qualification questions truthfully from profile data.
NEVER fabricates answers — returns None when unsure, queuing for human review.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.logger import get_logger

if TYPE_CHECKING:
    from .profile_data import ProfileManager

log = get_logger("screener")

# Keywords that indicate subjective/opinion questions — always defer to human
OPINION_KEYWORDS: list[str] = [
    "opinion",
    "think about",
    "how do you feel",
    "what do you think",
    "rate your",
    "would you recommend",
    "describe your experience",
    "tell us about",
    "what is your favorite",
    "preference",
    "agree or disagree",
    "satisfied",
    "how likely",
    "what matters most",
    "most important",
    "why do you",
    "explain",
    "in your own words",
    "open ended",
    "opina",
    "que piensas",
    "como te sientes",
    "tu experiencia",
]

# Keywords that indicate disqualifying "trap" questions
TRAP_KEYWORDS: list[str] = [
    "do you work in market research",
    "work for a company that",
    "employed by an advertising",
    "work in public relations",
    "investigacion de mercado",
]


class ScreenerBot:
    """Answers screener questions using real profile data. Never fabricates."""

    def __init__(self, profile_manager: ProfileManager) -> None:
        self.profile = profile_manager

    def should_skip(self, question: str) -> bool:
        """Detect opinion/subjective questions that need human input."""
        q = question.lower()
        return any(kw in q for kw in OPINION_KEYWORDS)

    def is_trap_question(self, question: str) -> bool:
        """Detect common disqualifying trap questions."""
        q = question.lower()
        return any(kw in q for kw in TRAP_KEYWORDS)

    def answer_screener(
        self, question: str, options: list[str]
    ) -> str | None:
        """Find the best truthful answer for a screener question.

        Returns:
            The matching option string, or None if unable to determine
            an answer from profile data (will be queued for human).
        """
        # Never answer opinion questions
        if self.should_skip(question):
            log.info(f"Skipping opinion question: {question[:60]}...")
            return None

        # Handle trap questions — answer "No" truthfully if applicable
        if self.is_trap_question(question):
            no_option = self._find_negative_option(options)
            if no_option:
                log.info(f"Trap question answered: {no_option}")
                return no_option
            return None

        # Delegate to ProfileManager's screener matching
        result = self.profile.match_screener(question, options)

        if result:
            log.info(f"Screener matched: '{question[:50]}...' → {result}")
        else:
            log.info(f"Screener unmatched (needs human): '{question[:60]}...'")

        return result

    @staticmethod
    def _find_negative_option(options: list[str]) -> str | None:
        """Find a 'No' option in the list."""
        for opt in options:
            opt_lower = opt.lower().strip()
            if opt_lower in ("no", "none", "none of the above", "no, i don't",
                             "no, i do not", "ninguno", "ninguna de las anteriores"):
                return opt
        return None
