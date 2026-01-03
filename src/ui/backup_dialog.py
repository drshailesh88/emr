"""Backup and Cloud Sync UI dialogs."""

import flet as ft
from typing import Callable, Optional, List
from datetime import datetime
from pathlib import Path
import threading

from ..services.backup import BackupService, BackupInfo
from ..services.crypto import is_crypto_available, get_crypto_backend, CryptoService


class BackupDialog:
    """Dialog for backup and restore operations."""

    def __init__(
        self,
        page: ft.Page,
        backup_service: BackupService,
        on_close: Optional[Callable] = None
    ):
        """Initialize backup dialog.

        Args:
            page: Flet page
            backup_service: Backup service instance
            on_close: Callback when dialog closes
        """
        self.page = page
        self.backup_service = backup_service
        self.on_close = on_close

        # UI state
        self.dialog: Optional[ft.AlertDialog] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.progress_text: Optional[ft.Text] = None
        self.backup_list: Optional[ft.ListView] = None
        self.password_field: Optional[ft.TextField] = None

        # Build and show dialog
        self._build_dialog()

    def _build_dialog(self):
        """Build the backup dialog."""

        # Check crypto availability
        crypto_available = is_crypto_available()
        crypto_backend = get_crypto_backend()

        # Tab content: Local Backups
        self.backup_list = ft.ListView(
            spacing=5,
            padding=10,
            height=250,
        )
        self._refresh_backup_list()

        # Progress indicators
        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=400,
        )
        self.progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False,
        )

        # Password field for encrypted backups
        self.password_field = ft.TextField(
            label="Backup Password",
            password=True,
            can_reveal_password=True,
            hint_text="Enter password for encryption",
            width=300,
        )

        # Encrypted backup checkbox
        self.encrypt_checkbox = ft.Checkbox(
            label="Encrypt backup",
            value=True,
            disabled=not crypto_available,
        )

        # Local backup tab
        local_tab = ft.Container(
            content=ft.Column([
                ft.Text("Local Backups", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"Encryption: {crypto_backend}" if crypto_available else "Encryption: Not available (install pynacl)",
                    size=11,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(),

                # Backup controls
                ft.Row([
                    self.encrypt_checkbox,
                    self.password_field,
                ], spacing=20),

                ft.Row([
                    ft.ElevatedButton(
                        "Create Backup",
                        icon=ft.Icons.BACKUP,
                        on_click=self._on_create_backup,
                    ),
                    ft.OutlinedButton(
                        "Refresh List",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: self._refresh_backup_list(),
                    ),
                ], spacing=10),

                self.progress_bar,
                self.progress_text,

                ft.Divider(),
                ft.Text("Available Backups:", weight=ft.FontWeight.W_500),
                self.backup_list,
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=15,
        )

        # Cloud sync tab
        self.cloud_api_key = ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            hint_text="Your DocAssist cloud API key",
            width=350,
        )

        self.cloud_status = ft.Text(
            "Not connected",
            size=12,
            color=ft.Colors.GREY_600,
        )

        # Storage backend dropdown
        self.storage_backend = ft.Dropdown(
            label="Storage Backend",
            width=200,
            options=[
                ft.dropdown.Option("docassist", "DocAssist Cloud"),
                ft.dropdown.Option("s3", "Amazon S3 / Backblaze B2"),
                ft.dropdown.Option("local", "Local Network Share"),
            ],
            value="docassist",
            on_change=self._on_backend_change,
        )

        # S3 config fields (hidden by default)
        self.s3_bucket = ft.TextField(
            label="Bucket Name",
            hint_text="my-emr-backups",
            width=200,
            visible=False,
        )
        self.s3_access_key = ft.TextField(
            label="Access Key",
            width=200,
            visible=False,
        )
        self.s3_secret_key = ft.TextField(
            label="Secret Key",
            password=True,
            width=200,
            visible=False,
        )
        self.s3_endpoint = ft.TextField(
            label="Endpoint URL (optional)",
            hint_text="https://s3.us-west-001.backblazeb2.com",
            width=350,
            visible=False,
        )

        # Local path field (hidden by default)
        self.local_path = ft.TextField(
            label="Network Path",
            hint_text="/mnt/backup or \\\\server\\share",
            width=350,
            visible=False,
        )

        self.s3_config_container = ft.Column([
            ft.Row([self.s3_bucket, self.s3_access_key, self.s3_secret_key], spacing=10),
            self.s3_endpoint,
        ], visible=False)

        cloud_tab = ft.Container(
            content=ft.Column([
                ft.Text("Cloud Backup", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "All data is encrypted before upload. We cannot see your data.",
                    size=11,
                    color=ft.Colors.GREEN_700,
                    italic=True,
                ),
                ft.Divider(),

                ft.Row([
                    self.storage_backend,
                    self.cloud_status,
                ], spacing=20, alignment=ft.MainAxisAlignment.START),

                # DocAssist cloud config
                self.cloud_api_key,

                # S3 config (hidden by default)
                self.s3_config_container,

                # Local path (hidden by default)
                self.local_path,

                ft.Divider(),

                ft.Row([
                    ft.ElevatedButton(
                        "Sync to Cloud",
                        icon=ft.Icons.CLOUD_UPLOAD,
                        on_click=self._on_sync_to_cloud,
                        disabled=not crypto_available,
                    ),
                    ft.OutlinedButton(
                        "List Cloud Backups",
                        icon=ft.Icons.CLOUD_DOWNLOAD,
                        on_click=self._on_list_cloud_backups,
                    ),
                ], spacing=10),

                ft.Container(
                    content=ft.Column([
                        ft.Text("Pricing:", weight=ft.FontWeight.W_500, size=12),
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Tier", size=11)),
                                ft.DataColumn(ft.Text("Storage", size=11)),
                                ft.DataColumn(ft.Text("Price", size=11)),
                            ],
                            rows=[
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text("Free", size=11)),
                                    ft.DataCell(ft.Text("1 GB", size=11)),
                                    ft.DataCell(ft.Text("₹0", size=11)),
                                ]),
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text("Basic", size=11)),
                                    ft.DataCell(ft.Text("10 GB", size=11)),
                                    ft.DataCell(ft.Text("₹99/mo", size=11)),
                                ]),
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text("Pro", size=11)),
                                    ft.DataCell(ft.Text("50 GB", size=11)),
                                    ft.DataCell(ft.Text("₹299/mo", size=11)),
                                ]),
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text("Clinic", size=11)),
                                    ft.DataCell(ft.Text("200 GB", size=11)),
                                    ft.DataCell(ft.Text("₹999/mo", size=11)),
                                ]),
                            ],
                            heading_row_height=30,
                            data_row_min_height=25,
                            data_row_max_height=30,
                        ),
                    ], spacing=5),
                    padding=ft.padding.only(top=10),
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=15,
        )

        # Recovery key tab
        self.recovery_key_display = ft.TextField(
            label="Your Recovery Key",
            value="",
            read_only=True,
            multiline=True,
            min_lines=2,
            max_lines=3,
            width=400,
            text_style=ft.TextStyle(font_family="monospace"),
        )

        recovery_tab = ft.Container(
            content=ft.Column([
                ft.Text("Recovery Key", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700, size=30),
                        ft.Text(
                            "Write this key down and store it safely!",
                            color=ft.Colors.ORANGE_700,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "If you forget your password, this is the ONLY way to recover your data.",
                            size=12,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=15,
                    border_radius=8,
                ),

                ft.Divider(),

                self.recovery_key_display,

                ft.Row([
                    ft.ElevatedButton(
                        "Generate New Key",
                        icon=ft.Icons.KEY,
                        on_click=self._on_generate_recovery_key,
                        disabled=not crypto_available,
                    ),
                    ft.OutlinedButton(
                        "Copy to Clipboard",
                        icon=ft.Icons.COPY,
                        on_click=self._on_copy_recovery_key,
                    ),
                ], spacing=10),

                ft.Container(
                    content=ft.Text(
                        "The recovery key is 64 characters long and allows you to decrypt your "
                        "backups even if you forget your password. We recommend printing it and "
                        "storing it in a safe place.",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                    padding=ft.padding.only(top=10),
                ),
            ], spacing=10),
            padding=15,
        )

        # Build tabs
        tabs = ft.Tabs(
            tabs=[
                ft.Tab(text="Local Backup", icon=ft.Icons.SAVE, content=local_tab),
                ft.Tab(text="Cloud Sync", icon=ft.Icons.CLOUD, content=cloud_tab),
                ft.Tab(text="Recovery Key", icon=ft.Icons.KEY, content=recovery_tab),
            ],
            expand=True,
        )

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.BACKUP, color=ft.Colors.BLUE_700),
                ft.Text("Backup & Restore"),
            ], spacing=10),
            content=ft.Container(
                content=tabs,
                width=550,
                height=450,
            ),
            actions=[
                ft.TextButton("Close", on_click=self._on_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Show dialog
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _refresh_backup_list(self):
        """Refresh the list of available backups."""
        self.backup_list.controls.clear()

        backups = self.backup_service.list_backups()

        if not backups:
            self.backup_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No backups found",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for backup in backups[:10]:  # Show max 10
                self.backup_list.controls.append(
                    self._build_backup_tile(backup)
                )

        if self.page:
            self.page.update()

    def _build_backup_tile(self, backup: BackupInfo) -> ft.Control:
        """Build a list tile for a backup."""
        # Format date
        try:
            dt = datetime.fromisoformat(backup.created_at)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = backup.created_at[:16] if backup.created_at else "Unknown"

        # Format size
        size_mb = backup.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB"

        # Icon based on encryption
        icon = ft.Icons.LOCK if backup.is_encrypted else ft.Icons.FOLDER_ZIP

        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color=ft.Colors.BLUE_700 if backup.is_encrypted else ft.Colors.GREY_600),
                ft.Column([
                    ft.Text(backup.filename, size=12, weight=ft.FontWeight.W_500),
                    ft.Text(
                        f"{date_str} | {size_str}" + (f" | {backup.patient_count} patients" if backup.patient_count else ""),
                        size=10,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.RESTORE,
                        tooltip="Restore",
                        icon_size=18,
                        on_click=lambda e, b=backup: self._on_restore_backup(b),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Delete",
                        icon_size=18,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, b=backup: self._on_delete_backup(b),
                    ),
                ], spacing=0),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=5,
            bgcolor=ft.Colors.GREY_100,
        )

    def _show_progress(self, message: str, percent: int = 0):
        """Show progress indicator."""
        self.progress_bar.visible = True
        self.progress_bar.value = percent / 100
        self.progress_text.visible = True
        self.progress_text.value = message
        if self.page:
            self.page.update()

    def _hide_progress(self):
        """Hide progress indicator."""
        self.progress_bar.visible = False
        self.progress_text.visible = False
        if self.page:
            self.page.update()

    def _on_create_backup(self, e):
        """Handle create backup button."""
        encrypt = self.encrypt_checkbox.value
        password = self.password_field.value

        if encrypt and not password:
            self._show_snackbar("Please enter a password for encryption", error=True)
            return

        def do_backup():
            def progress_cb(message, percent):
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_progress(message, percent))

            try:
                path = self.backup_service.create_backup(
                    encrypt=encrypt,
                    password=password if encrypt else None,
                    progress_callback=progress_cb
                )

                if self.page:
                    if path:
                        self.page.run_thread_safe(lambda: self._show_snackbar(f"Backup created: {path.name}"))
                        self.page.run_thread_safe(self._refresh_backup_list)
                    else:
                        self.page.run_thread_safe(lambda: self._show_snackbar("Backup failed", error=True))
                    self.page.run_thread_safe(self._hide_progress)

            except Exception as ex:
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_snackbar(f"Error: {ex}", error=True))
                    self.page.run_thread_safe(self._hide_progress)

        threading.Thread(target=do_backup, daemon=True).start()

    def _on_restore_backup(self, backup: BackupInfo):
        """Handle restore backup."""
        # If encrypted, prompt for password
        if backup.is_encrypted:
            self._show_password_dialog(
                "Enter Backup Password",
                lambda pwd: self._do_restore(backup, pwd)
            )
        else:
            self._do_restore(backup, None)

    def _do_restore(self, backup: BackupInfo, password: Optional[str]):
        """Perform the restore operation."""
        def do_restore():
            def progress_cb(message, percent):
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_progress(message, percent))

            try:
                success = self.backup_service.restore_backup(
                    backup.path,
                    password=password,
                    progress_callback=progress_cb
                )

                if self.page:
                    if success:
                        self.page.run_thread_safe(lambda: self._show_snackbar("Restore complete! Please restart the app."))
                    else:
                        self.page.run_thread_safe(lambda: self._show_snackbar("Restore failed - wrong password?", error=True))
                    self.page.run_thread_safe(self._hide_progress)

            except Exception as ex:
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_snackbar(f"Error: {ex}", error=True))
                    self.page.run_thread_safe(self._hide_progress)

        threading.Thread(target=do_restore, daemon=True).start()

    def _on_delete_backup(self, backup: BackupInfo):
        """Handle delete backup."""
        def do_delete(e):
            try:
                backup.path.unlink()
                self._show_snackbar(f"Deleted: {backup.filename}")
                self._refresh_backup_list()
            except Exception as ex:
                self._show_snackbar(f"Delete failed: {ex}", error=True)
            confirm_dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete backup '{backup.filename}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm(confirm_dialog)),
                ft.TextButton("Delete", on_click=do_delete),
            ],
        )
        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()

    def _close_confirm(self, dialog):
        """Close confirmation dialog."""
        dialog.open = False
        self.page.update()

    def _on_backend_change(self, e):
        """Handle storage backend change."""
        backend = self.storage_backend.value

        # Show/hide appropriate config fields
        self.cloud_api_key.visible = (backend == "docassist")
        self.s3_config_container.visible = (backend == "s3")
        self.s3_bucket.visible = (backend == "s3")
        self.s3_access_key.visible = (backend == "s3")
        self.s3_secret_key.visible = (backend == "s3")
        self.s3_endpoint.visible = (backend == "s3")
        self.local_path.visible = (backend == "local")

        self.page.update()

    def _on_sync_to_cloud(self, e):
        """Handle sync to cloud."""
        password = self.password_field.value
        if not password:
            self._show_snackbar("Please enter a backup password first", error=True)
            return

        backend_type = self.storage_backend.value
        backend_config = {"type": backend_type}

        if backend_type == "docassist":
            if not self.cloud_api_key.value:
                self._show_snackbar("Please enter your API key", error=True)
                return
            backend_config["api_key"] = self.cloud_api_key.value

        elif backend_type == "s3":
            if not all([self.s3_bucket.value, self.s3_access_key.value, self.s3_secret_key.value]):
                self._show_snackbar("Please fill in all S3 fields", error=True)
                return
            backend_config.update({
                "bucket": self.s3_bucket.value,
                "access_key": self.s3_access_key.value,
                "secret_key": self.s3_secret_key.value,
                "endpoint_url": self.s3_endpoint.value or None,
            })

        elif backend_type == "local":
            if not self.local_path.value:
                self._show_snackbar("Please enter the network path", error=True)
                return
            backend_config["path"] = self.local_path.value

        def do_sync():
            def progress_cb(message, percent):
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_progress(message, percent))

            try:
                success = self.backup_service.sync_to_cloud(
                    password=password,
                    backend_config=backend_config,
                    progress_callback=progress_cb
                )

                if self.page:
                    if success:
                        self.page.run_thread_safe(lambda: self._show_snackbar("Sync complete!"))
                    else:
                        self.page.run_thread_safe(lambda: self._show_snackbar("Sync failed", error=True))
                    self.page.run_thread_safe(self._hide_progress)

            except Exception as ex:
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_snackbar(f"Error: {ex}", error=True))
                    self.page.run_thread_safe(self._hide_progress)

        threading.Thread(target=do_sync, daemon=True).start()

    def _on_list_cloud_backups(self, e):
        """Handle list cloud backups."""
        # TODO: Implement cloud backup listing dialog
        self._show_snackbar("Cloud backup listing coming soon!")

    def _on_generate_recovery_key(self, e):
        """Generate a new recovery key."""
        try:
            crypto = CryptoService()
            key = crypto.generate_recovery_key()
            formatted = crypto.format_recovery_key(key)
            self.recovery_key_display.value = formatted
            self.page.update()
            self._show_snackbar("Recovery key generated - write it down!")
        except Exception as ex:
            self._show_snackbar(f"Error: {ex}", error=True)

    def _on_copy_recovery_key(self, e):
        """Copy recovery key to clipboard."""
        if self.recovery_key_display.value:
            self.page.set_clipboard(self.recovery_key_display.value.replace(" ", ""))
            self._show_snackbar("Copied to clipboard!")

    def _show_password_dialog(self, title: str, on_submit: Callable[[str], None]):
        """Show password input dialog."""
        pwd_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )

        def submit(e):
            pwd_dialog.open = False
            self.page.update()
            on_submit(pwd_field.value)

        pwd_dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=pwd_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_pwd_dialog(pwd_dialog)),
                ft.TextButton("Submit", on_click=submit),
            ],
        )
        self.page.overlay.append(pwd_dialog)
        pwd_dialog.open = True
        self.page.update()

    def _close_pwd_dialog(self, dialog):
        """Close password dialog."""
        dialog.open = False
        self.page.update()

    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_close(self, e):
        """Handle dialog close."""
        self.dialog.open = False
        self.page.update()
        if self.on_close:
            self.on_close()


def show_backup_dialog(page: ft.Page, backup_service: BackupService):
    """Show the backup dialog.

    Args:
        page: Flet page
        backup_service: Backup service instance
    """
    BackupDialog(page, backup_service)
