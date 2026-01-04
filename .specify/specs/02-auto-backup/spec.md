# Feature: Auto-Backup System

> Protect doctor's patient data with automatic, reliable backups

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, there is no backup mechanism. If the SQLite database or ChromaDB gets corrupted, all patient data is lost. For a medical practice, this is catastrophic - years of patient history could vanish.

## User Stories

### Primary User Story
**As a** doctor
**I want to** have my data automatically backed up
**So that** I never lose patient records even if my computer crashes

### Additional Stories
- As a doctor, I want to restore from a backup if something goes wrong
- As a doctor, I want to know when the last backup was taken
- As a doctor, I want backups to happen without slowing down my work
- As a doctor, I want to keep multiple backup versions in case recent ones are corrupted

## Requirements

### Functional Requirements
1. **FR-1**: Automatic backup on app startup
2. **FR-2**: Automatic backup on app close
3. **FR-3**: Automatic backup every N hours (configurable, default 4 hours)
4. **FR-4**: Manual backup trigger via UI
5. **FR-5**: Backup includes: SQLite DB, ChromaDB folder, settings
6. **FR-6**: Backup stored in timestamped zip files
7. **FR-7**: Keep last N backups (configurable, default 10)
8. **FR-8**: Restore from backup via UI
9. **FR-9**: Backup before any destructive operation (delete patient, etc.)
10. **FR-10**: Show last backup time in status bar

### Non-Functional Requirements
1. **NFR-1**: Backup must complete in < 30 seconds for typical practice (1000 patients)
2. **NFR-2**: Backup runs in background thread, no UI blocking
3. **NFR-3**: Backup file size optimized (zip compression)
4. **NFR-4**: Backup must be atomic (complete or not at all)

## Acceptance Criteria

- [ ] App creates backup on startup
- [ ] App creates backup on graceful close
- [ ] Background timer triggers backup every 4 hours
- [ ] Settings button opens backup/restore dialog
- [ ] Dialog shows list of available backups with timestamps
- [ ] "Backup Now" button creates immediate backup
- [ ] "Restore" button loads selected backup after confirmation
- [ ] Old backups beyond limit are auto-deleted
- [ ] Status bar shows "Last backup: X minutes ago"
- [ ] Deleting a patient triggers backup first

## Backup Structure

```
data/
├── clinic.db           # Active database
├── chroma/             # Active vector store
└── backups/
    ├── backup_2026-01-02_10-30-00.zip
    ├── backup_2026-01-02_14-30-00.zip
    └── backup_2026-01-02_18-30-00.zip
```

**Zip contents:**
```
backup_2026-01-02_10-30-00.zip
├── clinic.db
├── chroma/
│   └── [chroma files]
└── backup_manifest.json
    {
      "created_at": "2026-01-02T10:30:00",
      "version": "1.0",
      "patient_count": 150,
      "visit_count": 1200
    }
```

## Out of Scope

- Cloud backup (offline-first principle)
- Differential/incremental backups (full backup is simple and reliable)
- Backup encryption (future consideration)

## Dependencies

- None (uses standard library zipfile)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backup during active write corrupts data | High | Use SQLite backup API, not file copy |
| Disk full prevents backup | Medium | Check disk space before backup, warn user |
| User restores wrong backup | Medium | Show patient count, date in restore dialog |
| ChromaDB state inconsistent | Medium | Lock during backup, rebuild index on restore |

## Open Questions

- [x] Where to store backups? **Decision: data/backups/ folder**
- [x] Backup frequency? **Decision: 4 hours default, configurable**
- [x] How many to keep? **Decision: 10 default, configurable**

---
*Spec created: 2026-01-02*
