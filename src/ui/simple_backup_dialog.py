"""Simple backup dialog for DocAssist EMR.

Provides a clean, user-friendly interface for:
- Creating local backups (no encryption complexity)
- Viewing backup history
- Restoring from backups
- Managing backup settings (auto-backup, frequency, location)
"""

import flet as ft
from typing import Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import threading
import logging

from ..services.simple_backup import SimpleBackupService, SimpleBackupInfo

logger = logging.getLogger(__name__)


class SimpleBackupDialog:
    """Simple backup dialog without encryption complexity."""

    def __init__(
        self,
        page: ft.Page,
        backup_service: SimpleBackupService,
        on_close: Optional[Callable] = None
    ):
        """Initialize simple backup dialog.

        Args:
            page: Flet page
            backup_service: SimpleBackupService instance
            on_close: Callback when dialog closes
        """
        self.page = page
        self.backup_service = backup_service
        self.on_close_callback = on_close

        # UI state
        self.dialog: Optional[ft.AlertDialog] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.progress_text: Optional[ft.Text] = None
        self.backup_list: Optional[ft.ListView] = None
        self.location_text: Optional[ft.Text] = None
        self.stats_text: Optional[ft.Text] = None

        # Build and show dialog
        self._build_dialog()

    def _build_dialog(self):
        """Build the backup dialog."""

        # Backup location display
        self.location_text = ft.Text(
            f"Backup location: {self.backup_service.get_backup_location()}",
            size=11,
            color=ft.Colors.GREY_600,
        )

        # Statistics
        stats = self.backup_service.get_backup_stats()
        self.stats_text = ft.Text(
            f"{stats['total_backups']} backups | {stats['total_size_mb']:.1f} MB total",
            size=11,
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.W_500,
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

        # Backup list
        self.backup_list = ft.ListView(
            spacing=5,
            padding=10,
            height=300,
        )
        self._refresh_backup_list()

        # Build dialog content
        content = ft.Column([
            # Header with stats
            ft.Container(
                content=ft.Column([
                    ft.Text("Local Backups", size=16, weight=ft.FontWeight.BOLD),
                    self.location_text,
                    self.stats_text,
                ], spacing=5),
                padding=10,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8,
            ),

            ft.Divider(),

            # Action buttons
            ft.Row([
                ft.ElevatedButton(
                    "Create Backup Now",
                    icon=ft.Icons.BACKUP,
                    on_click=self._on_create_backup,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.OutlinedButton(
                    "Change Location",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=self._on_change_location,
                ),
                ft.OutlinedButton(
                    "Refresh",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self._refresh_backup_list(),
                ),
            ], spacing=10),

            # Progress indicators
            self.progress_bar,
            self.progress_text,

            ft.Divider(),

            # Backup list
            ft.Text("Available Backups:", weight=ft.FontWeight.W_500),
            ft.Container(
                content=self.backup_list,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
            ),

            # Info text
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.BLUE_700),
                    ft.Text(
                        "Backups include your database, patient records, settings, and prescriptions. "
                        "Create regular backups to protect your data. Restore creates a safety backup first.",
                        size=11,
                        color=ft.Colors.GREY_700,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=5),
                padding=10,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=5,
            ),
        ], spacing=10, scroll=ft.ScrollMode.AUTO, tight=True)

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.BACKUP, color=ft.Colors.BLUE_700),
                ft.Text("Backup & Restore"),
            ], spacing=10),
            content=ft.Container(
                content=content,
                width=600,
                height=550,
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
        if not self.backup_list:
            return

        self.backup_list.controls.clear()
        backups = self.backup_service.list_backups()

        if not backups:
            self.backup_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OFF, size=40, color=ft.Colors.GREY_400),
                        ft.Text(
                            "No backups found",
                            size=14,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Text(
                            "Click 'Create Backup Now' to create your first backup",
                            size=11,
                            color=ft.Colors.GREY_400,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for backup in backups:
                self.backup_list.controls.append(
                    self._build_backup_tile(backup)
                )

        # Update stats
        if self.stats_text:
            stats = self.backup_service.get_backup_stats()
            self.stats_text.value = f"{stats['total_backups']} backups | {stats['total_size_mb']:.1f} MB total"

        if self.page:
            self.page.update()

    def _build_backup_tile(self, backup: SimpleBackupInfo) -> ft.Control:
        """Build a list tile for a backup."""
        # Format date
        date_str = backup.created_at.strftime("%Y-%m-%d %H:%M")

        # Calculate age
        age = datetime.now() - backup.created_at
        if age.total_seconds() < 3600:
            age_str = f"{int(age.total_seconds() / 60)} min ago"
        elif age.total_seconds() < 86400:
            age_str = f"{int(age.total_seconds() / 3600)} hr ago"
        else:
            age_str = f"{int(age.days)} day{'s' if age.days > 1 else ''} ago"

        # Format size
        size_mb = backup.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB"

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_ZIP, size=24, color=ft.Colors.BLUE_700),
                ft.Column([
                    ft.Text(
                        backup.folder_name,
                        size=13,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        f"{date_str} ({age_str}) | {size_str} | {backup.patient_count} patients, {backup.visit_count} visits",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.RESTORE,
                        tooltip="Restore this backup",
                        icon_size=20,
                        icon_color=ft.Colors.GREEN_700,
                        on_click=lambda e, b=backup: self._on_restore_backup(b),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Delete this backup",
                        icon_size=20,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, b=backup: self._on_delete_backup(b),
                    ),
                ], spacing=0),
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            border_radius=5,
            bgcolor=ft.Colors.GREY_100,
            on_hover=lambda e: self._on_tile_hover(e),
        )

    def _on_tile_hover(self, e):
        """Handle hover effect on backup tiles."""
        if e.data == "true":
            e.control.bgcolor = ft.Colors.GREY_200
        else:
            e.control.bgcolor = ft.Colors.GREY_100
        e.control.update()

    def _show_progress(self, message: str, percent: int = 0):
        """Show progress indicator."""
        if self.progress_bar and self.progress_text:
            self.progress_bar.visible = True
            self.progress_bar.value = percent / 100 if percent > 0 else None
            self.progress_text.visible = True
            self.progress_text.value = message
            if self.page:
                self.page.update()

    def _hide_progress(self):
        """Hide progress indicator."""
        if self.progress_bar and self.progress_text:
            self.progress_bar.visible = False
            self.progress_text.visible = False
            if self.page:
                self.page.update()

    def _on_create_backup(self, e):
        """Handle create backup button."""
        def do_backup():
            def progress_cb(message, percent):
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_progress(message, percent))

            try:
                backup_path = self.backup_service.create_backup(progress_callback=progress_cb)

                if self.page:
                    if backup_path:
                        self.page.run_thread_safe(lambda: self._show_snackbar(f"Backup created successfully!"))
                        self.page.run_thread_safe(self._refresh_backup_list)
                    else:
                        self.page.run_thread_safe(lambda: self._show_snackbar("Backup failed - check logs", error=True))
                    self.page.run_thread_safe(self._hide_progress)

            except Exception as ex:
                logger.error(f"Backup error: {ex}", exc_info=True)
                if self.page:
                    self.page.run_thread_safe(lambda: self._show_snackbar(f"Error: {ex}", error=True))
                    self.page.run_thread_safe(self._hide_progress)

        threading.Thread(target=do_backup, daemon=True).start()

    def _on_restore_backup(self, backup: SimpleBackupInfo):
        """Handle restore backup with confirmation."""
        def do_restore(e):
            confirm_dialog.open = False
            self.page.update()

            def restore_thread():
                def progress_cb(message, percent):
                    if self.page:
                        self.page.run_thread_safe(lambda: self._show_progress(message, percent))

                try:
                    success = self.backup_service.restore_backup(
                        backup.path,
                        progress_callback=progress_cb
                    )

                    if self.page:
                        if success:
                            self.page.run_thread_safe(lambda: self._show_snackbar(
                                "Restore complete! Please restart the app to see changes."
                            ))
                        else:
                            self.page.run_thread_safe(lambda: self._show_snackbar(
                                "Restore failed - check logs", error=True
                            ))
                        self.page.run_thread_safe(self._hide_progress)

                except Exception as ex:
                    logger.error(f"Restore error: {ex}", exc_info=True)
                    if self.page:
                        self.page.run_thread_safe(lambda: self._show_snackbar(f"Error: {ex}", error=True))
                        self.page.run_thread_safe(self._hide_progress)

            threading.Thread(target=restore_thread, daemon=True).start()

        # Confirmation dialog
        confirm_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700),
                ft.Text("Confirm Restore"),
            ], spacing=10),
            content=ft.Column([
                ft.Text(
                    f"Restore from backup '{backup.folder_name}'?",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"Created: {backup.created_at.strftime('%Y-%m-%d %H:%M')}",
                    size=12,
                ),
                ft.Text(
                    f"Contains: {backup.patient_count} patients, {backup.visit_count} visits",
                    size=12,
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Text(
                        "⚠️ Current data will be replaced! A safety backup will be created first.",
                        size=12,
                        color=ft.Colors.ORANGE_700,
                    ),
                    padding=10,
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=5,
                ),
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm(confirm_dialog)),
                ft.ElevatedButton(
                    "Restore",
                    on_click=do_restore,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ORANGE_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
        )
        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()

    def _on_delete_backup(self, backup: SimpleBackupInfo):
        """Handle delete backup with confirmation."""
        def do_delete(e):
            try:
                import shutil
                shutil.rmtree(backup.path)
                self._show_snackbar(f"Deleted: {backup.folder_name}")
                self._refresh_backup_list()
            except Exception as ex:
                logger.error(f"Delete error: {ex}", exc_info=True)
                self._show_snackbar(f"Delete failed: {ex}", error=True)
            confirm_dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete backup '{backup.folder_name}'? This cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm(confirm_dialog)),
                ft.ElevatedButton(
                    "Delete",
                    on_click=do_delete,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
        )
        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()

    def _on_change_location(self, e):
        """Handle change backup location."""
        def on_result(e: ft.FilePickerResultEvent):
            if e.path:
                try:
                    new_location = Path(e.path)
                    self.backup_service.set_backup_location(new_location)
                    self.location_text.value = f"Backup location: {new_location}"
                    self._show_snackbar(f"Backup location changed to: {new_location}")
                    self._refresh_backup_list()
                except Exception as ex:
                    logger.error(f"Change location error: {ex}", exc_info=True)
                    self._show_snackbar(f"Error: {ex}", error=True)

        file_picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.get_directory_path(dialog_title="Choose Backup Location")

    def _close_confirm(self, dialog):
        """Close confirmation dialog."""
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
        if self.on_close_callback:
            self.on_close_callback()


def show_simple_backup_dialog(page: ft.Page, backup_service: SimpleBackupService):
    """Show the simple backup dialog.

    Args:
        page: Flet page
        backup_service: SimpleBackupService instance
    """
    SimpleBackupDialog(page, backup_service)
