# Feature: Chronic Disease Flowsheets

> Structured tracking for diabetes, hypertension, and other chronic conditions

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Chronic diseases require tracking multiple parameters over time: HbA1c every 3 months, annual eye exam, foot exam, etc. Currently, doctors must manually remember what's due. Flowsheets would provide at-a-glance chronic disease management.

## User Stories

### Primary User Story
**As a** doctor
**I want to** see a structured flowsheet for chronic conditions
**So that** I can ensure comprehensive care and nothing is missed

### Additional Stories
- As a doctor, I want to see what screenings are overdue
- As a doctor, I want to track DM control with HbA1c trends
- As a doctor, I want to see HTN control with BP trends
- As a doctor, I want to mark when annual exams are done

## Requirements

### Functional Requirements

**Flowsheet Types:**
1. **FR-1**: Diabetes flowsheet
2. **FR-2**: Hypertension flowsheet
3. **FR-3**: Chronic Kidney Disease flowsheet
4. **FR-4**: Custom flowsheets (future)

**Flowsheet Content:**
5. **FR-5**: Last value and date for each parameter
6. **FR-6**: Target ranges for each parameter
7. **FR-7**: Due/overdue status for periodic items
8. **FR-8**: Quick entry for flowsheet items

**Visualization:**
9. **FR-9**: Color coding (green=on target, yellow=borderline, red=off target)
10. **FR-10**: Trend sparklines for numeric values
11. **FR-11**: Checklist for annual/periodic items

**Alerts:**
12. **FR-12**: Highlight overdue items
13. **FR-13**: Show in patient summary if something is due

### Non-Functional Requirements
1. **NFR-1**: Flowsheet loads in < 500ms
2. **NFR-2**: Auto-populates from existing data
3. **NFR-3**: Works offline

## Acceptance Criteria

- [ ] DM flowsheet shows HbA1c, FBS, lipids, creatinine, eye exam, foot exam
- [ ] HTN flowsheet shows BP, potassium, creatinine, urinalysis
- [ ] Overdue items highlighted in red
- [ ] Can click item to enter new value
- [ ] Sparklines show trend
- [ ] Target ranges shown
- [ ] Patient card shows "Due: HbA1c" if overdue

## Diabetes Flowsheet Parameters

| Parameter | Frequency | Target | Source |
|-----------|-----------|--------|--------|
| HbA1c | 3 months | <7% | Labs |
| Fasting Blood Sugar | Each visit | 80-130 mg/dL | Labs/Vitals |
| Weight | Each visit | BMI <25 | Vitals |
| Blood Pressure | Each visit | <130/80 | Vitals |
| LDL Cholesterol | 1 year | <100 mg/dL | Labs |
| Serum Creatinine | 1 year | <1.3 mg/dL | Labs |
| Urine Microalbumin | 1 year | <30 mg/g | Labs |
| Dilated Eye Exam | 1 year | Normal | Procedures |
| Foot Exam | Each visit | No ulcers | Procedures |
| Flu Vaccine | 1 year | Done | Procedures |

## UI Design

### Diabetes Flowsheet
```
┌──────────────────────────────────────────────────────────────────┐
│ DIABETES MANAGEMENT FLOWSHEET                                    │
│ Ram Lal (M, 65) - Diagnosed: 2015                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ GLYCEMIC CONTROL                     Target: HbA1c <7%          │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ HbA1c        │ 7.8%    │ Dec 2025 │ ▁▂▃▄ │ 🔴 Above target  ││
│ │ FBS          │ 142     │ Today    │ ▃▂▃▄ │ 🟡 Borderline    ││
│ │ PPBS         │ 186     │ Today    │ ▂▃▄▅ │ 🔴 Above target  ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ CARDIOVASCULAR RISK                                              │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Blood Pressure│ 130/82  │ Today    │ ▄▃▂▂ │ 🟢 On target    ││
│ │ LDL Cholesterol│ 98     │ Nov 2025 │ ▅▄▃▂ │ 🟢 On target    ││
│ │ Weight/BMI    │ 72/26.4 │ Today    │ ▂▂▃▃ │ 🟡 Overweight   ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ COMPLICATIONS SCREENING                                          │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Creatinine   │ 1.4     │ Dec 2025 │ ▂▃▃▄ │ 🔴 Elevated     ││
│ │ Microalbumin │ 45      │ Jun 2025 │ ▂▂▃▄ │ 🔴 DUE RECHECK ││
│ │ Eye Exam     │ Normal  │ Mar 2025 │      │ 🟢 Next: Mar 26 ││
│ │ Foot Exam    │ Normal  │ Today    │      │ 🟢 Done         ││
│ │ Flu Vaccine  │ Done    │ Oct 2025 │      │ 🟢 Done         ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 📋 SUMMARY: HbA1c above target. Microalbumin recheck overdue.   │
│            Consider intensifying therapy.                        │
└──────────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
-- Patient chronic conditions
CREATE TABLE patient_conditions (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    condition_code TEXT NOT NULL,  -- 'DM2', 'HTN', 'CKD'
    diagnosed_date TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Flowsheet data auto-populated from existing tables
-- No new table needed - query investigations, vitals, procedures
```

## Out of Scope

- Custom flowsheet builder
- Medication adherence tracking
- Patient self-entry via portal

## Dependencies

- Vitals Tracking
- Lab Trends
- Investigations table

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Too much data overwhelms | Doctor ignores flowsheet | Highlight only actionable items |
| Wrong due dates | False alarms | Configurable schedules |
| Missing data incomplete | Flowsheet useless | Show "No data" clearly |

## Open Questions

- [x] Which conditions to support first? **Decision: DM, HTN, CKD**
- [x] Auto-populate from visits? **Decision: Yes, query existing data**

---
*Spec created: 2026-01-02*
