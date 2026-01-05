"""Translation system for DocAssist EMR with language persistence."""

import json
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Global state
_current_language = "en"
_translations: Dict[str, Dict[str, str]] = {}
_settings_path = Path("data/settings.json")


def _load_translation_file(lang_code: str) -> Dict[str, str]:
    """Load translation file for a given language code.

    Args:
        lang_code: Language code (e.g., 'en', 'hi')

    Returns:
        Dictionary of translations
    """
    translations_dir = Path(__file__).parent
    translation_file = translations_dir / f"{lang_code}.json"

    if not translation_file.exists():
        logger.warning(f"Translation file not found: {translation_file}")
        return {}

    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load translation file {translation_file}: {e}")
        return {}


def _load_all_translations():
    """Load all available translation files."""
    global _translations

    translations_dir = Path(__file__).parent
    for translation_file in translations_dir.glob("*.json"):
        lang_code = translation_file.stem
        _translations[lang_code] = _load_translation_file(lang_code)

    logger.info(f"Loaded translations for languages: {list(_translations.keys())}")


def _load_language_from_settings() -> str:
    """Load saved language from settings file.

    Returns:
        Language code (defaults to 'en' if not found)
    """
    if not _settings_path.exists():
        return "en"

    try:
        with open(_settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get("language", "en")
    except Exception as e:
        logger.error(f"Failed to load language from settings: {e}")
        return "en"


def _save_language_to_settings(lang_code: str):
    """Save selected language to settings file.

    Args:
        lang_code: Language code to save
    """
    # Create data directory if it doesn't exist
    _settings_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing settings or create new
    settings = {}
    if _settings_path.exists():
        try:
            with open(_settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load existing settings: {e}")

    # Update language
    settings["language"] = lang_code

    # Save settings
    try:
        with open(_settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved language preference: {lang_code}")
    except Exception as e:
        logger.error(f"Failed to save language to settings: {e}")


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language.

    Args:
        key: Translation key
        **kwargs: Optional format arguments for the translation string

    Returns:
        Translated string, or the key itself if translation not found

    Example:
        t("patient.name")  # Returns "Name" in English or "नाम" in Hindi
        t("patient.age_years", age=25)  # Returns "25 years" or "25 साल"
    """
    global _current_language, _translations

    # Lazy load translations on first call
    if not _translations:
        _load_all_translations()
        # Load saved language preference
        _current_language = _load_language_from_settings()

    # Get translation for current language
    lang_translations = _translations.get(_current_language, {})
    translated = lang_translations.get(key, key)

    # Apply format arguments if provided
    if kwargs:
        try:
            translated = translated.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to format translation key '{key}': {e}")

    return translated


def set_language(lang_code: str) -> bool:
    """Set the current language.

    Args:
        lang_code: Language code (e.g., 'en', 'hi')

    Returns:
        True if language was set successfully, False otherwise
    """
    global _current_language, _translations

    # Load translations if not already loaded
    if not _translations:
        _load_all_translations()

    # Check if language is available
    if lang_code not in _translations:
        logger.warning(f"Language '{lang_code}' not available")
        return False

    _current_language = lang_code
    _save_language_to_settings(lang_code)
    logger.info(f"Language set to: {lang_code}")
    return True


def get_language() -> str:
    """Get the current language code.

    Returns:
        Current language code
    """
    global _current_language, _translations

    # Lazy load on first call
    if not _translations:
        _load_all_translations()
        _current_language = _load_language_from_settings()

    return _current_language


def get_available_languages() -> List[Dict[str, str]]:
    """Get list of available languages.

    Returns:
        List of dictionaries with 'code' and 'name' keys
    """
    global _translations

    # Load translations if not already loaded
    if not _translations:
        _load_all_translations()

    # Return language info
    languages = []
    for lang_code in _translations.keys():
        lang_translations = _translations[lang_code]
        language_name = lang_translations.get("_language_name", lang_code)
        languages.append({
            "code": lang_code,
            "name": language_name
        })

    return languages


# Initialize on module import
_load_all_translations()
if _settings_path.exists():
    _current_language = _load_language_from_settings()
