"""
Premium Button Components for DocAssist EMR

Usage:
    from src.ui.widgets import PrimaryButton, SecondaryButton

    btn = PrimaryButton(
        text="Save Visit",
        icon=ft.Icons.SAVE,
        on_click=handle_save,
    )
"""

import flet as ft
from typing import Optional, Callable, Any

from ..tokens import Colors, Typography, Spacing, Radius, Motion


class PrimaryButton(ft.ElevatedButton):
    """
    Premium primary action button.

    Use for main actions like Save, Submit, Generate.
    Solid background with prominent styling.
    """

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        icon: Optional[str] = None,
        disabled: bool = False,
        loading: bool = False,
        tooltip: Optional[str] = None,
        width: Optional[int] = None,
        expand: bool = False,
        **kwargs
    ):
        # Build content with optional loading state
        if loading:
            content = ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                    ft.Text(text, size=Typography.LABEL_LARGE.size),
                ],
                spacing=Spacing.XS,
                alignment=ft.MainAxisAlignment.CENTER,
            )
            super().__init__(
                content=content,
                on_click=on_click,
                disabled=True,
                tooltip=tooltip,
                width=width,
                expand=expand,
                style=self._get_style(disabled=True),
                **kwargs
            )
        else:
            super().__init__(
                text=text,
                icon=icon,
                on_click=on_click,
                disabled=disabled,
                tooltip=tooltip,
                width=width,
                expand=expand,
                style=self._get_style(disabled),
                **kwargs
            )

    @staticmethod
    def _get_style(disabled: bool = False) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            color=Colors.NEUTRAL_0,
            bgcolor={
                ft.ControlState.DEFAULT: Colors.PRIMARY_500,
                ft.ControlState.HOVERED: Colors.PRIMARY_600,
                ft.ControlState.PRESSED: Colors.PRIMARY_700,
                ft.ControlState.DISABLED: Colors.NEUTRAL_300,
            },
            padding=ft.padding.symmetric(
                horizontal=Spacing.LG,
                vertical=Spacing.SM,
            ),
            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 4,
                ft.ControlState.PRESSED: 1,
            },
            animation_duration=Motion.FAST,
        )


class SecondaryButton(ft.OutlinedButton):
    """
    Premium secondary action button.

    Use for supporting actions like Cancel, Edit, View.
    Outlined style with transparent background.
    """

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        icon: Optional[str] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        width: Optional[int] = None,
        expand: bool = False,
        **kwargs
    ):
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            disabled=disabled,
            tooltip=tooltip,
            width=width,
            expand=expand,
            style=self._get_style(disabled),
            **kwargs
        )

    @staticmethod
    def _get_style(disabled: bool = False) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: Colors.PRIMARY_500,
                ft.ControlState.HOVERED: Colors.PRIMARY_600,
                ft.ControlState.PRESSED: Colors.PRIMARY_700,
                ft.ControlState.DISABLED: Colors.NEUTRAL_400,
            },
            bgcolor=ft.Colors.TRANSPARENT,
            overlay_color=Colors.SELECTED_OVERLAY,
            padding=ft.padding.symmetric(
                horizontal=Spacing.LG,
                vertical=Spacing.SM,
            ),
            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1.5, Colors.PRIMARY_500),
                ft.ControlState.HOVERED: ft.BorderSide(1.5, Colors.PRIMARY_600),
                ft.ControlState.PRESSED: ft.BorderSide(1.5, Colors.PRIMARY_700),
                ft.ControlState.DISABLED: ft.BorderSide(1.5, Colors.NEUTRAL_300),
            },
            animation_duration=Motion.FAST,
        )


class DangerButton(ft.ElevatedButton):
    """
    Premium danger/destructive action button.

    Use for delete, remove, or other destructive actions.
    Red background to indicate danger.
    """

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        icon: Optional[str] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        width: Optional[int] = None,
        expand: bool = False,
        **kwargs
    ):
        super().__init__(
            text=text,
            icon=icon if icon else ft.Icons.WARNING_AMBER_ROUNDED,
            on_click=on_click,
            disabled=disabled,
            tooltip=tooltip,
            width=width,
            expand=expand,
            style=self._get_style(disabled),
            **kwargs
        )

    @staticmethod
    def _get_style(disabled: bool = False) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            color=Colors.NEUTRAL_0,
            bgcolor={
                ft.ControlState.DEFAULT: Colors.ERROR_MAIN,
                ft.ControlState.HOVERED: Colors.ERROR_DARK,
                ft.ControlState.PRESSED: "#B71C1C",  # Darker red
                ft.ControlState.DISABLED: Colors.NEUTRAL_300,
            },
            padding=ft.padding.symmetric(
                horizontal=Spacing.LG,
                vertical=Spacing.SM,
            ),
            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 4,
                ft.ControlState.PRESSED: 1,
            },
            animation_duration=Motion.FAST,
        )


class GhostButton(ft.TextButton):
    """
    Premium ghost/text button.

    Use for tertiary actions or when you want minimal visual weight.
    No background, just text with hover effect.
    """

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        icon: Optional[str] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        width: Optional[int] = None,
        expand: bool = False,
        color: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            disabled=disabled,
            tooltip=tooltip,
            width=width,
            expand=expand,
            style=self._get_style(disabled, color),
            **kwargs
        )

    @staticmethod
    def _get_style(disabled: bool = False, color: Optional[str] = None) -> ft.ButtonStyle:
        text_color = color or Colors.NEUTRAL_700
        return ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: text_color,
                ft.ControlState.HOVERED: Colors.PRIMARY_500,
                ft.ControlState.PRESSED: Colors.PRIMARY_700,
                ft.ControlState.DISABLED: Colors.NEUTRAL_400,
            },
            bgcolor=ft.Colors.TRANSPARENT,
            overlay_color=Colors.HOVER_OVERLAY,
            padding=ft.padding.symmetric(
                horizontal=Spacing.MD,
                vertical=Spacing.XS,
            ),
            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            animation_duration=Motion.FAST,
        )


class IconActionButton(ft.IconButton):
    """
    Premium icon-only action button.

    Use for compact actions in toolbars or cards.
    Subtle hover effect with optional tooltip.
    """

    def __init__(
        self,
        icon: str,
        on_click: Optional[Callable] = None,
        tooltip: Optional[str] = None,
        disabled: bool = False,
        selected: bool = False,
        icon_size: int = 20,
        icon_color: Optional[str] = None,
        bgcolor: Optional[str] = None,
        **kwargs
    ):
        _icon_color = icon_color or Colors.NEUTRAL_600
        if selected:
            _icon_color = Colors.PRIMARY_500
            bgcolor = Colors.PRIMARY_50

        super().__init__(
            icon=icon,
            icon_color=_icon_color,
            icon_size=icon_size,
            on_click=on_click,
            tooltip=tooltip,
            disabled=disabled,
            bgcolor=bgcolor,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                overlay_color=Colors.HOVER_OVERLAY,
                animation_duration=Motion.FAST,
            ),
            **kwargs
        )


# Convenience aliases
SuccessButton = PrimaryButton  # Can be styled differently if needed
