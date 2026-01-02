# Feature: Settings Persistence

> Save doctor and clinic configuration for personalized experience

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, doctor name is hardcoded as "Dr. " and clinic information exists only in PDF templates. Every installation looks the same. Doctors need to personalize with their name, qualifications, and clinic details.

## User Stories

### Primary User Story
**As a** doctor
**I want to** save my name and clinic details
**So that** prescriptions show my correct information

### Additional Stories
- As a doctor, I want my settings to persist across app restarts
- As a doctor, I want to configure backup frequency
- As a doctor, I want to set my preferred model size

## Requirements

### Functional Requirements
1. **FR-1**: Settings dialog accessible from toolbar
2. **FR-2**: Save doctor profile: name, qualifications, registration number
3. **FR-3**: Save clinic info: name, address, phone, email
4. **FR-4**: Save app preferences: backup frequency, model preference
5. **FR-5**: Settings persist to disk (JSON file)
6. **FR-6**: Settings loaded on app startup
7. **FR-7**: Settings used in PDF generation
8. **FR-8**: Settings backed up with regular backups

### Non-Functional Requirements
1. **NFR-1**: Settings file in human-readable JSON
2. **NFR-2**: Missing settings use sensible defaults
3. **NFR-3**: Settings load in < 100ms

## Acceptance Criteria

- [ ] Settings icon in toolbar opens settings dialog
- [ ] Dialog has tabs: Doctor, Clinic, Preferences
- [ ] Doctor tab: Name, Qualifications (MBBS, MD, etc.), Reg. Number
- [ ] Clinic tab: Clinic Name, Address (multiline), Phone, Email
- [ ] Preferences tab: Backup frequency, Model size override
- [ ] Save button persists to data/settings.json
- [ ] Cancel discards changes
- [ ] App loads settings on startup
- [ ] PDF shows doctor name from settings
- [ ] PDF shows clinic info from settings

## Settings Schema

```json
{
  "version": 1,
  "doctor": {
    "name": "Dr. Rajesh Kumar",
    "qualifications": "MBBS, MD (Medicine)",
    "registration_number": "MCI-12345"
  },
  "clinic": {
    "name": "Kumar Clinic",
    "address": "123 Main Street\nMumbai 400001",
    "phone": "+91 98765 43210",
    "email": "dr.kumar@clinic.com"
  },
  "preferences": {
    "backup_frequency_hours": 4,
    "backup_retention_count": 10,
    "model_override": null,
    "theme": "light"
  }
}
```

## UI Design

### Settings Dialog
```
┌──────────────────────────────────────────────────────┐
│ Settings                                         [X] │
├──────────────────────────────────────────────────────┤
│ [Doctor] [Clinic] [Preferences]                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Doctor Name:     [Dr. Rajesh Kumar          ]       │
│                                                      │
│  Qualifications:  [MBBS, MD (Medicine)       ]       │
│                                                      │
│  Reg. Number:     [MCI-12345                 ]       │
│                                                      │
│                                                      │
├──────────────────────────────────────────────────────┤
│                              [Cancel]  [Save]        │
└──────────────────────────────────────────────────────┘
```

## Out of Scope

- Multiple doctor profiles
- Clinic logo upload (future)
- Custom prescription templates

## Dependencies

- None

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Settings file corrupted | App fails to start | Fallback to defaults, warn user |
| Settings file deleted | Lost configuration | Include in backup |
| Schema version mismatch | Old settings incompatible | Version field, migration logic |

## Open Questions

- [x] Where to store settings? **Decision: data/settings.json**
- [x] Include in backup? **Decision: Yes**

---
*Spec created: 2026-01-02*
