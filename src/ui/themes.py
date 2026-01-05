"""
Premium Theme System for DocAssist EMR

This module provides premium themes using design tokens.
All themes are built on the token system for consistency.

Usage:
    from src.ui.themes import get_theme, get_colors, is_dark_mode
"""

import flet as ft
from typing import Dict, Any

from .tokens import (
    Colors,
    Typography,
    Spacing,
    Radius,
    Shadows,
    Motion,
    create_premium_theme,
    get_theme_colors,
    primary_button_style,
    secondary_button_style,
    danger_button_style,
)


# =============================================================================
# PREMIUM THEMES - Built on Design Tokens
# =============================================================================

def get_light_theme() -> ft.Theme:
    """Get premium light theme."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            # Primary - Professional Blue
            primary=Colors.PRIMARY_500,
            on_primary=Colors.NEUTRAL_0,
            primary_container=Colors.PRIMARY_100,
            on_primary_container=Colors.PRIMARY_900,

            # Secondary
            secondary=Colors.PRIMARY_600,
            on_secondary=Colors.NEUTRAL_0,
            secondary_container=Colors.PRIMARY_50,
            on_secondary_container=Colors.PRIMARY_800,

            # Background - Pure white for focus
            background=Colors.NEUTRAL_0,
            on_background=Colors.NEUTRAL_900,

            # Surface - Subtle gray for depth
            surface=Colors.NEUTRAL_50,
            on_surface=Colors.NEUTRAL_800,
            surface_variant=Colors.NEUTRAL_100,
            on_surface_variant=Colors.NEUTRAL_700,

            # Error states
            error=Colors.ERROR_MAIN,
            on_error=Colors.NEUTRAL_0,
            error_container=Colors.ERROR_LIGHT,
            on_error_container=Colors.ERROR_DARK,

            # Utility
            outline=Colors.NEUTRAL_300,
            shadow=Colors.NEUTRAL_900,

            # Inverse (for contrast elements)
            inverse_surface=Colors.NEUTRAL_800,
            on_inverse_surface=Colors.NEUTRAL_100,
            inverse_primary=Colors.PRIMARY_200,
        ),
        use_material3=True,
    )


def get_dark_theme() -> ft.Theme:
    """Get premium dark theme - sophisticated, not just inverted."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            # Primary - Lighter for dark background contrast
            primary=Colors.PRIMARY_200,
            on_primary=Colors.NEUTRAL_900,
            primary_container=Colors.PRIMARY_700,
            on_primary_container=Colors.PRIMARY_100,

            # Secondary
            secondary=Colors.PRIMARY_300,
            on_secondary=Colors.NEUTRAL_900,
            secondary_container=Colors.PRIMARY_800,
            on_secondary_container=Colors.PRIMARY_100,

            # Background - Near black, OLED-friendly
            background=Colors.NEUTRAL_950,
            on_background=Colors.NEUTRAL_100,

            # Surface - Elevated dark surfaces
            surface="#1E1E1E",
            on_surface=Colors.NEUTRAL_200,
            surface_variant="#2D2D2D",
            on_surface_variant=Colors.NEUTRAL_400,

            # Error states - Lighter for dark mode
            error="#F28B82",  # Softer red
            on_error=Colors.NEUTRAL_900,
            error_container=Colors.ERROR_DARK,
            on_error_container="#FADADD",

            # Utility
            outline=Colors.NEUTRAL_600,
            shadow=Colors.NEUTRAL_950,

            # Inverse
            inverse_surface=Colors.NEUTRAL_100,
            on_inverse_surface=Colors.NEUTRAL_900,
            inverse_primary=Colors.PRIMARY_700,
        ),
        use_material3=True,
    )


# Legacy exports for backward compatibility
LIGHT_THEME = get_light_theme()
DARK_THEME = get_dark_theme()


# =============================================================================
# PANEL COLORS - Three-Panel Layout Specific
# =============================================================================

