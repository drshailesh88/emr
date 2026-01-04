"""Premium Dialog Components.

Styled dialog boxes with consistent design tokens.
"""

import flet as ft
from typing import Optional, Callable, List

from ..tokens import Colors, Typography, Spacing, Radius, Motion, Shadows


class PremiumDialog:
    """Base premium dialog with consistent styling."""

    @staticmethod
    def create(
        title: str,
        content: ft.Control,
        actions: List[ft.Control],
        icon: Optional[ft.Icons] = None,
        icon_color: Optional[str] = None,
        width: int = 480,
        is_dark: bool = False,
    ) -> ft.AlertDialog:
        """Create a premium styled dialog.

        Args:
            title: Dialog title text
            content: Main content control
            actions: List of action buttons
            icon: Optional icon for title
            icon_color: Color for title icon
            width: Dialog width
            is_dark: Dark mode flag

        Returns:
            Configured AlertDialog
        """
        # Title row with optional icon
        title_content = ft.Row([
            ft.Icon(
                icon,
                color=icon_color or Colors.PRIMARY_500,
                size=24
            ) if icon else ft.Container(),
            ft.Text(
                title,
                size=Typography.TITLE_MEDIUM.size,
                weight=ft.FontWeight.W_600,
                color=Colors.NEUTRAL_900 if not is_dark else Colors.NEUTRAL_100,
            ),
        ], spacing=Spacing.SM) if icon else ft.Text(
            title,
            size=Typography.TITLE_MEDIUM.size,
            weight=ft.FontWeight.W_600,
            color=Colors.NEUTRAL_900 if not is_dark else Colors.NEUTRAL_100,
        )

        return ft.AlertDialog(
            modal=True,
            title=title_content,
            title_padding=ft.padding.all(Spacing.LG),
            content=ft.Container(
                content=content,
                width=width,
                padding=ft.padding.symmetric(horizontal=Spacing.LG),
            ),
            content_padding=ft.padding.only(bottom=Spacing.MD),
            actions=actions,
            actions_padding=ft.padding.all(Spacing.MD),
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
            bgcolor=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
        )


class ConfirmDialog:
    """Premium confirmation dialog."""

    @staticmethod
    def show(
        page: ft.Page,
        title: str,
        message: str,
        on_confirm: Callable,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        is_destructive: bool = False,
        is_dark: bool = False,
    ):
        """Show a premium confirmation dialog.

        Args:
            page: Flet page
            title: Dialog title
            message: Confirmation message
            on_confirm: Callback on confirm
            confirm_text: Confirm button text
            cancel_text: Cancel button text
            is_destructive: Use destructive (red) styling
            is_dark: Dark mode flag
        """
        def close_dialog(e):
            dialog.open = False
            page.update()

        def confirm_and_close(e):
            dialog.open = False
            page.update()
            on_confirm()

        # Icon based on type
        icon = ft.Icons.WARNING_ROUNDED if is_destructive else ft.Icons.HELP_OUTLINE
        icon_color = Colors.ERROR_MAIN if is_destructive else Colors.PRIMARY_500

        # Message content
        content = ft.Text(
            message,
            size=Typography.BODY_MEDIUM.size,
            color=Colors.NEUTRAL_700 if not is_dark else Colors.NEUTRAL_300,
        )

        # Action buttons
        cancel_btn = ft.TextButton(
            cancel_text,
            on_click=close_dialog,
            style=ft.ButtonStyle(
                color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
                overlay_color=Colors.HOVER_OVERLAY,
                padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            ),
        )

        confirm_btn = ft.ElevatedButton(
            confirm_text,
            on_click=confirm_and_close,
            style=ft.ButtonStyle(
                bgcolor=Colors.ERROR_MAIN if is_destructive else Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.SM),
                animation_duration=Motion.FAST,
            ),
        )

        dialog = PremiumDialog.create(
            title=title,
            content=content,
            actions=[cancel_btn, confirm_btn],
            icon=icon,
            icon_color=icon_color,
            width=420,
            is_dark=is_dark,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()


class FormDialog:
    """Premium form dialog with fields."""

    @staticmethod
    def create_field(
        label: str,
        value: str = "",
        hint_text: str = "",
        multiline: bool = False,
        min_lines: int = 1,
        max_lines: int = 1,
        width: Optional[int] = None,
        required: bool = False,
        read_only: bool = False,
        is_dark: bool = False,
        **kwargs
    ) -> ft.TextField:
        """Create a premium styled form field.

        Args:
            label: Field label (adds * if required)
            value: Initial value
            hint_text: Placeholder hint
            multiline: Enable multiline
            min_lines: Minimum lines for multiline
            max_lines: Maximum lines for multiline
            width: Optional fixed width
            required: Mark as required
            read_only: Make read-only
            is_dark: Dark mode flag

        Returns:
            Configured TextField
        """
        display_label = f"{label} *" if required else label

        return ft.TextField(
            label=display_label,
            value=value,
            hint_text=hint_text,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            width=width,
            read_only=read_only,
            text_size=Typography.BODY_MEDIUM.size,
            label_style=ft.TextStyle(
                size=Typography.LABEL_MEDIUM.size,
                color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
            ),
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300 if not is_dark else Colors.NEUTRAL_600,
            focused_border_color=Colors.PRIMARY_500,
            focused_border_width=2,
            cursor_color=Colors.PRIMARY_500,
            content_padding=ft.padding.all(Spacing.INPUT_PADDING),
            **kwargs
        )

    @staticmethod
    def create_error_text(is_dark: bool = False) -> ft.Text:
        """Create an error text display."""
        return ft.Text(
            "",
            size=Typography.BODY_SMALL.size,
            color=Colors.ERROR_MAIN,
        )

    @staticmethod
    def create_actions(
        on_save: Callable,
        on_cancel: Callable,
        save_text: str = "Save",
        cancel_text: str = "Cancel",
        is_dark: bool = False,
    ) -> List[ft.Control]:
        """Create standard form action buttons.

        Args:
            on_save: Save callback
            on_cancel: Cancel callback
            save_text: Save button text
            cancel_text: Cancel button text
            is_dark: Dark mode flag

        Returns:
            List of action buttons
        """
        cancel_btn = ft.TextButton(
            cancel_text,
            on_click=on_cancel,
            style=ft.ButtonStyle(
                color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
                padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            ),
        )

        save_btn = ft.ElevatedButton(
            save_text,
            on_click=on_save,
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.SM),
                animation_duration=Motion.FAST,
            ),
        )

        return [cancel_btn, save_btn]


