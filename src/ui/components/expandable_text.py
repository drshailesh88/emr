"""Expandable text field component for quick phrase expansion."""

import flet as ft
from typing import Optional, Callable
import re

from ...services.database import DatabaseService


class ExpandableTextField(ft.TextField):
    """Text field that expands shortcuts to full text.

    When user types a shortcut followed by space or tab,
    it expands to the full text automatically.
    """

    def __init__(self, db: DatabaseService, **kwargs):
        """Initialize expandable text field.

        Args:
            db: Database service instance
            **kwargs: Additional TextField arguments
        """
        super().__init__(**kwargs)
        self.db = db
        self._original_on_change = kwargs.get('on_change')
        self.on_change = self._handle_change

        # Cache phrases in memory for faster lookups
        self._phrase_cache = {}
        self._load_phrase_cache()

    def _load_phrase_cache(self):
        """Load all phrases into cache."""
        try:
            phrases = self.db.get_all_phrases()
            for phrase in phrases:
                # Store lowercase shortcut for case-insensitive matching
                self._phrase_cache[phrase['shortcut'].lower()] = {
                    'expansion': phrase['expansion'],
                    'shortcut': phrase['shortcut']
                }
        except Exception as e:
            print(f"Warning: Could not load phrase cache: {e}")

    def reload_cache(self):
        """Reload phrase cache from database."""
        self._phrase_cache.clear()
        self._load_phrase_cache()

    def _handle_change(self, e):
        """Handle text change and expand shortcuts if needed."""
        # Call original on_change handler first if it exists
        if self._original_on_change:
            self._original_on_change(e)

        # Only expand if user just typed a space or is in single-line mode
        if not self.value:
            return

        # Get current value
        current_value = self.value

        # Check if we should try to expand
        # We expand when user types space after a potential shortcut
        if not current_value.endswith(' '):
            return

        # Get the last word before the space
        # Split by whitespace and newlines
        words = re.split(r'[\s\n]+', current_value.rstrip())
        if not words:
            return

        last_word = words[-1]

        # Check if it's a shortcut (case-insensitive)
        phrase_data = self._phrase_cache.get(last_word.lower())
        if phrase_data:
            # Calculate where to replace
            # Find the position of the last occurrence of the shortcut
            last_word_start = current_value.rstrip().rfind(last_word)

            if last_word_start >= 0:
                # Replace the shortcut with expansion
                before = current_value[:last_word_start]
                expansion = phrase_data['expansion']
                after = ' '  # Keep the trailing space

                new_value = before + expansion + after

                # Update the field value
                self.value = new_value

                # Track usage in database (non-blocking)
                try:
                    self.db.increment_phrase_usage(phrase_data['shortcut'])
                except Exception as e:
                    print(f"Warning: Could not increment phrase usage: {e}")

                # Update the UI
                if self.page:
                    self.update()


class ExpandableTextArea(ExpandableTextField):
    """Multiline version of ExpandableTextField.

    This is just an alias with multiline=True by default.
    """

    def __init__(self, db: DatabaseService, **kwargs):
        """Initialize expandable text area.

        Args:
            db: Database service instance
            **kwargs: Additional TextField arguments
        """
        # Set multiline defaults if not specified
        if 'multiline' not in kwargs:
            kwargs['multiline'] = True
        if 'min_lines' not in kwargs:
            kwargs['min_lines'] = 3

        super().__init__(db, **kwargs)
