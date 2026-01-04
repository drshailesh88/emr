"""
Design Tokens for DocAssist EMR Premium UI

This module defines the complete design system for creating a premium,
Apple/Mercedes/Nike-level user interface. All UI components MUST use
these tokens instead of hard-coded values.

Usage:
    from src.ui.tokens import COLORS, TYPOGRAPHY, SPACING, RADIUS, SHADOWS

Philosophy:
    - Quiet Luxury: Restrained palette, generous whitespace, subtle depth
    - Professional Authority: Medical-grade precision, clear hierarchy
    - Effortless Flow: Zero cognitive friction, natural eye movement
"""

import flet as ft
from typing import Dict, Any, Tuple
from dataclasses import dataclass


# =============================================================================
# COLOR PALETTE - Premium Medical Theme
# =============================================================================

class Colors:
    """Premium color palette with semantic meaning."""

    # ---------------------------------------------------------------------
    # Primary - Deep Professional Blue (Trust, Authority, Medical)
    # ---------------------------------------------------------------------
    PRIMARY_50 = "#E8F0FE"   # Lightest - backgrounds, hover states
    PRIMARY_100 = "#D2E3FC"  # Light - subtle highlights
    PRIMARY_200 = "#A8C7FA"  # Lighter - secondary backgrounds
    PRIMARY_300 = "#7CACF8"  # Light-medium
    PRIMARY_400 = "#4A90F5"  # Medium - interactive elements
    PRIMARY_500 = "#1A73E8"  # Base primary - buttons, links
    PRIMARY_600 = "#1557B0"  # Darker - hover states
    PRIMARY_700 = "#104D92"  # Dark - pressed states
    PRIMARY_800 = "#0B3D76"  # Darker
    PRIMARY_900 = "#062E5A"  # Darkest - text on light backgrounds

    # ---------------------------------------------------------------------
    # Accent - Warm Gold (Premium, Achievement, Attention)
    # ---------------------------------------------------------------------
    ACCENT_50 = "#FFF8E1"
    ACCENT_100 = "#FFECB3"
    ACCENT_200 = "#FFE082"
    ACCENT_300 = "#FFD54F"
    ACCENT_400 = "#FFCA28"  # Primary accent
    ACCENT_500 = "#FFC107"  # Base accent
    ACCENT_600 = "#FFB300"
    ACCENT_700 = "#FFA000"
    ACCENT_800 = "#FF8F00"
    ACCENT_900 = "#FF6F00"

    # ---------------------------------------------------------------------
    # Neutral - Sophisticated Grays (Professional, Clean)
    # ---------------------------------------------------------------------
    NEUTRAL_0 = "#FFFFFF"    # Pure white
    NEUTRAL_50 = "#FAFAFA"   # Off-white backgrounds
    NEUTRAL_100 = "#F5F5F5"  # Light backgrounds
    NEUTRAL_150 = "#F0F0F0"  # Slightly darker
    NEUTRAL_200 = "#EEEEEE"  # Borders, dividers
    NEUTRAL_300 = "#E0E0E0"  # Disabled states
    NEUTRAL_400 = "#BDBDBD"  # Placeholder text
    NEUTRAL_500 = "#9E9E9E"  # Secondary text
    NEUTRAL_600 = "#757575"  # Body text
    NEUTRAL_700 = "#616161"  # Strong text
    NEUTRAL_800 = "#424242"  # Headlines
    NEUTRAL_900 = "#212121"  # Primary text
    NEUTRAL_950 = "#121212"  # Near black

    # ---------------------------------------------------------------------
    # Semantic Colors (Contextual Meaning)
    # ---------------------------------------------------------------------

    # Success - Green (Positive, Complete, Safe)
    SUCCESS_LIGHT = "#E6F4EA"
    SUCCESS_MAIN = "#34A853"
    SUCCESS_DARK = "#1E8E3E"
    SUCCESS_CONTRAST = "#FFFFFF"

    # Warning - Amber (Caution, Attention)
    WARNING_LIGHT = "#FEF7E0"
    WARNING_MAIN = "#F9AB00"
    WARNING_DARK = "#E37400"
    WARNING_CONTRAST = "#000000"

    # Error - Red (Danger, Critical, Alert)
    ERROR_LIGHT = "#FCE8E6"
    ERROR_MAIN = "#EA4335"
    ERROR_DARK = "#C5221F"
    ERROR_CONTRAST = "#FFFFFF"

    # Info - Blue (Information, Guidance)
    INFO_LIGHT = "#E8F0FE"
    INFO_MAIN = "#4285F4"
    INFO_DARK = "#1967D2"
    INFO_CONTRAST = "#FFFFFF"

    # ---------------------------------------------------------------------
    # Panel-Specific Colors (Three-panel Layout)
    # ---------------------------------------------------------------------

    # Light Mode Panels
    PANEL_PATIENT_BG = "#FAFBFC"      # Subtle warm gray
    PANEL_CENTRAL_BG = "#FFFFFF"       # Pure white for focus
    PANEL_AGENT_BG = "#F0F4FF"         # Subtle blue tint

    # Dark Mode Panels
    PANEL_PATIENT_BG_DARK = "#1A1A1A"
    PANEL_CENTRAL_BG_DARK = "#121212"
    PANEL_AGENT_BG_DARK = "#1A1F2E"    # Slight blue tint

    # ---------------------------------------------------------------------
    # Interactive States
    # ---------------------------------------------------------------------
    HOVER_OVERLAY = "rgba(0, 0, 0, 0.04)"       # Light mode hover
    HOVER_OVERLAY_DARK = "rgba(255, 255, 255, 0.08)"  # Dark mode hover
    PRESSED_OVERLAY = "rgba(0, 0, 0, 0.08)"
    SELECTED_OVERLAY = "rgba(26, 115, 232, 0.12)"
    FOCUS_RING = "#1A73E8"


