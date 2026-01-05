# Hindi UI Translation System - Implementation Guide

## Overview

DocAssist EMR now supports Hindi UI translations with a robust internationalization (i18n) system. The system allows seamless switching between English and Hindi with persistent language preferences.

## Files Created

### Core Translation System

1. **`/home/user/emr/src/i18n/__init__.py`**
   - Main module exports
   - Exposes `t`, `set_language`, `get_language`, `get_available_languages`

2. **`/home/user/emr/src/i18n/translations.py`**
   - Core translation engine
   - Lazy loading of translation files
   - Language persistence to `data/settings.json`
   - Format string support for dynamic values

3. **`/home/user/emr/src/i18n/en.json`**
   - English translation strings
   - ~120 translation keys covering all UI elements

4. **`/home/user/emr/src/i18n/hi.json`**
   - Hindi translation strings
   - Complete Hindi translations for all UI elements

### Updated Files

5. **`/home/user/emr/src/ui/settings_dialog.py`**
   - Added language switcher dropdown in Preferences tab
   - Language change handler with immediate feedback
   - Imports translation functions

6. **`/home/user/emr/src/ui/patient_panel.py`**
   - Example integration of translation system
   - All hardcoded strings replaced with `t()` calls
   - Patient list, dialogs, buttons, tooltips translated

### Test Files

7. **`/home/user/emr/test_translations.py`**
   - Comprehensive test script for translation system
   - Tests language switching, formatted strings, missing keys

## Usage Guide

### Basic Translation

To translate a string in your UI component:

```python
from ..i18n import t

# Simple translation
button_text = t("common.save")  # "Save" in EN, "सहेजें" in HI

# With format arguments
message = t("backup.minutes_ago", minutes=15)  # "15m ago" / "15 मिनट पहले"
```

### Language Switching

```python
from ..i18n import set_language, get_language

# Get current language
current = get_language()  # "en" or "hi"

# Change language
set_language("hi")  # Switch to Hindi
```

### Available Languages

```python
from ..i18n import get_available_languages

languages = get_available_languages()
# Returns: [
#   {"code": "en", "name": "English"},
#   {"code": "hi", "name": "हिंदी"}
# ]
```

## Translation Keys Structure

Translation keys follow a hierarchical naming convention:

```
category.subcategory.item
```

### Key Categories

#### Common Actions
- `common.save`, `common.cancel`, `common.delete`, `common.edit`
- `common.search`, `common.add`, `common.remove`, `common.close`
- `common.yes`, `common.no`, `common.ok`, `common.confirm`

#### Patient Management
- `patient.new`, `patient.add`, `patient.edit`, `patient.delete`
- `patient.name`, `patient.age`, `patient.gender`, `patient.phone`
- `patient.male`, `patient.female`, `patient.other`
- `patient.sections.favorites`, `patient.sections.today`, `patient.sections.recent`

#### Vitals
- `vitals.bp`, `vitals.pulse`, `vitals.spo2`, `vitals.temperature`
- `vitals.weight`, `vitals.height`, `vitals.bmi`

#### Visits & Clinical
- `visit.chief_complaint`, `visit.clinical_notes`, `visit.diagnosis`
- `visit.prescription`, `visit.medications`, `visit.investigations`
- `visit.follow_up`, `visit.red_flags`

#### Settings
- `settings.title`, `settings.doctor`, `settings.clinic`, `settings.preferences`
- `settings.doctor.name`, `settings.doctor.qualifications`
- `settings.clinic.name`, `settings.clinic.address`
- `settings.preferences.theme`, `settings.preferences.backup_frequency`

#### Backup & Export
- `backup.title`, `backup.status`, `backup.last_backup`
- `export.title`, `export.pdf`, `export.json`, `export.bulk`

#### Time Units
- `time.days`, `time.weeks`, `time.months`, `time.years`

## Adding New Translations

### Step 1: Add to JSON Files

Add the key-value pair to both `en.json` and `hi.json`:

**en.json:**
```json
{
  "prescription.generate": "Generate Prescription"
}
```

**hi.json:**
```json
{
  "prescription.generate": "नुस्खा बनाएं"
}
```

### Step 2: Use in Code

```python
from ..i18n import t

button = ft.ElevatedButton(
    text=t("prescription.generate"),
    on_click=generate_prescription
)
```

### Step 3: Test

```python
# Test in English
set_language("en")
print(t("prescription.generate"))  # "Generate Prescription"

# Test in Hindi
set_language("hi")
print(t("prescription.generate"))  # "नुस्खा बनाएं"
```

## Format String Examples

Translations support Python format string syntax:

**en.json:**
```json
{
  "patient.age_years": "{age} years",
  "backup.last_backup": "Last backup: {time}",
  "export.success": "Success! {type} saved to: {path}"
}
```

