"""Detect Hindi, English, or code-mixed speech"""
import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect language of transcribed text"""

    HINDI_PATTERNS = [
        r'[\u0900-\u097F]',  # Devanagari script
        # Common Hindi words in Roman script
        r'\b(hai|hain|tha|thi|the|hoon|ho|ka|ki|ke|ko|se|mein|aur|ya|par|ke liye)\b',
        r'\b(kya|kaise|kab|kahan|kyun|kaun|kitna)\b',  # Question words
        r'\b(achha|theek|bilkul|shayad|zaroor)\b',  # Common words
        r'\b(din|raat|subah|shaam|kal|aaj|abhi)\b',  # Time words
        r'\b(ghar|kamra|sher|paani|khana|dawa)\b',  # Common nouns
    ]

    ENGLISH_PATTERNS = [
        r'\b(the|is|are|was|were|have|has|had|do|does|did)\b',
        r'\b(what|when|where|why|how|who|which)\b',
        r'\b(good|bad|very|much|many|some|all|any)\b',
        r'\b(doctor|patient|medicine|treatment|diagnosis)\b',
    ]

    def __init__(self):
        # Compile patterns for efficiency
        self.hindi_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.HINDI_PATTERNS]
        self.english_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.ENGLISH_PATTERNS]

    def detect(self, text: str) -> str:
        """
        Detect language of text.
        Returns: 'hi' (Hindi), 'en' (English), or 'hi-en' (code-mixed)
        """
        if not text or not text.strip():
            return "unknown"

        hindi_ratio, english_ratio = self.get_language_ratio(text)

        # Determine language based on ratios
        if hindi_ratio > 0.6:
            return "hi"
        elif english_ratio > 0.6:
            return "en"
        elif hindi_ratio > 0.2 and english_ratio > 0.2:
            # Both languages present significantly - code-mixed
            return "hi-en"
        elif hindi_ratio > english_ratio:
            return "hi"
        elif english_ratio > hindi_ratio:
            return "en"
        else:
            return "unknown"

    def get_language_ratio(self, text: str) -> Tuple[float, float]:
        """Return (hindi_ratio, english_ratio) for text"""
        if not text:
            return (0.0, 0.0)

        # Count matches for each language
        hindi_matches = 0
        for pattern in self.hindi_regex:
            hindi_matches += len(pattern.findall(text))

        english_matches = 0
        for pattern in self.english_regex:
            english_matches += len(pattern.findall(text))

        # Also check for Devanagari characters
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
        if devanagari_chars > 0:
            hindi_matches += devanagari_chars / 2  # Weight Devanagari heavily

        # Calculate word count
        words = text.split()
        word_count = max(len(words), 1)

        # Calculate ratios
        hindi_ratio = min(1.0, hindi_matches / word_count)
        english_ratio = min(1.0, english_matches / word_count)

        # Normalize if both are high (to prevent double-counting)
        total = hindi_ratio + english_ratio
        if total > 1.0:
            hindi_ratio = hindi_ratio / total
            english_ratio = english_ratio / total

        return (hindi_ratio, english_ratio)

    def is_code_mixed(self, text: str, threshold: float = 0.2) -> bool:
        """Check if text is code-mixed (both languages present)"""
        hindi_ratio, english_ratio = self.get_language_ratio(text)
        return hindi_ratio >= threshold and english_ratio >= threshold

    def get_dominant_language(self, text: str) -> str:
        """Get the dominant language in text"""
        hindi_ratio, english_ratio = self.get_language_ratio(text)

        if hindi_ratio > english_ratio:
            return "hi"
        elif english_ratio > hindi_ratio:
            return "en"
        else:
            return "unknown"
