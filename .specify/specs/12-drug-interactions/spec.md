# Feature: Drug Interaction Warnings

> Prevent harmful drug combinations by alerting doctors before prescribing

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Drug interactions are a leading cause of adverse events. Currently, doctors must remember all interactions. A warning system would catch dangerous combinations before the prescription is finalized.

## User Stories

### Primary User Story
**As a** doctor
**I want to** be warned when prescribing drugs that interact
**So that** I can prevent adverse drug reactions

### Additional Stories
- As a doctor, I want to see the severity of interactions (minor/moderate/severe)
- As a doctor, I want to see what the interaction effect is
- As a doctor, I want to override warnings with a reason when needed
- As a doctor, I want interactions checked against the patient's existing medications

## Requirements

### Functional Requirements

**Interaction Detection:**
1. **FR-1**: Check new drugs against prescription being written
2. **FR-2**: Check new drugs against patient's current medications (from past visits)
3. **FR-3**: Categorize interactions: Minor, Moderate, Severe, Contraindicated
4. **FR-4**: Show interaction details (mechanism, effect, recommendation)

**Warning System:**
5. **FR-5**: Display warning before saving prescription
6. **FR-6**: Block save for "Contraindicated" until acknowledged
7. **FR-7**: Require override reason for Severe interactions
8. **FR-8**: Log all overrides to audit trail

**Interaction Database:**
9. **FR-9**: Pre-built interaction rules for common drugs (500+ pairs)
10. **FR-10**: Store locally (offline-first)
11. **FR-11**: Updateable interaction database

### Non-Functional Requirements
1. **NFR-1**: Interaction check in < 100ms
2. **NFR-2**: Works offline
3. **NFR-3**: No false negatives for contraindicated pairs

## Acceptance Criteria

- [ ] Adding Warfarin + Aspirin shows Severe warning
- [ ] Adding ACE inhibitor + Potassium shows Moderate warning
- [ ] Contraindicated combo prevents save until acknowledged
- [ ] Override requires reason text
- [ ] Check includes patient's current medications
- [ ] Interaction details show mechanism and effect
- [ ] All warnings logged to audit

## Interaction Severity Levels

| Level | Color | Behavior |
|-------|-------|----------|
| Minor | Yellow | Informational, can proceed |
| Moderate | Orange | Warning, confirm to proceed |
| Severe | Red | Strong warning, must override with reason |
| Contraindicated | Red + Block | Must acknowledge, rarely override |

## Sample Interactions Database

```json
[
  {
    "drug1": "Warfarin",
    "drug2": "Aspirin",
    "severity": "Severe",
    "effect": "Increased risk of bleeding",
    "mechanism": "Both affect coagulation pathways",
    "recommendation": "Avoid combination. If necessary, monitor INR closely."
  },
  {
    "drug1": "ACE Inhibitor",
    "drug2": "Potassium Supplement",
    "severity": "Moderate",
    "effect": "Risk of hyperkalemia",
    "mechanism": "ACE inhibitors increase potassium retention",
    "recommendation": "Monitor serum potassium regularly"
  },
  {
    "drug1": "Metformin",
    "drug2": "IV Contrast",
    "severity": "Contraindicated",
    "effect": "Risk of lactic acidosis",
    "mechanism": "Contrast can impair renal function",
    "recommendation": "Hold metformin 48h before and after contrast"
  }
]
```

## Database Schema

```sql
CREATE TABLE drug_interactions (
    id INTEGER PRIMARY KEY,
    drug1_generic TEXT NOT NULL,
    drug2_generic TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('Minor', 'Moderate', 'Severe', 'Contraindicated')),
    effect TEXT,
    mechanism TEXT,
    recommendation TEXT,
    source TEXT,
    UNIQUE(drug1_generic, drug2_generic)
);

CREATE INDEX idx_interaction_drug1 ON drug_interactions(drug1_generic);
CREATE INDEX idx_interaction_drug2 ON drug_interactions(drug2_generic);

CREATE TABLE interaction_overrides (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    visit_id INTEGER,
    drug1 TEXT,
    drug2 TEXT,
    severity TEXT,
    reason TEXT NOT NULL,
    overridden_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (visit_id) REFERENCES visits(id)
);
```

## UI Design

### Interaction Warning Dialog
```
┌──────────────────────────────────────────────────────────┐
│ ⚠️ Drug Interaction Warning                          [X] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 🔴 SEVERE INTERACTION                                    │
│                                                          │
│ Warfarin + Aspirin                                       │
│                                                          │
│ Effect: Increased risk of bleeding                       │
│                                                          │
│ Mechanism: Both affect coagulation pathways              │
│                                                          │
│ Recommendation: Avoid combination. If necessary,         │
│ monitor INR closely and watch for bleeding signs.        │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│                                                          │
│ To proceed, provide a clinical reason:                   │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Patient on low-dose aspirin for secondary            │ │
│ │ prevention, will monitor INR weekly                  │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
├──────────────────────────────────────────────────────────┤
│              [Cancel Prescription]  [Proceed with Reason]│
└──────────────────────────────────────────────────────────┘
```

## Common Interaction Categories

1. **Anticoagulant + NSAID** - Bleeding risk
2. **ACE/ARB + Potassium** - Hyperkalemia
3. **Statin + Fibrate** - Myopathy
4. **Metformin + Contrast** - Lactic acidosis
5. **Digoxin + Diuretic** - Toxicity (hypokalemia)
6. **Warfarin + Antibiotic** - INR changes
7. **SSRI + MAOI** - Serotonin syndrome
8. **Beta-blocker + Verapamil** - Heart block
9. **Nitrate + PDE5 inhibitor** - Hypotension
10. **Lithium + NSAID** - Toxicity

## Out of Scope

- Drug-disease interactions (future)
- Drug-allergy checking (future)
- Dosage-based interactions
- Real-time database updates

## Dependencies

- Drug Database (for drug identification)
- Audit Trail (for override logging)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives annoy doctors | Override fatigue | Tune sensitivity, easy override |
| Missing interaction | Patient harm | Curate from reliable sources |
| Database outdated | Missing new drugs | Versioned updates, LLM backup |

## Open Questions

- [x] Check all past medications or recent only? **Decision: Last 6 months**
- [x] LLM as backup for unknown interactions? **Decision: Future enhancement**

---
*Spec created: 2026-01-02*
