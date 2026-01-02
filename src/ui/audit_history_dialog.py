"""Audit history dialog to show changes to patient records."""

import flet as ft
from typing import Optional
from datetime import datetime

from ..services.database import DatabaseService
from ..models.schemas import Patient


class AuditHistoryDialog:
    """Dialog to display audit history for a patient."""

    def __init__(self, db: DatabaseService):
        self.db = db
        self.dialog: Optional[ft.AlertDialog] = None
        self.history_list: Optional[ft.ListView] = None

    def show(self, page: ft.Page, patient: Patient):
        """Show audit history dialog for a patient."""
        # Get audit history
        audit_entries = self.db.get_patient_audit_history(patient.id)

        # Create history list
        self.history_list = ft.ListView(
            spacing=10,
            padding=10,
            expand=True,
            height=500,
        )

        if not audit_entries:
            self.history_list.controls.append(
                ft.Text(
                    "No audit history available",
                    color=ft.Colors.GREY_500,
                    italic=True
                )
            )
        else:
            for entry in audit_entries:
                card = self._create_audit_card(entry)
                self.history_list.controls.append(card)

        # Create dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_700),
                ft.Text(f"Audit History: {patient.name}", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=self.history_list,
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close(page)),
            ],
        )

        page.overlay.append(self.dialog)
        self.dialog.open = True
        page.update()

    def _create_audit_card(self, entry: dict) -> ft.Control:
        """Create a card for an audit entry."""
        # Parse timestamp
        timestamp_str = entry.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(timestamp_str)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp_str

        # Get operation details
        operation = entry.get('operation', '')
        table_name = entry.get('table_name', '')
        record_id = entry.get('record_id', '')

        # Color coding
        if operation == 'INSERT':
            color = ft.Colors.GREEN_700
            icon = ft.Icons.ADD_CIRCLE_OUTLINE
        elif operation == 'UPDATE':
            color = ft.Colors.ORANGE_700
            icon = ft.Icons.EDIT
        elif operation == 'DELETE':
            color = ft.Colors.RED_700
            icon = ft.Icons.DELETE_OUTLINE
        else:
            color = ft.Colors.GREY_700
            icon = ft.Icons.INFO_OUTLINE

        # Format table name
        table_display = table_name.upper()[:10]

        # Create content based on operation
        content_parts = []

        # Header row
        content_parts.append(
            ft.Row([
                ft.Icon(icon, color=color, size=20),
                ft.Text(formatted_time, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Container(
                    content=ft.Text(table_display, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=4,
                ),
                ft.Text(f"ID: {record_id}", size=11, color=ft.Colors.GREY_500),
            ], spacing=8)
        )

        # Show changes
        old_value = entry.get('old_value', {})
        new_value = entry.get('new_value', {})

        if operation == 'INSERT' and new_value:
            # Show created fields
            content_parts.append(ft.Text("Created:", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_700))
            for key, value in new_value.items():
                if value and key not in ['created_at', 'is_deleted']:
                    content_parts.append(
                        ft.Text(f"  {key}: {self._format_value(value)}", size=11, color=ft.Colors.GREY_700)
                    )

        elif operation == 'UPDATE' and old_value and new_value:
            # Show changed fields
            content_parts.append(ft.Text("Changed:", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.ORANGE_700))
            for key in new_value.keys():
                old_val = old_value.get(key)
                new_val = new_value.get(key)
                if old_val != new_val:
                    content_parts.append(
                        ft.Row([
                            ft.Text(f"  {key}:", size=11, weight=ft.FontWeight.W_500),
                            ft.Text(f"{self._format_value(old_val)}", size=11, color=ft.Colors.RED_600),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=ft.Colors.GREY_500),
                            ft.Text(f"{self._format_value(new_val)}", size=11, color=ft.Colors.GREEN_600),
                        ], spacing=5)
                    )

        elif operation == 'DELETE' and old_value:
            # Show deleted fields
            content_parts.append(ft.Text("Deleted:", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.RED_700))
            for key, value in old_value.items():
                if value and key not in ['created_at', 'is_deleted']:
                    content_parts.append(
                        ft.Text(f"  {key}: {self._format_value(value)}", size=11, color=ft.Colors.GREY_700)
                    )

        return ft.Container(
            content=ft.Column(content_parts, spacing=5),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

    def _format_value(self, value) -> str:
        """Format a value for display."""
        if value is None:
            return "(empty)"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, str) and len(value) > 100:
            return value[:100] + "..."
        return str(value)

    def _close(self, page: ft.Page):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            page.update()
