# DocAssist EMR - Internationalization (i18n)

This directory contains the internationalization system for DocAssist EMR.

## Files

- `__init__.py` - Module exports
- `translations.py` - Core translation engine
- `en.json` - English translations
- `hi.json` - Hindi translations (हिंदी)

## Quick Start

### Import

```python
from ..i18n import t, set_language, get_language
```

### Translate Strings

```python
# Simple translation
label = t("patient.name")  # "Name" or "नाम"

# With format arguments
message = t("backup.hours_ago", hours=3)  # "3h ago" or "3 घंटे पहले"
```

### Change Language

```python
set_language("hi")  # Switch to Hindi
set_language("en")  # Switch to English
```

### Get Current Language

```python
current = get_language()  # Returns "en" or "hi"
```

## Translation Keys

All translation keys follow the pattern: `category.subcategory.item`

### Examples

- `patient.new` - "New Patient" / "नया मरीज"
- `common.save` - "Save" / "सहेजें"
- `settings.title` - "Settings" / "सेटिंग्स"
- `visit.diagnosis` - "Diagnosis" / "निदान"

## Adding New Translations

1. Add key-value to both `en.json` and `hi.json`
2. Use `t("your.key")` in your UI code
3. Test with both languages

## Testing

Run the test script:

```bash
python test_translations.py
```

## Documentation

Full documentation: `/home/user/emr/docs/I18N_IMPLEMENTATION.md`

## Current Coverage

✅ 120+ translation keys
✅ Patient management
✅ Settings and preferences
✅ Backup and export
✅ Common actions
✅ Error messages

## Language Support

- 🇬🇧 English (`en`)
- 🇮🇳 Hindi (`hi`) - हिंदी

More languages coming soon!
