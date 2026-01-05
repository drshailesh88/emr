"""Language detection indicator - shows detected language in text input."""

import flet as ft
from typing import Optional, Tuple
import re


class LanguageDetector:
    """Simple pattern-based language detector for English, Hindi, and Hinglish."""

    # Hindi Unicode range (Devanagari script)
    DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]+')

    # Common Hinglish medical terms (transliterated Hindi in Roman script)
    HINGLISH_PATTERNS = [
        # Medical symptoms
        r'\bbukhar\b', r'\bdard\b', r'\bkhasi\b', r'\bulti\b', r'\bdast\b',
        r'\bchakkar\b', r'\bpet\b', r'\bsar\b', r'\bgala\b', r'\bkaan\b',
        r'\baankh\b', r'\bsaans\b', r'\bseena\b', r'\bkamzori\b', r'\bthand\b',

        # Common Hindi words in medical context
        r'\bpatient ko\b', r'\busko\b', r'\bunko\b', r'\bmujhe\b',
        r'\bdin\b', r'\bhafte\b', r'\bmahine\b', r'\bsaal\b',
        r'\bsubah\b', r'\bsham\b', r'\braat\b',

        # Common Hinglish patterns
        r'\bho raha\b', r'\bho gaya\b', r'\bnahi\b', r'\bhai\b',
        r'\btheek\b', r'\bbahut\b', r'\bthoda\b', r'\bkafi\b',

        # Medical Hinglish
        r'\bdawa\b', r'\bilaj\b', r'\bjanch\b', r'\breport\b',
        r'\bkharabi\b', r'\btakleef\b', r'\bbeemari\b',
    ]

    # Compile Hinglish patterns
    HINGLISH_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in HINGLISH_PATTERNS]

    @staticmethod
    def detect(text: str) -> Tuple[str, float]:
        """
        Detect language and confidence.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language, confidence) where:
            - language: "English", "Hindi", or "Hinglish"
            - confidence: 0.0 to 1.0
        """
        if not text or len(text.strip()) < 3:
            return "English", 0.0

        text = text.strip()
        total_chars = len(text)

        # Count Devanagari characters
        devanagari_matches = LanguageDetector.DEVANAGARI_PATTERN.findall(text)
        devanagari_chars = sum(len(match) for match in devanagari_matches)
        devanagari_ratio = devanagari_chars / total_chars if total_chars > 0 else 0

        # If >50% Devanagari, it's Hindi
        if devanagari_ratio > 0.5:
            confidence = min(0.9, 0.5 + devanagari_ratio)  # 0.5 to 0.9
            return "Hindi", confidence

        # If 10-50% Devanagari, it's likely Hinglish
        if devanagari_ratio > 0.1:
            confidence = 0.6 + (devanagari_ratio * 0.3)  # 0.6 to 0.75
            return "Hinglish", confidence

        # Check for Hinglish patterns in Roman script
        words = text.lower().split()
        word_count = len(words)
        hinglish_match_count = 0

        for word in words:
            for pattern in LanguageDetector.HINGLISH_REGEX:
                if pattern.search(word):
                    hinglish_match_count += 1
                    break

        hinglish_word_ratio = hinglish_match_count / word_count if word_count > 0 else 0

        # If >15% Hinglish words, classify as Hinglish
        if hinglish_word_ratio > 0.15:
            confidence = 0.5 + min(0.4, hinglish_word_ratio * 2)  # 0.5 to 0.9
            return "Hinglish", confidence

        # If 5-15% Hinglish words, likely Hinglish with lower confidence
        if hinglish_word_ratio > 0.05:
            confidence = 0.4 + (hinglish_word_ratio * 2)  # 0.4 to 0.7
            return "Hinglish", confidence

        # Default to English
        # Higher confidence for longer text
        confidence = min(0.8, 0.5 + (word_count / 100))  # 0.5 to 0.8
        return "English", confidence


