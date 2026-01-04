"""
Mobile Design Tokens - Imports from desktop with mobile adaptations.

For mobile, we adjust:
- Touch targets: minimum 48px (vs 24px on desktop)
- Typography: slightly larger for legibility
- Spacing: more generous for finger taps
"""

import sys
import os

# Try to import from desktop
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from src.ui.tokens import (
        Colors,
        Typography,
        Spacing,
        Radius,
        Shadows,
        Motion,
        get_theme_colors,
    )
    DESKTOP_TOKENS_AVAILABLE = True
except ImportError:
    DESKTOP_TOKENS_AVAILABLE = False

    # Fallback: Define essential tokens for mobile standalone
    class Colors:
        """Premium color palette."""
        PRIMARY_500 = "#1A73E8"
        PRIMARY_600 = "#1557B0"
        PRIMARY_50 = "#E8F0FE"
        PRIMARY_100 = "#D2E3FC"
        PRIMARY_200 = "#A8C7FA"

        ACCENT_500 = "#FFC107"

        NEUTRAL_0 = "#FFFFFF"
        NEUTRAL_50 = "#FAFAFA"
        NEUTRAL_100 = "#F5F5F5"
        NEUTRAL_200 = "#EEEEEE"
        NEUTRAL_300 = "#E0E0E0"
        NEUTRAL_400 = "#BDBDBD"
        NEUTRAL_500 = "#9E9E9E"
        NEUTRAL_600 = "#757575"
        NEUTRAL_700 = "#616161"
        NEUTRAL_800 = "#424242"
        NEUTRAL_900 = "#212121"
        NEUTRAL_950 = "#121212"

        SUCCESS_MAIN = "#34A853"
        WARNING_MAIN = "#F9AB00"
        ERROR_MAIN = "#EA4335"
        INFO_MAIN = "#4285F4"

        SUCCESS_LIGHT = "#E6F4EA"
        ERROR_LIGHT = "#FCE8E6"

        HOVER_OVERLAY = "rgba(0, 0, 0, 0.04)"
        SELECTED_OVERLAY = "rgba(26, 115, 232, 0.12)"

    class Spacing:
        """Spacing scale (4px base)."""
        XXS = 4
        XS = 8
        SM = 12
        MD = 16
        LG = 24
        XL = 32
        XXL = 48

    class Radius:
        """Border radius scale."""
        SM = 4
        MD = 8
        LG = 12
        XL = 16
        FULL = 9999
        CARD = 12
        BUTTON = 8


# Mobile-specific overrides
class MobileSpacing(Spacing):
    """Mobile-adjusted spacing for touch targets."""

    # Touch target minimum (48px per Material Design)
    TOUCH_TARGET = 48

    # More generous padding for mobile
    CARD_PADDING = 16
    SCREEN_PADDING = 16
    LIST_ITEM_PADDING = 16

    # Bottom navigation height
    NAV_HEIGHT = 64


class MobileTypography:
    """Mobile-adjusted typography for legibility."""

    # Slightly larger for mobile screens
    DISPLAY_LARGE = 28
    DISPLAY_MEDIUM = 24
    HEADLINE_LARGE = 22
    HEADLINE_MEDIUM = 20
    TITLE_LARGE = 18
    TITLE_MEDIUM = 16
    BODY_LARGE = 16
    BODY_MEDIUM = 14
    BODY_SMALL = 12
    LABEL_LARGE = 14
    LABEL_MEDIUM = 12
    CAPTION = 11


# Export mobile-specific tokens
__all__ = [
    'Colors',
    'Spacing',
    'MobileSpacing',
    'Radius',
    'MobileTypography',
    'DESKTOP_TOKENS_AVAILABLE',
]
