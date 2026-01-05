"""WhatsApp setup and configuration UI."""

import flet as ft
from typing import Callable, Optional
import threading
from ...services.whatsapp_settings import WhatsAppSettingsService, WhatsAppCredentials


class WhatsAppSetupPanel:
    """WhatsApp Business API configuration panel."""

    def __init__(
        self,
        page: ft.Page,
        settings_service: WhatsAppSettingsService,
        on_settings_changed: Optional[Callable] = None
    ):
        """Initialize WhatsApp setup panel.

        Args:
            page: Flet page
            settings_service: WhatsApp settings service
            on_settings_changed: Callback when settings are changed
        """
        self.page = page
        self.settings_service = settings_service
        self.on_settings_changed = on_settings_changed

        # Load current credentials
        self.credentials = settings_service.get_credentials()

        # UI components
        self.phone_number_field: Optional[ft.TextField] = None
        self.access_token_field: Optional[ft.TextField] = None
        self.business_account_field: Optional[ft.TextField] = None
        self.webhook_token_field: Optional[ft.TextField] = None
        self.enabled_switch: Optional[ft.Switch] = None
        self.mock_mode_switch: Optional[ft.Switch] = None
        self.status_indicator: Optional[ft.Container] = None
        self.status_text: Optional[ft.Text] = None
        self.test_btn: Optional[ft.ElevatedButton] = None
        self.save_btn: Optional[ft.ElevatedButton] = None
        self.clear_btn: Optional[ft.TextButton] = None
        self.container: Optional[ft.Container] = None

    def build(self) -> ft.Container:
        """Build the setup panel UI.

        Returns:
            Container with WhatsApp setup UI
        """
        # Status indicator
        status_color = ft.Colors.GREEN_400 if self.credentials.is_configured() and self.credentials.enabled else ft.Colors.GREY_400
        status_text = "Connected" if self.credentials.is_configured() and self.credentials.enabled else "Not Configured"

        if self.credentials.mock_mode and self.credentials.enabled:
            status_color = ft.Colors.AMBER_400
            status_text = "Mock Mode"

        self.status_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CIRCLE,
                    color=status_color,
                    size=12
                ),
                ft.Text(
                    status_text,
                    size=12,
                    weight=ft.FontWeight.W_500
                )
            ], spacing=5),
            padding=5,
            border_radius=5,
            bgcolor=ft.Colors.with_opacity(0.1, status_color)
        )

        # Configuration fields
        self.phone_number_field = ft.TextField(
            label="Phone Number ID",
            value=self.credentials.phone_number_id,
            hint_text="Your WhatsApp Business phone number ID",
            width=400,
            password=False,
            can_reveal_password=False,
        )

        self.access_token_field = ft.TextField(
            label="Access Token",
            value=self.credentials.access_token,
            hint_text="Your WhatsApp Business API access token",
            width=400,
            password=True,
            can_reveal_password=True,
        )

        self.business_account_field = ft.TextField(
            label="Business Account ID (Optional)",
            value=self.credentials.business_account_id,
            hint_text="Your WhatsApp Business account ID",
            width=400,
        )

        self.webhook_token_field = ft.TextField(
            label="Webhook Verify Token (Optional)",
            value=self.credentials.webhook_verify_token,
            hint_text="Token for webhook verification",
            width=400,
            password=True,
            can_reveal_password=True,
        )

        # Enable/Disable switch
        self.enabled_switch = ft.Switch(
            label="Enable WhatsApp Features",
            value=self.credentials.enabled,
            on_change=self._on_enabled_change
        )

        # Mock mode switch
        self.mock_mode_switch = ft.Switch(
            label="Mock Mode (Log messages instead of sending)",
            value=self.credentials.mock_mode,
            on_change=self._on_mock_mode_change
        )

        # Test connection button
        self.test_btn = ft.ElevatedButton(
            "Test Connection",
            icon=ft.Icons.CLOUD_SYNC,
            on_click=self._on_test_connection,
            disabled=not self.credentials.is_configured()
        )

        # Save button
        self.save_btn = ft.ElevatedButton(
            "Save Settings",
            icon=ft.Icons.SAVE,
            on_click=self._on_save,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
        )

        # Clear credentials button
        self.clear_btn = ft.TextButton(
            "Clear All Credentials",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._on_clear,
            style=ft.ButtonStyle(color=ft.Colors.RED_700)
        )

        # Status text
        self.status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False
        )

        # Help text
        help_text = ft.Container(
            content=ft.Column([
                ft.Text(
                    "How to get WhatsApp Business API credentials:",
                    size=12,
                    weight=ft.FontWeight.W_500
                ),
                ft.Text(
                    "1. Go to Meta Business Suite (business.facebook.com)",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
                ft.Text(
                    "2. Navigate to WhatsApp > API Setup",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
                ft.Text(
                    "3. Copy your Phone Number ID and Access Token",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
                ft.Text(
                    "4. Paste them here and save",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
                ft.Divider(height=1),
                ft.Text(
                    "Note: Keep your access token secure. Never share it publicly.",
                    size=11,
                    color=ft.Colors.RED_700,
                    italic=True
                ),
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=5,
            bgcolor=ft.Colors.BLUE_50,
        )

        # Mock mode info
        mock_info = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Mock Mode Information:",
                    size=12,
                    weight=ft.FontWeight.W_500
                ),
                ft.Text(
                    "When mock mode is enabled, messages will be logged to the console instead of being sent via WhatsApp. "
                    "This is useful for testing and demos without API credentials.",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.AMBER_200),
            border_radius=5,
            bgcolor=ft.Colors.AMBER_50,
        )

        # Main content
        content = ft.Column([
            ft.Row([
                ft.Text(
                    "WhatsApp Business API Configuration",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                self.status_indicator
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Divider(height=20),

            help_text,

            ft.Container(height=20),

            self.phone_number_field,
            self.access_token_field,
            self.business_account_field,
            self.webhook_token_field,

            ft.Container(height=10),

            self.enabled_switch,
            self.mock_mode_switch,

            ft.Container(height=10),

            mock_info,

            ft.Container(height=20),

            ft.Row([
                self.test_btn,
                self.save_btn,
                self.clear_btn,
            ], spacing=10),

            self.status_text,

        ], spacing=15, scroll=ft.ScrollMode.AUTO)

        self.container = ft.Container(
            content=content,
            padding=20,
            expand=True,
        )

        return self.container

    def _on_enabled_change(self, e):
        """Handle enable/disable switch change."""
        # Just update UI, actual save happens when user clicks Save
        pass

    def _on_mock_mode_change(self, e):
        """Handle mock mode switch change."""
        # Just update UI, actual save happens when user clicks Save
        pass

    def _on_test_connection(self, e):
        """Handle test connection button click."""
        def test():
            # Update UI to show testing
            self.test_btn.disabled = True
            self.status_text.value = "Testing connection..."
            self.status_text.color = ft.Colors.BLUE_700
            self.status_text.visible = True
            self.page.update()

            # Test connection
            success, message = self.settings_service.test_connection()

            # Update UI with result
            self.status_text.value = message
            self.status_text.color = ft.Colors.GREEN_700 if success else ft.Colors.RED_700
            self.test_btn.disabled = False
            self.page.update()

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=test, daemon=True)
        thread.start()

    def _on_save(self, e):
        """Handle save button click."""
        # Get values from fields
        phone_number_id = self.phone_number_field.value.strip()
        access_token = self.access_token_field.value.strip()
        business_account_id = self.business_account_field.value.strip()
        webhook_token = self.webhook_token_field.value.strip()
        enabled = self.enabled_switch.value
        mock_mode = self.mock_mode_switch.value

        # Create credentials object
        credentials = WhatsAppCredentials(
            phone_number_id=phone_number_id,
            access_token=access_token,
            business_account_id=business_account_id,
            webhook_verify_token=webhook_token,
            enabled=enabled,
            mock_mode=mock_mode
        )

        # Save
        success = self.settings_service.save_credentials(credentials)

        if success:
            self.credentials = credentials
            self.status_text.value = "Settings saved successfully!"
            self.status_text.color = ft.Colors.GREEN_700
            self.status_text.visible = True

            # Update status indicator
            self._update_status_indicator()

            # Enable/disable test button
            self.test_btn.disabled = not credentials.is_configured()

            # Call callback
            if self.on_settings_changed:
                self.on_settings_changed()

            # Show snackbar
            self.page.open(ft.SnackBar(
                content=ft.Text("WhatsApp settings saved successfully!"),
                bgcolor=ft.Colors.GREEN_700
            ))
        else:
            self.status_text.value = "Error saving settings"
            self.status_text.color = ft.Colors.RED_700
            self.status_text.visible = True

            self.page.open(ft.SnackBar(
                content=ft.Text("Error saving WhatsApp settings"),
                bgcolor=ft.Colors.RED_700
            ))

        self.page.update()

    def _on_clear(self, e):
        """Handle clear credentials button click."""
        def confirm_clear(confirmed: bool):
            if confirmed:
                # Clear credentials
                success = self.settings_service.clear_credentials()

                if success:
                    # Update UI
                    self.phone_number_field.value = ""
                    self.access_token_field.value = ""
                    self.business_account_field.value = ""
                    self.webhook_token_field.value = ""
                    self.enabled_switch.value = False
                    self.mock_mode_switch.value = True
                    self.credentials = self.settings_service.get_credentials()
                    self.test_btn.disabled = True

                    self.status_text.value = "Credentials cleared"
                    self.status_text.color = ft.Colors.GREY_600
                    self.status_text.visible = True

                    self._update_status_indicator()

                    # Call callback
                    if self.on_settings_changed:
                        self.on_settings_changed()

                    self.page.update()

        # Show confirmation dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Clear"),
            content=ft.Text("Are you sure you want to clear all WhatsApp credentials?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm_dialog()),
                ft.ElevatedButton(
                    "Clear",
                    on_click=lambda e: (confirm_clear(True), self._close_confirm_dialog()),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _close_confirm_dialog(self):
        """Close confirmation dialog."""
        for overlay in self.page.overlay:
            if isinstance(overlay, ft.AlertDialog):
                overlay.open = False
        self.page.update()

    def _update_status_indicator(self):
        """Update status indicator based on current credentials."""
        if self.credentials.is_configured() and self.credentials.enabled:
            if self.credentials.mock_mode:
                color = ft.Colors.AMBER_400
                text = "Mock Mode"
            else:
                color = ft.Colors.GREEN_400
                text = "Connected"
        else:
            color = ft.Colors.GREY_400
            text = "Not Configured"

        self.status_indicator.content = ft.Row([
            ft.Icon(ft.Icons.CIRCLE, color=color, size=12),
            ft.Text(text, size=12, weight=ft.FontWeight.W_500)
        ], spacing=5)
        self.status_indicator.bgcolor = ft.Colors.with_opacity(0.1, color)

    def refresh(self):
        """Refresh the panel with latest settings."""
        self.credentials = self.settings_service.get_credentials()

        if self.phone_number_field:
            self.phone_number_field.value = self.credentials.phone_number_id
            self.access_token_field.value = self.credentials.access_token
            self.business_account_field.value = self.credentials.business_account_id
            self.webhook_token_field.value = self.credentials.webhook_verify_token
            self.enabled_switch.value = self.credentials.enabled
            self.mock_mode_switch.value = self.credentials.mock_mode
            self.test_btn.disabled = not self.credentials.is_configured()
            self._update_status_indicator()
            self.page.update()
