# Splash Screen

This directory should contain the splash screen shown while the app loads.

## Required File

**File**: `splash.png`
**Size**: 2048x2048 pixels (or 1242x2688 for full screen)
**Format**: PNG with transparency
**Usage**: Displayed while app initializes

## Design Guidelines

### Layout
- **Background**: Solid color (#0066CC - DocAssist primary)
- **Logo**: Centered, ~40% of screen height
- **Tagline** (optional): Below logo, small text
- **Safe area**: Keep content within center 80% to avoid notch/status bar

### Branding
- Use DocAssist logo (white on blue background)
- Include tagline: "Privacy-first EMR for Indian doctors"
- Keep design minimal for fast perceived load time

### Platform Considerations

**Android**:
- Android 12+ uses new splash screen API
- Shows icon from `pyproject.toml` on colored background
- Legacy Android shows full splash.png

**iOS**:
- Uses splash.png as launch image
- System applies safe area insets automatically

## Quick Start (Placeholder Splash)

### Option 1: Simple Color + Text

Create with ImageMagick:
```bash
# Create blue background with white text
convert -size 2048x2048 xc:'#0066CC' \
        -gravity center -fill white -font Arial-Bold \
        -pointsize 120 -annotate +0-200 'DocAssist' \
        -pointsize 60 -annotate +0+200 'Privacy-first EMR' \
        splash.png
```

### Option 2: Python Script

```python
from PIL import Image, ImageDraw, ImageFont

# Create image
img = Image.new('RGB', (2048, 2048), color='#0066CC')
draw = ImageDraw.Draw(img)

# Add logo text
font_large = ImageFont.truetype("Arial", 180)
font_small = ImageFont.truetype("Arial", 80)

draw.text((1024, 824), "DocAssist", fill='white', anchor='mm', font=font_large)
draw.text((1024, 1224), "Privacy-first EMR", fill='white', anchor='mm', font=font_small)

img.save('splash.png')
print("Splash screen created: splash.png")
```

### Option 3: Use Default

If no splash.png is provided, Flet uses a default splash with your app icon.

## Android 12+ Splash API

For Android 12+, the splash is configured in `pyproject.toml`:

```toml
[tool.flet.splash]
color = "#0066CC"  # Background color
image = "assets/splash/splash.png"  # Icon (not full screen)
android_12 = true  # Use new API
```

On Android 12+, the system shows:
- Colored background (from `color`)
- App icon centered
- System-controlled animation

## Testing

### Test on Different Screen Sizes
- Small phone: 5.5" (1920x1080)
- Medium phone: 6.1" (2532x1170)
- Large phone: 6.7" (3120x1440)
- Tablet: 10" (2560x1600)

### Test on Both Platforms
- Android: Various manufacturers (Samsung, Xiaomi, OnePlus)
- iOS: Different models (iPhone 13, 14, 15, Plus, Pro Max)

### Performance
- Keep file size under 500KB (use PNG compression)
- Test cold start time on low-end device
- Ensure splash doesn't show longer than 2 seconds

## Best Practices

✅ **DO**:
- Use brand colors consistently
- Keep design simple and clean
- Optimize image size (compress PNG)
- Test on actual devices
- Support dark mode (optional: splash_dark.png)

❌ **DON'T**:
- Include loading indicators (system provides)
- Use complex animations (not supported)
- Add version numbers (changes too often)
- Use small text (hard to read quickly)

## Checklist

- [ ] Create 2048x2048 splash.png
- [ ] Verify colors match brand guidelines (#0066CC)
- [ ] Test on Android device (check Android 12+ behavior)
- [ ] Test on iOS device (check safe area)
- [ ] Optimize file size (<500KB)
- [ ] (Optional) Create splash_dark.png for dark mode