# =============================================================================
# TYPOGRAPHY - Clear Hierarchy
# =============================================================================

@dataclass(frozen=True)
class TypeStyle:
    """Typography style definition."""
    size: int
    weight: str  # 'w300', 'w400', 'w500', 'w600', 'w700'
    letter_spacing: float = 0
    line_height: float = 1.4

    def to_flet_weight(self) -> ft.FontWeight:
        """Convert weight string to Flet FontWeight."""
        weights = {
            'w300': ft.FontWeight.W_300,
            'w400': ft.FontWeight.W_400,
            'w500': ft.FontWeight.W_500,
            'w600': ft.FontWeight.W_600,
            'w700': ft.FontWeight.W_700,
        }
        return weights.get(self.weight, ft.FontWeight.W_400)


class Typography:
    """Typography scale for consistent text hierarchy."""

    # Display - Large headlines, branding
    DISPLAY_LARGE = TypeStyle(size=32, weight='w300', letter_spacing=-0.5)
    DISPLAY_MEDIUM = TypeStyle(size=28, weight='w300', letter_spacing=-0.25)
    DISPLAY_SMALL = TypeStyle(size=24, weight='w400')

    # Headline - Section titles
    HEADLINE_LARGE = TypeStyle(size=22, weight='w500')
    HEADLINE_MEDIUM = TypeStyle(size=20, weight='w500')
    HEADLINE_SMALL = TypeStyle(size=18, weight='w500')

    # Title - Component titles, cards
    TITLE_LARGE = TypeStyle(size=18, weight='w500')
    TITLE_MEDIUM = TypeStyle(size=16, weight='w500', letter_spacing=0.15)
    TITLE_SMALL = TypeStyle(size=14, weight='w500', letter_spacing=0.1)

    # Body - Main content
    BODY_LARGE = TypeStyle(size=16, weight='w400', letter_spacing=0.5)
    BODY_MEDIUM = TypeStyle(size=14, weight='w400', letter_spacing=0.25)
    BODY_SMALL = TypeStyle(size=12, weight='w400', letter_spacing=0.4)

    # Label - Form labels, buttons
    LABEL_LARGE = TypeStyle(size=14, weight='w500', letter_spacing=0.1)
    LABEL_MEDIUM = TypeStyle(size=12, weight='w500', letter_spacing=0.5)
    LABEL_SMALL = TypeStyle(size=11, weight='w500', letter_spacing=0.5)

    # Caption - Supporting text
    CAPTION = TypeStyle(size=11, weight='w400', letter_spacing=0.4)
    OVERLINE = TypeStyle(size=10, weight='w500', letter_spacing=1.5)