class SuccessDialog:
    """Premium success feedback dialog."""

    @staticmethod
    def show(
        page: ft.Page,
        title: str = "Success",
        message: str = "Operation completed successfully.",
        on_close: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        """Show a success dialog.

        Args:
            page: Flet page
            title: Dialog title
            message: Success message
            on_close: Optional close callback
            is_dark: Dark mode flag
        """
        def close_dialog(e):
            dialog.open = False
            page.update()
            if on_close:
                on_close()

        content = ft.Column([
            ft.Container(
                content=ft.Icon(
                    ft.Icons.CHECK_CIRCLE_ROUNDED,
                    color=Colors.SUCCESS_MAIN,
                    size=48,
                ),
                alignment=ft.alignment.center,
            ),
            ft.Text(
                message,
                size=Typography.BODY_MEDIUM.size,
                color=Colors.NEUTRAL_700 if not is_dark else Colors.NEUTRAL_300,
                text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=Spacing.MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        ok_btn = ft.ElevatedButton(
            "OK",
            on_click=close_dialog,
            style=ft.ButtonStyle(
                bgcolor=Colors.SUCCESS_MAIN,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                padding=ft.padding.symmetric(horizontal=Spacing.XL, vertical=Spacing.SM),
            ),
        )

        dialog = PremiumDialog.create(
            title=title,
            content=content,
            actions=[ok_btn],
            icon=None,
            width=360,
            is_dark=is_dark,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()


class InfoDialog:
    """Premium information dialog."""

    @staticmethod
    def show(
        page: ft.Page,
        title: str,
        message: str,
        on_close: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        """Show an info dialog.

        Args:
            page: Flet page
            title: Dialog title
            message: Info message
            on_close: Optional close callback
            is_dark: Dark mode flag
        """
        def close_dialog(e):
            dialog.open = False
            page.update()
            if on_close:
                on_close()

        content = ft.Text(
            message,
            size=Typography.BODY_MEDIUM.size,
            color=Colors.NEUTRAL_700 if not is_dark else Colors.NEUTRAL_300,
        )

        ok_btn = ft.ElevatedButton(
            "OK",
            on_click=close_dialog,
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                padding=ft.padding.symmetric(horizontal=Spacing.XL, vertical=Spacing.SM),
            ),
        )

        dialog = PremiumDialog.create(
            title=title,
            content=content,
            actions=[ok_btn],
            icon=ft.Icons.INFO_OUTLINE,
            icon_color=Colors.INFO_MAIN,
            width=420,
            is_dark=is_dark,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()
