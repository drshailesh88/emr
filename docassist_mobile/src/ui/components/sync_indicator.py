"""Sync Indicator Component - Shows sync status."""

import flet as ft
from ..tokens import Colors, MobileSpacing, MobileTypography


class SyncIndicator(ft.Container):
    """Sync status indicator widget."""

    def __init__(
        self,
        status: str = "synced",  # synced, syncing, error, offline
        last_sync: str = "Just now",
    ):
        # Icon and color based on status
        if status == "synced":
            icon = ft.Icons.CHECK_CIRCLE
            color = Colors.SUCCESS_MAIN
            text = f"Synced {last_sync}"
        elif status == "syncing":
            icon = ft.Icons.SYNC
            color = Colors.PRIMARY_500
            text = "Syncing..."
        elif status == "error":
            icon = ft.Icons.ERROR
            color = Colors.ERROR_MAIN
            text = "Sync failed"
        else:  # offline
            icon = ft.Icons.CLOUD_OFF
            color = Colors.NEUTRAL_500
            text = "Offline"

        content = ft.Row(
            [
                ft.Icon(icon, size=16, color=color),
                ft.Text(
                    text,
                    size=MobileTypography.CAPTION,
                    color=Colors.NEUTRAL_600,
                ),
            ],
            spacing=MobileSpacing.XXS,
        )

        super().__init__(
            content=content,
            padding=ft.padding.symmetric(
                horizontal=MobileSpacing.MD,
                vertical=MobileSpacing.XS,
            ),
        )
