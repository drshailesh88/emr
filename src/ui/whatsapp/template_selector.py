"""Template selector for WhatsApp message templates."""

import flet as ft
from typing import Callable, Optional, Dict, List
from datetime import datetime, date
from ...services.whatsapp.templates import MessageTemplates


class TemplateSelector(ft.UserControl):
    """Template selector component for pre-approved WhatsApp templates."""

    def __init__(
        self,
        on_template_selected: Optional[Callable[[str, Dict], None]] = None,
        is_dark: bool = False
    ):
        """Initialize template selector.

        Args:
            on_template_selected: Callback when template is selected (template_name, params)
            is_dark: Dark mode flag
        """
        super().__init__()
        self.on_template_selected = on_template_selected
        self.is_dark = is_dark

        # State
        self.selected_template: Optional[str] = None
        self.template_params: Dict[str, str] = {}

        # UI components
        self.template_list: Optional[ft.ListView] = None
        self.params_panel: Optional[ft.Container] = None
        self.preview_panel: Optional[ft.Container] = None
        self.use_btn: Optional[ft.ElevatedButton] = None

    def build(self):
        """Build the template selector UI."""
        # Template list
        templates = [
            {
                "name": MessageTemplates.APPOINTMENT_REMINDER,
                "title": "Appointment Reminder",
                "description": "Remind patient about upcoming appointment",
                "icon": ft.Icons.CALENDAR_TODAY,
                "color": ft.Colors.BLUE_700
            },
            {
                "name": MessageTemplates.PRESCRIPTION_DELIVERY,
                "title": "Prescription Ready",
                "description": "Notify patient that prescription is ready",
                "icon": ft.Icons.MEDICATION,
                "color": ft.Colors.GREEN_700
            },
            {
                "name": MessageTemplates.FOLLOW_UP_REMINDER,
                "title": "Follow-up Reminder",
                "description": "Remind patient to schedule follow-up",
                "icon": ft.Icons.EVENT_REPEAT,
                "color": ft.Colors.PURPLE_700
            },
            {
                "name": MessageTemplates.LAB_RESULT_READY,
                "title": "Lab Results Ready",
                "description": "Notify patient that lab results are available",
                "icon": ft.Icons.SCIENCE,
                "color": ft.Colors.ORANGE_700
            },
        ]

        template_items = []
        for template in templates:
            template_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            template["icon"],
                            color=template["color"],
                            size=32
                        ),
                        ft.Column([
                            ft.Text(
                                template["title"],
                                size=14,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Text(
                                template["description"],
                                size=11,
                                color=ft.Colors.GREY_600
                            )
                        ], spacing=2, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD_IOS,
                            icon_size=16,
                            on_click=lambda e, t=template: self._on_template_click(t["name"])
                        )
                    ], spacing=10),
                    padding=15,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                    on_click=lambda e, t=template: self._on_template_click(t["name"])
                )
            )

        self.template_list = ft.ListView(
            controls=template_items,
            spacing=10,
            expand=True
        )

        # Parameters panel (initially hidden)
        self.params_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._on_back_click
                    ),
                    ft.Text(
                        "Fill Template Parameters",
                        size=16,
                        weight=ft.FontWeight.BOLD
                    )
                ]),
                ft.Divider(height=1),
                ft.Column(
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO
                )  # Param fields will be added here
            ]),
            visible=False
        )

        # Preview panel
        self.preview_panel = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Preview",
                    size=14,
                    weight=ft.FontWeight.W_500
                ),
                ft.Container(
                    content=ft.Text(
                        "Select a template to preview",
                        size=12,
                        color=ft.Colors.GREY_600,
                        selectable=True
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    bgcolor=ft.Colors.GREEN_50,
                    expand=True
                )
            ], spacing=5),
            visible=False
        )

        # Use template button
        self.use_btn = ft.ElevatedButton(
            "Use This Template",
            icon=ft.Icons.CHECK,
            on_click=self._on_use_template,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE
            )
        )

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Select Message Template",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(height=10),
                ft.Container(
                    content=ft.Column([
                        self.template_list,
                        self.params_panel,
                    ]),
                    expand=True
                ),
                self.preview_panel,
                self.use_btn,
            ], spacing=15),
            padding=20,
            expand=True
        )

    def _on_template_click(self, template_name: str):
        """Handle template selection."""
        self.selected_template = template_name

        # Hide list, show params
        self.template_list.visible = False
        self.params_panel.visible = True
        self.preview_panel.visible = True
        self.use_btn.visible = True

        # Build parameter fields
        params_column = self.params_panel.content.controls[2]
        params_column.controls.clear()

        param_fields = self._get_template_params(template_name)

        for field in param_fields:
            params_column.controls.append(
                ft.TextField(
                    label=field["label"],
                    hint_text=field["hint"],
                    value=field.get("default", ""),
                    on_change=lambda e, key=field["key"]: self._on_param_change(key, e.control.value)
                )
            )

        self._update_preview()
        self.update()

    def _on_back_click(self, e):
        """Handle back button click."""
        self.template_list.visible = True
        self.params_panel.visible = False
        self.preview_panel.visible = False
        self.use_btn.visible = False
        self.selected_template = None
        self.template_params.clear()
        self.update()

    def _on_param_change(self, key: str, value: str):
        """Handle parameter value change."""
        self.template_params[key] = value
        self._update_preview()

    def _on_use_template(self, e):
        """Handle use template button click."""
        if self.on_template_selected and self.selected_template:
            self.on_template_selected(self.selected_template, self.template_params)

    def _get_template_params(self, template_name: str) -> List[Dict]:
        """Get parameter fields for a template."""
        if template_name == MessageTemplates.APPOINTMENT_REMINDER:
            return [
                {"key": "patient_name", "label": "Patient Name", "hint": "e.g., Rajesh Kumar", "default": ""},
                {"key": "doctor_name", "label": "Doctor Name", "hint": "e.g., Dr. Kumar", "default": ""},
                {"key": "appointment_date", "label": "Appointment Date", "hint": "e.g., Monday, 15 January 2024", "default": ""},
                {"key": "appointment_time", "label": "Appointment Time", "hint": "e.g., 10:00 AM", "default": ""},
                {"key": "clinic_address", "label": "Clinic Address", "hint": "e.g., 123 Main Street", "default": ""},
            ]
        elif template_name == MessageTemplates.PRESCRIPTION_DELIVERY:
            return [
                {"key": "patient_name", "label": "Patient Name", "hint": "e.g., Rajesh Kumar", "default": ""},
                {"key": "doctor_name", "label": "Doctor Name", "hint": "e.g., Dr. Kumar", "default": ""},
                {"key": "visit_date", "label": "Visit Date", "hint": "e.g., 15 January 2024", "default": ""},
                {"key": "medication_summary", "label": "Medication Summary", "hint": "e.g., Metformin 500mg BD", "default": ""},
                {"key": "follow_up", "label": "Follow-up", "hint": "e.g., 2 weeks", "default": ""},
            ]
        elif template_name == MessageTemplates.FOLLOW_UP_REMINDER:
            return [
                {"key": "patient_name", "label": "Patient Name", "hint": "e.g., Rajesh Kumar", "default": ""},
                {"key": "doctor_name", "label": "Doctor Name", "hint": "e.g., Dr. Kumar", "default": ""},
                {"key": "due_date", "label": "Due Date", "hint": "e.g., 22 January 2024", "default": ""},
                {"key": "reason", "label": "Reason", "hint": "e.g., Check blood sugar levels", "default": ""},
            ]
        elif template_name == MessageTemplates.LAB_RESULT_READY:
            return [
                {"key": "patient_name", "label": "Patient Name", "hint": "e.g., Rajesh Kumar", "default": ""},
                {"key": "test_name", "label": "Test Name", "hint": "e.g., HbA1c, Lipid Profile", "default": ""},
                {"key": "clinic_name", "label": "Clinic Name", "hint": "e.g., Kumar Clinic", "default": ""},
            ]
        else:
            return []

    def _update_preview(self):
        """Update message preview."""
        if not self.selected_template:
            return

        # Generate preview text
        preview_text = self._generate_preview_text()

        # Update preview panel
        preview_container = self.preview_panel.content.controls[1]
        preview_container.content = ft.Text(
            preview_text,
            size=12,
            color=ft.Colors.BLACK,
            selectable=True
        )
        self.update()

    def _generate_preview_text(self) -> str:
        """Generate preview text for current template and params."""
        if not self.selected_template:
            return "No template selected"

        # This is a simplified preview - actual WhatsApp templates may have different formatting
        if self.selected_template == MessageTemplates.APPOINTMENT_REMINDER:
            return f"""Dear {self.template_params.get('patient_name', '[Patient Name]')},

This is a reminder for your appointment with {self.template_params.get('doctor_name', '[Doctor Name]')}.

📅 Date: {self.template_params.get('appointment_date', '[Appointment Date]')}
🕐 Time: {self.template_params.get('appointment_time', '[Appointment Time]')}
📍 Location: {self.template_params.get('clinic_address', '[Clinic Address]')}

Please arrive 10 minutes early. If you need to reschedule, please contact us.

Thank you!"""

        elif self.selected_template == MessageTemplates.PRESCRIPTION_DELIVERY:
            return f"""Dear {self.template_params.get('patient_name', '[Patient Name]')},

Your prescription from your visit on {self.template_params.get('visit_date', '[Visit Date]')} with {self.template_params.get('doctor_name', '[Doctor Name]')} is ready.

💊 Medications: {self.template_params.get('medication_summary', '[Medication Summary]')}

📋 Follow-up: {self.template_params.get('follow_up', '[Follow-up]')}

Please collect your prescription from the clinic or we can arrange delivery.

Get well soon!"""

        elif self.selected_template == MessageTemplates.FOLLOW_UP_REMINDER:
            return f"""Dear {self.template_params.get('patient_name', '[Patient Name]')},

This is a reminder to schedule your follow-up visit with {self.template_params.get('doctor_name', '[Doctor Name]')}.

📅 Due Date: {self.template_params.get('due_date', '[Due Date]')}
📝 Reason: {self.template_params.get('reason', '[Reason]')}

Please contact us to book your appointment.

Take care!"""

        elif self.selected_template == MessageTemplates.LAB_RESULT_READY:
            return f"""Dear {self.template_params.get('patient_name', '[Patient Name]')},

Your test results are ready!

🧪 Tests: {self.template_params.get('test_name', '[Test Name]')}

Please visit {self.template_params.get('clinic_name', '[Clinic Name]')} to collect your reports and discuss with the doctor.

Thank you!"""

        return "Preview not available"


