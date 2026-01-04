# Feature: Drug Database with Autocomplete

> Speed up prescription writing with smart drug suggestions

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Doctors type the same drug names hundreds of times. Typos cause confusion at pharmacies. Different doctors spell drugs differently. A standardized drug database with autocomplete would save time and reduce errors.

## User Stories

### Primary User Story
**As a** doctor
**I want to** type a few letters and select from drug suggestions
**So that** I can write prescriptions faster without typos

### Additional Stories
- As a doctor, I want to see common dosages when selecting a drug
- As a doctor, I want to add drugs I use frequently to favorites
- As a doctor, I want to see both generic and brand names
- As a doctor, I want to add new drugs to my local database

## Requirements

### Functional Requirements

**Drug Search:**
1. **FR-1**: Autocomplete dropdown when typing drug name
2. **FR-2**: Search by generic name or brand name
3. **FR-3**: Show top 10 matches, sorted by frequency of use
4. **FR-4**: Fuzzy matching (Paracetamol = Paracetmol)

**Drug Database:**
5. **FR-5**: Pre-populated with 500+ common Indian drugs
6. **FR-6**: Each drug has: generic name, common brands, strengths, forms
7. **FR-7**: Add custom drugs to local database
8. **FR-8**: Drugs stored in SQLite (drugs table)

**Usage Tracking:**
9. **FR-9**: Track how often each drug is prescribed
10. **FR-10**: Most-used drugs appear first in suggestions
11. **FR-11**: Recently used drugs section

**Integration:**
12. **FR-12**: Autocomplete in prescription notes field
13. **FR-13**: Autocomplete in central panel Rx editor
14. **FR-14**: Selected drug auto-fills strength and form

### Non-Functional Requirements
1. **NFR-1**: Autocomplete shows results in < 50ms
2. **NFR-2**: Works offline (local database)
3. **NFR-3**: Drug database < 5MB

## Acceptance Criteria

- [ ] Typing "met" shows Metformin, Metoprolol, etc.
- [ ] Selecting a drug fills in strength options
- [ ] Most prescribed drugs appear at top
- [ ] Can add custom drug via "+" button
- [ ] Fuzzy search handles typos
- [ ] Brand names show generic in parentheses

## Database Schema

```sql
CREATE TABLE drugs (
    id INTEGER PRIMARY KEY,
    generic_name TEXT NOT NULL,
    brand_names TEXT,  -- JSON array
    strengths TEXT,    -- JSON array ["500mg", "850mg", "1000mg"]
    forms TEXT,        -- JSON array ["tablet", "syrup", "injection"]
    category TEXT,     -- "antidiabetic", "antihypertensive", etc.
    is_custom INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    last_used TEXT
);

CREATE INDEX idx_drugs_generic ON drugs(generic_name);
CREATE INDEX idx_drugs_usage ON drugs(usage_count DESC);
```

## Sample Drug Data

```json
{
  "generic_name": "Metformin",
  "brand_names": ["Glycomet", "Glucophage", "Obimet"],
  "strengths": ["500mg", "850mg", "1000mg"],
  "forms": ["tablet", "SR tablet"],
  "category": "antidiabetic"
}
```

## UI Design

### Autocomplete Dropdown
```
┌─────────────────────────────────────────┐
│ Drug: [met                          ]   │
│       ┌─────────────────────────────┐   │
│       │ ⭐ Metformin 500mg tablet   │   │
│       │    (Glycomet) - used 45x    │   │
│       │ Metoprolol 25mg tablet      │   │
│       │    (Betaloc) - used 23x     │   │
│       │ Metronidazole 400mg tablet  │   │
│       │    (Flagyl) - used 12x      │   │
│       │ + Add new drug...           │   │
│       └─────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Initial Drug Categories

1. **Antidiabetics** - Metformin, Glimepiride, Sitagliptin, etc.
2. **Antihypertensives** - Amlodipine, Telmisartan, Losartan, etc.
3. **Cardiac** - Aspirin, Clopidogrel, Atorvastatin, etc.
4. **Antibiotics** - Amoxicillin, Azithromycin, Ciprofloxacin, etc.
5. **Analgesics** - Paracetamol, Ibuprofen, Diclofenac, etc.
6. **GI** - Omeprazole, Pantoprazole, Domperidone, etc.
7. **Respiratory** - Salbutamol, Montelukast, Cetirizine, etc.
8. **Vitamins** - B-complex, Calcium, Iron, etc.

## Out of Scope

- Drug interaction checking (separate feature)
- Drug allergy tracking (separate feature)
- Prescription validation

## Dependencies

- None (new standalone table)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Outdated drug list | Wrong suggestions | Allow custom additions |
| Database too large | Slow startup | Lazy loading, index properly |
| Brand name variations | Confusion | Focus on generic, brands secondary |

## Open Questions

- [x] Source for drug database? **Decision: Curate top 500 manually from Indian formulary**
- [x] Include controlled substances? **Decision: Yes, doctors prescribe them**

---
*Spec created: 2026-01-02*
