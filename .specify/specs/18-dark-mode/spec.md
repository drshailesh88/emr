# Feature: Dark Mode

> Eye-friendly dark theme for late-night clinics and personal preference

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Many doctors work late evening or night clinics. Bright screens cause eye strain. Some doctors simply prefer dark mode. A dark theme would improve comfort and accessibility.

## User Stories

### Primary User Story
**As a** doctor
**I want to** switch to a dark theme
**So that** I can reduce eye strain during evening clinics

### Additional Stories
- As a doctor, I want to toggle between light and dark mode
- As a doctor, I want my theme preference to persist
- As a doctor, I want the app to follow my system theme

## Requirements

### Functional Requirements

**Theme Switching:**
1. **FR-1**: Toggle button in toolbar for quick switching
2. **FR-2**: Theme option in settings (Light / Dark / System)
3. **FR-3**: Theme persists across sessions
4. **FR-4**: Smooth transition when switching

**Dark Theme Design:**
5. **FR-5**: Dark background for all panels
6. **FR-6**: High contrast text for readability
7. **FR-7**: Colored elements (buttons, alerts) adjusted for dark mode
8. **FR-8**: Charts and graphs visible in dark mode

**Accessibility:**
9. **FR-9**: Sufficient contrast ratios (WCAG AA)
10. **FR-10**: No pure black (#000) - use dark gray for reduced strain

### Non-Functional Requirements
1. **NFR-1**: Theme switch < 100ms
2. **NFR-2**: All UI elements properly themed
3. **NFR-3**: No flash of wrong theme on startup

## Acceptance Criteria

- [ ] Toggle button in toolbar switches theme
- [ ] Settings has theme dropdown (Light/Dark/System)
- [ ] Theme preference saved and restored
- [ ] All panels use dark colors in dark mode
- [ ] Text readable with good contrast
- [ ] Buttons and icons visible
- [ ] Charts adapted for dark background
- [ ] PDF preview readable (may stay light)

## Color Palette

### Light Theme (Current)
| Element | Color |
|---------|-------|
| Background | #FFFFFF |
| Surface | #F5F5F5 |
| Primary | #2196F3 |
| Text | #212121 |
| Text Secondary | #757575 |

### Dark Theme
| Element | Color |
|---------|-------|
| Background | #121212 |
| Surface | #1E1E1E |
| Primary | #64B5F6 |
| Text | #E0E0E0 |
| Text Secondary | #9E9E9E |
| Success | #81C784 |
| Warning | #FFB74D |
| Error | #EF5350 |
| Card | #2D2D2D |

## UI Comparison

### Light Mode
```
┌──────────────────────────────────────────────────────────────────┐
│  DocAssist EMR                              [🌙] [⚙️] [?]       │
├─────────────┬────────────────────────────┬───────────────────────┤
│ PATIENTS    │     CENTRAL PANEL          │   AI ASSISTANT        │
│ (white bg)  │     (white bg)             │   (white bg)          │
│             │                            │                       │
│ Light text  │  Light text                │  Light text           │
│ on white    │  on white                  │  on white             │
```

### Dark Mode
```
┌──────────────────────────────────────────────────────────────────┐
│  DocAssist EMR                              [☀️] [⚙️] [?]       │
├─────────────┬────────────────────────────┬───────────────────────┤
│ PATIENTS    │     CENTRAL PANEL          │   AI ASSISTANT        │
│ (dark bg)   │     (dark bg)              │   (dark bg)           │
│             │                            │                       │
│ Light text  │  Light text                │  Light text           │
│ on dark     │  on dark                   │  on dark              │
```

## Implementation in Flet

```python
def toggle_theme(page: ft.Page):
    if page.theme_mode == ft.ThemeMode.LIGHT:
        page.theme_mode = ft.ThemeMode.DARK
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
    page.update()

# Custom dark theme
dark_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=ft.colors.BLUE_200,
        on_primary=ft.colors.BLACK,
        background=ft.colors.GREY_900,
        surface=ft.colors.GREY_850,
        on_surface=ft.colors.WHITE,
    )
)

page.dark_theme = dark_theme
page.theme_mode = ft.ThemeMode.SYSTEM  # or LIGHT/DARK
```

## Special Considerations

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Patient Card (selected) | Light Blue | Dark Blue |
| Alert Critical | Red on White | Red on Dark (lighter red) |
| Prescription Box | White | Dark Gray |
| Charts | Dark lines on light | Light lines on dark |
| PDF Preview | Light (not themed) | Light (paper is white) |
| Code/JSON | Light bg | Dark bg (syntax highlight adjusted) |

## Out of Scope

- Custom color themes beyond Light/Dark
- Scheduled theme switching (sunset)
- Per-panel theme settings

## Dependencies

- Flet theme support

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missed elements stay light | Inconsistent UI | Thorough testing, style audit |
| Charts unreadable | Data not visible | Separate chart theme colors |
| Insufficient contrast | Accessibility issue | WCAG contrast checker |

## Open Questions

- [x] Follow system theme? **Decision: Yes, as an option**
- [x] Pure black or dark gray? **Decision: Dark gray (#121212) for OLED friendliness**

---
*Spec created: 2026-01-02*
