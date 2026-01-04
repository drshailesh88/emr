# Feature: Appointment Calendar

> Basic appointment scheduling to know who's coming when

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, there's no way to track appointments. Doctors use separate systems (paper, Google Calendar) for scheduling. A simple built-in calendar would streamline the workflow by showing who's coming today.

## User Stories

### Primary User Story
**As a** doctor
**I want to** see my appointments for the day
**So that** I know who's coming and when

### Additional Stories
- As a doctor, I want to schedule follow-up when ending a visit
- As a doctor, I want to see appointments for the week
- As a staff, I want to book appointments over phone

## Requirements

### Functional Requirements

**Appointment Management:**
1. **FR-1**: Create appointment (patient, date, time, type)
2. **FR-2**: View daily appointment list
3. **FR-3**: View weekly calendar
4. **FR-4**: Edit/cancel appointments
5. **FR-5**: Link appointment to patient record

**Quick Scheduling:**
6. **FR-6**: "Schedule Follow-up" button after visit
7. **FR-7**: Suggest follow-up date based on prescription
8. **FR-8**: Show available slots

**Views:**
9. **FR-9**: Today's appointments in sidebar
10. **FR-10**: Calendar view (day/week)
11. **FR-11**: Filter by appointment type

**Status:**
12. **FR-12**: Mark as: Scheduled, Arrived, In-Progress, Completed, No-Show
13. **FR-13**: Auto-mark as completed when visit saved

### Non-Functional Requirements
1. **NFR-1**: View today's appointments in < 100ms
2. **NFR-2**: Works offline
3. **NFR-3**: Simple - not a full practice management system

## Acceptance Criteria

- [ ] Can create new appointment
- [ ] Today's appointments show in sidebar
- [ ] Calendar view shows week
- [ ] Can click patient name to open record
- [ ] Appointment status updates work
- [ ] "Schedule Follow-up" works from visit
- [ ] Completed visit marks appointment done

## Database Schema

```sql
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT,
    duration_minutes INTEGER DEFAULT 15,
    appointment_type TEXT DEFAULT 'follow-up',
        -- 'new', 'follow-up', 'procedure', 'lab-review'
    status TEXT DEFAULT 'scheduled',
        -- 'scheduled', 'confirmed', 'arrived', 'in-progress', 'completed', 'cancelled', 'no-show'
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE INDEX idx_appt_date ON appointments(appointment_date);
CREATE INDEX idx_appt_patient ON appointments(patient_id);
CREATE INDEX idx_appt_status ON appointments(status);
```

## Appointment Types

| Type | Color | Duration |
|------|-------|----------|
| New Patient | Blue | 30 min |
| Follow-up | Green | 15 min |
| Procedure | Orange | 45 min |
| Lab Review | Purple | 10 min |

## UI Design

### Today's Appointments (Sidebar)
```
┌─────────────────────────────────────┐
│ 📅 TODAY (5 appointments)           │
├─────────────────────────────────────┤
│ 09:00 🔵 Ram Lal - New              │
│ 09:30 🟢 Priya Sharma - F/U     ✓  │
│ 10:00 🟢 Amit Kumar - F/U       →  │ ← In progress
│ 10:15 🟢 Sunita Devi - F/U          │
│ 10:30 🟣 Vijay Singh - Labs         │
├─────────────────────────────────────┤
│ [+ New Appointment]                 │
└─────────────────────────────────────┘
```

### Calendar View
```
┌──────────────────────────────────────────────────────────────────┐
│ [<] January 2026 [>]                          [Day] [Week] [Mo] │
├────────┬────────┬────────┬────────┬────────┬────────┬────────────┤
│  Mon   │  Tue   │  Wed   │  Thu   │  Fri   │  Sat   │    Sun     │
│   5    │   6    │   7    │   8    │   9    │  10    │    11      │
├────────┼────────┼────────┼────────┼────────┼────────┼────────────┤
│ 09:00  │ 09:00  │ 09:00  │ 09:30  │ 10:00  │        │            │
│ Ram L. │ Priya  │ Amit   │ Sunita │ Mohan  │ OFF    │   OFF      │
│        │        │        │        │        │        │            │
│ 10:00  │ 09:30  │        │ 11:00  │ 11:00  │        │            │
│ Kumar  │ Vijay  │        │ Deepa  │ Kavita │        │            │
└────────┴────────┴────────┴────────┴────────┴────────┴────────────┘
```

### Schedule Follow-up Dialog
```
┌─────────────────────────────────────────┐
│ Schedule Follow-up                  [X] │
├─────────────────────────────────────────┤
│                                         │
│ Patient: Ram Lal                        │
│                                         │
│ Suggested: 2 weeks (as per prescription)│
│                                         │
│ Date: [📅 16-Jan-2026    ]              │
│ Time: [10:00 AM       ▼]                │
│ Type: [Follow-up      ▼]                │
│                                         │
│ Notes: [DM follow-up with labs    ]     │
│                                         │
├─────────────────────────────────────────┤
│              [Cancel]  [Schedule]       │
└─────────────────────────────────────────┘
```

## Integration Points

1. **Visit Completion**: Offer to schedule follow-up
2. **Patient Panel**: Show next appointment
3. **Today Widget**: Quick view of daily schedule
4. **Prescription**: Parse follow-up text for suggested date

## Out of Scope

- Online booking by patients
- SMS/email reminders (separate feature)
- Room/resource scheduling
- Staff scheduling
- Revenue/billing

## Dependencies

- Patient database

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-engineering scheduling | Complex, slow | Keep minimal features |
| Conflicts with existing calendar | Confusion | Easy export to Google/iCal |
| Doctor doesn't use it | Wasted effort | Make it optional, not mandatory |

## Open Questions

- [x] Time slots or free-form? **Decision: Free-form time entry, simple**
- [x] Multiple doctors? **Decision: No, single doctor assumption**
- [x] Working hours config? **Decision: Future enhancement**

---
*Spec created: 2026-01-02*
