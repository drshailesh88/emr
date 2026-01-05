#!/usr/bin/env python3
"""
Create Placeholder Assets for DocAssist Mobile

Generates basic app icon and splash screen for quick testing.
Replace with professional assets before production release.

Usage:
    python create_placeholder_assets.py
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL (Pillow) not installed. Install with: pip install Pillow")


def create_app_icon():
    """Create a basic app icon."""
    if not PIL_AVAILABLE:
        return False

    print("Creating app icon...")

    # Create 1024x1024 image with DocAssist blue background
    img = Image.new('RGB', (1024, 1024), color='#0066CC')
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    try:
        # Try common font locations
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 400)
                break

        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # Draw "D+" in white
    text = "D+"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    x = (1024 - text_width) // 2
    y = (1024 - text_height) // 2

    draw.text((x, y), text, fill='white', font=font)

    # Add small medical cross in corner
    cross_size = 60
    cross_margin = 80
    cross_x = 1024 - cross_margin - cross_size
    cross_y = cross_margin

    # Vertical bar of cross
    draw.rectangle(
        [cross_x + cross_size//3, cross_y,
         cross_x + 2*cross_size//3, cross_y + cross_size],
        fill='white'
    )
    # Horizontal bar of cross
    draw.rectangle(
        [cross_x, cross_y + cross_size//3,
         cross_x + cross_size, cross_y + 2*cross_size//3],
        fill='white'
    )

    # Save icon
    icon_path = Path("assets/icons/icon.png")
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(icon_path, 'PNG')

    print(f"✓ App icon created: {icon_path}")
    print(f"  Size: {os.path.getsize(icon_path) / 1024:.1f} KB")

    return True


def create_splash_screen():
    """Create a basic splash screen."""
    if not PIL_AVAILABLE:
        return False

    print("\nCreating splash screen...")

    # Create 2048x2048 image with DocAssist blue background
    img = Image.new('RGB', (2048, 2048), color='#0066CC')
    draw = ImageDraw.Draw(img)

    # Try to use a nice font
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        font_large = None
        font_small = None

        for path in font_paths:
            if os.path.exists(path):
                font_large = ImageFont.truetype(path, 180)
                font_small = ImageFont.truetype(path, 80)
                break

        if not font_large:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw "DocAssist" centered
    title = "DocAssist"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    text_width = bbox[2] - bbox[0]
    x = (2048 - text_width) // 2
    y = 800

    draw.text((x, y), title, fill='white', font=font_large)

    # Draw tagline below
    tagline = "Privacy-first EMR"
    bbox = draw.textbbox((0, 0), tagline, font=font_small)
    text_width = bbox[2] - bbox[0]
    x = (2048 - text_width) // 2
    y = 1100

    draw.text((x, y), tagline, fill='white', font=font_small)

    # Add medical cross at top
    cross_size = 120
    cross_x = (2048 - cross_size) // 2
    cross_y = 500

    # Vertical bar
    draw.rectangle(
        [cross_x + cross_size//3, cross_y,
         cross_x + 2*cross_size//3, cross_y + cross_size],
        fill='white'
    )
    # Horizontal bar
    draw.rectangle(
        [cross_x, cross_y + cross_size//3,
         cross_x + cross_size, cross_y + 2*cross_size//3],
        fill='white'
    )

    # Save splash
    splash_path = Path("assets/splash/splash.png")
    splash_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(splash_path, 'PNG', optimize=True)

    print(f"✓ Splash screen created: {splash_path}")
    print(f"  Size: {os.path.getsize(splash_path) / 1024:.1f} KB")

    return True


def create_adaptive_foreground():
    """Create Android adaptive icon foreground."""
    if not PIL_AVAILABLE:
        return False

    print("\nCreating adaptive icon foreground...")

    # Create 1024x1024 transparent image
    img = Image.new('RGBA', (1024, 1024), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Safe zone: center 66% (684x684)
    # Draw "D+" in white, centered in safe zone
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 350)
                break

        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    text = "D+"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (1024 - text_width) // 2
    y = (1024 - text_height) // 2

    draw.text((x, y), text, fill='white', font=font)

    # Save adaptive foreground
    adaptive_path = Path("assets/icons/adaptive_foreground.png")
    adaptive_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(adaptive_path, 'PNG')

    print(f"✓ Adaptive icon foreground created: {adaptive_path}")
    print(f"  Size: {os.path.getsize(adaptive_path) / 1024:.1f} KB")

    return True


def main():
    """Create all placeholder assets."""
    print("="*60)
    print("DocAssist Mobile - Create Placeholder Assets")
    print("="*60)
    print()

    if not PIL_AVAILABLE:
        print("ERROR: Pillow library required")
        print("Install with: pip install Pillow")
        return 1

    success = True

    # Create app icon
    if not create_app_icon():
        success = False

    # Create splash screen
    if not create_splash_screen():
        success = False

    # Create adaptive foreground (optional)
    create_adaptive_foreground()

    print()
    print("="*60)
    if success:
        print("✓ All placeholder assets created successfully!")
        print()
        print("IMPORTANT:")
        print("- These are PLACEHOLDER assets for testing only")
        print("- Create professional assets before production release")
        print("- See assets/icons/README.md and assets/splash/README.md")
        print()
        print("Next steps:")
        print("1. Test build: ./build_android.sh")
        print("2. Replace with professional assets")
        print("3. Build for release: ./build_android.sh --release")
    else:
        print("✗ Some assets could not be created")
        print("Check error messages above")
        return 1

    print("="*60)

    return 0


if __name__ == "__main__":
    exit(main())