class TemplateSelectionDialog:
    """Dialog for selecting and filling WhatsApp message templates."""

    def __init__(
        self,
        page: ft.Page,
        on_template_selected: Optional[Callable[[str, Dict], None]] = None
    ):
        """Initialize template selection dialog.

        Args:
            page: Flet page
            on_template_selected: Callback when template is selected
        """
        self.page = page
        self.on_template_selected = on_template_selected
        self.dialog: Optional[ft.AlertDialog] = None

    def show(self):
        """Show the template selection dialog."""
        selector = TemplateSelector(
            on_template_selected=self._on_template_selected
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("WhatsApp Message Templates"),
            content=ft.Container(
                content=selector,
                width=500,
                height=600,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self._close_dialog()
                ),
            ]
        )

        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _on_template_selected(self, template_name: str, params: Dict):
        """Handle template selection."""
        if self.on_template_selected:
            self.on_template_selected(template_name, params)
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            self.page.update()


def show_template_selector(
    page: ft.Page,
    on_template_selected: Optional[Callable[[str, Dict], None]] = None
):
    """Show template selector dialog.

    Args:
        page: Flet page
        on_template_selected: Callback when template is selected (template_name, params)
    """
    dialog = TemplateSelectionDialog(
        page=page,
        on_template_selected=on_template_selected
    )
    dialog.show()
