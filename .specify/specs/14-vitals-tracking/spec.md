# Feature: Vitals Tracking

> Record and visualize vital signs to monitor patient health over time

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, vitals are buried in clinical notes as free text. There's no structured way to track BP, weight, or blood sugar over time. Chronic disease management requires seeing trends in vitals.

## User Stories

### Primary User Story
**As a** doctor
**I want to** record vitals in structured fields
**So that** I can track trends and manage chronic diseases better

### Additional Stories
- As a doctor, I want to quickly enter today's vitals
- As a doctor, I want to see BP trends for hypertensive patients
- As a doctor, I want to see weight trends for diabetic patients
- As a doctor, I want vitals auto-populated in clinical notes

## Requirements

### Functional Requirements

**Vitals Recording:**
1. **FR-1**: Quick vitals entry form in visit panel
2. **FR-2**: Record: BP (sys/dia), Pulse, Temperature, SpO2, Weight, Height, BMI (calculated)
3. **FR-3**: Record: Blood Sugar (FBS/RBS/PPBS)
4. **FR-4**: Auto-calculate BMI from weight and height
5. **FR-5**: Save vitals with timestamp

**Vitals Display:**
6. **FR-6**: Show latest vitals on patient card
7. **FR-7**: Vitals history table
8. **FR-8**: Vitals trend charts (like lab trends)
9. **FR-9**: Color-code abnormal values

**Smart Features:**
10. **FR-10**: Flag high/low values
11. **FR-11**: Remember last height (doesn't change often)
12. **FR-12**: Calculate weight change from last visit

### Non-Functional Requirements
1. **NFR-1**: Vitals entry < 10 seconds
2. **NFR-2**: Works with numeric keyboard only
3. **NFR-3**: Validation for realistic ranges

## Acceptance Criteria

- [ ] Vitals section visible in visit panel
- [ ] Can enter BP, Pulse, Temp, SpO2, Weight, Height
- [ ] BMI calculated automatically
- [ ] Abnormal values highlighted (e.g., BP > 140/90)
- [ ] Latest vitals show on patient card
- [ ] Can view vitals history for patient
- [ ] Vitals trend charts available
- [ ] Weight change shown from last visit

## Database Schema

```sql
CREATE TABLE vitals (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    visit_id INTEGER,
    recorded_at TEXT DEFAULT (datetime('now')),

    -- Blood Pressure
    bp_systolic INTEGER,
    bp_diastolic INTEGER,

    -- Other vitals
    pulse INTEGER,
    temperature REAL,
    spo2 INTEGER,
    respiratory_rate INTEGER,

    -- Anthropometry
    weight REAL,
    height REAL,
    bmi REAL,

    -- Blood Sugar
    blood_sugar REAL,
    sugar_type TEXT CHECK (sugar_type IN ('FBS', 'RBS', 'PPBS')),

    notes TEXT,

    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (visit_id) REFERENCES visits(id)
);

CREATE INDEX idx_vitals_patient ON vitals(patient_id);
CREATE INDEX idx_vitals_date ON vitals(recorded_at DESC);
```

## Normal Ranges

| Vital | Normal Range | Warning | Critical |
|-------|--------------|---------|----------|
| BP Systolic | 90-120 | 121-139 | ≥140 or <90 |
| BP Diastolic | 60-80 | 81-89 | ≥90 or <60 |
| Pulse | 60-100 | 50-59 or 101-110 | <50 or >110 |
| Temperature | 97.0-99.0°F | 99.1-100.4°F | >100.4°F or <96°F |
| SpO2 | 95-100% | 92-94% | <92% |
| BMI | 18.5-24.9 | 25-29.9 or 17-18.4 | ≥30 or <17 |
| FBS | 70-100 | 101-125 | ≥126 or <70 |

## UI Design

### Vitals Entry Form
```
┌──────────────────────────────────────────────────────────────────┐
│ VITALS                                              [Expand ▼]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ BP: [130]/[85] mmHg   Pulse: [78] /min   SpO2: [98] %           │
│                                                                  │
│ Temp: [98.6] °F   Weight: [72] kg   Height: [165] cm            │
│                                                                  │
│ BMI: 26.4 (Overweight)   Δ Weight: +1.5 kg from last visit      │
│                                                                  │
│ Blood Sugar: [156] mg/dL  Type: [PPBS ▼]                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Patient Card with Vitals
```
┌─────────────────────────────────────────┐
│ Ram Lal (M, 65)            ⭐           │
│ UHID: EMR-2024-0001                     │
│ ─────────────────────────────────────── │
│ BP: 130/85  │  PR: 78  │  SpO2: 98%    │
│ Wt: 72 kg   │  BMI: 26.4               │
└─────────────────────────────────────────┘
```

### Vitals History Table
```
┌──────────────────────────────────────────────────────────────────┐
│ Vitals History                                                   │
├──────────────────────────────────────────────────────────────────┤
│ Date       │ BP       │ Pulse │ SpO2 │ Weight │ BMI  │ Sugar    │
│ ─────────────────────────────────────────────────────────────── │
│ 02-Jan-26  │ 130/85   │ 78    │ 98%  │ 72 kg  │ 26.4 │ 156 PPBS │
│ 15-Dec-25  │ 142/88 ⚠ │ 82    │ 97%  │ 70.5 kg│ 25.9 │ 148 PPBS │
│ 01-Dec-25  │ 138/86   │ 76    │ 98%  │ 70 kg  │ 25.7 │ 162 PPBS │
│ 15-Nov-25  │ 145/92 ⚠ │ 84    │ 96%  │ 71 kg  │ 26.1 │ 178 FBS  │
└──────────────────────────────────────────────────────────────────┘
```

## Out of Scope

- Vitals from wearables/devices
- Automated BP machine integration
- Vitals alerts/reminders

## Dependencies

- Lab Trends (reuse charting)
- Visit management

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vitals entry slows workflow | Doctors skip it | Make minimal, use defaults |
| Wrong units (lbs vs kg) | Incorrect data | Default to metric, convert on entry |
| Missing historical vitals | Incomplete trends | Bulk import option |

## Open Questions

- [x] Metric or imperial? **Decision: Metric with conversion helper**
- [x] Temperature in F or C? **Decision: F with toggle**

---
*Spec created: 2026-01-02*
