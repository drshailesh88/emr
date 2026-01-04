# Feature: Clinical Templates

> One-click templates for common conditions to standardize care and save time

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Doctors prescribe similar treatments for common conditions daily. Typing "Tab Metformin 500mg BD" for every diabetic is wasteful. Templates would standardize care and save significant time.

## User Stories

### Primary User Story
**As a** doctor
**I want to** select a template for common conditions
**So that** I can generate a complete prescription with one click

### Additional Stories
- As a doctor, I want to create my own templates for conditions I see often
- As a doctor, I want to modify a template after applying it
- As a doctor, I want templates for different severity levels (mild/moderate/severe)

## Requirements

### Functional Requirements

**Template Library:**
1. **FR-1**: Pre-built templates for top 20 conditions
2. **FR-2**: Template includes: diagnosis, medications, investigations, advice, follow-up
3. **FR-3**: Templates categorized by specialty/system

**Template Usage:**
4. **FR-4**: "Templates" button in prescription panel
5. **FR-5**: Search/filter templates by name
6. **FR-6**: Preview template before applying
7. **FR-7**: Apply template populates prescription fields
8. **FR-8**: Can edit after applying (template is starting point)

**Custom Templates:**
9. **FR-9**: Create template from current prescription
10. **FR-10**: Edit existing templates
11. **FR-11**: Delete custom templates
12. **FR-12**: Mark templates as favorites

### Non-Functional Requirements
1. **NFR-1**: Templates load instantly
2. **NFR-2**: Maximum 50 custom templates
3. **NFR-3**: Template changes don't affect past prescriptions

## Acceptance Criteria

- [ ] "Templates" button visible in prescription panel
- [ ] Click opens template browser with categories
- [ ] Can search templates by name
- [ ] Clicking template shows preview
- [ ] "Apply" fills in all prescription fields
- [ ] Can edit applied template before saving
- [ ] "Save as Template" button creates new template
- [ ] Custom templates appear in library

## Pre-built Templates (Top 20)

| # | Condition | Category |
|---|-----------|----------|
| 1 | Type 2 Diabetes (new) | Metabolic |
| 2 | Type 2 Diabetes (follow-up) | Metabolic |
| 3 | Hypertension (new) | Cardiac |
| 4 | Hypertension (controlled) | Cardiac |
| 5 | URTI / Common Cold | Respiratory |
| 6 | Acute Gastritis | GI |
| 7 | Acid Peptic Disease | GI |
| 8 | Urinary Tract Infection | Renal |
| 9 | Acute Diarrhea | GI |
| 10 | Allergic Rhinitis | Respiratory |
| 11 | Bronchial Asthma | Respiratory |
| 12 | Migraine | Neuro |
| 13 | Low Back Pain | Musculoskeletal |
| 14 | Osteoarthritis | Musculoskeletal |
| 15 | Anemia | Hematology |
| 16 | Hypothyroidism | Metabolic |
| 17 | Anxiety | Psychiatry |
| 18 | Insomnia | Psychiatry |
| 19 | Skin Infection | Dermatology |
| 20 | Viral Fever | Infectious |

## Template Schema

```json
{
  "id": "dm-type2-new",
  "name": "Type 2 Diabetes - New Diagnosis",
  "category": "Metabolic",
  "is_custom": false,
  "prescription": {
    "diagnosis": ["Type 2 Diabetes Mellitus"],
    "medications": [
      {
        "drug_name": "Metformin",
        "strength": "500mg",
        "form": "tablet",
        "dose": "1",
        "frequency": "BD",
        "duration": "30 days",
        "instructions": "after meals"
      }
    ],
    "investigations": ["FBS", "PPBS", "HbA1c", "Lipid Profile", "Creatinine"],
    "advice": [
      "Dietary modification - reduce sugar and refined carbs",
      "Regular exercise - 30 mins walking daily",
      "Weight reduction if overweight"
    ],
    "follow_up": "2 weeks with reports",
    "red_flags": ["Excessive thirst", "Frequent urination", "Blurred vision", "Foot numbness"]
  }
}
```

## Database Schema

```sql
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    prescription_json TEXT NOT NULL,
    is_custom INTEGER DEFAULT 0,
    is_favorite INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_favorite ON templates(is_favorite);
```

## UI Design

### Template Browser
```
┌───────────────────────────────────────────────────────────┐
│ Templates                                             [X] │
├───────────────────────────────────────────────────────────┤
│ [🔍 Search templates...]                                  │
├───────────────────────────────────────────────────────────┤
│ ⭐ FAVORITES                                              │
│   • Type 2 Diabetes - New                                 │
│   • Hypertension - Controlled                             │
├───────────────────────────────────────────────────────────┤
│ 📂 METABOLIC                                              │
│   • Type 2 Diabetes - New                                 │
│   • Type 2 Diabetes - Follow-up                           │
│   • Hypothyroidism                                        │
├───────────────────────────────────────────────────────────┤
│ 📂 CARDIAC                                                │
│   • Hypertension - New                                    │
│   • Hypertension - Controlled                             │
├───────────────────────────────────────────────────────────┤
│ 📂 MY TEMPLATES                                           │
│   • Chest Pain Workup (custom)                            │
│   [+ Create new template]                                 │
└───────────────────────────────────────────────────────────┘
```

## Out of Scope

- Template sharing between doctors
- Template version history
- Age/gender-specific template variations

## Dependencies

- Drug Database (templates reference drugs)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Templates become outdated | Suboptimal care | Regular review, versioning |
| Over-reliance on templates | Missing unique factors | Always editable, AI review |
| Template overload | Hard to find right one | Search, favorites, usage-sort |

## Open Questions

- [x] How many pre-built templates? **Decision: 20 for MVP**
- [x] Template format? **Decision: Same as prescription JSON**

---
*Spec created: 2026-01-02*
