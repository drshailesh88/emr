# Tutorial Overlay System

## Overview

The tutorial overlay system provides an interactive first-run experience for new users of DocAssist EMR. It guides users through the key features of the application with a step-by-step visual tutorial.

## Architecture

### Components

1. **TutorialStep** - Data class representing a single tutorial step
2. **TutorialOverlay** - Main component that renders the tutorial UI
3. **Settings Integration** - Tracks tutorial completion status

### Files

- `/src/ui/components/tutorial_overlay.py` - Tutorial overlay component
- `/src/services/settings.py` - Settings service with tutorial tracking
- `/src/ui/app.py` - Integration into main app

## Features

### Visual Design

- **Semi-transparent dark overlay** (rgba(0,0,0,0.75)) covers the entire screen
- **Spotlight effect** highlights the relevant UI area for each step
- **Animated transitions** between steps (400ms ease-in-out)
- **Floating content card** at the bottom with tutorial information
- **Progress dots** indicate current step and progress

### Tutorial Steps

1. **Patient Panel** - Explains patient search and management
2. **Recording Visits** - Shows how to enter clinical notes
3. **AI Prescription Generation** - Demonstrates prescription creation
4. **AI Assistant** - Introduces the RAG-powered chat feature
5. **Settings & Backup** - Covers configuration and data protection

### User Controls

- **Skip Tutorial** - Dismisses tutorial and marks as completed
- **Previous** - Goes back to the previous step (disabled on first step)
- **Next** - Advances to the next step
- **Complete Tutorial** - Shown on final step, marks tutorial as done

### Spotlight Positioning

The spotlight dynamically positions itself based on the current step:

- **Horizontal**: left, center, right
- **Vertical**: top, middle, bottom
- **Size**: Varies based on the UI element being highlighted

Example positions:
```python
# Patient panel (left side)
spotlight_position="left", spotlight_vertical="middle"

# Central panel (middle)
spotlight_position="center", spotlight_vertical="middle"

# AI Assistant (right side)
spotlight_position="right", spotlight_vertical="top"
```

## Integration

### First-Run Flow

1. User completes setup wizard
2. Main app loads
3. Settings service checks `tutorial_completed` flag
4. If `False`, tutorial overlay is displayed
5. User completes or skips tutorial
6. Flag is set to `True` in settings.json

### Re-triggering Tutorial

Users can re-trigger the tutorial from the Help menu:

1. Click Help button in header
2. Click "Show Tutorial Again" button
3. Tutorial overlay appears with reset state

## Settings Persistence

### AppSettings Schema

```python
@dataclass
class AppSettings:
    version: str = "1.0"
    backup: BackupSettings
    doctor: DoctorSettings
    theme: str = "light"
    language: str = "en"
    tutorial_completed: bool = False  # Tutorial tracking
```

### Settings Methods

```python
# Check if tutorial was completed
settings.is_tutorial_completed() -> bool

# Mark tutorial as completed
settings.mark_tutorial_completed()

# Reset tutorial (for re-triggering)
settings.reset_tutorial()
```

### Storage Location

Settings are stored in: `data/settings.json`

Example:
```json
{
  "version": "1.0",
  "backup": {...},
  "doctor": {...},
  "theme": "light",
  "language": "en",
  "tutorial_completed": false
}
```

## Responsive Design

### Dark Mode Support

The tutorial overlay adapts to the current theme:

```python
tutorial = TutorialOverlay(
    page=page,
    on_complete=callback,
    is_dark=True  # Adapts colors for dark mode
)
```

### Mobile-Friendly

- Touch-friendly button sizes (48px minimum)
- Responsive layout that works on different screen sizes
- Smooth animations optimized for performance

## Accessibility

- **Clear visual hierarchy** with large text and icons
- **High contrast** overlay and spotlight
- **Keyboard navigation** support (via Flet)
- **Screen reader friendly** text descriptions

## Customization

### Adding New Steps

To add a new tutorial step:

```python
# In TutorialOverlay.__init__()
self.steps.append(
    TutorialStep(
        title="New Feature",
        description="Explanation of the new feature...",
        icon=ft.Icons.NEW_RELEASES_ROUNDED,
        spotlight_position="center",
        spotlight_vertical="middle",
    )
)
```

### Modifying Spotlight Behavior

Spotlight behavior can be customized in `_build_spotlight()`:

