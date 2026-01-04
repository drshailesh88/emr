# Feature: Recent Patients & Favorites

> Quick access to frequently seen and recently accessed patients

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Doctors often see the same patients for follow-ups. Scrolling through a long patient list or searching every time wastes time. Quick access to recent and favorite patients would speed up workflows.

## User Stories

### Primary User Story
**As a** doctor
**I want to** quickly access patients I saw recently
**So that** I don't have to search for them every time

### Additional Stories
- As a doctor, I want to pin frequent patients as favorites
- As a doctor, I want to see today's patients at the top
- As a doctor, I want to quickly switch between patients I'm comparing

## Requirements

### Functional Requirements

**Recent Patients:**
1. **FR-1**: Show last 10 accessed patients at top of list
2. **FR-2**: "Recent" section in patient panel
3. **FR-3**: Auto-update when patient is selected
4. **FR-4**: Clear recent list option

**Favorite Patients:**
5. **FR-5**: Star/pin patients as favorites
6. **FR-6**: Favorites section above recents
7. **FR-7**: Favorites persist across sessions
8. **FR-8**: Unstar to remove from favorites

**Today's Patients:**
9. **FR-9**: Show patients with visits today
10. **FR-10**: Visual indicator for "seen today"

**Quick Switch:**
11. **FR-11**: `Ctrl+Tab` cycles through last 5 patients
12. **FR-12**: History dropdown for quick switch

### Non-Functional Requirements
1. **NFR-1**: Recent list updates instantly
2. **NFR-2**: Maximum 10 recents, 20 favorites
3. **NFR-3**: Favorites survive database migration

## Acceptance Criteria

- [ ] Patient panel shows sections: Favorites → Today → Recent → All
- [ ] Selecting patient adds to recent list
- [ ] Star icon on patient card toggles favorite
- [ ] Favorites section shows starred patients
- [ ] Today section shows patients with visits today
- [ ] `Ctrl+Tab` opens quick-switch popup
- [ ] Clear option for recent list

## UI Design

### Patient Panel Sections
```
┌─────────────────────────────────────┐
│ PATIENTS                            │
├─────────────────────────────────────┤
│ [🔍 Search patients...]             │
├─────────────────────────────────────┤
│ ⭐ FAVORITES                        │
│ ├── Ram Lal (M, 65) ⭐              │
│ └── Priya Sharma (F, 45) ⭐         │
├─────────────────────────────────────┤
│ 📅 TODAY (3)                        │
│ ├── Amit Kumar (M, 50) 🕐           │
│ ├── Sunita Devi (F, 62) 🕐          │
│ └── Vijay Singh (M, 38) 🕐          │
├─────────────────────────────────────┤
│ 🕐 RECENT                           │
│ ├── Ram Lal (M, 65)                 │
│ ├── Mohan Das (M, 72)               │
│ ├── Kavita Jain (F, 55)             │
│ └── [Clear recent]                  │
├─────────────────────────────────────┤
│ ALL PATIENTS                        │
│ ├── Arun Bhatt (M, 45)              │
│ ├── Deepa Nair (F, 33)              │
│ └── ...                             │
└─────────────────────────────────────┘
```

### Quick Switch Popup (Ctrl+Tab)
```
┌─────────────────────────────────┐
│ Quick Switch                    │
├─────────────────────────────────┤
│ → Ram Lal (M, 65)              │ ← currently selected
│   Priya Sharma (F, 45)         │
│   Amit Kumar (M, 50)           │
│   Mohan Das (M, 72)            │
│   Kavita Jain (F, 55)          │
├─────────────────────────────────┤
│ ↑↓ Navigate  Enter: Select     │
└─────────────────────────────────┘
```

## Database Changes

```sql
-- Add favorite flag to patients
ALTER TABLE patients ADD COLUMN is_favorite INTEGER DEFAULT 0;

-- Track access history
CREATE TABLE patient_access_log (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    accessed_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE INDEX idx_access_patient ON patient_access_log(patient_id);
CREATE INDEX idx_access_time ON patient_access_log(accessed_at DESC);
```

## Out of Scope

- Patient groups/tags
- Multiple favorite lists
- Smart suggestions based on schedule

## Dependencies

- Keyboard Shortcuts (Ctrl+Tab)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Access log grows large | Storage bloat | Keep only last 100 accesses per patient |
| Too many sections clutters UI | Confusion | Collapsible sections |
| Favorites lost on reinstall | User frustration | Include in backup |

## Open Questions

- [x] How many recents? **Decision: 10**
- [x] How many favorites max? **Decision: 20**
- [x] Show time in recent? **Decision: No, just order**

---
*Spec created: 2026-01-02*
