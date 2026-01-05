"""Encryption Key Dialog - Display and manage encryption keys."""

import flet as ft
from typing import Optional, Callable

from ...services.crypto import CryptoService, is_crypto_available


class EncryptionKeyDialog:
    """Dialog for displaying and managing encryption keys."""

    def __init__(
        self,
        page: ft.Page,
        key_type: str = "password",  # "password" or "recovery"
        existing_key: Optional[str] = None,
        on_save: Optional[Callable[[str, str], None]] = None,
    ):
        """Initialize encryption key dialog.

        Args:
            page: Flet page
            key_type: Type of key ("password" or "recovery")
            existing_key: Existing key to display
            on_save: Callback when key is saved (key_type, key_value)
        """
        self.page = page
        self.key_type = key_type
        self.existing_key = existing_key
        self.on_save = on_save

        # UI components
        self.dialog: Optional[ft.AlertDialog] = None
        self.key_saved_checkbox: Optional[ft.Checkbox] = None

        # Build and show dialog
        self._build_dialog()

    def _build_dialog(self):
        """Build the encryption key dialog."""
        if not is_crypto_available():
            self._show_error_dialog("Encryption library not available. Please install pynacl.")
            return

        crypto = CryptoService()

        # Generate or use existing key
        if self.key_type == "recovery":
            if self.existing_key:
                raw_key = self.existing_key
            else:
                raw_key = crypto.generate_recovery_key()

            formatted_key = crypto.format_recovery_key(raw_key)
            key_display = formatted_key

            title = "Recovery Key"
            description = (
                "This 64-character recovery key allows you to decrypt your backups "
                "even if you forget your password. WRITE IT DOWN and store it in a safe place."
            )
            warning = (
                "CRITICAL: If you lose this key AND your password, your data is PERMANENTLY LOST. "
                "There is no way to recover it. Print this key and store it safely."
            )
        else:
            # Password-based
            key_display = self.existing_key or ""
            raw_key = key_display

            title = "Backup Password"
            description = (
                "This password will be used to encrypt your backups before uploading to the cloud. "
                "Choose a strong password that you'll remember."
            )
            warning = (
                "WARNING: If you forget this password, your backups cannot be decrypted. "
                "We recommend using a password manager or writing it down securely."
            )

        # Key display field
        if self.key_type == "recovery":
            self.key_field = ft.TextField(
                label="Recovery Key",
                value=key_display,
                read_only=True,
                multiline=True,
                min_lines=3,
                max_lines=4,
                width=500,
                text_style=ft.TextStyle(
                    font_family="monospace",
                    size=13,
                ),
                border_color=ft.Colors.BLUE_700,
            )
        else:
            self.key_field = ft.TextField(
                label="Password",
                value=key_display,
                password=True,
                can_reveal_password=True,
                width=400,
            )

        # "I have saved my key" checkbox
        self.key_saved_checkbox = ft.Checkbox(
            label="I have written down this key/password and stored it safely",
            value=False,
        )

        # Warning banner
        warning_banner = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.RED_700, size=32),
                    ft.Text(
                        "Data Loss Warning",
                        color=ft.Colors.RED_700,
                        weight=ft.FontWeight.BOLD,
                        size=16,
                    ),
                ], spacing=10),
                ft.Text(
                    warning,
                    size=12,
                    color=ft.Colors.RED_900,
                ),
            ], spacing=8),
            bgcolor=ft.Colors.RED_50,
            padding=15,
            border_radius=8,
            border=ft.border.all(2, ft.Colors.RED_300),
        )

        # Security info
        security_info = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCK, color=ft.Colors.GREEN_700, size=24),
                    ft.Text(
                        "Zero-Knowledge Encryption",
                        color=ft.Colors.GREEN_700,
                        weight=ft.FontWeight.BOLD,
                    ),
                ], spacing=10),
                ft.Text(
                    "Your data is encrypted on your device BEFORE upload. "
                    "The cloud service never sees your unencrypted data or your encryption key.",
                    size=11,
                    color=ft.Colors.GREEN_900,
                ),
            ], spacing=5),
            bgcolor=ft.Colors.GREEN_50,
            padding=15,
            border_radius=8,
        )

        # Action buttons
        copy_button = ft.ElevatedButton(
            "Copy to Clipboard",
            icon=ft.Icons.COPY,
            on_click=lambda e: self._on_copy(raw_key),
        )

        print_button = ft.OutlinedButton(
            "Print Key",
            icon=ft.Icons.PRINT,
            on_click=lambda e: self._on_print(key_display),
        )

        save_button = ft.ElevatedButton(
            "I Have Saved It",
            icon=ft.Icons.CHECK,
            on_click=self._on_save_click,
            disabled=True,
        )

        # Enable save button when checkbox is checked
        def on_checkbox_change(e):
            save_button.disabled = not self.key_saved_checkbox.value
            self.page.update()

        self.key_saved_checkbox.on_change = on_checkbox_change

        # Build dialog content
        content = ft.Column([
            ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
            ft.Text(description, size=12, color=ft.Colors.GREY_700),
            ft.Divider(),

            security_info,
            ft.Divider(),

            self.key_field,

            ft.Row([copy_button, print_button], spacing=10),

            ft.Divider(),
            warning_banner,
            ft.Divider(),

            self.key_saved_checkbox,
        ], spacing=10, scroll=ft.ScrollMode.AUTO, width=550, height=500)

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.KEY, color=ft.Colors.BLUE_700),
                ft.Text(title),
            ], spacing=10),
            content=content,
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                save_button,
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Show dialog
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

        # Store the raw key for callback
        self.raw_key = raw_key

    def _on_copy(self, key: str):
        """Copy key to clipboard."""
        # Remove spaces for easier pasting
        clean_key = key.replace(' ', '')
        self.page.set_clipboard(clean_key)
        self._show_snackbar("Copied to clipboard!")

    def _on_print(self, key: str):
        """Print key (open print dialog)."""
        # Create a simple HTML page for printing
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DocAssist EMR - Encryption Key</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 2px solid #ffc107;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 8px;
                }}
                .key-box {{
                    background-color: #f8f9fa;
                    border: 2px solid #007bff;
                    padding: 20px;
                    margin: 20px 0;
                    font-family: monospace;
                    font-size: 14px;
                    word-break: break-all;
                }}
                .instructions {{
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #e7f3ff;
                    border-radius: 8px;
                }}
                @media print {{
                    body {{ padding: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DocAssist EMR</h1>
                <h2>Encryption Key Backup</h2>
                <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <div class="warning">
                <h3>⚠️ CRITICAL SECURITY INFORMATION</h3>
                <p><strong>This key is required to decrypt your backups.</strong></p>
                <p>Store this document in a secure location. Do not share it with anyone.</p>
                <p>If you lose this key AND your password, your data is permanently unrecoverable.</p>
            </div>

            <div class="key-box">
                <h3>Your Encryption Key:</h3>
                <p style="font-size: 16px;">{key}</p>
            </div>

            <div class="instructions">
                <h3>Storage Instructions:</h3>
                <ul>
                    <li>Store this document in a fireproof safe</li>
                    <li>Consider making multiple copies in different secure locations</li>
                    <li>Do not store digitally on the same device as your backups</li>
                    <li>Do not email or message this key to anyone</li>
                </ul>
            </div>

            <script>
                window.onload = function() {{
                    window.print();
                }};
            </script>
        </body>
        </html>
        """

        # Write to temp file and open
        import tempfile
        import webbrowser
        from datetime import datetime

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name

        webbrowser.open(f'file://{temp_path}')
        self._show_snackbar("Opening print dialog...")

    def _on_save_click(self, e):
        """Handle save button click."""
        if not self.key_saved_checkbox.value:
            self._show_snackbar("Please confirm you have saved the key", error=True)
            return

        # Close dialog
        self.dialog.open = False
        self.page.update()

        # Call callback
        if self.on_save:
            self.on_save(self.key_type, self.raw_key)

    def _on_cancel(self, e):
        """Handle cancel button."""
        self.dialog.open = False
        self.page.update()

    def _show_snackbar(self, message: str, error: bool = False):
        """Show snackbar message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _show_error_dialog(self, message: str):
        """Show error dialog."""
        error_dialog = ft.AlertDialog(
            title=ft.Text("Error"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: self._close_error(error_dialog)),
            ],
        )
        self.page.overlay.append(error_dialog)
        error_dialog.open = True
        self.page.update()

    def _close_error(self, dialog):
        """Close error dialog."""
        dialog.open = False
        self.page.update()


def show_encryption_key_dialog(
    page: ft.Page,
    key_type: str = "recovery",
    existing_key: Optional[str] = None,
    on_save: Optional[Callable[[str, str], None]] = None,
):
    """Show encryption key dialog.

    Args:
        page: Flet page
        key_type: Type of key ("password" or "recovery")
        existing_key: Existing key to display
        on_save: Callback when key is saved (key_type, key_value)
    """
    EncryptionKeyDialog(page, key_type, existing_key, on_save)
