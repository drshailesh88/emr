# Feature: Clinical Decision Support Alerts

> Proactive alerts to catch critical findings and remind about important care gaps

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Critical values and care gaps can be missed in busy clinics. An alert system would proactively flag high-risk findings (like critically high potassium) and remind about overdue preventive care.

## User Stories

### Primary User Story
**As a** doctor
**I want to** be alerted about critical findings immediately
**So that** I don't miss anything dangerous

### Additional Stories
- As a doctor, I want to know when labs are critically abnormal
- As a doctor, I want to know when screenings are overdue
- As a doctor, I want alerts that don't interrupt my workflow excessively

## Requirements

### Functional Requirements

**Alert Types:**
1. **FR-1**: Critical lab value alerts (e.g., K+ > 6.0)
2. **FR-2**: Drug interaction alerts (from feature #12)
3. **FR-3**: Overdue screening alerts (from flowsheets)
4. **FR-4**: High-risk medication alerts (e.g., opioids, anticoagulants)
5. **FR-5**: Allergy alerts (future)

**Alert Display:**
6. **FR-6**: Non-blocking banner for informational alerts
7. **FR-7**: Modal popup for critical alerts
8. **FR-8**: Alert badge on patient card
9. **FR-9**: Alert summary panel

**Alert Management:**
10. **FR-10**: Acknowledge/dismiss alerts
11. **FR-11**: Snooze alerts for a period
12. **FR-12**: Alert history log
13. **FR-13**: Configure alert thresholds

### Non-Functional Requirements
1. **NFR-1**: Critical alerts show within 100ms of triggering event
2. **NFR-2**: Alert check doesn't slow down normal operations
3. **NFR-3**: Minimize alert fatigue (tuned thresholds)

## Acceptance Criteria

- [ ] Adding K+ = 6.5 triggers critical alert immediately
- [ ] Alert modal requires acknowledgment
- [ ] Patient card shows alert badge
- [ ] Overdue screening shows as informational alert
- [ ] Drug interactions trigger alerts
- [ ] Can view alert history
- [ ] Can configure alert thresholds in settings

## Alert Severity Levels

| Level | Display | Behavior |
|-------|---------|----------|
| Info | Blue banner | Auto-dismiss after 5s |
| Warning | Yellow banner | Must dismiss manually |
| Critical | Red modal popup | Must acknowledge with action |

## Critical Value Rules

| Lab | Critical Low | Critical High |
|-----|--------------|---------------|
| Potassium | <2.5 mEq/L | >6.0 mEq/L |
| Sodium | <120 mEq/L | >160 mEq/L |
| Glucose | <50 mg/dL | >500 mg/dL |
| Hemoglobin | <6 g/dL | >20 g/dL |
| Creatinine | - | >10 mg/dL |
| INR | - | >5.0 |
| Platelets | <20,000 | >1,000,000 |
| WBC | <1,000 | >50,000 |

## UI Design

### Critical Alert Modal
```
┌──────────────────────────────────────────────────────────────┐
│ ⚠️ CRITICAL ALERT                                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  🔴 CRITICAL POTASSIUM LEVEL                                 │
│                                                              │
│  Patient: Ram Lal (EMR-2024-0001)                           │
│  Lab: Potassium = 6.8 mEq/L                                 │
│  Normal Range: 3.5-5.0 mEq/L                                │
│                                                              │
│  ⚠️ Risk of cardiac arrhythmia                              │
│                                                              │
│  Recommended Actions:                                        │
│  • Obtain ECG immediately                                    │
│  • Consider calcium gluconate                                │
│  • Review medications (ACE-I, K+ supplements)               │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│               [View Patient]  [Acknowledge & Continue]       │
└──────────────────────────────────────────────────────────────┘
```

### Alert Banner (Non-Critical)
```
┌──────────────────────────────────────────────────────────────────┐
│ 🟡 Ram Lal: HbA1c due for recheck (last: 6 months ago)    [×]   │
└──────────────────────────────────────────────────────────────────┘
```

### Patient Card with Alert Badge
```
┌─────────────────────────────────────────┐
│ Ram Lal (M, 65)            ⭐  🔴 2     │ ← 2 active alerts
│ UHID: EMR-2024-0001                     │
│ ─────────────────────────────────────── │
│ BP: 130/85  │  PR: 78  │  SpO2: 98%    │
└─────────────────────────────────────────┘
```

## Database Schema

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,  -- 'critical_lab', 'drug_interaction', 'overdue_screening'
    severity TEXT CHECK (severity IN ('info', 'warning', 'critical')),
    title TEXT NOT NULL,
    message TEXT,
    triggered_at TEXT DEFAULT (datetime('now')),
    acknowledged_at TEXT,
    acknowledged_action TEXT,  -- What was done
    snoozed_until TEXT,
    is_resolved INTEGER DEFAULT 0,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE INDEX idx_alerts_patient ON alerts(patient_id);
CREATE INDEX idx_alerts_active ON alerts(is_resolved, snoozed_until);
```

## Out of Scope

- SMS/email notifications
- Alert escalation to other providers
- Machine learning predictions
- Real-time lab feed integration

## Dependencies

- Drug Interactions (#12)
- Flowsheets (#15)
- Investigations table

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alert fatigue | Doctors ignore all alerts | Tune thresholds, minimize low-value alerts |
| Missing alert | Patient harm | Test critical paths extensively |
| Too many popups | Workflow disruption | Use banners for non-critical |

## Open Questions

- [x] Alert fatigue concern? **Decision: Strict thresholds, easy dismiss**
- [x] Store dismissed alerts? **Decision: Yes, for audit**

---
*Spec created: 2026-01-02*
