# Feature: Quick Phrases / Text Expansion

> Type abbreviations, get full text - like TextExpander for clinical notes

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Doctors use common phrases repeatedly: "Patient complains of", "No significant past history", "Vitals stable". Typing these wastes time. Text expansion would let doctors type shortcuts that expand to full text.

## User Stories

### Primary User Story
**As a** doctor
**I want to** type "c/o" and have it expand to "complains of"
**So that** I can write notes faster

### Additional Stories
- As a doctor, I want to create my own shortcuts
- As a doctor, I want medical abbreviations to expand correctly
- As a doctor, I want shortcuts to work in all text fields

## Requirements

### Functional Requirements

**Text Expansion:**
1. **FR-1**: Type shortcut + trigger key (Tab/Space) to expand
2. **FR-2**: Expansion works in: clinical notes, chief complaint, prescription fields
3. **FR-3**: Pre-built phrases for common medical abbreviations

**Phrase Management:**
4. **FR-4**: View list of all phrases
5. **FR-5**: Add custom phrases
6. **FR-6**: Edit/delete phrases
7. **FR-7**: Import/export phrases

**Smart Features:**
8. **FR-8**: Placeholders in phrases (e.g., "Patient is a |age| year old |gender|")
9. **FR-9**: Date insertion ({today}, {tomorrow})

### Non-Functional Requirements
1. **NFR-1**: Expansion feels instant (< 50ms)
2. **NFR-2**: No conflict with normal typing
3. **NFR-3**: Works offline

## Acceptance Criteria

- [ ] Typing "c/o " expands to "complains of "
- [ ] Typing "nkda " expands to "no known drug allergies "
- [ ] Settings shows phrase manager
- [ ] Can add custom phrase
- [ ] Phrases work in all text areas
- [ ] Placeholders prompt for values

## Pre-built Phrases

| Shortcut | Expansion |
|----------|-----------|
| c/o | complains of |
| h/o | history of |
| k/c/o | known case of |
| nkda | no known drug allergies |
| nkfa | no known food allergies |
| nsph | no significant past history |
| wdwn | well developed, well nourished |
| nad | no acute distress |
| heent | Head, Eyes, Ears, Nose, Throat |
| cvs | cardiovascular system |
| rs | respiratory system |
| cns | central nervous system |
| gi | gastrointestinal |
| gu | genitourinary |
| msk | musculoskeletal |
| vitals | Vitals: BP: /mmHg, PR: /min, Temp: °F, SpO2: % |
| pe | Physical Examination: |
| dx | Diagnosis: |
| rx | Prescription: |
| f/u | follow up |
| sos | if needed |
| prn | as needed |
| od | once daily |
| bd | twice daily |
| tds | thrice daily |
| qid | four times daily |
| hs | at bedtime |
| ac | before meals |
| pc | after meals |
| stat | immediately |
| sig | directions |

## Database Schema

```sql
CREATE TABLE phrases (
    id INTEGER PRIMARY KEY,
    shortcut TEXT UNIQUE NOT NULL,
    expansion TEXT NOT NULL,
    category TEXT,
    is_custom INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_phrases_shortcut ON phrases(shortcut);
```

## UI Design

### Phrase Manager
```
┌─────────────────────────────────────────────────────────┐
│ Quick Phrases                                       [X] │
├─────────────────────────────────────────────────────────┤
│ [🔍 Search...]                         [+ Add Phrase]   │
├─────────────────────────────────────────────────────────┤
│ Shortcut        Expansion                     Actions   │
│ ──────────────────────────────────────────────────────  │
│ c/o             complains of                   [✏️][🗑️] │
│ h/o             history of                     [✏️][🗑️] │
│ nkda            no known drug allergies        [✏️][🗑️] │
│ vitals          Vitals: BP: /mmHg, PR: /min... [✏️][🗑️] │
│ ...                                                     │
├─────────────────────────────────────────────────────────┤
│ 💡 Type shortcut + Space to expand in any text field   │
└─────────────────────────────────────────────────────────┘
```

### Add Phrase Dialog
```
┌─────────────────────────────────────────────┐
│ Add Quick Phrase                        [X] │
├─────────────────────────────────────────────┤
│                                             │
│ Shortcut:  [htn     ]                       │
│                                             │
│ Expansion:                                  │
│ ┌─────────────────────────────────────────┐ │
│ │ Hypertension                            │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Category:  [Medical Abbreviations     ▼]   │
│                                             │
├─────────────────────────────────────────────┤
│                    [Cancel]  [Save]         │
└─────────────────────────────────────────────┘
```

## Implementation Notes

Flet text field handling:
```python
def on_text_change(e):
    text = e.control.value
    # Check if last word matches a shortcut
    words = text.split()
    if words and words[-1] in phrases:
        expanded = text[:-len(words[-1])] + phrases[words[-1]]
        e.control.value = expanded
        e.control.update()
```

## Out of Scope

- Multi-line shortcut triggers
- Rich text formatting in expansion
- Conditional expansions

## Dependencies

- None

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Shortcut conflicts | Unexpected expansion | Review pre-built list carefully |
| Slow typing feels interrupted | User frustration | Fast matching, debounce |
| Shortcut forgotten | Feature unused | Show hint on hover |

## Open Questions

- [x] Trigger key? **Decision: Space or Tab**
- [x] Case sensitive? **Decision: No, all lowercase**

---
*Spec created: 2026-01-02*
