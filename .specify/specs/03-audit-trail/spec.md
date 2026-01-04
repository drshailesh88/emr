# Feature: Audit Trail

> Track all changes to clinical data for accountability and compliance

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, there's no record of who changed what and when. In medical practice, this is critical for:
- Legal protection (proving what was recorded when)
- Debugging (understanding how data got into current state)
- Compliance (audit requirements)

## User Stories

### Primary User Story
**As a** doctor
**I want to** see the history of changes to any patient record
**So that** I can understand what was modified and when

### Additional Stories
- As a doctor, I want to know when a prescription was modified
- As a doctor, I want to see deleted records (soft delete)
- As a doctor, I want to prove the original entry time for legal purposes

## Requirements

### Functional Requirements
1. **FR-1**: Log all INSERT operations on clinical tables
2. **FR-2**: Log all UPDATE operations with before/after values
3. **FR-3**: Log all DELETE operations (soft delete - mark as deleted)
4. **FR-4**: Each log entry includes: timestamp, table, record_id, operation, old_value, new_value
5. **FR-5**: View audit history for any patient
6. **FR-6**: View audit history for any specific record (visit, investigation, etc.)
7. **FR-7**: Audit logs are append-only (cannot be modified or deleted)
8. **FR-8**: Show "Modified" indicator on records that have been edited

### Non-Functional Requirements
1. **NFR-1**: Audit logging must not slow down normal operations (< 10ms overhead)
2. **NFR-2**: Audit logs must be stored in same database (atomic with data changes)
3. **NFR-3**: Audit data must be included in backups

## Acceptance Criteria

- [ ] Creating a patient logs the INSERT
- [ ] Editing a patient logs UPDATE with old/new values
- [ ] Deleting a patient marks as deleted, logs DELETE
- [ ] Creating a visit logs INSERT
- [ ] Editing a visit logs UPDATE
- [ ] Patient detail view has "History" button showing audit trail
- [ ] Visit view shows "Edited" badge if modified after creation
- [ ] Audit log cannot be tampered with from UI
- [ ] Backup includes audit_log table

## Database Schema

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_value TEXT,  -- JSON of previous state
    new_value TEXT,  -- JSON of new state
    -- No foreign key - audit survives record deletion
    -- No user_id - single user system
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
```

## UI Integration

### Patient Detail View
```
┌──────────────────────────────────────────┐
│ Patient: Ram Lal                    [📋] │ ← History button
├──────────────────────────────────────────┤
│ UHID: EMR-2024-0001                      │
│ ...                                      │
└──────────────────────────────────────────┘
```

### Audit History Dialog
```
┌─────────────────────────────────────────────────────────┐
│ Audit History: Ram Lal                              [X] │
├─────────────────────────────────────────────────────────┤
│ 2026-01-02 10:30 │ VISIT    │ Created visit #45        │
│ 2026-01-02 09:15 │ PATIENT  │ Updated phone number     │
│                  │          │ Old: 9876543210          │
│                  │          │ New: 9876543211          │
│ 2026-01-01 14:00 │ INVEST.  │ Added Creatinine: 1.4    │
│ 2025-12-15 11:00 │ PATIENT  │ Created patient          │
└─────────────────────────────────────────────────────────┘
```

## Out of Scope

- User authentication (single doctor assumed)
- Audit log export (can be added later)
- Audit log search/filter (can be added later)

## Dependencies

- Soft delete support in database layer

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Audit log grows too large | Performance degradation | Archive old logs after 2 years |
| JSON storage inefficient | Storage bloat | Only store changed fields in UPDATE |
| Forgot to add audit trigger | Missing audit data | Add audit as decorator/wrapper |

## Open Questions

- [x] Store full record or just changed fields? **Decision: Changed fields only for UPDATE, full record for INSERT/DELETE**
- [x] UI to view audit log? **Decision: Dialog accessible from patient detail**

---
*Spec created: 2026-01-02*
