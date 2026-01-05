# Tutorial Overlay - Quick Reference

## For Developers

### Importing

```python
from src.ui.components.tutorial_overlay import (
    TutorialOverlay,
    TutorialStep,
    show_tutorial_overlay
)
```

### Basic Usage

```python
# Show tutorial
tutorial = show_tutorial_overlay(
    page=page,
    on_complete=lambda: print("Done!"),
    on_skip=lambda: print("Skipped"),
    is_dark=False
)

# Add to page
page.overlay.append(tutorial)
page.update()
```

### Check Tutorial Status

```python
from src.services.settings import SettingsService

settings = SettingsService()

# Check if completed
if not settings.is_tutorial_completed():
    # Show tutorial
    pass

# Mark as completed
settings.mark_tutorial_completed()

# Reset (for testing)
settings.reset_tutorial()
```

### Custom Tutorial Steps

```python
tutorial = TutorialOverlay(page=page, on_complete=callback)

# Add custom step
tutorial.steps.append(
    TutorialStep(
        title="Custom Feature",
        description="Explanation here...",
        icon=ft.Icons.STAR,
        spotlight_position="center",  # "left", "center", "right"
        spotlight_vertical="middle"    # "top", "middle", "bottom"
    )
)
```

## For Users

### First-Time Experience

1. Launch DocAssist EMR
2. Complete setup wizard (or skip)
3. Tutorial automatically appears
4. Follow 5 steps to learn features
5. Click "Complete" or "Skip"

### Re-watching Tutorial

1. Click Help button (? icon) in header
2. Click "Show Tutorial Again"
3. Tutorial replays from step 1

### Tutorial Steps Overview

| Step | Topic | What You'll Learn |
|------|-------|-------------------|
| 1 | Patient Panel | Search, add, manage patients |
| 2 | Recording Visits | Enter notes, use voice input |
| 3 | AI Prescription | Generate prescriptions with AI |
| 4 | AI Assistant | Query patient history |
| 5 | Settings & Backup | Configure app, enable backups |

### Keyboard Controls

- **Next**: Click "Next" button or Space
- **Previous**: Click "Previous" button
- **Skip**: Click "Skip Tutorial"
- **Complete**: Click "Complete Tutorial" on last step

## For Testers

### Reset Tutorial

```bash
# Method 1: Python script
python3 -c "
from src.services.settings import SettingsService
SettingsService().reset_tutorial()
"

# Method 2: Manual edit
# Edit data/settings.json:
# Set "tutorial_completed": false
```

### Test Scenarios

1. **First run**: Delete `data/settings.json`, restart app
2. **Skip tutorial**: Click "Skip Tutorial" on any step
3. **Complete tutorial**: Step through all 5 steps
4. **Re-trigger**: Use "Show Tutorial Again" from Help
5. **Dark mode**: Toggle dark mode, check tutorial appearance
6. **Navigation**: Test Previous/Next buttons thoroughly
7. **Persistence**: Complete tutorial, restart app, verify no tutorial

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Configuration

### Settings File Location

```
data/settings.json
```

### Tutorial Setting

```json
{
  "tutorial_completed": false  // false = show, true = hide
}
```

### Customization Points

| Property | File | Line | Description |
|----------|------|------|-------------|
| Steps | tutorial_overlay.py | 63-104 | Tutorial step definitions |
| Overlay opacity | tutorial_overlay.py | 123 | Background transparency |
| Animation duration | tutorial_overlay.py | 155, 225 | Transition speed |
| Spotlight size | tutorial_overlay.py | 151-172 | Highlight dimensions |
| Card position | tutorial_overlay.py | 216-231 | Content card placement |

## Troubleshooting

### Tutorial Not Showing

1. Check `data/settings.json` exists
2. Verify `tutorial_completed` is `false`
3. Check logs for errors
4. Ensure first run is detected

### Spotlight Misaligned

1. Verify UI layout hasn't changed
2. Check spotlight position values
3. Adjust dimensions in `_build_spotlight()`

### Animation Lag

1. Reduce animation duration (400ms → 200ms)
2. Simplify shadow effects
3. Check system resources

## Support

- **Documentation**: `/docs/TUTORIAL_SYSTEM.md`
- **Implementation**: `/docs/TUTORIAL_IMPLEMENTATION_SUMMARY.md`
- **Demo**: `python examples/tutorial_overlay_demo.py`
- **Source**: `/src/ui/components/tutorial_overlay.py`

---

**Version**: 1.0
**Last Updated**: 2026-01-05