# =============================================================================
# SPACING - Consistent Rhythm (4px Base Unit)
# =============================================================================

class Spacing:
    """Spacing scale based on 4px grid system."""

    NONE = 0
    XXS = 4    # Tight spacing
    XS = 8     # Small elements
    SM = 12    # Compact spacing
    MD = 16    # Default spacing
    LG = 24    # Section spacing
    XL = 32    # Large gaps
    XXL = 48   # Major sections
    XXXL = 64  # Page-level

    # Semantic spacing aliases
    INLINE = 8           # Between inline elements
    STACK = 16           # Between stacked elements
    SECTION = 32         # Between sections
    PAGE_MARGIN = 24     # Page margins
    CARD_PADDING = 16    # Card internal padding
    INPUT_PADDING = 12   # Form input padding
    BUTTON_PADDING_H = 24  # Button horizontal
    BUTTON_PADDING_V = 12  # Button vertical


# =============================================================================
# BORDER RADIUS - Soft but Professional
# =============================================================================

class Radius:
    """Border radius scale for consistent roundness."""

    NONE = 0
    XS = 2      # Minimal rounding
    SM = 4      # Subtle rounding
    MD = 8      # Default rounding
    LG = 12     # Cards, dialogs
    XL = 16     # Large containers
    XXL = 24    # Prominent elements
    FULL = 9999 # Fully rounded (pills)

    # Semantic aliases
    BUTTON = 8
    CARD = 12
    DIALOG = 16
    INPUT = 8
    CHIP = 16
    AVATAR = 9999


# =============================================================================
# SHADOWS - Subtle Depth
# =============================================================================

@dataclass(frozen=True)
class Shadow:
    """Shadow definition for elevation."""
    blur: int
    spread: int
    offset_x: int
    offset_y: int
    opacity: float

    def to_flet_shadow(self, is_dark: bool = False) -> ft.BoxShadow:
        """Convert to Flet BoxShadow."""
        color = f"rgba(0,0,0,{self.opacity})" if not is_dark else f"rgba(0,0,0,{self.opacity * 1.5})"
        return ft.BoxShadow(
            blur_radius=self.blur,
            spread_radius=self.spread,
            offset=ft.Offset(self.offset_x, self.offset_y),
            color=color,
        )


class Shadows:
    """Shadow scale for elevation hierarchy."""

    NONE = Shadow(blur=0, spread=0, offset_x=0, offset_y=0, opacity=0)

    # Subtle elevation
    XS = Shadow(blur=2, spread=0, offset_x=0, offset_y=1, opacity=0.05)

    # Light elevation - buttons, cards
    SM = Shadow(blur=4, spread=0, offset_x=0, offset_y=2, opacity=0.08)

    # Medium elevation - dropdowns, menus
    MD = Shadow(blur=8, spread=0, offset_x=0, offset_y=4, opacity=0.12)

    # High elevation - dialogs, modals
    LG = Shadow(blur=16, spread=2, offset_x=0, offset_y=8, opacity=0.15)

    # Maximum elevation - popovers
    XL = Shadow(blur=24, spread=4, offset_x=0, offset_y=12, opacity=0.18)

    # Semantic aliases
    CARD = SM
    CARD_HOVER = MD
    DROPDOWN = MD
    DIALOG = LG
    TOOLTIP = SM


