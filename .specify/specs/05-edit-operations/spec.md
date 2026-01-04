# Feature: Edit Operations

> Complete CRUD operations for all clinical data

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, visits, investigations, and procedures can only be created, not edited or deleted. Doctors make mistakes and need to correct records. The incomplete CRUD makes the system frustrating to use.

## User Stories

### Primary User Story
**As a** doctor
**I want to** edit and delete clinical records
**So that** I can correct mistakes and keep accurate patient history

### Additional Stories
- As a doctor, I want to edit a past visit if I made a typo
- As a doctor, I want to delete a duplicate investigation entry
- As a doctor, I want to correct a procedure date if entered wrong
- As a doctor, I want to update patient demographics

## Requirements

### Functional Requirements

**Visits:**
1. **FR-1**: Edit existing visit (complaint, notes, diagnosis, prescription)
2. **FR-2**: Delete visit (soft delete with confirmation)
3. **FR-3**: Show edit/delete buttons on visit history items

**Investigations:**
4. **FR-4**: Edit investigation (result, date, reference range)
5. **FR-5**: Delete investigation (soft delete)
6. **FR-6**: Bulk add investigations (common for lab reports)

**Procedures:**
7. **FR-7**: Edit procedure (name, details, date, notes)
8. **FR-8**: Delete procedure (soft delete)

**Patients:**
9. **FR-9**: Edit patient demographics (already partially exists, complete it)
10. **FR-10**: Delete patient (soft delete, requires confirmation)

### Non-Functional Requirements
1. **NFR-1**: All deletes are soft deletes (is_deleted flag)
2. **NFR-2**: All edits trigger audit log
3. **NFR-3**: Confirmation dialog for delete operations
4. **NFR-4**: Backup triggered before delete

## Acceptance Criteria

- [ ] Visit history shows edit/delete icons
- [ ] Clicking edit opens visit in editable mode
- [ ] Save updates the visit, logs to audit
- [ ] Clicking delete shows confirmation dialog
- [ ] Confirmed delete sets is_deleted=true
- [ ] Deleted items hidden from normal view
- [ ] Investigation list shows edit/delete icons
- [ ] Procedure list shows edit/delete icons
- [ ] Patient can be edited (all fields)
- [ ] Patient can be deleted (with strong warning)

## UI Integration

### Visit History with Edit/Delete
```
┌─────────────────────────────────────────────────────────┐
│ Visit History                                           │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2026-01-02                              [✏️] [🗑️] │ │
│ │ Chest pain, SOB                                     │ │
│ │ Dx: Unstable Angina                                 │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2025-12-15                              [✏️] [🗑️] │ │
│ │ Follow-up                                           │ │
│ │ Dx: Hypertension - controlled                       │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Delete Confirmation Dialog
```
┌──────────────────────────────────────────┐
│ ⚠️ Delete Visit?                         │
├──────────────────────────────────────────┤
│                                          │
│ This will delete the visit from          │
│ 2026-01-02 for Ram Lal.                  │
│                                          │
│ The record will be soft-deleted and      │
│ can be recovered from backups.           │
│                                          │
├──────────────────────────────────────────┤
│           [Cancel]  [Delete]             │
└──────────────────────────────────────────┘
```

## Database Changes

```sql
-- Add soft delete columns to all tables
ALTER TABLE patients ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE visits ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE investigations ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE procedures ADD COLUMN is_deleted INTEGER DEFAULT 0;

-- Update all queries to filter deleted records
-- e.g., SELECT * FROM patients WHERE is_deleted = 0
```

## Out of Scope

- Undo delete (restore from backup instead)
- Bulk delete
- Merge duplicate patients

## Dependencies

- Audit Trail (FR-3 logs all changes)
- Auto-Backup (backup before delete)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accidental delete | Data loss | Confirmation dialog, soft delete |
| Edit overwrites important data | Loss of history | Audit trail preserves old values |
| Cascade delete issues | Orphan records | Soft delete doesn't cascade |

## Open Questions

- [x] Hard delete or soft delete? **Decision: Soft delete only**
- [x] Show deleted records anywhere? **Decision: No, only in backups**

---
*Spec created: 2026-01-02*
