"""Restore from Cloud Dialog - List and restore cloud backups."""

import flet as ft
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
from pathlib import Path
import threading

from ...services.backup import BackupService
from ...services.settings import SettingsService


class RestoreFromCloudDialog:
    """Dialog for restoring backups from cloud storage."""

    def __init__(
        self,
        page: ft.Page,
        backup_service: BackupService,
        settings_service: SettingsService,
        on_restore_complete: Optional[Callable] = None,
    ):
        """Initialize restore from cloud dialog.

        Args:
            page: Flet page
            backup_service: Backup service instance
            settings_service: Settings service instance
            on_restore_complete: Callback when restore is complete
        """
        self.page = page
        self.backup_service = backup_service
        self.settings_service = settings_service
        self.on_restore_complete = on_restore_complete

        # UI components
        self.dialog: Optional[ft.AlertDialog] = None
        self.backup_list: Optional[ft.ListView] = None
        self.status_text: Optional[ft.Text] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.progress_text: Optional[ft.Text] = None

        # Cloud backups
        self.cloud_backups: List[Dict[str, Any]] = []

        # Build and show dialog
        self._build_dialog()

    def _build_dialog(self):
        """Build the restore dialog."""
        backup_settings = self.settings_service.get_backup_settings()

        if not backup_settings.cloud_sync_enabled or not backup_settings.cloud_config:
            self._show_error_dialog("Cloud backup is not configured. Please set it up first.")
            return

        # Backup list
        self.backup_list = ft.ListView(
            spacing=8,
            padding=10,
            height=300,
        )

        # Status text
        self.status_text = ft.Text(
            "Loading cloud backups...",
            size=12,
            color=ft.Colors.GREY_600,
        )

        # Progress indicators
        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=500,
        )

        self.progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False,
        )

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CLOUD_DOWNLOAD, color=ft.Colors.BLUE_700),
                ft.Text("Restore from Cloud"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Select a backup to restore. This will replace your current data.",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(),

                    self.status_text,
                    self.backup_list,

                    self.progress_bar,
                    self.progress_text,

                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700, size=24),
                            ft.Text(
                                "WARNING: Restoring will replace your current data. "
                                "Make sure you have a recent local backup first.",
                                size=11,
                                color=ft.Colors.ORANGE_900,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        bgcolor=ft.Colors.ORANGE_50,
                        padding=15,
                        border_radius=8,
                    ),
                ], spacing=10),
                width=550,
                height=500,
            ),
            actions=[
                ft.TextButton("Close", on_click=self._on_close),
                ft.OutlinedButton(
                    "Refresh List",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self._load_cloud_backups(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Show dialog
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

        # Load cloud backups
        self._load_cloud_backups()

    def _load_cloud_backups(self):
        """Load list of cloud backups."""
        self.status_text.value = "Loading cloud backups..."
        self.backup_list.controls.clear()
        self.page.update()

        def do_load():
            try:
                backup_settings = self.settings_service.get_backup_settings()
                backend_config = backup_settings.cloud_config
                backend_config['type'] = backup_settings.cloud_backend_type

                # List cloud backups
                backups = self.backup_service.list_cloud_backups(backend_config)

                if self.page:
                    self.page.run_thread_safe(lambda: self._display_backups(backups))

            except Exception as ex:
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_error(f"Failed to load backups: {ex}"))

        threading.Thread(target=do_load, daemon=True).start()

    def _display_backups(self, backups: List[Dict[str, Any]]):
        """Display cloud backups in list."""
        self.cloud_backups = backups
        self.backup_list.controls.clear()

        if not backups:
            self.status_text.value = "No cloud backups found"
            self.backup_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No backups available in cloud storage",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            self.status_text.value = f"Found {len(backups)} backup(s)"
            for backup in backups:
                self.backup_list.controls.append(
                    self._build_backup_tile(backup)
                )

        self.page.update()

    def _build_backup_tile(self, backup: Dict[str, Any]) -> ft.Control:
        """Build a list tile for a cloud backup."""
        # Extract backup info
        key = backup.get('key', '')
        size = backup.get('size', 0)
        modified = backup.get('modified', '')

        # Format date
        try:
            if modified:
                dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = "Unknown"
        except Exception:
            date_str = modified[:16] if modified else "Unknown"

        # Format size
        size_mb = size / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB"

        # Extract filename from key
        filename = key.split('/')[-1] if '/' in key else key

        # Get device ID if available (from filename)
        device_info = ""
        if 'device-' in filename:
            device_info = " | Device backup"

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CLOUD, size=20, color=ft.Colors.BLUE_700),
                ft.Column([
                    ft.Text(filename, size=12, weight=ft.FontWeight.W_500),
                    ft.Text(
                        f"{date_str} | {size_str}{device_info}",
                        size=10,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=2, expand=True),
                ft.ElevatedButton(
                    "Restore",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e, b=backup: self._on_restore_backup(b),
                ),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=5,
            bgcolor=ft.Colors.GREY_100,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

    def _on_restore_backup(self, backup: Dict[str, Any]):
        """Handle restore backup button."""
        # Show password input dialog
        self._show_password_dialog(backup)

    def _show_password_dialog(self, backup: Dict[str, Any]):
        """Show password input dialog."""
        password_field = ft.TextField(
            label="Encryption Password",
            password=True,
            can_reveal_password=True,
            hint_text="Enter the password used to encrypt this backup",
            width=400,
            autofocus=True,
        )

        recovery_key_field = ft.TextField(
            label="Or Recovery Key",
            hint_text="Enter 64-character recovery key",
            width=400,
            visible=False,
        )

        use_recovery_key = ft.Checkbox(
            label="Use recovery key instead of password",
            value=False,
            on_change=lambda e: self._toggle_recovery_key(e, password_field, recovery_key_field),
        )

        def submit(e):
            pwd_or_key = recovery_key_field.value if use_recovery_key.value else password_field.value
            if not pwd_or_key:
                self._show_snackbar("Please enter password or recovery key", error=True)
                return

            pwd_dialog.open = False
            self.page.update()
            self._do_restore(backup, pwd_or_key, use_recovery_key.value)

        pwd_dialog = ft.AlertDialog(
            title=ft.Text("Enter Decryption Password"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "This backup is encrypted. Enter your password or recovery key to decrypt.",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(),
                    password_field,
                    use_recovery_key,
                    recovery_key_field,
                ], spacing=10),
                width=450,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_pwd_dialog(pwd_dialog)),
                ft.ElevatedButton("Restore", icon=ft.Icons.DOWNLOAD, on_click=submit),
            ],
        )
        self.page.overlay.append(pwd_dialog)
        pwd_dialog.open = True
        self.page.update()

    def _toggle_recovery_key(self, e, password_field, recovery_key_field):
        """Toggle between password and recovery key."""
        use_key = e.control.value
        password_field.visible = not use_key
        recovery_key_field.visible = use_key
        self.page.update()

    def _do_restore(self, backup: Dict[str, Any], password: str, is_recovery_key: bool = False):
        """Perform the restore operation."""
        remote_key = backup.get('key', '')

        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.progress_text.value = "Starting restore..."
        self.page.update()

        def do_restore():
            try:
                def progress_cb(message, percent):
                    if self.page:
                        self.page.run_thread_safe(lambda: self._update_progress(message, percent))

                # Restore from cloud
                success = self.backup_service.restore_from_cloud(
                    remote_key=remote_key,
                    password=password,
                    backend_config=self._get_backend_config(),
                    progress_callback=progress_cb
                )

                if self.page:
                    if success:
                        self.page.run_thread_safe(lambda: self._show_success())
                    else:
                        self.page.run_thread_safe(lambda: self._show_snackbar(
                            "Restore failed - wrong password or corrupted backup?",
                            error=True
                        ))
                        self.page.run_thread_safe(self._hide_progress)

            except Exception as ex:
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_snackbar(f"Error: {ex}", error=True))
                    self.page.run_thread_safe(self._hide_progress)

        threading.Thread(target=do_restore, daemon=True).start()

    def _get_backend_config(self) -> Dict[str, Any]:
        """Get backend config from settings."""
        backup_settings = self.settings_service.get_backup_settings()
        config = backup_settings.cloud_config.copy()
        config['type'] = backup_settings.cloud_backend_type
        return config

    def _update_progress(self, message: str, percent: int):
        """Update progress indicators."""
        self.progress_bar.value = percent / 100
        self.progress_text.value = message
        self.page.update()

    def _hide_progress(self):
        """Hide progress indicators."""
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.page.update()

    def _show_success(self):
        """Show restore success dialog."""
        self._hide_progress()

        success_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=32),
                ft.Text("Restore Complete!"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Your data has been successfully restored from the cloud backup.",
                        size=14,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Please restart DocAssist EMR for the changes to take effect.",
                        size=12,
                        color=ft.Colors.ORANGE_700,
                        weight=ft.FontWeight.BOLD,
                    ),
                ], spacing=10),
                width=400,
            ),
            actions=[
                ft.ElevatedButton(
                    "Close & Restart Later",
                    on_click=lambda e: self._close_success(success_dialog),
                ),
            ],
        )
        self.page.overlay.append(success_dialog)
        success_dialog.open = True
        self.page.update()

        # Call completion callback
        if self.on_restore_complete:
            self.on_restore_complete()

    def _close_success(self, dialog):
        """Close success dialog."""
        dialog.open = False
        self.dialog.open = False
        self.page.update()

    def _close_pwd_dialog(self, dialog):
        """Close password dialog."""
        dialog.open = False
        self.page.update()

    def _show_error(self, message: str):
        """Show error message."""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_700
        self.page.update()

    def _on_close(self, e):
        """Handle close button."""
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


def show_restore_from_cloud(
    page: ft.Page,
    backup_service: BackupService,
    settings_service: SettingsService,
    on_restore_complete: Optional[Callable] = None,
):
    """Show restore from cloud dialog.

    Args:
        page: Flet page
        backup_service: Backup service instance
        settings_service: Settings service instance
        on_restore_complete: Callback when restore is complete
    """
    RestoreFromCloudDialog(page, backup_service, settings_service, on_restore_complete)