# =============================================================================
# MOTION - Smooth Animations
# =============================================================================

class Motion:
    """Animation timing values in milliseconds."""

    INSTANT = 0
    FAST = 100        # Quick interactions
    NORMAL = 200      # Standard transitions
    SLOW = 300        # Deliberate animations
    EMPHASIS = 400    # Attention-grabbing
    ENTRANCE = 250    # Elements entering
    EXIT = 200        # Elements leaving

    # Easing curves (for reference - Flet uses AnimationCurve)
    EASE_OUT = "cubic-bezier(0, 0, 0.2, 1)"
    EASE_IN = "cubic-bezier(0.4, 0, 1, 1)"
    EASE_IN_OUT = "cubic-bezier(0.4, 0, 0.2, 1)"


# =============================================================================
# BREAKPOINTS - Responsive Design
# =============================================================================

class Breakpoints:
    """Screen width breakpoints for responsive design."""

    XS = 0      # Mobile small
    SM = 600    # Mobile large / tablet portrait
    MD = 960    # Tablet landscape
    LG = 1280   # Desktop
    XL = 1920   # Large desktop


# =============================================================================
# Z-INDEX - Layer Management
# =============================================================================

class ZIndex:
    """Z-index scale for layering."""

    BASE = 0
    DROPDOWN = 100
    STICKY = 200
    OVERLAY = 300
    MODAL = 400
    POPOVER = 500
    TOOLTIP = 600
    TOAST = 700


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_theme_colors(is_dark: bool) -> Dict[str, str]:
    """Get theme-aware color set.

    Args:
        is_dark: Whether dark mode is active

    Returns:
        Dictionary of color values for current theme
    """
    if is_dark:
        return {
            'background': Colors.NEUTRAL_950,
            'surface': "#1E1E1E",
            'surface_variant': "#2D2D2D",
            'on_background': Colors.NEUTRAL_100,
            'on_surface': Colors.NEUTRAL_200,
            'primary': Colors.PRIMARY_200,
            'on_primary': Colors.NEUTRAL_900,
            'secondary': Colors.PRIMARY_300,
            'divider': Colors.NEUTRAL_700,
            'outline': Colors.NEUTRAL_600,
            'patient_panel': Colors.PANEL_PATIENT_BG_DARK,
            'central_panel': Colors.PANEL_CENTRAL_BG_DARK,
            'agent_panel': Colors.PANEL_AGENT_BG_DARK,
        }
    else:
        return {
            'background': Colors.NEUTRAL_0,
            'surface': Colors.NEUTRAL_50,
            'surface_variant': Colors.NEUTRAL_100,
            'on_background': Colors.NEUTRAL_900,
            'on_surface': Colors.NEUTRAL_800,
            'primary': Colors.PRIMARY_500,
            'on_primary': Colors.NEUTRAL_0,
            'secondary': Colors.PRIMARY_600,
            'divider': Colors.NEUTRAL_200,
            'outline': Colors.NEUTRAL_300,
            'patient_panel': Colors.PANEL_PATIENT_BG,
            'central_panel': Colors.PANEL_CENTRAL_BG,
            'agent_panel': Colors.PANEL_AGENT_BG,
        }