**Usage:**
```python
age_text = t("patient.age_years", age=25)
backup_text = t("backup.last_backup", time="2 hours ago")
export_text = t("export.success", type="PDF", path="/data/exports/file.pdf")
```

## Integration Checklist

When adding translations to a new UI component:

- [ ] Import translation function: `from ..i18n import t`
- [ ] Replace all hardcoded strings with `t("key")`
- [ ] Add tooltips translations: `tooltip=t("tooltip.key")`
- [ ] Translate dialog titles and messages
- [ ] Translate button labels
- [ ] Translate error messages
- [ ] Translate placeholder text (`hint_text`)
- [ ] Test both English and Hindi
- [ ] Verify format strings work correctly

## Example: Patient Panel Integration

Before:
```python
new_patient_btn = ft.ElevatedButton(
    text="New Patient",
    tooltip="Add new patient (Ctrl+N)",
)
```

After:
```python
from ..i18n import t

new_patient_btn = ft.ElevatedButton(
    text=t("patient.new"),
    tooltip=t("patient.add_tooltip"),
)
```

## Language Persistence

The selected language is automatically saved to `data/settings.json`:

```json
{
  "language": "hi"
}
```

On app restart, the last selected language is automatically loaded.

## UI Language Switcher

The language switcher is located in **Settings → Preferences** tab:

1. Open Settings dialog
2. Navigate to Preferences tab
3. Select language from "Language / भाषा" dropdown
4. Change takes effect immediately
5. A snackbar confirms the change

## Translation Coverage

Current translation coverage: **120+ strings**

### Covered Areas
✅ Patient management (list, add, edit, delete)
✅ Search and navigation
✅ Settings dialog (all tabs)
✅ Backup management
✅ Export features
✅ Common actions and buttons
✅ Tooltips and help text
✅ Error messages
✅ Time units

### To Be Translated (Future)
- [ ] Central panel (prescription form)
- [ ] Agent panel (RAG chat)
- [ ] Appointment scheduling
- [ ] Lab trends dialog
- [ ] WhatsApp integration
- [ ] Voice input features
- [ ] Audit history
- [ ] Template browser

## Testing

Run the test suite to verify translations:

```bash
python test_translations.py
```

Expected output:
```
============================================================
DocAssist EMR - Translation System Test
============================================================

Available languages:
  - hi: हिंदी
  - en: English

Testing English translations:
  patient.new: New Patient
  patient.search: Search patients...
  ...

Testing Hindi translations:
  patient.new: नया मरीज
  patient.search: मरीज़ खोजें...
  ...

Translation system test completed successfully!
```

## Best Practices

1. **Use Descriptive Keys**: `patient.delete_confirm_title` is better than `msg1`
2. **Consistent Naming**: Follow the `category.subcategory.item` pattern
3. **Group Related Keys**: Keep patient-related keys under `patient.*`
4. **Test Both Languages**: Always verify Hindi translations render correctly
5. **Avoid Hardcoding**: Never hardcode UI strings, always use `t()`
6. **Format Strings**: Use `{variable}` for dynamic content
7. **Fallback Gracefully**: Missing keys return the key itself (not an error)

## Troubleshooting

### Translation Not Showing

1. Check key exists in both `en.json` and `hi.json`
2. Verify `t()` function is imported
3. Ensure key name is correct (case-sensitive)
4. Check for typos in key name

### Hindi Text Not Rendering

1. Ensure UTF-8 encoding in JSON files
2. Verify font supports Devanagari script
3. Check `ensure_ascii=False` in JSON write operations

### Language Not Persisting

1. Check `data/settings.json` file exists and is writable
2. Verify `set_language()` is called correctly
3. Check file permissions on `data/` directory

## Future Enhancements

### Planned Features
1. **Dynamic Language Reload**: Refresh UI without app restart
2. **More Languages**: Add support for Tamil, Telugu, Bengali
3. **RTL Support**: Right-to-left language support
4. **Pluralization**: Handle singular/plural forms correctly
5. **Date/Time Formatting**: Locale-aware date formatting
6. **Number Formatting**: Indian number system (लाख, करोड़)

### Contributing Translations

To add a new language:

1. Create `/home/user/emr/src/i18n/{lang_code}.json`
2. Copy structure from `en.json`
3. Translate all values to target language
4. Add `_language_name` key with native name
5. Test with `test_translations.py`
6. Submit pull request

## Related Files

- Translation system: `/home/user/emr/src/i18n/`
- Settings dialog: `/home/user/emr/src/ui/settings_dialog.py`
- Patient panel: `/home/user/emr/src/ui/patient_panel.py`
- Test script: `/home/user/emr/test_translations.py`

## Support

For issues or questions about the translation system:
- Check this documentation first
- Review example usage in `patient_panel.py`
- Run `test_translations.py` to verify setup
- Check translation key spelling in JSON files

---

**Translation System Version**: 1.0
**Last Updated**: 2026-01-05
**Status**: Production Ready ✅
