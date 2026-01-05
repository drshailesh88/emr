"""Sync Conflict Dialog - Handle cloud/local data conflicts."""

import flet as ft
from typing import Optional, Callable, Dict, Any
from datetime import datetime


class SyncConflictDialog:
    """Dialog for resolving sync conflicts between cloud and local data."""

    def __init__(
        self,
        page: ft.Page,
        local_info: Dict[str, Any],
        cloud_info: Dict[str, Any],
        on_resolve: Optional[Callable[[str], None]] = None,
    ):
        """Initialize sync conflict dialog.

        Args:
            page: Flet page
            local_info: Information about local backup
            cloud_info: Information about cloud backup
            on_resolve: Callback when conflict is resolved ("local", "cloud", or "both")
        """
        self.page = page
        self.local_info = local_info
        self.cloud_info = cloud_info
        self.on_resolve = on_resolve

        # UI components
        self.dialog: Optional[ft.AlertDialog] = None

        # Build and show dialog
        self._build_dialog()

    def _build_dialog(self):
        """Build the conflict resolution dialog."""
        # Extract info
        local_date = self.local_info.get('modified', '')
        local_size = self.local_info.get('size', 0)
        local_patients = self.local_info.get('patient_count', 0)
        local_visits = self.local_info.get('visit_count', 0)

        cloud_date = self.cloud_info.get('modified', '')
        cloud_size = self.cloud_info.get('size', 0)
        cloud_patients = self.cloud_info.get('patient_count', 0)
        cloud_visits = self.cloud_info.get('visit_count', 0)

        # Format dates
        local_date_str = self._format_date(local_date)
        cloud_date_str = self._format_date(cloud_date)

        # Determine which is newer
        local_newer = False
        cloud_newer = False
        try:
            local_dt = datetime.fromisoformat(local_date.replace('Z', '+00:00'))
            cloud_dt = datetime.fromisoformat(cloud_date.replace('Z', '+00:00'))
            if local_dt > cloud_dt:
                local_newer = True
            else:
                cloud_newer = True
        except Exception:
            pass

        # Build comparison table
        comparison = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Property", weight=ft.FontWeight.BOLD, size=12)),
                ft.DataColumn(ft.Text(
                    "Local Data" + (" (Newer)" if local_newer else ""),
                    weight=ft.FontWeight.BOLD,
                    size=12,
                    color=ft.Colors.GREEN_700 if local_newer else None,
                )),
                ft.DataColumn(ft.Text(
                    "Cloud Data" + (" (Newer)" if cloud_newer else ""),
                    weight=ft.FontWeight.BOLD,
                    size=12,
                    color=ft.Colors.BLUE_700 if cloud_newer else None,
                )),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Last Modified", size=11)),
                    ft.DataCell(ft.Text(local_date_str, size=11)),
                    ft.DataCell(ft.Text(cloud_date_str, size=11)),
                ]),
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Size", size=11)),
                    ft.DataCell(ft.Text(self._format_size(local_size), size=11)),
                    ft.DataCell(ft.Text(self._format_size(cloud_size), size=11)),
                ]),
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Patients", size=11)),
                    ft.DataCell(ft.Text(str(local_patients) if local_patients else "N/A", size=11)),
                    ft.DataCell(ft.Text(str(cloud_patients) if cloud_patients else "N/A", size=11)),
                ]),
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Visits", size=11)),
                    ft.DataCell(ft.Text(str(local_visits) if local_visits else "N/A", size=11)),
                    ft.DataCell(ft.Text(str(cloud_visits) if cloud_visits else "N/A", size=11)),
                ]),
            ],
            heading_row_height=40,
            data_row_min_height=30,
        )

        # Action buttons
        use_local_button = ft.ElevatedButton(
            "Use Local Data",
            icon=ft.Icons.COMPUTER,
            on_click=lambda e: self._on_resolve("local"),
            tooltip="Keep local data, upload to cloud",
        )

        use_cloud_button = ft.ElevatedButton(
            "Use Cloud Data",
            icon=ft.Icons.CLOUD,
            on_click=lambda e: self._on_resolve("cloud"),
            tooltip="Download cloud data, replace local",
        )

        keep_both_button = ft.OutlinedButton(
            "Keep Both (Manual Merge)",
            icon=ft.Icons.MERGE_TYPE,
            on_click=lambda e: self._on_resolve("both"),
            tooltip="Keep local, download cloud as separate backup",
        )

        # Build dialog content
        content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SYNC_PROBLEM, color=ft.Colors.ORANGE_700, size=32),
                ft.Column([
                    ft.Text("Sync Conflict Detected", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Your local and cloud data differ. Choose which version to keep.",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ], spacing=5, expand=True),
            ], spacing=15),

            ft.Divider(),

            comparison,

            ft.Divider(),

            ft.Container(
                content=ft.Column([
                    ft.Text("What should I do?", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(
                        "• Use Local Data: Keep what's on this device, upload to cloud\n"
                        "• Use Cloud Data: Replace local with cloud backup (CAUTION: local changes will be lost)\n"
                        "• Keep Both: Download cloud backup separately for manual review",
                        size=11,
                        color=ft.Colors.GREY_700,
                    ),
                ], spacing=5),
                bgcolor=ft.Colors.BLUE_50,
                padding=15,
                border_radius=8,
            ),

            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=ft.Colors.GREEN_700, size=20),
                    ft.Text(
                        f"Recommendation: Use {'Local' if local_newer else 'Cloud'} Data (it's newer)",
                        size=12,
                        color=ft.Colors.GREEN_700,
                        weight=ft.FontWeight.BOLD,
                    ),
                ], spacing=10),
                bgcolor=ft.Colors.GREEN_50,
                padding=10,
                border_radius=8,
                visible=local_newer or cloud_newer,
            ),
        ], spacing=15, scroll=ft.ScrollMode.AUTO, width=600, height=500)

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SYNC_PROBLEM, color=ft.Colors.ORANGE_700),
                ft.Text("Resolve Sync Conflict"),
            ], spacing=10),
            content=content,
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                keep_both_button,
                use_cloud_button if cloud_newer else use_local_button,
                use_local_button if cloud_newer else use_cloud_button,
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Show dialog
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _format_date(self, date_str: str) -> str:
        """Format date string."""
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return "Unknown"
        except Exception:
            return date_str[:19] if len(date_str) >= 19 else date_str

    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _on_resolve(self, resolution: str):
        """Handle conflict resolution."""
        # Show confirmation dialog
        if resolution == "cloud":
            self._show_confirmation_dialog(
                "Replace Local Data?",
                "This will REPLACE your local data with the cloud backup. "
                "Any local changes will be LOST. Are you sure?",
                lambda: self._finish_resolve(resolution)
            )
        elif resolution == "local":
            self._show_confirmation_dialog(
                "Upload Local Data?",
                "This will upload your local data to the cloud, replacing the cloud backup. Continue?",
                lambda: self._finish_resolve(resolution)
            )
        else:
            # Keep both - no confirmation needed
            self._finish_resolve(resolution)

    def _show_confirmation_dialog(self, title: str, message: str, on_confirm: Callable):
        """Show confirmation dialog."""
        confirm_dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700, size=32),
                    ft.Text(message, size=13, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                width=350,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm(confirm_dialog)),
                ft.ElevatedButton(
                    "Yes, Continue",
                    on_click=lambda e: self._confirm_and_close(confirm_dialog, on_confirm),
                ),
            ],
        )
        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()

    def _close_confirm(self, dialog):
        """Close confirmation dialog."""
        dialog.open = False
        self.page.update()

    def _confirm_and_close(self, dialog, on_confirm):
        """Confirm and close dialog."""
        dialog.open = False
        self.page.update()
        on_confirm()

    def _finish_resolve(self, resolution: str):
        """Finish resolving conflict."""
        self.dialog.open = False
        self.page.update()

        # Show processing message
        self._show_snackbar(f"Resolving conflict using {resolution} data...")

        # Call callback
        if self.on_resolve:
            self.on_resolve(resolution)

    def _on_cancel(self, e):
        """Handle cancel button."""
        self.dialog.open = False
        self.page.update()

    def _show_snackbar(self, message: str, error: bool = False):
        """Show snackbar message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.BLUE_700,
        )
        self.page.snack_bar.open = True
        self.page.update()


def show_sync_conflict_dialog(
    page: ft.Page,
    local_info: Dict[str, Any],
    cloud_info: Dict[str, Any],
    on_resolve: Optional[Callable[[str], None]] = None,
):
    """Show sync conflict dialog.

    Args:
        page: Flet page
        local_info: Information about local backup
        cloud_info: Information about cloud backup
        on_resolve: Callback when conflict is resolved ("local", "cloud", or "both")
    """
    SyncConflictDialog(page, local_info, cloud_info, on_resolve)
