"""Reusable dialog components for the EMR application with premium styling."""

import flet as ft
from typing import Callable, Optional
from datetime import date

from .tokens import Colors, Typography, Spacing, Radius, Motion


class ConfirmationDialog:
    """Premium confirmation dialog with warning styling."""

    @staticmethod
    def show(
        page: ft.Page,
        title: str,
        message: str,
        on_confirm: Callable,
        confirm_text: str = "Delete",
        cancel_text: str = "Cancel",
        is_destructive: bool = True,
        is_dark: bool = False,
    ):
        """Show a premium confirmation dialog.

        Args:
            page: The Flet page to show the dialog on
            title: Dialog title
            message: Confirmation message
            on_confirm: Callback function when confirmed
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            is_destructive: If True, uses red/warning styling
            is_dark: Dark mode flag
        """
        def close_dialog(e):
            dialog.open = False
            page.update()

        def confirm_and_close(e):
            dialog.open = False
            page.update()
            on_confirm()

        # Icon and colors
        icon = ft.Icons.WARNING_ROUNDED if is_destructive else ft.Icons.HELP_OUTLINE
        icon_color = Colors.ERROR_MAIN if is_destructive else Colors.PRIMARY_500

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=22),
                    width=36,
                    height=36,
                    bgcolor=Colors.ERROR_LIGHT if is_destructive else Colors.PRIMARY_50,
                    border_radius=Radius.MD,
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    title,
                    size=Typography.TITLE_MEDIUM.size,
                    weight=ft.FontWeight.W_600,
                    color=Colors.NEUTRAL_900 if not is_dark else Colors.NEUTRAL_100,
                ),
            ], spacing=Spacing.SM),
            title_padding=ft.padding.all(Spacing.LG),
            content=ft.Container(
                content=ft.Text(
                    message,
                    size=Typography.BODY_MEDIUM.size,
                    color=Colors.NEUTRAL_700 if not is_dark else Colors.NEUTRAL_300,
                ),
                width=420,
                padding=ft.padding.symmetric(horizontal=Spacing.LG),
            ),
            content_padding=ft.padding.only(bottom=Spacing.MD),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=close_dialog,
                    style=ft.ButtonStyle(
                        color=Colors.NEUTRAL_600,
                        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
                    ),
                ),
                ft.ElevatedButton(
                    confirm_text,
                    on_click=confirm_and_close,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.ERROR_MAIN if is_destructive else Colors.PRIMARY_500,
                        color=Colors.NEUTRAL_0,
                        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.SM),
                        animation_duration=Motion.FAST,
                    ),
                ),
            ],
            actions_padding=ft.padding.all(Spacing.MD),
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
            bgcolor=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()


def _create_premium_field(
    label: str,
    value: str = "",
    width: Optional[int] = None,
    multiline: bool = False,
    min_lines: int = 1,
    max_lines: int = 1,
    read_only: bool = False,
    autofocus: bool = False,
    is_dark: bool = False,
) -> ft.TextField:
    """Create a premium styled text field for dialogs."""
    return ft.TextField(
        label=label,
        value=value,
        width=width,
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines,
        read_only=read_only,
        autofocus=autofocus,
        text_size=Typography.BODY_MEDIUM.size,
        label_style=ft.TextStyle(
            size=Typography.LABEL_MEDIUM.size,
            color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
        ),
        border_radius=Radius.INPUT,
        border_color=Colors.NEUTRAL_300 if not is_dark else Colors.NEUTRAL_600,
        focused_border_color=Colors.PRIMARY_500,
        focused_border_width=2,
        cursor_color=Colors.PRIMARY_500,
        content_padding=ft.padding.all(Spacing.INPUT_PADDING),
    )