```python
def _build_spotlight(self) -> ft.Container:
    step = self.steps[self.current_step]

    # Custom positioning logic
    if step.title == "Custom Feature":
        left = 400
        width = 600
        # ... custom size and position
```

### Styling

Colors and styles can be adjusted in the component:

```python
# Overlay background opacity
overlay_bg = ft.Container(
    bgcolor="rgba(0,0,0,0.75)",  # Adjust alpha for opacity
    expand=True,
)

# Content card styling
card = ft.Container(
    bgcolor="#1E1E1E" if self.is_dark else ft.Colors.GREY_900,
    border_radius=16,
    padding=30,
    # ... other styles
)
```

## Testing

### Manual Testing Checklist

- [ ] Tutorial appears on first run after setup wizard
- [ ] Tutorial does not appear on subsequent runs
- [ ] Skip button marks tutorial as completed
- [ ] Complete button marks tutorial as completed
- [ ] Navigation works correctly (Previous/Next)
- [ ] Spotlight highlights correct areas
- [ ] Animations are smooth
- [ ] Dark mode renders correctly
- [ ] Re-trigger from Help menu works
- [ ] Settings persist correctly

### Reset for Testing

To reset the tutorial for testing:

```python
# In Python console or test script
from src.services.settings import SettingsService

settings = SettingsService()
settings.reset_tutorial()
```

Or manually edit `data/settings.json`:
```json
{
  "tutorial_completed": false
}
```

## Future Enhancements

### Planned Features

1. **Interactive hotspots** - Clickable elements during tutorial
2. **Video demonstrations** - Embedded short video clips
3. **Contextual tips** - Show tutorial for specific features when first used
4. **Multi-language support** - Translated tutorial steps
5. **Analytics** - Track which steps users skip/complete
6. **Adaptive tutorial** - Customize based on user role (doctor/nurse/admin)

### Advanced Customization

```python
# Custom tutorial for specific user roles
if user_role == "doctor":
    tutorial_steps = DOCTOR_TUTORIAL_STEPS
elif user_role == "nurse":
    tutorial_steps = NURSE_TUTORIAL_STEPS

# Feature-specific tutorials
def show_feature_tutorial(feature_name: str):
    """Show tutorial for a specific feature."""
    # Implementation...
```

## Troubleshooting

### Tutorial Not Appearing

1. Check `settings.json` - ensure `tutorial_completed` is `false`
2. Verify settings service is initialized correctly
3. Check console logs for errors
4. Ensure first run is detected (doctor profile not set)

### Spotlight Misaligned

1. Verify spotlight position values in TutorialStep
2. Check page layout hasn't changed
3. Adjust spotlight dimensions in `_build_spotlight()`

### Animation Lag

1. Reduce animation duration (currently 400ms)
2. Simplify spotlight shadow effects
3. Optimize page rendering

## Code Examples

### Basic Usage

```python
from src.ui.components.tutorial_overlay import show_tutorial_overlay

# Show tutorial
tutorial_overlay = show_tutorial_overlay(
    page=page,
    on_complete=lambda: print("Tutorial completed"),
    on_skip=lambda: print("Tutorial skipped"),
    is_dark=False,
)

# Add to page
page.overlay.append(tutorial_overlay)
page.update()
```

### Integration in Custom Component

```python
class MyComponent:
    def __init__(self, page):
        self.page = page
        self.settings = SettingsService()

    def show_tutorial_if_needed(self):
        if not self.settings.is_tutorial_completed():
            self._show_tutorial()

    def _show_tutorial(self):
        tutorial = show_tutorial_overlay(
            page=self.page,
            on_complete=self._on_tutorial_done,
            is_dark=self.is_dark_mode(),
        )
        self.page.overlay.append(tutorial)
        self.page.update()

    def _on_tutorial_done(self):
        self.settings.mark_tutorial_completed()
        # Remove overlay...
```

## Performance Considerations

- Tutorial overlay uses Flet's Stack for efficient rendering
- Animations use hardware acceleration when available
- Minimal re-rendering during step transitions
- Lazy loading of tutorial content

## Security & Privacy

- Tutorial does not collect any user data
- No network calls or analytics
- Settings stored locally only
- No external dependencies

## License

Tutorial overlay system is part of DocAssist EMR and follows the same license.

---

**Last Updated**: 2026-01-05
**Version**: 1.0
**Maintainer**: DocAssist Development Team
