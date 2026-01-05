"""Override Dialog - Capture reason for overriding clinical warnings."""

import flet as ft
from typing import Optional, Callable


class OverrideDialog(ft.AlertDialog):
    """Dialog for documenting override reasons.

    Features:
    - Required reason input
    - Predefined common reasons dropdown
    - Acknowledgment checkbox
    - Returns override reason for audit logging
    """

    # Common override reasons
    COMMON_REASONS = [
        "Patient-specific clinical decision",
        "Benefit outweighs risk",
        "Previous tolerance documented",
        "Alternative therapy contraindicated",
        "Consulted specialist",
        "Patient preference after counseling",
        "Emergency situation",
        "Other (specify below)",
    ]

    def __init__(
        self,
        alert_title: str,
        on_override: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        """Initialize override dialog.

        Args:
            alert_title: Title of the alert being overridden
            on_override: Callback with override reason
            on_cancel: Callback when user cancels
            is_dark: Whether dark mode is active
        """
        self.alert_title = alert_title
        self.on_override_callback = on_override
        self.on_cancel_callback = on_cancel
        self.is_dark = is_dark

        # UI components
        self.reason_dropdown: Optional[ft.Dropdown] = None
        self.reason_text: Optional[ft.TextField] = None
        self.acknowledge_checkbox: Optional[ft.Checkbox] = None
        self.confirm_button: Optional[ft.ElevatedButton] = None
        self.error_text: Optional[ft.Text] = None

        super().__init__(
            modal=True,
            title=self._build_title(),
            content=self._build_content(),
            actions=self._build_actions(),
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _build_title(self) -> ft.Container:
        """Build dialog title."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.WARNING,
                    color=ft.Colors.ORANGE_700,
                    size=24,
                ),
                ft.Text(
                    "Override Warning",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
                ),
            ], spacing=10),
        )

    def _build_content(self) -> ft.Container:
        """Build dialog content."""
        # Alert being overridden
        alert_info = ft.Container(
            content=ft.Column([
                ft.Text(
                    "You are overriding:",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
                ft.Text(
                    self.alert_title,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ORANGE_700,
                ),
            ], spacing=5),
            padding=10,
            bgcolor="#3D2E14" if self.is_dark else "#FFF3E0",
            border_radius=8,
            border=ft.border.all(1, ft.Colors.ORANGE_700),
        )

        # Reason dropdown
        self.reason_dropdown = ft.Dropdown(
            label="Select Common Reason",
            options=[ft.dropdown.Option(r) for r in self.COMMON_REASONS],
            border_color=ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_400,
            focused_border_color=ft.Colors.ORANGE_600,
            on_change=self._on_reason_changed,
            width=500,
        )

        # Additional reason text
        self.reason_text = ft.TextField(
            label="Additional Details (Required)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_400,
            focused_border_color=ft.Colors.ORANGE_600,
            hint_text="Provide detailed clinical reasoning for this override...",
            on_change=self._validate_input,
            width=500,
        )

        # Acknowledgment checkbox
        self.acknowledge_checkbox = ft.Checkbox(
            label="I acknowledge full clinical responsibility for this override",
            value=False,
            on_change=self._validate_input,
        )

        # Error message
        self.error_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.RED_700,
            visible=False,
        )

        return ft.Container(
            content=ft.Column([
                alert_info,
                ft.Container(height=15),
                ft.Text(
                    "⚠️ This override will be logged in the audit trail",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True,
                ),
                ft.Container(height=10),
                self.reason_dropdown,
                ft.Container(height=10),
                self.reason_text,
                ft.Container(height=10),
                self.acknowledge_checkbox,
                ft.Container(height=5),
                self.error_text,
            ], spacing=0),
            width=500,
            padding=10,
        )

    def _build_actions(self) -> list:
        """Build dialog action buttons."""
        self.confirm_button = ft.ElevatedButton(
            text="Confirm Override",
            icon=ft.Icons.CHECK_CIRCLE,
            bgcolor=ft.Colors.ORANGE_700,
            color=ft.Colors.WHITE,
            on_click=self._handle_override,
            disabled=True,  # Initially disabled
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._handle_cancel,
        )

        return [cancel_button, self.confirm_button]

    def _on_reason_changed(self, e):
        """Handle reason dropdown change."""
        # If "Other" is selected, focus on text field
        if self.reason_dropdown.value == "Other (specify below)":
            if self.reason_text and self.reason_text.page:
                self.reason_text.focus()

        self._validate_input(e)

    def _validate_input(self, e):
        """Validate user input and enable/disable confirm button."""
        is_valid = True
        error_messages = []

        # Check if dropdown is selected
        if not self.reason_dropdown.value:
            is_valid = False
            error_messages.append("Please select a reason")

        # Check if detailed text is provided
        if not self.reason_text.value or len(self.reason_text.value.strip()) < 10:
            is_valid = False
            error_messages.append("Please provide detailed reasoning (minimum 10 characters)")

        # Check if acknowledged
        if not self.acknowledge_checkbox.value:
            is_valid = False
            error_messages.append("Please acknowledge responsibility")

        # Update UI
        if self.confirm_button:
            self.confirm_button.disabled = not is_valid

        if self.error_text:
            if error_messages and not is_valid:
                self.error_text.value = " • " + "\n • ".join(error_messages)
                self.error_text.visible = True
            else:
                self.error_text.visible = False

        # Update dialog
        if self.page:
            self.update()

    def _handle_override(self, e):
        """Handle override confirmation."""
        # Compile full reason
        full_reason = f"{self.reason_dropdown.value}\n\nDetails: {self.reason_text.value.strip()}"

        # Close dialog
        if self.page:
            self.open = False
            self.page.update()

        # Call callback
        if self.on_override_callback:
            self.on_override_callback(full_reason)

    def _handle_cancel(self, e):
        """Handle cancel."""
        # Close dialog
        if self.page:
            self.open = False
            self.page.update()

        # Call callback
        if self.on_cancel_callback:
            self.on_cancel_callback()

    def show(self, page: ft.Page):
        """Show the dialog.

        Args:
            page: Flet page to show dialog on
        """
        page.open(self)


def show_override_dialog(
    page: ft.Page,
    alert_title: str,
    on_override: Callable[[str], None],
    on_cancel: Optional[Callable] = None,
    is_dark: bool = False,
) -> OverrideDialog:
    """Convenience function to show override dialog.

    Args:
        page: Flet page
        alert_title: Title of alert being overridden
        on_override: Callback with override reason
        on_cancel: Callback when cancelled
        is_dark: Whether dark mode is active

    Returns:
        OverrideDialog instance
    """
    dialog = OverrideDialog(
        alert_title=alert_title,
        on_override=on_override,
        on_cancel=on_cancel,
        is_dark=is_dark,
    )

    dialog.show(page)
    return dialog