class LanguageIndicator(ft.UserControl):
    """
    Language indicator badge that shows detected language.

    Features:
    - Real-time language detection
    - Color-coded badges (Blue=English, Orange=Hindi, Purple=Hinglish)
    - Confidence percentage display
    - Pill-shaped design
    """

    # Color scheme
    COLORS = {
        "English": {
            "bg": ft.Colors.BLUE_50,
            "border": ft.Colors.BLUE_300,
            "text": ft.Colors.BLUE_900,
        },
        "Hindi": {
            "bg": ft.Colors.ORANGE_50,
            "border": ft.Colors.ORANGE_300,
            "text": ft.Colors.ORANGE_900,
        },
        "Hinglish": {
            "bg": ft.Colors.PURPLE_50,
            "border": ft.Colors.PURPLE_300,
            "text": ft.Colors.PURPLE_900,
        },
    }

    def __init__(self, visible: bool = True):
        """
        Initialize language indicator.

        Args:
            visible: Whether indicator is visible initially
        """
        super().__init__()
        self.visible = visible
        self.current_language = "English"
        self.current_confidence = 0.0
        self.container: Optional[ft.Container] = None
        self.badge_text: Optional[ft.Text] = None
        self.confidence_text: Optional[ft.Text] = None

    def build(self):
        """Build the indicator UI."""
        self.badge_text = ft.Text(
            "EN",
            size=10,
            weight=ft.FontWeight.BOLD,
            color=self.COLORS["English"]["text"],
        )

        self.confidence_text = ft.Text(
            "",
            size=9,
            color=self.COLORS["English"]["text"],
        )

        self.container = ft.Container(
            content=ft.Row(
                [
                    self.badge_text,
                    self.confidence_text,
                ],
                spacing=4,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
            bgcolor=self.COLORS["English"]["bg"],
            border=ft.border.all(1, self.COLORS["English"]["border"]),
            tooltip="Detected language: English",
            visible=self.visible,
        )

        return self.container

    def update_text(self, text: str):
        """
        Update language detection based on new text.

        Args:
            text: Text to analyze
        """
        # Detect language
        language, confidence = LanguageDetector.detect(text)

        # Update state
        self.current_language = language
        self.current_confidence = confidence

        # Update UI
        self._update_ui()

    def _update_ui(self):
        """Update the UI with current language and confidence."""
        if not self.container or not self.badge_text or not self.confidence_text:
            return

        language = self.current_language
        confidence = self.current_confidence

        # Get color scheme
        colors = self.COLORS.get(language, self.COLORS["English"])

        # Update badge text
        if language == "English":
            badge = "EN"
        elif language == "Hindi":
            badge = "हिं"  # Hindi abbreviation
        else:  # Hinglish
            badge = "HI"

        self.badge_text.value = badge
        self.badge_text.color = colors["text"]

        # Update confidence (only show if >0)
        if confidence > 0:
            self.confidence_text.value = f"{int(confidence * 100)}%"
            self.confidence_text.color = colors["text"]
            self.confidence_text.visible = True
        else:
            self.confidence_text.visible = False

        # Update container colors
        self.container.bgcolor = colors["bg"]
        self.container.border = ft.border.all(1, colors["border"])
        self.container.tooltip = f"Detected language: {language} ({int(confidence * 100)}% confidence)"

        # Show indicator if text is meaningful
        self.container.visible = self.visible and confidence > 0.3

        # Update page
        if self.container.page:
            self.container.update()

    def set_visible(self, visible: bool):
        """
        Set visibility of the indicator.

        Args:
            visible: Whether to show the indicator
        """
        self.visible = visible
        if self.container:
            self.container.visible = visible
            if self.container.page:
                self.container.update()

    def get_language(self) -> str:
        """Get currently detected language."""
        return self.current_language

    def get_confidence(self) -> float:
        """Get confidence of current detection."""
        return self.current_confidence


class LanguageIndicatedTextField(ft.UserControl):
    """
    TextField with integrated language indicator.

    Wraps a TextField with a language indicator positioned at top-right.
    """

    def __init__(
        self,
        label: str = "",
        hint_text: str = "",
        multiline: bool = False,
        min_lines: int = 1,
        max_lines: int = 1,
        on_change: Optional[callable] = None,
        **kwargs
    ):
        """
        Initialize language-indicated text field.

        Args:
            label: Field label
            hint_text: Hint text
            multiline: Whether field is multiline
            min_lines: Minimum lines
            max_lines: Maximum lines
            on_change: Change callback
            **kwargs: Additional TextField arguments
        """
        super().__init__()
        self.label = label
        self.hint_text = hint_text
        self.multiline = multiline
        self.min_lines = min_lines
        self.max_lines = max_lines
        self.user_on_change = on_change
        self.text_field: Optional[ft.TextField] = None
        self.language_indicator: Optional[LanguageIndicator] = None
        self.kwargs = kwargs

    def build(self):
        """Build the field with language indicator."""
        # Create language indicator
        self.language_indicator = LanguageIndicator(visible=True)

        # Create text field
        self.text_field = ft.TextField(
            label=self.label,
            hint_text=self.hint_text,
            multiline=self.multiline,
            min_lines=self.min_lines,
            max_lines=self.max_lines,
            on_change=self._handle_change,
            **self.kwargs
        )

        # Stack field with indicator at top-right
        return ft.Stack(
            [
                self.text_field,
                ft.Container(
                    content=self.language_indicator,
                    right=10,
                    top=8,
                ),
            ],
        )

    def _handle_change(self, e):
        """Handle text field change."""
        text = e.control.value or ""

        # Update language indicator
        if self.language_indicator:
            self.language_indicator.update_text(text)

        # Call user's on_change callback
        if self.user_on_change:
            self.user_on_change(e)

    @property
    def value(self):
        """Get text field value."""
        return self.text_field.value if self.text_field else ""

    @value.setter
    def value(self, val):
        """Set text field value."""
        if self.text_field:
            self.text_field.value = val
            # Update language indicator
            if self.language_indicator:
                self.language_indicator.update_text(val or "")

    def get_language(self) -> str:
        """Get detected language."""
        return self.language_indicator.get_language() if self.language_indicator else "English"

    def get_confidence(self) -> float:
        """Get detection confidence."""
        return self.language_indicator.get_confidence() if self.language_indicator else 0.0
