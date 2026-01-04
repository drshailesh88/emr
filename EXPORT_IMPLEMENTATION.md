# Data Export Implementation - DocAssist EMR

## Overview
Implemented complete data export functionality for DocAssist EMR based on spec `.specify/specs/06-data-export/spec.md`.

## Files Created

### 1. `/home/user/emr/src/services/export.py` (506 lines)
Complete export service with the following methods:

#### Single Patient Exports
- `export_patient_summary_pdf(patient_id, output_path)` - Export complete patient history as PDF
  - Includes demographics, all visits with diagnoses, all investigations in table format, all procedures
  - Professional formatting matching existing prescription PDF style
  - Auto-generates filename with patient name and timestamp

- `export_patient_json(patient_id, output_path)` - Export patient data as JSON
  - Complete patient record with all related visits, investigations, and procedures
  - Machine-readable format for data portability

#### Bulk Exports
- `export_all_patients_csv(output_path)` - Export all patients to CSV
- `export_all_visits_csv(output_path)` - Export all visits to CSV
- `export_all_investigations_csv(output_path)` - Export all investigations to CSV
- `export_all_procedures_csv(output_path)` - Export all procedures to CSV
- `export_full_database_json(output_path)` - Export entire database as JSON bundle

#### Features
- UTF-8 with BOM encoding for Excel compatibility on CSV files
- Auto-generated filenames with timestamps
- Default export location: `data/exports/`
- Proper handling of newlines and special characters in CSV
- Progress-friendly design (each method is synchronous and returns path)

## Files Modified

### 2. `/home/user/emr/src/ui/settings_dialog.py`
Added complete "Export" tab to settings dialog:
- Single patient export section (PDF & JSON) - only enabled when patient is selected
- Bulk export section with all CSV and JSON options
- Real-time status messages (success/error)
- Disabled state for patient exports when no patient selected
- Clear user feedback with file paths on success

New methods:
- `_build_export_tab()` - Build export UI
- `_show_export_status(message, is_error)` - Display status messages
- `_on_export_patient_pdf(e)` - Handle patient PDF export
- `_on_export_patient_json(e)` - Handle patient JSON export
- `_on_export_patients_csv(e)` - Handle patients CSV export
- `_on_export_visits_csv(e)` - Handle visits CSV export
- `_on_export_investigations_csv(e)` - Handle investigations CSV export
- `_on_export_procedures_csv(e)` - Handle procedures CSV export
- `_on_export_full_database(e)` - Handle full database JSON export

### 3. `/home/user/emr/src/ui/app.py`
Integrated export service:
- Import `ExportService` class
- Initialize export service: `self.export = ExportService(db=self.db, pdf_service=self.pdf)`
- Pass export service and current patient ID to SettingsDialog

### 4. `/home/user/emr/src/services/__init__.py`
- Added `ExportService` to service exports

## Directory Structure

```
data/
├── exports/          # Created - All exports save here
│   ├── PatientSummary_<name>_<timestamp>.pdf
│   ├── Patient_<name>_<timestamp>.json
│   ├── Patients_<timestamp>.csv
│   ├── Visits_<timestamp>.csv
│   ├── Investigations_<timestamp>.csv
│   ├── Procedures_<timestamp>.csv
│   └── FullDatabase_<timestamp>.json
```

## Export Formats

### Patient Summary PDF
```
┌─────────────────────────────────────────────────┐
│              PATIENT SUMMARY                     │
│                                                  │
│ Patient Information                              │
│ ──────────────────────────────────────────────  │
│ Name: Ram Lal                                    │
│ UHID: EMR-2024-0001                             │
│ Age: 65 years                                    │
│ Gender: Male                                     │
│                                                  │
│ Visit History                                    │
│ ──────────────────────────────────────────────  │
│ Visit 1 - 2026-01-02                            │
│   Chief Complaint: Chest pain                    │
│   Diagnosis: Unstable Angina                     │
│   Medications:                                   │
│     - Aspirin 150mg                             │
│     - Atorvastatin 40mg                         │
│                                                  │
│ Investigation Results                            │
│ ──────────────────────────────────────────────  │
│ Date       | Test      | Result  | Reference    │
│ 2026-01-02 | Creat     | 1.4*    | 0.7-1.3     │
│ 2026-01-02 | HbA1c     | 7.2     | <6.5        │
│                                                  │
│ Procedures                                       │
│ ──────────────────────────────────────────────  │
│ 1. Coronary Angiography - 2025-11-01           │
│    Details: LAD 80% stenosis                    │
└─────────────────────────────────────────────────┘
```