class EditInvestigationDialog:
    """Premium dialog for editing an investigation."""

    @staticmethod
    def show(
        page: ft.Page,
        investigation: Optional[dict],
        patient_id: int,
        on_save: Callable[[dict], None],
        is_dark: bool = False,
    ):
        """Show edit investigation dialog.

        Args:
            page: The Flet page
            investigation: Existing investigation data or None for new
            patient_id: Patient ID
            on_save: Callback with investigation data
            is_dark: Dark mode flag
        """
        is_new = investigation is None

        # Initialize fields with premium styling
        test_name_field = _create_premium_field(
            label="Test Name *",
            value=investigation.get("test_name", "") if investigation else "",
            autofocus=True,
            is_dark=is_dark,
        )
        result_field = _create_premium_field(
            label="Result",
            value=investigation.get("result", "") if investigation else "",
            is_dark=is_dark,
        )
        unit_field = _create_premium_field(
            label="Unit",
            value=investigation.get("unit", "") if investigation else "",
            width=150,
            is_dark=is_dark,
        )
        reference_field = _create_premium_field(
            label="Reference Range",
            value=investigation.get("reference_range", "") if investigation else "",
            width=200,
            is_dark=is_dark,
        )

        # Test date picker
        test_date_value = investigation.get("test_date") if investigation else date.today()
        if isinstance(test_date_value, str):
            test_date_value = date.fromisoformat(test_date_value)

        test_date_field = _create_premium_field(
            label="Test Date",
            value=str(test_date_value),
            read_only=True,
            width=150,
            is_dark=is_dark,
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
            icon_color=Colors.PRIMARY_500,
            on_click=pick_date,
            tooltip="Pick date",
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_50,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            ),
        )

        is_abnormal_checkbox = ft.Checkbox(
            label="Mark as Abnormal",
            value=investigation.get("is_abnormal", False) if investigation else False,
            active_color=Colors.ERROR_MAIN,
        )

        error_text = ft.Text("", color=Colors.ERROR_MAIN, size=Typography.BODY_SMALL.size)

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
            modal=True,
            title=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.SCIENCE, color=Colors.PRIMARY_500, size=20),
                    width=36,
                    height=36,
                    bgcolor=Colors.PRIMARY_50,
                    border_radius=Radius.MD,
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    "Add Investigation" if is_new else "Edit Investigation",
                    size=Typography.TITLE_MEDIUM.size,
                    weight=ft.FontWeight.W_600,
                    color=Colors.NEUTRAL_900 if not is_dark else Colors.NEUTRAL_100,
                ),
            ], spacing=Spacing.SM),
            title_padding=ft.padding.all(Spacing.LG),
            content=ft.Container(
                content=ft.Column([
                    test_name_field,
                    result_field,
                    ft.Row([unit_field, reference_field], spacing=Spacing.SM),
                    ft.Row([test_date_field, date_button], spacing=Spacing.XS, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    is_abnormal_checkbox,
                    error_text,
                ], spacing=Spacing.MD, tight=True),
                width=500,
                padding=ft.padding.symmetric(horizontal=Spacing.LG),
            ),
            content_padding=ft.padding.only(bottom=Spacing.MD),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(
                        color=Colors.NEUTRAL_600,
                        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
                    ),
                ),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_investigation,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.PRIMARY_500,
                        color=Colors.NEUTRAL_0,
                        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.SM),
                        animation_duration=Motion.FAST,
                    ),
                ),
            ],
            actions_padding=ft.padding.all(Spacing.MD),
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
            bgcolor=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()


class EditProcedureDialog:
    """Premium dialog for editing a procedure."""

    @staticmethod
    def show(
        page: ft.Page,
        procedure: Optional[dict],
        patient_id: int,
        on_save: Callable[[dict], None],
        is_dark: bool = False,
    ):
        """Show edit procedure dialog.

        Args:
            page: The Flet page
            procedure: Existing procedure data or None for new
            patient_id: Patient ID
            on_save: Callback with procedure data
            is_dark: Dark mode flag
        """
        is_new = procedure is None

        # Initialize fields with premium styling
        procedure_name_field = _create_premium_field(
            label="Procedure Name *",
            value=procedure.get("procedure_name", "") if procedure else "",
            autofocus=True,
            is_dark=is_dark,
        )
        details_field = _create_premium_field(
            label="Details",
            value=procedure.get("details", "") if procedure else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            is_dark=is_dark,
        )
        notes_field = _create_premium_field(
            label="Notes",
            value=procedure.get("notes", "") if procedure else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            is_dark=is_dark,
        )

        # Procedure date picker
        procedure_date_value = procedure.get("procedure_date") if procedure else date.today()
        if isinstance(procedure_date_value, str):
            procedure_date_value = date.fromisoformat(procedure_date_value)

        procedure_date_field = _create_premium_field(
            label="Procedure Date",
            value=str(procedure_date_value),
            read_only=True,
            width=150,
            is_dark=is_dark,
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
            icon_color=Colors.PRIMARY_500,
            on_click=pick_date,
            tooltip="Pick date",
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_50,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            ),
        )

        error_text = ft.Text("", color=Colors.ERROR_MAIN, size=Typography.BODY_SMALL.size)

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
            modal=True,
            title=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.MEDICAL_SERVICES, color=Colors.PRIMARY_500, size=20),
                    width=36,
                    height=36,
                    bgcolor=Colors.PRIMARY_50,
                    border_radius=Radius.MD,
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    "Add Procedure" if is_new else "Edit Procedure",
                    size=Typography.TITLE_MEDIUM.size,
                    weight=ft.FontWeight.W_600,
                    color=Colors.NEUTRAL_900 if not is_dark else Colors.NEUTRAL_100,
                ),
            ], spacing=Spacing.SM),
            title_padding=ft.padding.all(Spacing.LG),
            content=ft.Container(
                content=ft.Column([
                    procedure_name_field,
                    ft.Row([procedure_date_field, date_button], spacing=Spacing.XS, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    details_field,
                    notes_field,
                    error_text,
                ], spacing=Spacing.MD, tight=True),
                width=500,
                padding=ft.padding.symmetric(horizontal=Spacing.LG),
            ),
            content_padding=ft.padding.only(bottom=Spacing.MD),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(
                        color=Colors.NEUTRAL_600,
                        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
                    ),
                ),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_procedure,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.PRIMARY_500,
                        color=Colors.NEUTRAL_0,
                        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.SM),
                        animation_duration=Motion.FAST,
                    ),
                ),
            ],
            actions_padding=ft.padding.all(Spacing.MD),
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
            bgcolor=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()
