# Feature: Data Export

> Enable doctors to export patient data for portability and analysis

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, data is locked in SQLite. Doctors may need to:
- Share patient records with another doctor
- Analyze their practice patterns
- Migrate to another system
- Print a patient's complete history

## User Stories

### Primary User Story
**As a** doctor
**I want to** export patient data
**So that** I can share records, analyze trends, or migrate systems

### Additional Stories
- As a doctor, I want to export a single patient's complete record as PDF
- As a doctor, I want to export all data as CSV for spreadsheet analysis
- As a doctor, I want to export data in a standard format for migration

## Requirements

### Functional Requirements

**Single Patient Export:**
1. **FR-1**: Export patient summary as PDF (demographics + all visits + labs + procedures)
2. **FR-2**: Export patient data as JSON (machine-readable)

**Bulk Export:**
3. **FR-3**: Export all patients as CSV
4. **FR-4**: Export all visits as CSV
5. **FR-5**: Export all investigations as CSV
6. **FR-6**: Export all procedures as CSV
7. **FR-7**: Export complete database as JSON bundle

**Export UI:**
8. **FR-8**: Export menu in toolbar (Settings → Export)
9. **FR-9**: Choose export format and scope
10. **FR-10**: Choose destination folder

### Non-Functional Requirements
1. **NFR-1**: Export must work offline
2. **NFR-2**: CSV must be Excel-compatible (UTF-8 BOM)
3. **NFR-3**: Export 1000 patients in < 60 seconds
4. **NFR-4**: Progress indicator for large exports

## Acceptance Criteria

- [ ] "Export" option in settings/toolbar menu
- [ ] Export dialog shows format options (PDF, CSV, JSON)
- [ ] Export dialog shows scope (single patient, all data)
- [ ] Single patient PDF includes all history
- [ ] CSV files open correctly in Excel
- [ ] JSON export is valid and complete
- [ ] Progress bar for large exports
- [ ] Success message with file location

## Export Formats

### Patient Summary PDF
```
┌─────────────────────────────────────────────────────────┐
│                    PATIENT SUMMARY                      │
│                                                         │
│ Name: Ram Lal              UHID: EMR-2024-0001         │
│ Age/Gender: 65/M           Phone: 9876543210           │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ VISIT HISTORY                                           │
│ ─────────────────────────────────────────────────────── │
│ 2026-01-02 | Chest pain, SOB | Unstable Angina         │
│ 2025-12-15 | Follow-up      | HTN - controlled         │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ INVESTIGATIONS                                          │
│ ─────────────────────────────────────────────────────── │
│ Date       | Test         | Result  | Ref Range        │
│ 2026-01-02 | Creatinine   | 1.4*    | 0.7-1.3          │
│ 2025-12-15 | HbA1c        | 7.2     | <6.5             │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ PROCEDURES                                              │
│ ─────────────────────────────────────────────────────── │
│ 2025-11-01 | Coronary Angiography | Normal LV function │
└─────────────────────────────────────────────────────────┘
```

### CSV Format (patients.csv)
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
  "patients": [...],
  "visits": [...],
  "investigations": [...],
  "procedures": [...]
}
```

## Out of Scope

- Import from other EMR systems
- Selective field export
- Encrypted export

## Dependencies

- PDF service (extend existing)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PHI exposure in exports | Privacy breach | Warn user, no auto-share |
| Large export crashes | User frustration | Streaming export, chunking |
| CSV encoding issues | Data corruption | Use UTF-8 BOM for Excel |

## Open Questions

- [x] Default export location? **Decision: data/exports/ with timestamp**
- [x] Include deleted records? **Decision: No, only active records**

---
*Spec created: 2026-01-02*