def get_panel_colors(is_dark: bool) -> Dict[str, str]:
    """Get premium panel-specific colors.

    Args:
        is_dark: Whether dark mode is active

    Returns:
        Dictionary of panel color values
    """
    if is_dark:
        return {
            # Panel backgrounds with subtle distinction
            'patient_panel_bg': Colors.PANEL_PATIENT_BG_DARK,
            'patient_panel_border': Colors.NEUTRAL_700,
            'central_panel_bg': Colors.PANEL_CENTRAL_BG_DARK,
            'agent_panel_bg': Colors.PANEL_AGENT_BG_DARK,

            # Header
            'header_bg': "#1A1A1A",
            'header_border': Colors.NEUTRAL_800,

            # Cards
            'card_bg': "#252525",
            'card_hover_bg': "#2D2D2D",
            'card_selected_bg': "rgba(160, 199, 250, 0.15)",
            'card_selected_border': Colors.PRIMARY_300,

            # Text hierarchy
            'text_primary': Colors.NEUTRAL_100,
            'text_secondary': Colors.NEUTRAL_400,
            'text_tertiary': Colors.NEUTRAL_500,

            # Status
            'status_text': Colors.NEUTRAL_400,
            'status_success': Colors.SUCCESS_MAIN,
            'status_error': "#F28B82",

            # Dividers & borders
            'divider': Colors.NEUTRAL_800,
            'border': Colors.NEUTRAL_700,

            # Interactive
            'hover_overlay': Colors.HOVER_OVERLAY_DARK,
            'focus_ring': Colors.PRIMARY_300,
        }
    else:
        return {
            # Panel backgrounds - subtle warmth
            'patient_panel_bg': Colors.PANEL_PATIENT_BG,
            'patient_panel_border': Colors.NEUTRAL_200,
            'central_panel_bg': Colors.PANEL_CENTRAL_BG,
            'agent_panel_bg': Colors.PANEL_AGENT_BG,

            # Header - clean white with subtle shadow
            'header_bg': Colors.NEUTRAL_0,
            'header_border': Colors.NEUTRAL_200,

            # Cards
            'card_bg': Colors.NEUTRAL_0,
            'card_hover_bg': Colors.NEUTRAL_50,
            'card_selected_bg': Colors.PRIMARY_50,
            'card_selected_border': Colors.PRIMARY_500,

            # Text hierarchy
            'text_primary': Colors.NEUTRAL_900,
            'text_secondary': Colors.NEUTRAL_600,
            'text_tertiary': Colors.NEUTRAL_500,

            # Status
            'status_text': Colors.NEUTRAL_600,
            'status_success': Colors.SUCCESS_MAIN,
            'status_error': Colors.ERROR_MAIN,

            # Dividers & borders
            'divider': Colors.NEUTRAL_200,
            'border': Colors.NEUTRAL_300,

            # Interactive
            'hover_overlay': Colors.HOVER_OVERLAY,
            'focus_ring': Colors.PRIMARY_500,
        }


# =============================================================================
# SEMANTIC COLORS - Alert States
# =============================================================================

def get_alert_colors(is_dark: bool) -> Dict[str, str]:
    """Get semantic alert colors.

    Args:
        is_dark: Whether dark mode is active

    Returns:
        Dictionary of alert color values
    """
    if is_dark:
        return {
            'success': Colors.SUCCESS_MAIN,
            'success_bg': "rgba(52, 168, 83, 0.15)",
            'warning': Colors.WARNING_MAIN,
            'warning_bg': "rgba(249, 171, 0, 0.15)",
            'error': "#F28B82",
            'error_bg': "rgba(234, 67, 53, 0.15)",
            'info': Colors.PRIMARY_200,
            'info_bg': "rgba(66, 133, 244, 0.15)",
        }
    else:
        return {
            'success': Colors.SUCCESS_DARK,
            'success_bg': Colors.SUCCESS_LIGHT,
            'warning': Colors.WARNING_DARK,
            'warning_bg': Colors.WARNING_LIGHT,
            'error': Colors.ERROR_DARK,
            'error_bg': Colors.ERROR_LIGHT,
            'info': Colors.INFO_DARK,
            'info_bg': Colors.INFO_LIGHT,
        }


# =============================================================================
# COMPONENT STYLE FACTORIES
# =============================================================================

