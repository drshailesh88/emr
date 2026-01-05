#!/usr/bin/env python3
"""Test script for i18n translation system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from i18n import t, set_language, get_language, get_available_languages


def test_translations():
    """Test translation functionality."""

    print("=" * 60)
    print("DocAssist EMR - Translation System Test")
    print("=" * 60)
    print()

    # Test available languages
    print("Available languages:")
    languages = get_available_languages()
    for lang in languages:
        print(f"  - {lang['code']}: {lang['name']}")
    print()

    # Test English translations
    print("Testing English translations:")
    print(f"  Current language: {get_language()}")
    print(f"  patient.new: {t('patient.new')}")
    print(f"  patient.search: {t('patient.search')}")
    print(f"  patient.name: {t('patient.name')}")
    print(f"  patient.age: {t('patient.age')}")
    print(f"  patient.gender: {t('patient.gender')}")
    print(f"  patient.male: {t('patient.male')}")
    print(f"  patient.female: {t('patient.female')}")
    print(f"  common.save: {t('common.save')}")
    print(f"  common.cancel: {t('common.cancel')}")
    print()

    # Switch to Hindi
    print("Switching to Hindi...")
    set_language("hi")
    print()

    # Test Hindi translations
    print("Testing Hindi translations:")
    print(f"  Current language: {get_language()}")
    print(f"  patient.new: {t('patient.new')}")
    print(f"  patient.search: {t('patient.search')}")
    print(f"  patient.name: {t('patient.name')}")
    print(f"  patient.age: {t('patient.age')}")
    print(f"  patient.gender: {t('patient.gender')}")
    print(f"  patient.male: {t('patient.male')}")
    print(f"  patient.female: {t('patient.female')}")
    print(f"  common.save: {t('common.save')}")
    print(f"  common.cancel: {t('common.cancel')}")
    print()

    # Test formatted strings
    print("Testing formatted strings:")
    set_language("en")
    print(f"  EN - backup.minutes_ago: {t('backup.minutes_ago', minutes=15)}")
    print(f"  EN - backup.hours_ago: {t('backup.hours_ago', hours=3)}")

    set_language("hi")
    print(f"  HI - backup.minutes_ago: {t('backup.minutes_ago', minutes=15)}")
    print(f"  HI - backup.hours_ago: {t('backup.hours_ago', hours=3)}")
    print()

    # Test missing key (should return key itself)
    print("Testing missing key:")
    print(f"  missing.key: {t('missing.key')}")
    print()

    # Switch back to English
    set_language("en")
    print("Switched back to English")
    print(f"  Current language: {get_language()}")
    print()

    print("=" * 60)
    print("Translation system test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_translations()
