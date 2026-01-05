"""Cloud Status Panel - Shows cloud sync status and quick actions."""

import flet as ft
from typing import Optional, Callable
from datetime import datetime, timedelta
import threading

from ...services.settings import SettingsService


class CloudStatusPanel(ft.Container):
    """Panel showing cloud sync status."""

    def __init__(
        self,
        settings_service: SettingsService,
        cloud_backup_manager=None,
        on_sync_click: Optional[Callable] = None,
        on_settings_click: Optional[Callable] = None,
    ):
        """Initialize cloud status panel.

        Args:
            settings_service: Settings service instance
            cloud_backup_manager: CloudBackupManager instance
            on_sync_click: Callback when sync button clicked
            on_settings_click: Callback when settings button clicked
        """
        self.settings_service = settings_service
        self.cloud_backup_manager = cloud_backup_manager
        self.on_sync_click = on_sync_click
        self.on_settings_click = on_settings_click

        # Build UI
        self._build_panel()

        # Initialize container
        super().__init__(
            content=self.panel_content,
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_panel(self):
        """Build the status panel UI."""
        backup_settings = self.settings_service.get_backup_settings()

        # Check if cloud sync is configured
        if not backup_settings.cloud_sync_enabled or not backup_settings.cloud_config:
            self.panel_content = self._build_not_configured()
        else:
            self.panel_content = self._build_status_view()

    def _build_not_configured(self) -> ft.Control:
        """Build view when cloud sync is not configured."""
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CLOUD_OFF, color=ft.Colors.GREY_400, size=24),
                ft.Text("Cloud Backup Not Configured", weight=ft.FontWeight.BOLD),
            ], spacing=10),
            ft.Text(
                "Set up cloud backup to sync your data across devices and protect against data loss.",
                size=12,
                color=ft.Colors.GREY_600,
            ),
            ft.ElevatedButton(
                "Set Up Cloud Backup",
                icon=ft.Icons.CLOUD_UPLOAD,
                on_click=lambda e: self._on_setup_click(),
            ),
        ], spacing=10)

    def _build_status_view(self) -> ft.Control:
        """Build status view when cloud sync is configured."""
        backup_settings = self.settings_service.get_backup_settings()

        # Get provider name
        provider = backup_settings.cloud_backend_type
        provider_names = {
            'docassist': 'DocAssist Cloud',
            's3': 'Amazon S3',
            'gdrive': 'Google Drive',
            'local': 'Local Network',
        }
        provider_name = provider_names.get(provider, provider.upper())

        # Sync status
        self.sync_status_icon = ft.Icon(ft.Icons.CLOUD_QUEUE, color=ft.Colors.GREY_600, size=20)
        self.sync_status_text = ft.Text("Checking...", size=12, color=ft.Colors.GREY_600)

        # Last sync time
        self.last_sync_text = ft.Text("Never synced", size=11, color=ft.Colors.GREY_500)

        # Storage usage (if available)
        self.storage_progress = ft.ProgressBar(value=0, width=200, visible=False)
        self.storage_text = ft.Text("", size=11, color=ft.Colors.GREY_600, visible=False)

        # Action buttons
        self.sync_button = ft.IconButton(
            icon=ft.Icons.SYNC,
            tooltip="Sync Now",
            icon_size=20,
            on_click=lambda e: self._on_sync_now(),
        )

        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="Cloud Settings",
            icon_size=20,
            on_click=lambda e: self._on_settings(),
        )

        # Build layout
        content = ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.CLOUD, color=ft.Colors.BLUE_700, size=24),
                ft.Column([
                    ft.Text("Cloud Backup", weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(provider_name, size=11, color=ft.Colors.GREY_600),
                ], spacing=0, expand=True),
                self.sync_button,
                self.settings_button,
            ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Divider(height=5),

            # Status
            ft.Row([
                self.sync_status_icon,
                self.sync_status_text,
            ], spacing=8),

            # Last sync
            ft.Row([
                ft.Icon(ft.Icons.SCHEDULE, size=16, color=ft.Colors.GREY_400),
                self.last_sync_text,
            ], spacing=8),

            # Storage usage (if available)
            self.storage_progress,
            self.storage_text,
        ], spacing=8)

        # Start status update
        self._update_status()

        return content

    def _update_status(self):
        """Update sync status."""
        if not self.cloud_backup_manager:
            # Try to get status from settings
            self._update_from_settings()
            return

        def do_update():
            try:
                status = self.cloud_backup_manager.get_sync_status()

                # Update UI on main thread
                if hasattr(self, 'sync_status_text'):
                    def update():
                        # Status icon and text
                        if status.get('syncing'):
                            self.sync_status_icon.name = ft.Icons.CLOUD_SYNC
                            self.sync_status_icon.color = ft.Colors.BLUE_700
                            self.sync_status_text.value = "Syncing..."
                            self.sync_status_text.color = ft.Colors.BLUE_700
                        elif status.get('error'):
                            self.sync_status_icon.name = ft.Icons.CLOUD_OFF
                            self.sync_status_icon.color = ft.Colors.RED_700
                            self.sync_status_text.value = "Sync Error"
                            self.sync_status_text.color = ft.Colors.RED_700
                        else:
                            self.sync_status_icon.name = ft.Icons.CLOUD_DONE
                            self.sync_status_icon.color = ft.Colors.GREEN_700
                            self.sync_status_text.value = "Synced"
                            self.sync_status_text.color = ft.Colors.GREEN_700

                        # Last sync time
                        if status.get('last_sync_time'):
                            last_sync = status['last_sync_time']
                            now = datetime.now()
                            delta = now - last_sync

                            if delta < timedelta(minutes=1):
                                self.last_sync_text.value = "Just now"
                            elif delta < timedelta(hours=1):
                                mins = int(delta.total_seconds() / 60)
                                self.last_sync_text.value = f"{mins} minute{'s' if mins != 1 else ''} ago"
                            elif delta < timedelta(days=1):
                                hours = int(delta.total_seconds() / 3600)
                                self.last_sync_text.value = f"{hours} hour{'s' if hours != 1 else ''} ago"
                            else:
                                days = delta.days
                                self.last_sync_text.value = f"{days} day{'s' if days != 1 else ''} ago"
                        else:
                            self.last_sync_text.value = "Never synced"

                        # Storage usage
                        if status.get('storage_used') is not None and status.get('storage_quota') is not None:
                            used = status['storage_used']
                            quota = status['storage_quota']
                            percent = (used / quota * 100) if quota > 0 else 0

                            self.storage_progress.value = percent / 100
                            self.storage_progress.visible = True

                            # Format bytes
                            def format_bytes(b):
                                if b < 1024:
                                    return f"{b} B"
                                elif b < 1024 * 1024:
                                    return f"{b / 1024:.1f} KB"
                                elif b < 1024 * 1024 * 1024:
                                    return f"{b / (1024 * 1024):.1f} MB"
                                else:
                                    return f"{b / (1024 * 1024 * 1024):.1f} GB"

                            self.storage_text.value = f"{format_bytes(used)} / {format_bytes(quota)} ({percent:.1f}%)"
                            self.storage_text.visible = True

                        self.update()

                    # Run on main thread if page is available
                    if hasattr(self, 'page') and self.page:
                        self.page.run_thread_safe(update)
                    else:
                        update()

            except Exception as ex:
                print(f"Error updating cloud status: {ex}")

        threading.Thread(target=do_update, daemon=True).start()

    def _update_from_settings(self):
        """Update status from settings (fallback when manager not available)."""
        # Just show configured status
        if hasattr(self, 'sync_status_text'):
            self.sync_status_icon.name = ft.Icons.CLOUD
            self.sync_status_icon.color = ft.Colors.BLUE_700
            self.sync_status_text.value = "Configured"
            self.sync_status_text.color = ft.Colors.BLUE_700
            self.update()

    def _on_sync_now(self):
        """Handle sync now button."""
        if self.on_sync_click:
            self.on_sync_click()
        elif self.cloud_backup_manager:
            # Trigger sync
            def do_sync():
                try:
                    self.cloud_backup_manager.sync_now()
                    # Refresh status after sync
                    self._update_status()
                except Exception as ex:
                    print(f"Sync error: {ex}")

            threading.Thread(target=do_sync, daemon=True).start()

    def _on_settings(self):
        """Handle settings button."""
        if self.on_settings_click:
            self.on_settings_click()

    def _on_setup_click(self):
        """Handle setup button."""
        if self.on_settings_click:
            self.on_settings_click()

    def refresh(self):
        """Refresh the status panel."""
        self._build_panel()
        self.content = self.panel_content
        self.update()

    def start_auto_refresh(self, interval_seconds: int = 30):
        """Start auto-refresh of status.

        Args:
            interval_seconds: Refresh interval in seconds
        """
        def refresh_loop():
            import time
            while True:
                time.sleep(interval_seconds)
                if hasattr(self, 'page') and self.page:
                    self.page.run_thread_safe(self._update_status)
                else:
                    self._update_status()

        threading.Thread(target=refresh_loop, daemon=True).start()