def create_premium_theme(is_dark: bool = False) -> ft.Theme:
    """Create premium Flet theme.

    Args:
        is_dark: Whether to create dark theme

    Returns:
        Configured Flet Theme object
    """
    colors = get_theme_colors(is_dark)

    if is_dark:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=Colors.PRIMARY_200,
                on_primary=Colors.NEUTRAL_900,
                primary_container=Colors.PRIMARY_700,
                on_primary_container=Colors.PRIMARY_100,
                secondary=Colors.PRIMARY_300,
                on_secondary=Colors.NEUTRAL_900,
                background=Colors.NEUTRAL_950,
                on_background=Colors.NEUTRAL_100,
                surface="#1E1E1E",
                on_surface=Colors.NEUTRAL_200,
                surface_variant="#2D2D2D",
                on_surface_variant=Colors.NEUTRAL_400,
                error=Colors.ERROR_MAIN,
                on_error=Colors.NEUTRAL_0,
                outline=Colors.NEUTRAL_600,
            ),
            use_material3=True,
        )
    else:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=Colors.PRIMARY_500,
                on_primary=Colors.NEUTRAL_0,
                primary_container=Colors.PRIMARY_100,
                on_primary_container=Colors.PRIMARY_900,
                secondary=Colors.PRIMARY_600,
                on_secondary=Colors.NEUTRAL_0,
                background=Colors.NEUTRAL_0,
                on_background=Colors.NEUTRAL_900,
                surface=Colors.NEUTRAL_50,
                on_surface=Colors.NEUTRAL_800,
                surface_variant=Colors.NEUTRAL_100,
                on_surface_variant=Colors.NEUTRAL_700,
                error=Colors.ERROR_MAIN,
                on_error=Colors.NEUTRAL_0,
                outline=Colors.NEUTRAL_300,
            ),
            use_material3=True,
        )


# =============================================================================
# COMPONENT STYLE HELPERS
# =============================================================================

def primary_button_style(is_dark: bool = False) -> ft.ButtonStyle:
    """Get premium primary button style."""
    return ft.ButtonStyle(
        color=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
        bgcolor=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200,
        padding=ft.padding.symmetric(
            horizontal=Spacing.BUTTON_PADDING_H,
            vertical=Spacing.BUTTON_PADDING_V
        ),
        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
        elevation=2,
        animation_duration=Motion.FAST,
    )


def secondary_button_style(is_dark: bool = False) -> ft.ButtonStyle:
    """Get premium secondary button style."""
    return ft.ButtonStyle(
        color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200,
        bgcolor=ft.Colors.TRANSPARENT,
        overlay_color=Colors.SELECTED_OVERLAY,
        padding=ft.padding.symmetric(
            horizontal=Spacing.BUTTON_PADDING_H,
            vertical=Spacing.BUTTON_PADDING_V
        ),
        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
        side=ft.BorderSide(
            width=1.5,
            color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200
        ),
        animation_duration=Motion.FAST,
    )


def danger_button_style(is_dark: bool = False) -> ft.ButtonStyle:
    """Get premium danger button style."""
    return ft.ButtonStyle(
        color=Colors.ERROR_CONTRAST,
        bgcolor=Colors.ERROR_MAIN if not is_dark else Colors.ERROR_DARK,
        padding=ft.padding.symmetric(
            horizontal=Spacing.BUTTON_PADDING_H,
            vertical=Spacing.BUTTON_PADDING_V
        ),
        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
        elevation=2,
        animation_duration=Motion.FAST,
    )


def card_container(is_dark: bool = False, selected: bool = False) -> Dict[str, Any]:
    """Get premium card container properties."""
    colors = get_theme_colors(is_dark)

    if selected:
        bgcolor = Colors.SELECTED_OVERLAY if not is_dark else f"rgba(160, 199, 250, 0.15)"
        border = ft.border.all(2, Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200)
    else:
        bgcolor = colors['surface']
        border = ft.border.all(1, colors['divider'])

    return {
        'bgcolor': bgcolor,
        'border': border,
        'border_radius': Radius.CARD,
        'padding': Spacing.CARD_PADDING,
        'shadow': Shadows.CARD.to_flet_shadow(is_dark),
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'Colors',
    'Typography',
    'TypeStyle',
    'Spacing',
    'Radius',
    'Shadow',
    'Shadows',
    'Motion',
    'Breakpoints',
    'ZIndex',
    'get_theme_colors',
    'create_premium_theme',
    'primary_button_style',
    'secondary_button_style',
    'danger_button_style',
    'card_container',
]