def get_button_style(
    variant: str = "primary",
    is_dark: bool = False,
    size: str = "medium"
) -> ft.ButtonStyle:
    """Get premium button style.

    Args:
        variant: "primary", "secondary", "danger", "ghost"
        is_dark: Whether dark mode is active
        size: "small", "medium", "large"

    Returns:
        Configured ButtonStyle
    """
    # Size configurations
    sizes = {
        "small": {"h_pad": Spacing.MD, "v_pad": Spacing.XS, "radius": Radius.SM},
        "medium": {"h_pad": Spacing.LG, "v_pad": Spacing.SM, "radius": Radius.MD},
        "large": {"h_pad": Spacing.XL, "v_pad": Spacing.MD, "radius": Radius.MD},
    }
    size_config = sizes.get(size, sizes["medium"])

    # Base style
    base_style = {
        "padding": ft.padding.symmetric(
            horizontal=size_config["h_pad"],
            vertical=size_config["v_pad"]
        ),
        "shape": ft.RoundedRectangleBorder(radius=size_config["radius"]),
        "animation_duration": Motion.FAST,
    }

    if variant == "primary":
        return ft.ButtonStyle(
            **base_style,
            color=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
            bgcolor=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200,
            elevation=2,
        )
    elif variant == "secondary":
        return ft.ButtonStyle(
            **base_style,
            color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200,
            bgcolor=ft.Colors.TRANSPARENT,
            overlay_color=Colors.SELECTED_OVERLAY,
            side=ft.BorderSide(
                width=1.5,
                color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_200
            ),
        )
    elif variant == "danger":
        return ft.ButtonStyle(
            **base_style,
            color=Colors.NEUTRAL_0,
            bgcolor=Colors.ERROR_MAIN if not is_dark else Colors.ERROR_DARK,
            elevation=2,
        )
    elif variant == "ghost":
        return ft.ButtonStyle(
            **base_style,
            color=Colors.NEUTRAL_700 if not is_dark else Colors.NEUTRAL_300,
            bgcolor=ft.Colors.TRANSPARENT,
            overlay_color=Colors.HOVER_OVERLAY if not is_dark else Colors.HOVER_OVERLAY_DARK,
        )
    else:
        return primary_button_style(is_dark)


def get_text_field_style(is_dark: bool = False) -> Dict[str, Any]:
    """Get premium text field properties.

    Args:
        is_dark: Whether dark mode is active

    Returns:
        Dictionary of TextField properties
    """
    colors = get_panel_colors(is_dark)

    return {
        "border_radius": Radius.INPUT,
        "border_color": colors['border'],
        "focused_border_color": colors['focus_ring'],
        "bgcolor": colors['card_bg'],
        "color": colors['text_primary'],
        "cursor_color": colors['focus_ring'],
        "selection_color": Colors.SELECTED_OVERLAY,
        "label_style": ft.TextStyle(
            color=colors['text_secondary'],
            size=Typography.LABEL_MEDIUM.size,
        ),
        "hint_style": ft.TextStyle(
            color=colors['text_tertiary'],
            size=Typography.BODY_MEDIUM.size,
        ),
        "content_padding": ft.padding.symmetric(
            horizontal=Spacing.MD,
            vertical=Spacing.SM,
        ),
    }


def get_card_style(
    is_dark: bool = False,
    selected: bool = False,
    elevated: bool = True
) -> Dict[str, Any]:
    """Get premium card container properties.

    Args:
        is_dark: Whether dark mode is active
        selected: Whether card is selected
        elevated: Whether to show shadow

    Returns:
        Dictionary of Container properties
    """
    colors = get_panel_colors(is_dark)

    if selected:
        return {
            "bgcolor": colors['card_selected_bg'],
            "border": ft.border.all(2, colors['card_selected_border']),
            "border_radius": Radius.CARD,
            "padding": Spacing.CARD_PADDING,
            "shadow": Shadows.CARD_HOVER.to_flet_shadow(is_dark) if elevated else None,
        }
    else:
        return {
            "bgcolor": colors['card_bg'],
            "border": ft.border.all(1, colors['border']),
            "border_radius": Radius.CARD,
            "padding": Spacing.CARD_PADDING,
            "shadow": Shadows.CARD.to_flet_shadow(is_dark) if elevated else None,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Themes
    'get_light_theme',
    'get_dark_theme',
    'LIGHT_THEME',
    'DARK_THEME',

    # Color getters
    'get_panel_colors',
    'get_alert_colors',

    # Style factories
    'get_button_style',
    'get_text_field_style',
    'get_card_style',

    # Re-exports from tokens
    'Colors',
    'Typography',
    'Spacing',
    'Radius',
    'Shadows',
    'Motion',
]
