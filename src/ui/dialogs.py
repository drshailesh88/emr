"""Reusable dialog components for the EMR application."""

import flet as ft
from typing import Callable, Optional
from datetime import date


class ConfirmationDialog:
    """Reusable confirmation dialog with warning styling."""

    @staticmethod
    def show(
        page: ft.Page,
        title: str,
        message: str,
        on_confirm: Callable,
        confirm_text: str = "Delete",
        cancel_text: str = "Cancel",
        is_destructive: bool = True
    ):
        """Show a confirmation dialog.

        Args:
            page: The Flet page to show the dialog on
            title: Dialog title
            message: Confirmation message
            on_confirm: Callback function when confirmed
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            is_destructive: If True, uses red/warning styling
        """
        def close_dialog(e):
            dialog.open = False
            page.update()

        def confirm_and_close(e):
            dialog.open = False
            page.update()
            on_confirm()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(
                    ft.Icons.WARNING_AMBER_ROUNDED if is_destructive else ft.Icons.HELP_OUTLINE,
                    color=ft.Colors.RED_700 if is_destructive else ft.Colors.BLUE_700
                ),
                ft.Text(title, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Text(message, size=14),
                width=400,
            ),
            actions=[
                ft.TextButton(cancel_text, on_click=close_dialog),
                ft.ElevatedButton(
                    confirm_text,
                    on_click=confirm_and_close,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_700 if is_destructive else ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()


class EditInvestigationDialog:
    """Dialog for editing an investigation."""

    @staticmethod
    def show(
        page: ft.Page,
        investigation: Optional[dict],
        patient_id: int,
        on_save: Callable[[dict], None]
    ):
        """Show edit investigation dialog.

        Args:
            page: The Flet page
            investigation: Existing investigation data or None for new
            patient_id: Patient ID
            on_save: Callback with investigation data
        """
        is_new = investigation is None

        # Initialize fields
        test_name_field = ft.TextField(
            label="Test Name *",
            value=investigation.get("test_name", "") if investigation else "",
            autofocus=True
        )
        result_field = ft.TextField(
            label="Result",
            value=investigation.get("result", "") if investigation else ""
        )
        unit_field = ft.TextField(
            label="Unit",
            value=investigation.get("unit", "") if investigation else "",
            width=150
        )
        reference_field = ft.TextField(
            label="Reference Range",
            value=investigation.get("reference_range", "") if investigation else "",
            width=200
        )

        # Test date picker
        test_date_value = investigation.get("test_date") if investigation else date.today()
        if isinstance(test_date_value, str):
            test_date_value = date.fromisoformat(test_date_value)

        test_date_field = ft.TextField(
            label="Test Date",
            value=str(test_date_value),
            read_only=True,
            width=150
        )

        def pick_date(e):
            def on_date_change(e):
                if date_picker.value:
                    test_date_field.value = str(date_picker.value.date())
                    page.update()

            date_picker = ft.DatePicker(
                on_change=on_date_change,
                value=test_date_value
            )
            page.overlay.append(date_picker)
            date_picker.open = True
            page.update()

        date_button = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=pick_date,
            tooltip="Pick date"
        )

        is_abnormal_checkbox = ft.Checkbox(
            label="Abnormal",
            value=investigation.get("is_abnormal", False) if investigation else False
        )

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def save_investigation(e):
            if not test_name_field.value.strip():
                error_text.value = "Test name is required"
                page.update()
                return

            inv_data = {
                "patient_id": patient_id,
                "test_name": test_name_field.value.strip(),
                "result": result_field.value.strip(),
                "unit": unit_field.value.strip(),
                "reference_range": reference_field.value.strip(),
                "test_date": test_date_field.value,
                "is_abnormal": is_abnormal_checkbox.value,
            }

            if not is_new:
                inv_data["id"] = investigation["id"]

            dialog.open = False
            page.update()
            on_save(inv_data)

        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Investigation" if is_new else "Edit Investigation"),
            content=ft.Container(
                content=ft.Column([
                    test_name_field,
                    result_field,
                    ft.Row([unit_field, reference_field], spacing=10),
                    ft.Row([test_date_field, date_button], spacing=10),
                    is_abnormal_checkbox,
                    error_text,
                ], spacing=15, tight=True),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Save", on_click=save_investigation),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()


class EditProcedureDialog:
    """Dialog for editing a procedure."""

    @staticmethod
    def show(
        page: ft.Page,
        procedure: Optional[dict],
        patient_id: int,
        on_save: Callable[[dict], None]
    ):
        """Show edit procedure dialog.

        Args:
            page: The Flet page
            procedure: Existing procedure data or None for new
            patient_id: Patient ID
            on_save: Callback with procedure data
        """
        is_new = procedure is None

        # Initialize fields
        procedure_name_field = ft.TextField(
            label="Procedure Name *",
            value=procedure.get("procedure_name", "") if procedure else "",
            autofocus=True
        )
        details_field = ft.TextField(
            label="Details",
            value=procedure.get("details", "") if procedure else "",
            multiline=True,
            min_lines=2,
            max_lines=4
        )
        notes_field = ft.TextField(
            label="Notes",
            value=procedure.get("notes", "") if procedure else "",
            multiline=True,
            min_lines=2,
            max_lines=4
        )

        # Procedure date picker
        procedure_date_value = procedure.get("procedure_date") if procedure else date.today()
        if isinstance(procedure_date_value, str):
            procedure_date_value = date.fromisoformat(procedure_date_value)

        procedure_date_field = ft.TextField(
            label="Procedure Date",
            value=str(procedure_date_value),
            read_only=True,
            width=150
        )

        def pick_date(e):
            def on_date_change(e):
                if date_picker.value:
                    procedure_date_field.value = str(date_picker.value.date())
                    page.update()

            date_picker = ft.DatePicker(
                on_change=on_date_change,
                value=procedure_date_value
            )
            page.overlay.append(date_picker)
            date_picker.open = True
            page.update()

        date_button = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=pick_date,
            tooltip="Pick date"
        )

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def save_procedure(e):
            if not procedure_name_field.value.strip():
                error_text.value = "Procedure name is required"
                page.update()
                return

            proc_data = {
                "patient_id": patient_id,
                "procedure_name": procedure_name_field.value.strip(),
                "details": details_field.value.strip(),
                "procedure_date": procedure_date_field.value,
                "notes": notes_field.value.strip(),
            }

            if not is_new:
                proc_data["id"] = procedure["id"]

            dialog.open = False
            page.update()
            on_save(proc_data)

        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Procedure" if is_new else "Edit Procedure"),
            content=ft.Container(
                content=ft.Column([
                    procedure_name_field,
                    ft.Row([procedure_date_field, date_button], spacing=10),
                    details_field,
                    notes_field,
                    error_text,
                ], spacing=15, tight=True),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Save", on_click=save_procedure),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()
