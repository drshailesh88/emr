# Feature: Keyboard Shortcuts

> Enable power users to work at lightning speed without touching the mouse

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Doctors seeing 50+ patients/day can't afford to click through menus. Every mouse movement costs time. Power users expect keyboard shortcuts for every common action.

## User Stories

### Primary User Story
**As a** doctor
**I want to** use keyboard shortcuts for common actions
**So that** I can work faster without reaching for the mouse

### Additional Stories
- As a doctor, I want to save with Ctrl+S without thinking
- As a doctor, I want to quickly search patients with a hotkey
- As a doctor, I want to navigate between panels with keyboard
- As a doctor, I want to see a list of all shortcuts

## Requirements

### Functional Requirements

**Global Shortcuts:**
1. **FR-1**: `Ctrl+N` - New Patient
2. **FR-2**: `Ctrl+S` - Save current (visit, settings, etc.)
3. **FR-3**: `Ctrl+P` - Print prescription PDF
4. **FR-4**: `Ctrl+F` - Focus patient search
5. **FR-5**: `Ctrl+G` - Generate prescription (LLM)
6. **FR-6**: `Ctrl+B` - Manual backup
7. **FR-7**: `Ctrl+,` - Open settings
8. **FR-8**: `F1` - Open help/shortcuts reference
9. **FR-9**: `Escape` - Close dialog/cancel

**Navigation:**
10. **FR-10**: `Ctrl+1` - Focus left panel (patients)
11. **FR-11**: `Ctrl+2` - Focus center panel (prescription)
12. **FR-12**: `Ctrl+3` - Focus right panel (AI assistant)
13. **FR-13**: `Tab` / `Shift+Tab` - Navigate fields
14. **FR-14**: `↑` / `↓` - Navigate patient list

**AI Assistant:**
15. **FR-15**: `Ctrl+Enter` - Send message to AI
16. **FR-16**: `Ctrl+L` - Clear chat

**Other:**
17. **FR-17**: Show shortcuts help overlay
18. **FR-18**: Shortcuts work regardless of focus

### Non-Functional Requirements
1. **NFR-1**: Shortcuts must not conflict with OS defaults
2. **NFR-2**: Visual indicator when shortcut triggered
3. **NFR-3**: Customizable shortcuts (future)

## Acceptance Criteria

- [ ] All 16 shortcuts are functional
- [ ] Shortcuts work from any panel
- [ ] `F1` opens shortcuts reference panel
- [ ] Shortcuts shown in tooltips ("Save Ctrl+S")
- [ ] Shortcuts shown in menu items
- [ ] No conflicts with browser/OS shortcuts (if running in web)

## Keyboard Reference

```
┌──────────────────────────────────────────────────────────┐
│ KEYBOARD SHORTCUTS                                   [X] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ GENERAL                          NAVIGATION              │
│ ─────────────────────           ─────────────────────    │
│ Ctrl+N    New Patient           Ctrl+1   Patients Panel  │
│ Ctrl+S    Save                  Ctrl+2   Rx Panel        │
│ Ctrl+P    Print PDF             Ctrl+3   AI Panel        │
│ Ctrl+F    Search Patients       Tab      Next Field      │
│ Ctrl+G    Generate Rx           ↑↓       Navigate List   │
│ Ctrl+B    Backup Now                                     │
│ Ctrl+,    Settings              AI ASSISTANT             │
│ F1        This Help             ─────────────────────    │
│ Esc       Close/Cancel          Ctrl+Enter  Send         │
│                                 Ctrl+L      Clear Chat   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Implementation Notes

Flet keyboard handling:
```python
def on_keyboard(e: ft.KeyboardEvent):
    if e.ctrl and e.key == "s":
        save_current()
    elif e.ctrl and e.key == "n":
        new_patient()
    # etc.

page.on_keyboard_event = on_keyboard
```

## Out of Scope

- Custom shortcut mapping (future)
- Vim-style keybindings
- Macro recording

## Dependencies

- None

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Shortcut conflicts | Feature unusable | Test on all platforms |
| Flet limitation | Can't implement | Check Flet docs first |
| Users don't discover | Low adoption | Show on first run, tooltips |

## Open Questions

- [x] Ctrl or Cmd on Mac? **Decision: Flet handles automatically**
- [x] Function keys available? **Decision: Yes, F1-F12 work**

---
*Spec created: 2026-01-02*
