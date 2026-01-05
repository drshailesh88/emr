# i18n Quick Reference Card

## Import

```python
from ..i18n import t, set_language, get_language
```

## Basic Usage

```python
# Translate a string
label = t("patient.name")  # "Name" or "नाम"

# Format string with variables
msg = t("backup.hours_ago", hours=3)  # "3h ago" or "3 घंटे पहले"

# Get current language
lang = get_language()  # "en" or "hi"

# Change language
set_language("hi")  # Switch to Hindi
set_language("en")  # Switch to English
```

## Common Translation Keys

### Patient Management
```python
t("patient.new")         # New Patient / नया मरीज
t("patient.search")      # Search patients... / मरीज़ खोजें...
t("patient.name")        # Name / नाम
t("patient.age")         # Age / उम्र
t("patient.gender")      # Gender / लिंग
t("patient.phone")       # Phone / फ़ोन
t("patient.address")     # Address / पता
t("patient.male")        # Male / पुरुष
t("patient.female")      # Female / महिला
```

### Common Actions
```python
t("common.save")         # Save / सहेजें
t("common.cancel")       # Cancel / रद्द करें
t("common.delete")       # Delete / हटाएं
t("common.edit")         # Edit / संपादित करें
t("common.search")       # Search / खोजें
t("common.add")          # Add / जोड़ें
```

### Clinical Terms
```python
t("visit.chief_complaint")  # Chief Complaint / मुख्य शिकायत
t("visit.clinical_notes")   # Clinical Notes / चिकित्सा नोट्स
t("visit.diagnosis")        # Diagnosis / निदान
t("visit.prescription")     # Prescription / नुस्खा
t("visit.medications")      # Medications / दवाइयाँ
t("visit.follow_up")        # Follow Up / अगली मुलाकात
```

### Settings
```python
t("settings.title")         # Settings / सेटिंग्स
t("settings.doctor")        # Doctor / डॉक्टर
t("settings.clinic")        # Clinic / क्लिनिक
t("settings.preferences")   # Preferences / प्राथमिकताएं
t("settings.language")      # Language / भाषा
```

## Integration Example

Before:
```python
button = ft.ElevatedButton(
    text="New Patient",
    tooltip="Add new patient"
)
```

After:
```python
from ..i18n import t

button = ft.ElevatedButton(
    text=t("patient.new"),
    tooltip=t("patient.add_tooltip")
)
```

## Adding New Keys

1. Add to both JSON files:

**en.json:**
```json
{
  "my.new.key": "My English Text"
}
```

**hi.json:**
```json
{
  "my.new.key": "मेरा हिंदी टेक्स्ट"
}
```

2. Use in code:
```python
text = t("my.new.key")
```

## Testing

```bash
# Run test suite
python test_translations.py

# Quick test in Python
python3 -c "from src.i18n import t; print(t('patient.new'))"
```

## Language Switcher Location

Settings → Preferences → Language / भाषा

## Files

- **Translations**: `/home/user/emr/src/i18n/`
  - `en.json` - English
  - `hi.json` - Hindi
  - `translations.py` - Core engine

- **Documentation**:
  - `/home/user/emr/docs/I18N_IMPLEMENTATION.md` - Full guide
  - `/home/user/emr/HINDI_TRANSLATIONS_SUMMARY.md` - Summary

## Supported Languages

- 🇬🇧 English (`en`)
- 🇮🇳 Hindi (`hi`) - हिंदी

## Key Naming Convention

```
category.subcategory.item
```

Examples:
- `patient.name`
- `settings.doctor.name`
- `visit.medications`
- `common.save`

## Pro Tips

✓ Always use `t()` for UI strings
✓ Test in both languages
✓ Use descriptive key names
✓ Add keys to both en.json and hi.json
✓ Use format strings for dynamic content
✓ Check key spelling (case-sensitive)

✗ Don't hardcode UI strings
✗ Don't use generic key names (msg1, text2)
✗ Don't skip Hindi translation
✗ Don't forget to import `t`

---

For full documentation, see: `/home/user/emr/docs/I18N_IMPLEMENTATION.md`
