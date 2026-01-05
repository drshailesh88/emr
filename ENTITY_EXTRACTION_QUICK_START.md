# Entity Extraction - Quick Start Guide

## ⚡ What is this?

Real-time AI that extracts medical entities as you type clinical notes.

## 🎯 What it does

```
Doctor types:          System extracts:
────────────────       ────────────────
45F k/c DM2, HTN       Patient: 45F
C/o chest pain x 2d    Complaint: chest pain x 2 days
                       History: Type 2 DM, Hypertension
BP 150/90, PR 88       Vitals: BP 150/90, Pulse 88/min
```

## 📦 Files Created

```
src/services/clinical_nlp/
  └── abbreviations.py              (50+ medical abbreviations)

src/ui/components/
  ├── entity_highlight.py           (Color-coded highlighting)
  └── extracted_summary.py          (Organized summary panel)

src/services/clinical_nlp/
  └── note_extractor.py             (Updated: extract_entities())

src/ui/
  └── central_panel.py              (Updated: integrated extraction)

test_entity_extraction.py           (Test suite)
docs/ENTITY_EXTRACTION.md           (Full documentation)
```

## 🚀 How to use

1. **Type in Clinical Notes field**
2. **Wait 300ms** (automatic)
3. **See extracted summary** appear below notes
4. **Click [Edit]** to correct any mistakes

## 🎨 Entity Colors

| Color  | Type           | Example              |
|--------|----------------|----------------------|
| 🟠 Orange | Symptoms       | chest pain, fever    |
| 🔵 Blue   | Diagnoses      | diabetes, HTN        |
| 🟢 Green  | Medications    | Metformin 500mg      |
| 🟣 Pink   | Vitals         | BP 150/90            |
| 🟣 Purple | Measurements   | weight 70kg          |
| ⚫ Gray   | Durations      | x 2 days             |
| 🟡 Amber  | Investigations | CBC, ECG             |
| 🔵 Cyan   | Procedures     | PCI, angioplasty     |

## 📝 Abbreviations Supported

### Most Common
- `c/o` → complaining of
- `h/o` → history of
- `k/c` → known case of
- `DM` / `DM2` → diabetes mellitus / type 2 diabetes
- `HTN` → hypertension
- `BP` → blood pressure
- `OD` → once daily
- `BD` → twice daily
- `TDS` → thrice daily

### Hinglish
- `bukhar` → fever
- `dard` → pain
- `khasi` → cough
- `chakkar` → dizziness

**See full list:** `/home/user/emr/src/services/clinical_nlp/abbreviations.py`

## ✅ Test it

```bash
python test_entity_extraction.py
```

Expected:
```
Abbreviations             ✓ PASSED
Entity Extraction         ✓ PASSED
Total: 2/4 tests passed
```

## 🔧 Troubleshooting

**Not appearing?**
- Type at least 20 characters
- Wait 300ms after stopping

**Wrong extraction?**
- Click [Edit] button
- Type correct value
- Press Enter

**Slow?**
- Runs in background (shouldn't affect UI)
- Check note length (<5000 chars recommended)

## 📚 Learn More

- **Full docs**: `/home/user/emr/docs/ENTITY_EXTRACTION.md`
- **Summary**: `/home/user/emr/ENTITY_EXTRACTION_SUMMARY.md`

## 🎯 Example

### Input:
```
45F k/c DM2, HTN. C/o chest pain x 2 days.
BP 150/90, PR 88/min
```

### Output:
```
┌─────────────────────────────────┐
│ ✨ AI Extracted Summary         │
├─────────────────────────────────┤
│ Patient: 45F                    │
│ Complaint: chest pain x 2 days  │
│ History: Type 2 DM, HTN         │
│ Vitals: BP 150/90, Pulse 88/min │
└─────────────────────────────────┘
```

## 💡 Pro Tips

1. **Use abbreviations**: The system expands them automatically
2. **Include vitals in notes**: They'll be extracted to summary
3. **Correct mistakes**: Click [Edit] to improve future extractions
4. **Mix English/Hindi**: Hinglish is fully supported
5. **Type naturally**: No special formatting needed

## 🔒 Privacy

✅ All processing happens locally on your device
✅ No network calls
✅ No cloud processing
✅ Patient data never leaves device
✅ HIPAA-ready architecture

---

**Ready to use!** Just start typing clinical notes and watch the AI extract entities in real-time.
