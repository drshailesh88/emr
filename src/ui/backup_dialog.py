"""Backup and Cloud Sync UI dialogs."""

import flet as ft
from typing import Callable, Optional, List
from datetime import datetime
from pathlib import Path
import threading

from ..services.backup import BackupService, BackupInfo
from ..services.crypto import is_crypto_available, get_crypto_backend, CryptoService
from ..services.cloud_backup_manager import CloudBackupManager
from .cloud.cloud_setup_wizard import show_cloud_setup_wizard
from .cloud.cloud_status_panel import CloudStatusPanel
from .cloud.encryption_key_dialog import show_encryption_key_dialog
from .cloud.restore_from_cloud import show_restore_from_cloud
from .cloud.sync_conflict_dialog import show_sync_conflict_dialog


class BackupDialog:
    """Dialog for backup and restore operations."""

    def __init__(
        self,
        page: ft.Page,
        backup_service: BackupService,
        scheduler=None,
        settings_service=None,
        cloud_backup_manager: Optional[CloudBackupManager] = None,
        on_close: Optional[Callable] = None
    ):
        """Initialize backup dialog.

        Args:
            page: Flet page
            backup_service: Backup service instance
            scheduler: BackupScheduler instance (optional)
            settings_service: SettingsService instance (optional)
            cloud_backup_manager: CloudBackupManager instance (optional)
            on_close: Callback when dialog closes
        """
        self.page = page
        self.backup_service = backup_service
        self.scheduler = scheduler
        self.settings_service = settings_service
        self.cloud_backup_manager = cloud_backup_manager
        self.on_close = on_close

        # UI state
        self.dialog: Optional[ft.AlertDialog] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.progress_text: Optional[ft.Text] = None
        self.backup_list: Optional[ft.ListView] = None
        self.password_field: Optional[ft.TextField] = None

        # Auto-backup controls
        self.auto_backup_enabled: Optional[ft.Switch] = None
        self.frequency_dropdown: Optional[ft.Dropdown] = None
        self.backup_on_close_switch: Optional[ft.Switch] = None
        self.cloud_sync_switch: Optional[ft.Switch] = None
        self.scheduler_status_text: Optional[ft.Text] = None

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

        # Auto-backup controls (if scheduler is available)
        auto_backup_section = None
        if self.scheduler and self.settings_service:
            backup_settings = self.settings_service.get_backup_settings()
            scheduler_status = self.scheduler.get_status()

            self.auto_backup_enabled = ft.Switch(
                label="Enable auto-backup",
                value=backup_settings.auto_backup_enabled,
                on_change=self._on_auto_backup_toggle,
            )

            self.frequency_dropdown = ft.Dropdown(
                label="Backup frequency",
                width=150,
                options=[
                    ft.dropdown.Option("1", "Every hour"),
                    ft.dropdown.Option("4", "Every 4 hours"),
                    ft.dropdown.Option("12", "Every 12 hours"),
                    ft.dropdown.Option("24", "Every 24 hours"),
                ],
                value=str(backup_settings.backup_frequency_hours),
                on_change=self._on_frequency_change,
            )

            self.backup_on_close_switch = ft.Switch(
                label="Backup on app close",
                value=backup_settings.backup_on_close,
                on_change=self._on_backup_on_close_toggle,
            )

            self.cloud_sync_switch = ft.Switch(
                label="Auto-sync to cloud",
                value=backup_settings.cloud_sync_enabled,
                on_change=self._on_cloud_sync_toggle,
            )

            # Status text
            last_backup_text = "Never"
            next_backup_text = "N/A"
            if scheduler_status.get('last_backup_hours_ago') is not None:
                hours_ago = scheduler_status['last_backup_hours_ago']
                if hours_ago < 1:
                    last_backup_text = f"{int(hours_ago * 60)} minutes ago"
                else:
                    last_backup_text = f"{hours_ago:.1f} hours ago"

            if scheduler_status.get('next_backup_in_minutes') is not None:
                minutes = scheduler_status['next_backup_in_minutes']
                if minutes < 60:
                    next_backup_text = f"in {minutes} minutes"
                else:
                    next_backup_text = f"in {minutes // 60} hours"

            self.scheduler_status_text = ft.Text(
                f"Last backup: {last_backup_text} | Next backup: {next_backup_text}",
                size=11,
                color=ft.Colors.GREY_600,
            )

            auto_backup_section = ft.Container(
                content=ft.Column([
                    ft.Text("Auto-Backup", size=14, weight=ft.FontWeight.W_500),
                    self.auto_backup_enabled,
                    ft.Row([
                        self.frequency_dropdown,
                        self.backup_on_close_switch,
                    ], spacing=20),
                    self.cloud_sync_switch,
                    self.scheduler_status_text,
                ], spacing=8),
                bgcolor=ft.Colors.BLUE_50,
                padding=10,
                border_radius=8,
            )

        # Local backup tab
        local_tab_controls = [
            ft.Text("Local Backups", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"Encryption: {crypto_backend}" if crypto_available else "Encryption: Not available (install pynacl)",
                size=11,
                color=ft.Colors.GREY_600,
            ),
            ft.Divider(),
        ]

        # Add auto-backup section if available
        if auto_backup_section:
            local_tab_controls.append(auto_backup_section)
            local_tab_controls.append(ft.Divider())

        # Add manual backup controls
        local_tab_controls.extend([
            ft.Text("Manual Backup", size=14, weight=ft.FontWeight.W_500),
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
        ])

        local_tab = ft.Container(
            content=ft.Column(local_tab_controls, spacing=10, scroll=ft.ScrollMode.AUTO),
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

        # Build cloud tab with new components
        cloud_tab_content = []

        # Check if cloud is configured
        if self.settings_service:
            backup_settings = self.settings_service.get_backup_settings()
            cloud_configured = backup_settings.cloud_sync_enabled and backup_settings.cloud_config

            if cloud_configured:
                # Show cloud status panel
                try:
                    status_panel = CloudStatusPanel(
                        settings_service=self.settings_service,
                        cloud_backup_manager=self.cloud_backup_manager,
                        on_sync_click=lambda: self._on_sync_to_cloud(None),
                        on_settings_click=lambda: self._on_cloud_setup_wizard(),
                    )
                    cloud_tab_content.append(status_panel)
                    cloud_tab_content.append(ft.Divider())
                except Exception as ex:
                    print(f"Error creating cloud status panel: {ex}")

        # Cloud actions
        cloud_tab_content.extend([
            ft.Text("Cloud Backup Actions", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(
                "All data is encrypted before upload. Zero-knowledge security.",
                size=11,
                color=ft.Colors.GREEN_700,
                italic=True,
            ),
            ft.Divider(),

            # Quick setup wizard button
            ft.ElevatedButton(
                "Setup Cloud Backup",
                icon=ft.Icons.CLOUD_UPLOAD,
                on_click=lambda e: self._on_cloud_setup_wizard(),
            ),

            ft.Divider(),

            # Action buttons
            ft.Row([
                ft.ElevatedButton(
                    "Sync Now",
                    icon=ft.Icons.SYNC,
                    on_click=self._on_sync_to_cloud,
                    disabled=not crypto_available,
                ),
                ft.OutlinedButton(
                    "Restore from Cloud",
                    icon=ft.Icons.CLOUD_DOWNLOAD,
                    on_click=lambda e: self._on_restore_from_cloud(),
                ),
            ], spacing=10),

            ft.Divider(),

            # Advanced actions
            ft.Text("Advanced", size=14, weight=ft.FontWeight.W_500),
            ft.Row([
                ft.OutlinedButton(
                    "Generate Recovery Key",
                    icon=ft.Icons.KEY,
                    on_click=lambda e: self._on_show_encryption_key(),
                ),
                ft.OutlinedButton(
                    "Test Connection",
                    icon=ft.Icons.WIFI_TETHERING,
                    on_click=lambda e: self._on_test_cloud_connection(),
                ),
            ], spacing=10),

            ft.Divider(),

            # Manual configuration (for advanced users)
            ft.ExpansionTile(
                title=ft.Text("Manual Configuration", size=13),
                subtitle=ft.Text("For advanced users", size=11, color=ft.Colors.GREY_600),
                initially_expanded=False,
                controls=[
                    ft.Column([
                        ft.Row([
                            self.storage_backend,
                            self.cloud_status,
                        ], spacing=20),
                        self.cloud_api_key,
                        self.s3_config_container,
                        self.local_path,
                    ], spacing=10),
                ],
            ),

            ft.Divider(),

            # Pricing info
            ft.Container(
                content=ft.Column([
                    ft.Text("DocAssist Cloud Pricing", weight=ft.FontWeight.W_500, size=12),
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
                                ft.DataCell(ft.Text("Essential", size=11)),
                                ft.DataCell(ft.Text("10 GB", size=11)),
                                ft.DataCell(ft.Text("₹199/mo", size=11)),
                            ]),
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text("Professional", size=11)),
                                ft.DataCell(ft.Text("50 GB", size=11)),
                                ft.DataCell(ft.Text("₹499/mo", size=11)),
                            ]),
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text("Clinic", size=11)),
                                ft.DataCell(ft.Text("200 GB", size=11)),
                                ft.DataCell(ft.Text("₹2,499/mo", size=11)),
                            ]),
                        ],
                        heading_row_height=30,
                        data_row_min_height=25,
                        data_row_max_height=30,
                    ),
                ], spacing=5),
                padding=ft.padding.only(top=10),
            ),
        ])

        cloud_tab = ft.Container(
            content=ft.Column(cloud_tab_content, spacing=10, scroll=ft.ScrollMode.AUTO),
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
        self._on_restore_from_cloud()

    def _on_cloud_setup_wizard(self):
        """Show cloud setup wizard."""
        if not self.settings_service:
            self._show_snackbar("Settings service not available", error=True)
            return

        def on_complete(config):
            self._show_snackbar("Cloud backup configured successfully!")
            # Refresh dialog if needed
            pass

        show_cloud_setup_wizard(self.page, self.settings_service, on_complete)

    def _on_restore_from_cloud(self):
        """Show restore from cloud dialog."""
        if not self.settings_service:
            self._show_snackbar("Settings service not available", error=True)
            return

        def on_complete():
            self._show_snackbar("Restore complete! Please restart the app.")

        show_restore_from_cloud(
            self.page,
            self.backup_service,
            self.settings_service,
            on_complete
        )

    def _on_show_encryption_key(self):
        """Show encryption key dialog."""
        def on_save(key_type, key_value):
            self._show_snackbar(f"{key_type.title()} key saved!")

        show_encryption_key_dialog(
            self.page,
            key_type="recovery",
            on_save=on_save
        )

    def _on_test_cloud_connection(self):
        """Test cloud connection."""
        if not self.settings_service or not self.cloud_backup_manager:
            self._show_snackbar("Cloud backup not configured", error=True)
            return

        # Get backend config
        settings = self.settings_service.get_backup_settings()
        if not settings.cloud_config:
            self._show_snackbar("Please configure cloud storage first", error=True)
            return

        backend_config = settings.cloud_config.copy()
        backend_config['type'] = settings.cloud_backend_type

        # Test connection in background
        def do_test():
            success, error = self.cloud_backup_manager.test_connection(backend_config)
            if self.page:
                if success:
                    self.page.run_thread_safe(lambda: self._show_snackbar("Connection test successful!"))
                else:
                    self.page.run_thread_safe(lambda: self._show_snackbar(f"Connection test failed: {error}", error=True))

        self._show_snackbar("Testing connection...")
        threading.Thread(target=do_test, daemon=True).start()

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

    def _on_auto_backup_toggle(self, e):
        """Handle auto-backup toggle."""
        if not self.settings_service or not self.scheduler:
            return

        enabled = self.auto_backup_enabled.value
        self.settings_service.enable_auto_backup(enabled)

        if enabled:
            self.scheduler.start()
            self._show_snackbar("Auto-backup enabled")
        else:
            self.scheduler.stop()
            self._show_snackbar("Auto-backup disabled")

        self._update_scheduler_status()

    def _on_frequency_change(self, e):
        """Handle backup frequency change."""
        if not self.settings_service or not self.scheduler:
            return

        hours = int(self.frequency_dropdown.value)
        self.settings_service.set_backup_frequency(hours)
        self.scheduler.set_frequency(hours)
        self._show_snackbar(f"Backup frequency set to {hours} hours")
        self._update_scheduler_status()

    def _on_backup_on_close_toggle(self, e):
        """Handle backup on close toggle."""
        if not self.settings_service:
            return

        enabled = self.backup_on_close_switch.value
        self.settings_service.enable_backup_on_close(enabled)
        self._show_snackbar(f"Backup on close {'enabled' if enabled else 'disabled'}")

    def _on_cloud_sync_toggle(self, e):
        """Handle cloud sync toggle."""
        if not self.settings_service or not self.scheduler:
            return

        enabled = self.cloud_sync_switch.value

        if enabled:
            # Need password and cloud config
            password = self.password_field.value
            if not password:
                self._show_snackbar("Please enter a backup password first", error=True)
                self.cloud_sync_switch.value = False
                self.page.update()
                return

            # Get cloud config from settings
            backup_settings = self.settings_service.get_backup_settings()
            if not backup_settings.cloud_config:
                self._show_snackbar("Please configure cloud storage first", error=True)
                self.cloud_sync_switch.value = False
                self.page.update()
                return

            self.scheduler.enable_cloud_sync(enabled, password, backup_settings.cloud_config)
            self._show_snackbar("Auto-sync to cloud enabled")
        else:
            self.scheduler.enable_cloud_sync(False)
            self._show_snackbar("Auto-sync to cloud disabled")

    def _update_scheduler_status(self):
        """Update scheduler status text."""
        if not self.scheduler or not self.scheduler_status_text:
            return

        scheduler_status = self.scheduler.get_status()

        last_backup_text = "Never"
        next_backup_text = "N/A"

        if scheduler_status.get('last_backup_hours_ago') is not None:
            hours_ago = scheduler_status['last_backup_hours_ago']
            if hours_ago < 1:
                last_backup_text = f"{int(hours_ago * 60)} minutes ago"
            else:
                last_backup_text = f"{hours_ago:.1f} hours ago"

        if scheduler_status.get('next_backup_in_minutes') is not None:
            minutes = scheduler_status['next_backup_in_minutes']
            if minutes < 60:
                next_backup_text = f"in {minutes} minutes"
            else:
                next_backup_text = f"in {minutes // 60} hours"

        self.scheduler_status_text.value = f"Last backup: {last_backup_text} | Next backup: {next_backup_text}"
        self.page.update()


def show_backup_dialog(
    page: ft.Page,
    backup_service: BackupService,
    scheduler=None,
    settings_service=None,
    cloud_backup_manager: Optional[CloudBackupManager] = None
):
    """Show the backup dialog.

    Args:
        page: Flet page
        backup_service: Backup service instance
        scheduler: BackupScheduler instance (optional)
        settings_service: SettingsService instance (optional)
        cloud_backup_manager: CloudBackupManager instance (optional)
    """
    BackupDialog(page, backup_service, scheduler, settings_service, cloud_backup_manager)
