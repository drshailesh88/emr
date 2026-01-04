"""Theme definitions for light and dark modes."""

import flet as ft


# Light Theme
LIGHT_THEME = ft.Theme(
    color_scheme=ft.ColorScheme(
        # Primary colors
        primary=ft.Colors.BLUE_700,
        on_primary=ft.Colors.WHITE,
        primary_container=ft.Colors.BLUE_100,
        on_primary_container=ft.Colors.BLUE_900,

        # Secondary colors
        secondary=ft.Colors.BLUE_600,
        on_secondary=ft.Colors.WHITE,
        secondary_container=ft.Colors.BLUE_50,
        on_secondary_container=ft.Colors.BLUE_800,

        # Background colors
        background=ft.Colors.WHITE,
        on_background=ft.Colors.GREY_900,

        # Surface colors
        surface=ft.Colors.GREY_100,
        on_surface=ft.Colors.GREY_900,
        surface_variant=ft.Colors.GREY_200,
        on_surface_variant=ft.Colors.GREY_700,

        # Utility colors
        error=ft.Colors.RED_700,
        on_error=ft.Colors.WHITE,
        error_container=ft.Colors.RED_100,
        on_error_container=ft.Colors.RED_900,

        outline=ft.Colors.GREY_300,
        shadow=ft.Colors.BLACK,

        # Inverse colors
        inverse_surface=ft.Colors.GREY_800,
        on_inverse_surface=ft.Colors.GREY_100,
        inverse_primary=ft.Colors.BLUE_200,
    ),
    use_material3=True,
)


# Dark Theme
DARK_THEME = ft.Theme(
    color_scheme=ft.ColorScheme(
        # Primary colors - lighter shades for dark mode
        primary=ft.Colors.BLUE_200,
        on_primary=ft.Colors.BLACK,
        primary_container=ft.Colors.BLUE_700,
        on_primary_container=ft.Colors.BLUE_100,

        # Secondary colors
        secondary=ft.Colors.BLUE_300,
        on_secondary=ft.Colors.BLACK,
        secondary_container=ft.Colors.BLUE_800,
        on_secondary_container=ft.Colors.BLUE_100,

        # Background colors - #121212 for dark, not pure black
        background="#121212",
        on_background=ft.Colors.GREY_100,

        # Surface colors
        surface="#1E1E1E",
        on_surface=ft.Colors.GREY_200,
        surface_variant="#2D2D2D",
        on_surface_variant=ft.Colors.GREY_400,

        # Utility colors - adjusted for dark mode
        error=ft.Colors.RED_300,
        on_error=ft.Colors.BLACK,
        error_container=ft.Colors.RED_900,
        on_error_container=ft.Colors.RED_200,

        outline=ft.Colors.GREY_700,
        shadow=ft.Colors.BLACK,

        # Inverse colors
        inverse_surface=ft.Colors.GREY_100,
        on_inverse_surface=ft.Colors.GREY_900,
        inverse_primary=ft.Colors.BLUE_700,
    ),
    use_material3=True,
)


# Custom colors for specific UI elements (theme-aware)
def get_panel_colors(is_dark: bool) -> dict:
    """Get panel-specific colors based on theme.

    Args:
        is_dark: Whether dark mode is active

    Returns:
        Dictionary of color definitions
    """
    if is_dark:
        return {
            'patient_panel_bg': "#1E1E1E",
            'patient_panel_border': ft.Colors.GREY_800,
            'central_panel_bg': "#121212",
            'agent_panel_bg': "#1A2332",  # Slight blue tint
            'header_bg': "#1E1E1E",
            'header_border': ft.Colors.GREY_800,
            'card_bg': "#2D2D2D",
            'card_selected_bg': "#1565C0",
            'status_text': ft.Colors.GREY_400,
            'status_error': ft.Colors.RED_300,
            'divider': ft.Colors.GREY_800,
        }
    else:
        return {
            'patient_panel_bg': ft.Colors.GREY_50,
            'patient_panel_border': ft.Colors.GREY_300,
            'central_panel_bg': ft.Colors.WHITE,
            'agent_panel_bg': ft.Colors.BLUE_50,
            'header_bg': ft.Colors.WHITE,
            'header_border': ft.Colors.GREY_300,
            'card_bg': ft.Colors.WHITE,
            'card_selected_bg': ft.Colors.BLUE_100,
            'status_text': ft.Colors.GREY_600,
            'status_error': ft.Colors.RED_600,
            'divider': ft.Colors.GREY_300,
        }


# Alert colors (accessible in both modes)
def get_alert_colors(is_dark: bool) -> dict:
    """Get alert colors based on theme.

    Args:
        is_dark: Whether dark mode is active

    Returns:
        Dictionary of alert color definitions
    """
    if is_dark:
        return {
            'success': ft.Colors.GREEN_300,
            'warning': ft.Colors.ORANGE_300,
            'error': ft.Colors.RED_300,
            'info': ft.Colors.BLUE_300,
        }
    else:
        return {
            'success': ft.Colors.GREEN_700,
            'warning': ft.Colors.ORANGE_700,
            'error': ft.Colors.RED_700,
            'info': ft.Colors.BLUE_700,
        }
