# App Icons

This directory should contain app icons for Android and iOS builds.

## Required Files

### 1. Main App Icon
**File**: `icon.png`
**Size**: 1024x1024 pixels
**Format**: PNG with transparency
**Usage**: Main app icon for both platforms

**Design Guidelines**:
- Use DocAssist brand colors (Primary: #0066CC)
- Keep design simple and recognizable at small sizes
- Include medical/EMR symbolism (e.g., stethoscope, medical cross, clipboard)
- Avoid text (icon should work globally)
- Use rounded corners (iOS will apply mask automatically)

### 2. Android Adaptive Icon (Optional)
**File**: `adaptive_foreground.png`
**Size**: 1024x1024 pixels
**Format**: PNG with transparency
**Usage**: Android 8.0+ adaptive icons

**Design Guidelines**:
- Safe zone: Keep important content in center 66% (684x684px)
- Outer 15% may be masked on some devices
- Transparent background (color set in pyproject.toml)

## Icon Generation Tools

### Option 1: Online Generator
Use a free tool like:
- https://easyappicon.com/
- https://appicon.co/
- https://www.appicon.build/

Upload your 1024x1024 PNG and it generates all sizes.

### Option 2: Manual Creation
Create in design tools:
- Figma (recommended for SVG workflow)
- Adobe Illustrator
- Sketch
- Affinity Designer

Export as 1024x1024 PNG.

### Option 3: Use Flet Default
If no icon is provided, Flet uses a default icon during build.

## Quick Start (Placeholder Icon)

To create a simple placeholder icon:

```python
# Run this script to generate a basic placeholder
from PIL import Image, ImageDraw, ImageFont

# Create 1024x1024 image
img = Image.new('RGB', (1024, 1024), color='#0066CC')
draw = ImageDraw.Draw(img)

# Add a white "D+" symbol
draw.text((512, 512), "D+", fill='white', anchor='mm',
          font=ImageFont.truetype("Arial", 400))

img.save('icon.png')
print("Placeholder icon created: icon.png")
```

Or use ImageMagick:
```bash
convert -size 1024x1024 xc:'#0066CC' \
        -gravity center -fill white -font Arial-Bold -pointsize 400 \
        -annotate +0+0 'D+' \
        icon.png
```

## Checklist

- [ ] Create 1024x1024 icon.png
- [ ] Test icon visibility at small sizes (48px, 72px)
- [ ] Verify icon matches brand guidelines
- [ ] (Optional) Create adaptive_foreground.png for Android
- [ ] Update pyproject.toml if using custom adaptive background color