### CSV Format (Patients)
```csv
uhid,name,age,gender,phone,address,created_at
EMR-2024-0001,Ram Lal,65,M,9876543210,"123 Street, City",2024-01-15
EMR-2024-0002,Priya Sharma,45,F,8765432109,"456 Road, Town",2024-02-20
```

### JSON Bundle
```json
{
  "export_version": "1.0",
  "exported_at": "2026-01-02T10:30:00",
  "patient_count": 150,
  "visit_count": 450,
  "investigation_count": 800,
  "procedure_count": 25,
  "patients": [...],
  "visits": [...],
  "investigations": [...],
  "procedures": [...]
}
```

## Usage

### From UI
1. Open Settings (Ctrl+,)
2. Navigate to "Export" tab
3. Choose export type:
   - **Single Patient**: Select a patient first, then export as PDF or JSON
   - **Bulk Data**: Export all data as CSV or JSON
4. Click export button
5. Success message shows file path

### Programmatically
```python
from src.services.database import DatabaseService
from src.services.pdf import PDFService
from src.services.export import ExportService

# Initialize
db = DatabaseService()
pdf = PDFService()
export = ExportService(db=db, pdf_service=pdf)

# Export patient summary
pdf_path = export.export_patient_summary_pdf(patient_id=1)

# Export all patients to CSV
csv_path = export.export_all_patients_csv()

# Export full database
json_path = export.export_full_database_json()
```

## Acceptance Criteria Status

- ✅ "Export" option in settings dialog (new Export tab)
- ✅ Export dialog shows format options (PDF, CSV, JSON)
- ✅ Export dialog shows scope (single patient, all data)
- ✅ Single patient PDF includes all history
- ✅ CSV files are Excel-compatible (UTF-8 BOM)
- ✅ JSON export is valid and complete
- ✅ Progress indication via status messages
- ✅ Success message with file location

## Technical Details

### CSV Encoding
- Uses `utf-8-sig` encoding (UTF-8 with BOM)
- Ensures Excel compatibility on Windows
- Proper CSV quoting for text fields with newlines

### PDF Generation
- Uses existing fpdf2 patterns from PDFService
- Professional formatting with tables for investigations
- Auto-page-break for long patient histories

### JSON Export
- Uses Pydantic model serialization (model_dump)
- ISO format for dates/datetimes
- Custom serializer for date objects (default=str)

### File Naming
- Sanitizes patient names for filesystem safety
- Includes timestamp in format YYYYMMDD_HHMMSS
- Prevents filename collisions

### Error Handling
- ValueError for patient not found
- Graceful exception handling in UI
- Error messages shown to user in red

## Testing

Use `test_export.py` to test all export functions:
```bash
python3 test_export.py
```

This will:
1. Test patient summary PDF export
2. Test patient JSON export
3. Test all CSV exports
4. Test full database JSON export
5. Display file paths for verification

## Performance

All exports are synchronous (not threaded) because:
- Export operations are relatively fast
- User expects immediate feedback
- File I/O is the bottleneck (not CPU)
- Can be enhanced later with threading if needed

## Privacy Note

The implementation includes a note in the UI:
> "Note: All exports are saved to data/exports/ folder with timestamp. CSV files are Excel-compatible (UTF-8 with BOM)."

Exports contain PHI (Protected Health Information) - users should be cautious about sharing exported files.

## Future Enhancements (Out of Scope)

- Import from other EMR systems
- Selective field export
- Encrypted export
- Background export with progress bars
- Email export directly
- Cloud backup integration

## Dependencies

No new dependencies added. Uses existing:
- fpdf2 (PDF generation)
- csv (built-in)
- json (built-in)
- pathlib (built-in)

---
*Implementation completed: 2026-01-02*
