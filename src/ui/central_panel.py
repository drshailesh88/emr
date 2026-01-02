"""Central panel - Main content area with prescription form."""

import flet as ft
from typing import Callable, Optional, List
import json
from datetime import date

from ..models.schemas import Patient, Visit, Prescription, Medication, Investigation, Procedure
from ..services.llm import LLMService
from ..services.database import DatabaseService
from .audit_history_dialog import AuditHistoryDialog
from .dialogs import ConfirmationDialog, EditInvestigationDialog, EditProcedureDialog
from .components.expandable_text import ExpandableTextField, ExpandableTextArea
from .components.drug_autocomplete import DrugAutocomplete
from .template_browser import TemplateBrowser, SaveTemplateDialog
from .lab_trends_dialog import LabTrendsDialog
from ..services.reference_ranges import TREND_PANELS, get_reference_range
from ..services.trend_calculator import calculate_trend, prepare_chart_data
from .flowsheet_panel import ConditionManager
from .whatsapp_share_dialog import show_whatsapp_share
from .appointment_panel import show_schedule_followup


class CentralPanel:
    """Central panel for clinical notes and prescription."""

    def __init__(
        self,
        on_generate_rx: Callable[[str, Callable], None],
        on_save_visit: Callable[[dict], bool],
        on_print_pdf: Callable[[Prescription, str], Optional[str]],
        llm: LLMService,
        db: DatabaseService
    ):
        self.on_generate_rx = on_generate_rx
        self.on_save_visit = on_save_visit
        self.on_print_pdf = on_print_pdf
        self.llm = llm
        self.db = db

        self.current_patient: Optional[Patient] = None
        self.current_prescription: Optional[Prescription] = None
        self.visits: List[Visit] = []
        self.investigations: List[Investigation] = []
        self.procedures: List[Procedure] = []
        self.editing_visit_id: Optional[int] = None  # Track if editing existing visit

        # UI components
        self.patient_header: Optional[ft.Container] = None
        self.vitals_section: Optional[ft.Container] = None
        self.vitals_expanded: bool = True
        self.bp_systolic_field: Optional[ft.TextField] = None
        self.bp_diastolic_field: Optional[ft.TextField] = None
        self.pulse_field: Optional[ft.TextField] = None
        self.spo2_field: Optional[ft.TextField] = None
        self.temperature_field: Optional[ft.TextField] = None
        self.weight_field: Optional[ft.TextField] = None
        self.height_field: Optional[ft.TextField] = None
        self.bmi_text: Optional[ft.Text] = None
        self.weight_change_text: Optional[ft.Text] = None
        self.blood_sugar_field: Optional[ft.TextField] = None
        self.sugar_type_dropdown: Optional[ft.Dropdown] = None
        self.complaint_field: Optional[ft.TextField] = None
        self.notes_field: Optional[ft.TextField] = None
        self.rx_display: Optional[ft.Column] = None
        self.generate_btn: Optional[ft.ElevatedButton] = None
        self.save_btn: Optional[ft.ElevatedButton] = None
        self.print_btn: Optional[ft.ElevatedButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.tabs: Optional[ft.Tabs] = None
        self.audit_history_btn: Optional[ft.IconButton] = None
        self.history_list: Optional[ft.ListView] = None
        self.investigations_list: Optional[ft.ListView] = None
        self.procedures_list: Optional[ft.ListView] = None
        self.vitals_history_list: Optional[ft.ListView] = None
        self.trends_container: Optional[ft.Container] = None
        self.flowsheets_container: Optional[ft.Container] = None

        # Audit dialog
        self.audit_dialog = AuditHistoryDialog(db)

        # Template browser
        self.template_browser = TemplateBrowser(db, self._on_template_applied)

    def build(self) -> ft.Control:
        """Build the central panel UI."""

        # Patient header
        self.patient_header = ft.Container(
            content=ft.Text(
                "Select a patient to begin",
                size=16,
                color=ft.Colors.GREY_500,
                italic=True,
            ),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
        )

        # Vitals section
        self.vitals_section = self._build_vitals_section()

        # Chief complaint field (with text expansion)
        self.complaint_field = ExpandableTextField(
            db=self.db,
            label="Chief Complaint",
            hint_text="e.g., Chest pain x 2 days, fever, breathlessness (Try: c/o for 'complains of')",
            multiline=True,
            min_lines=1,
            max_lines=2,
            border_radius=8,
        )

        # Clinical notes field (with text expansion)
        self.notes_field = ExpandableTextArea(
            db=self.db,
            label="Clinical Notes",
            hint_text="Enter clinical findings, vitals, examination notes...\n\nTry shortcuts: c/o, h/o, vitals, cvs, rs, etc.\n\nExample:\nPt c/o chest pain x 2 days, radiating to left arm.\nH/o HTN, DM type 2.\nBP: 140/90, PR: 88/min\nCVS: S1S2 normal, no murmur\nRS: NVBS bilateral\n\nImpr: Unstable angina, r/o ACS",
            multiline=True,
            min_lines=8,
            max_lines=12,
            border_radius=8,
            text_size=13,
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)

        # Templates button
        self.templates_btn = ft.ElevatedButton(
            text="Templates",
            icon=ft.Icons.DESCRIPTION,
            tooltip="Use clinical template",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._on_templates_click,
            disabled=True,
        )

        # Generate button
        self.generate_btn = ft.ElevatedButton(
            text="Generate Rx",
            icon=ft.Icons.AUTO_AWESOME,
            tooltip="Generate prescription with AI (Ctrl+G)",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._on_generate_click,
            disabled=True,
        )

        # Prescription display area
        self.rx_display = ft.Column(
            [],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        # Save button
        self.save_btn = ft.ElevatedButton(
            text="Save Visit",
            icon=ft.Icons.SAVE,
            tooltip="Save current visit (Ctrl+S)",
            on_click=self._on_save_click,
            disabled=True,
        )

        # Print button
        self.print_btn = ft.ElevatedButton(
            text="Print PDF",
            icon=ft.Icons.PRINT,
            tooltip="Print prescription as PDF (Ctrl+P)",
            on_click=self._on_print_click,
            disabled=True,
        )

        # WhatsApp share button
        self.whatsapp_btn = ft.ElevatedButton(
            text="Share WhatsApp",
            icon=ft.Icons.CHAT,
            tooltip="Share prescription via WhatsApp",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._on_whatsapp_click,
            disabled=True,
        )

        # Save as template button
        self.save_template_btn = ft.ElevatedButton(
            text="Save as Template",
            icon=ft.Icons.BOOKMARK_ADD,
            tooltip="Save this prescription as a template",
            on_click=self._on_save_template_click,
            disabled=True,
        )

        # Prescription tab content
        rx_tab_content = ft.Container(
            content=ft.Column([
                self.vitals_section,
                self.complaint_field,
                self.notes_field,
                ft.Row([
                    self.templates_btn,
                    self.generate_btn,
                    self.loading_indicator,
                ], spacing=10),
                ft.Divider(),
                ft.Text("Generated Prescription:", weight=ft.FontWeight.BOLD, size=14),
                ft.Container(
                    content=self.rx_display,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8,
                    padding=15,
                    expand=True,
                ),
                ft.Row([
                    self.save_btn,
                    self.print_btn,
                    self.whatsapp_btn,
                    self.save_template_btn,
                ], spacing=10),
            ], spacing=15, expand=True),
            padding=20,
            expand=True,
        )

        # History tab content
        self.history_list = ft.ListView(spacing=10, padding=10, expand=True)
        history_tab_content = ft.Container(
            content=self.history_list,
            padding=10,
            expand=True,
        )

        # Investigations tab content
        self.investigations_list = ft.ListView(spacing=10, padding=10, expand=True)
        investigations_tab_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Investigations", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "Add Investigation",
                        icon=ft.Icons.ADD,
                        on_click=self._add_investigation,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    content=self.investigations_list,
                    expand=True,
                ),
            ], spacing=10, expand=True),
            padding=10,
            expand=True,
        )

        # Procedures tab content
        self.procedures_list = ft.ListView(spacing=10, padding=10, expand=True)
        procedures_tab_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Procedures", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "Add Procedure",
                        icon=ft.Icons.ADD,
                        on_click=self._add_procedure,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    content=self.procedures_list,
                    expand=True,
                ),
            ], spacing=10, expand=True),
            padding=10,
            expand=True,
        )

        # Vitals History tab content
        self.vitals_history_list = ft.ListView(spacing=10, padding=10, expand=True)
        vitals_history_tab_content = ft.Container(
            content=ft.Column([
                ft.Text("Vitals History", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(
                    content=self.vitals_history_list,
                    expand=True,
                ),
            ], spacing=10, expand=True),
            padding=10,
            expand=True,
        )

        # Trends tab content (dynamically built when patient is selected)
        self.trends_container = ft.Container(
            content=ft.Text(
                "Select a patient to view trends",
                size=14,
                color=ft.Colors.GREY_600,
                italic=True
            ),
            padding=20,
            alignment=ft.alignment.center,
            expand=True,
        )

        # Flowsheets tab content (for chronic disease management)
        self.flowsheets_container = ft.Container(
            content=ft.Text(
                "Select a patient to view chronic disease flowsheets",
                size=14,
                color=ft.Colors.GREY_600,
                italic=True
            ),
            padding=20,
            alignment=ft.alignment.center,
            expand=True,
        )

        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Prescription",
                    icon=ft.Icons.MEDICATION,
                    content=rx_tab_content,
                ),
                ft.Tab(
                    text="History",
                    icon=ft.Icons.HISTORY,
                    content=history_tab_content,
                ),
                ft.Tab(
                    text="Vitals",
                    icon=ft.Icons.FAVORITE,
                    content=vitals_history_tab_content,
                ),
                ft.Tab(
                    text="Investigations",
                    icon=ft.Icons.SCIENCE,
                    content=investigations_tab_content,
                ),
                ft.Tab(
                    text="Trends",
                    icon=ft.Icons.TRENDING_UP,
                    content=self.trends_container,
                ),
                ft.Tab(
                    text="Procedures",
                    icon=ft.Icons.MEDICAL_SERVICES,
                    content=procedures_tab_content,
                ),
                ft.Tab(
                    text="Flowsheets",
                    icon=ft.Icons.MONITOR_HEART,
                    content=self.flowsheets_container,
                ),
            ],
            expand=True,
        )

        return ft.Column([
            self.patient_header,
            ft.Container(
                content=self.tabs,
                expand=True,
            ),
        ], spacing=0, expand=True)

    def _build_vitals_section(self) -> ft.Container:
        """Build the collapsible vitals entry section."""
        # Create vitals fields
        self.bp_systolic_field = ft.TextField(
            label="BP Sys",
            hint_text="120",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=13,
            on_change=self._on_vitals_change,
        )
        self.bp_diastolic_field = ft.TextField(
            label="BP Dia",
            hint_text="80",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=13,
            on_change=self._on_vitals_change,
        )
        self.pulse_field = ft.TextField(
            label="Pulse",
            hint_text="72",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="/min",
            text_size=13,
        )
        self.spo2_field = ft.TextField(
            label="SpO2",
            hint_text="98",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="%",
            text_size=13,
            on_change=self._on_vitals_change,
        )
        self.temperature_field = ft.TextField(
            label="Temp",
            hint_text="98.6",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="°F",
            text_size=13,
            on_change=self._on_vitals_change,
        )
        self.weight_field = ft.TextField(
            label="Weight",
            hint_text="70",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="kg",
            text_size=13,
            on_change=self._on_weight_height_change,
        )
        self.height_field = ft.TextField(
            label="Height",
            hint_text="170",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="cm",
            text_size=13,
            on_change=self._on_weight_height_change,
        )
        self.bmi_text = ft.Text("BMI: --", size=13, weight=ft.FontWeight.W_500)
        self.weight_change_text = ft.Text("", size=12, italic=True)

        self.blood_sugar_field = ft.TextField(
            label="Blood Sugar",
            hint_text="100",
            width=110,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="mg/dL",
            text_size=13,
        )
        self.sugar_type_dropdown = ft.Dropdown(
            label="Type",
            width=100,
            options=[
                ft.dropdown.Option("FBS"),
                ft.dropdown.Option("RBS"),
                ft.dropdown.Option("PPBS"),
            ],
            value="RBS",
            text_size=13,
        )

        # Vitals content
        vitals_content = ft.Column([
            ft.Row([
                self.bp_systolic_field,
                ft.Text("/", size=20, weight=ft.FontWeight.BOLD),
                self.bp_diastolic_field,
                ft.Text("mmHg", size=11, color=ft.Colors.GREY_600),
                ft.Container(width=20),
                self.pulse_field,
                ft.Container(width=20),
                self.spo2_field,
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            ft.Row([
                self.temperature_field,
                ft.Container(width=20),
                self.weight_field,
                ft.Container(width=20),
                self.height_field,
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            ft.Row([
                self.bmi_text,
                ft.Container(width=20),
                self.weight_change_text,
            ], spacing=5),
            ft.Row([
                self.blood_sugar_field,
                self.sugar_type_dropdown,
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
        ], spacing=10)

        # Collapsible container
        vitals_container = ft.Container(
            content=vitals_content,
            padding=15,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
            visible=self.vitals_expanded,
        )

        # Header with expand/collapse button
        def toggle_vitals(e):
            self.vitals_expanded = not self.vitals_expanded
            vitals_container.visible = self.vitals_expanded
            expand_icon.name = ft.Icons.EXPAND_LESS if self.vitals_expanded else ft.Icons.EXPAND_MORE
            if vitals_container.page:
                vitals_container.page.update()

        expand_icon = ft.IconButton(
            icon=ft.Icons.EXPAND_LESS,
            icon_size=20,
            on_click=toggle_vitals,
        )

        header = ft.Container(
            content=ft.Row([
                ft.Text("VITALS", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                expand_icon,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(left=15, right=5, top=5, bottom=5),
            bgcolor=ft.Colors.BLUE_100,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

        return ft.Container(
            content=ft.Column([
                header,
                vitals_container,
            ], spacing=0),
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
        )

    def _on_weight_height_change(self, e):
        """Auto-calculate BMI when weight or height changes."""
        try:
            weight = float(self.weight_field.value) if self.weight_field.value else None
            height = float(self.height_field.value) if self.height_field.value else None

            if weight and height:
                height_m = height / 100  # Convert cm to m
                bmi = round(weight / (height_m ** 2), 1)

                # Determine BMI category and color
                if bmi < 18.5:
                    category = "Underweight"
                    color = ft.Colors.ORANGE_700
                elif bmi < 25:
                    category = "Normal"
                    color = ft.Colors.GREEN_700
                elif bmi < 30:
                    category = "Overweight"
                    color = ft.Colors.ORANGE_700
                else:
                    category = "Obese"
                    color = ft.Colors.RED_700

                self.bmi_text.value = f"BMI: {bmi} ({category})"
                self.bmi_text.color = color
            else:
                self.bmi_text.value = "BMI: --"
                self.bmi_text.color = None

            # Calculate weight change from last visit
            if weight and self.current_patient:
                last_vitals = self.db.get_latest_vitals(self.current_patient.id)
                if last_vitals and last_vitals.get('weight'):
                    last_weight = last_vitals['weight']
                    weight_change = round(weight - last_weight, 1)
                    if weight_change > 0:
                        self.weight_change_text.value = f"↑ +{weight_change} kg from last visit"
                        self.weight_change_text.color = ft.Colors.ORANGE_700
                    elif weight_change < 0:
                        self.weight_change_text.value = f"↓ {weight_change} kg from last visit"
                        self.weight_change_text.color = ft.Colors.BLUE_700
                    else:
                        self.weight_change_text.value = "No change from last visit"
                        self.weight_change_text.color = ft.Colors.GREY_600
                else:
                    self.weight_change_text.value = ""

            if self.bmi_text.page:
                self.bmi_text.page.update()
        except (ValueError, ZeroDivisionError):
            pass

    def _on_vitals_change(self, e):
        """Color-code abnormal vitals."""
        try:
            # BP Systolic
            if self.bp_systolic_field.value:
                bp_sys = int(self.bp_systolic_field.value)
                if bp_sys >= 140 or bp_sys < 90:
                    self.bp_systolic_field.border_color = ft.Colors.RED_700
                else:
                    self.bp_systolic_field.border_color = None

            # BP Diastolic
            if self.bp_diastolic_field.value:
                bp_dia = int(self.bp_diastolic_field.value)
                if bp_dia >= 90 or bp_dia < 60:
                    self.bp_diastolic_field.border_color = ft.Colors.RED_700
                else:
                    self.bp_diastolic_field.border_color = None

            # SpO2
            if self.spo2_field.value:
                spo2 = int(self.spo2_field.value)
                if spo2 < 95:
                    self.spo2_field.border_color = ft.Colors.RED_700
                else:
                    self.spo2_field.border_color = None

            # Temperature
            if self.temperature_field.value:
                temp = float(self.temperature_field.value)
                if temp > 100.4 or temp < 96:
                    self.temperature_field.border_color = ft.Colors.RED_700
                else:
                    self.temperature_field.border_color = None

            if e.page:
                e.page.update()
        except (ValueError, AttributeError):
            pass

    def set_patient(self, patient: Patient):
        """Set the current patient."""
        self.current_patient = patient
        self.current_prescription = None
        self.editing_visit_id = None

        # Update header
        header_text = f"{patient.name}"
        details = []
        if patient.age:
            details.append(f"{patient.age}y")
        if patient.gender:
            details.append(patient.gender)
        if patient.uhid:
            details.append(f"UHID: {patient.uhid}")

        # Create audit history button
        self.audit_history_btn = ft.IconButton(
            icon=ft.Icons.HISTORY,
            tooltip="View audit history",
            on_click=self._show_audit_history,
            icon_size=20,
        )

        self.patient_header.content = ft.Row([
            ft.Column([
                ft.Text(header_text, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(" | ".join(details), size=13, color=ft.Colors.GREY_600),
            ], spacing=2),
            self.audit_history_btn,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Enable generate and templates buttons
        self.generate_btn.disabled = False
        self.templates_btn.disabled = False
        self.save_btn.disabled = True
        self.print_btn.disabled = True
        self.whatsapp_btn.disabled = True
        self.save_template_btn.disabled = True

        # Clear fields
        self.complaint_field.value = ""
        self.notes_field.value = ""
        self.rx_display.controls.clear()

        # Clear and pre-fill vitals
        self._clear_vitals()
        last_height = self.db.get_last_height(patient.id)
        if last_height:
            self.height_field.value = str(int(last_height))

        # Load investigations, procedures, and vitals
        self.investigations = self.db.get_patient_investigations(patient.id)
        self.procedures = self.db.get_patient_procedures(patient.id)
        self._refresh_investigations()
        self._refresh_procedures()
        self._refresh_vitals_history()
        self._refresh_trends()
        self._refresh_flowsheets()

        if self.patient_header.page:
            self.patient_header.page.update()

    def _show_audit_history(self, e):
        """Show audit history dialog for current patient."""
        if self.current_patient and e.page:
            self.audit_dialog.show(e.page, self.current_patient)

    def _build_trends_tab(self) -> ft.Control:
        """Build the trends tab with pre-built trend panels."""
        panels = []

        for panel_name, test_names in TREND_PANELS.items():
            panel_items = []

            for test_name in test_names:
                # Get all investigations for this test
                test_invs = [
                    inv for inv in self.investigations
                    if inv.test_name.lower() == test_name.lower() and inv.result
                ]

                if not test_invs:
                    continue

                # Get latest value
                latest = test_invs[-1]
                try:
                    latest_value = float(latest.result)
                    value_str = f"{latest_value:.1f} {latest.unit}"
                except ValueError:
                    value_str = latest.result

                # Calculate trend
                trend_arrow = "→"
                if len(test_invs) >= 2:
                    try:
                        values = [float(inv.result) for inv in test_invs[-3:]]
                        trend_arrow = calculate_trend(values)
                    except ValueError:
                        pass

                # Get reference range
                normal_min, normal_max, _ = get_reference_range(test_name)

                # Determine if abnormal
                is_abnormal = latest.is_abnormal

                # Create panel item
                panel_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(test_name, size=12, weight=ft.FontWeight.W_500),
                                ft.Text(value_str, size=11, color=ft.Colors.GREY_700),
                            ], spacing=2, expand=True),
                            ft.Row([
                                ft.Text(
                                    trend_arrow,
                                    size=16,
                                    color=ft.Colors.ORANGE_700 if trend_arrow == "↑" else
                                          ft.Colors.BLUE_700 if trend_arrow == "↓" else
                                          ft.Colors.GREY_600
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SHOW_CHART,
                                    icon_size=14,
                                    tooltip="View trend",
                                    icon_color=ft.Colors.BLUE_700,
                                    on_click=lambda e, tn=test_name: self._show_trend_from_panel(e, tn),
                                ),
                            ], spacing=0),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=8,
                        bgcolor=ft.Colors.RED_50 if is_abnormal else ft.Colors.WHITE,
                        border_radius=5,
                    )
                )

            if panel_items:
                panels.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"{panel_name.upper()} PANEL",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_700
                            ),
                            ft.Column(panel_items, spacing=5),
                        ], spacing=10),
                        padding=15,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        width=250,
                    )
                )

        if not panels:
            return ft.Container(
                content=ft.Text(
                    "No investigation data available for trend panels",
                    size=14,
                    color=ft.Colors.GREY_600,
                    italic=True
                ),
                padding=20,
                alignment=ft.alignment.center,
            )

        # Arrange panels in a grid
        rows = []
        for i in range(0, len(panels), 3):
            row_panels = panels[i:i+3]
            rows.append(ft.Row(row_panels, spacing=15, wrap=True))

        return ft.Container(
            content=ft.Column(
                rows,
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )

    def _show_trend_from_panel(self, e, test_name: str):
        """Show trend chart from a trend panel."""
        if not e.page or not self.current_patient:
            return

        # Get all investigations for this test
        test_investigations = [
            i for i in self.investigations
            if i.test_name.lower() == test_name.lower()
        ]

        if not test_investigations:
            return

        # Show dialog
        dialog = LabTrendsDialog(
            test_name=test_name,
            investigations=test_investigations,
            all_investigations=self.investigations
        )
        dialog.show(e.page)

    def _refresh_trends(self):
        """Refresh the trends tab."""
        if not self.trends_container:
            return

        # Build new trends content
        trends_content = self._build_trends_tab()
        self.trends_container.content = trends_content

        if self.trends_container.page:
            self.trends_container.update()

    def _refresh_flowsheets(self):
        """Refresh the flowsheets tab with chronic condition management."""
        if not self.flowsheets_container or not self.current_patient:
            return

        # Build condition manager for this patient
        condition_manager = ConditionManager(
            db=self.db,
            patient_id=self.current_patient.id
        )

        self.flowsheets_container.content = condition_manager.build()

        if self.flowsheets_container.page:
            self.flowsheets_container.update()

    def set_visits(self, visits: List[Visit]):
        """Set visits for history tab."""
        self.visits = visits
        self._refresh_history()

    def _refresh_history(self):
        """Refresh the history list."""
        self.history_list.controls.clear()

        if not self.visits:
            self.history_list.controls.append(
                ft.Text("No previous visits", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for visit in self.visits:
                visit_card = self._create_visit_card(visit)
                self.history_list.controls.append(visit_card)

        if self.history_list.page:
            self.history_list.update()

    def _create_visit_card(self, visit: Visit) -> ft.Control:
        """Create a card for a visit."""
        content_parts = []

        if visit.chief_complaint:
            content_parts.append(ft.Text(
                f"CC: {visit.chief_complaint}",
                size=13,
                weight=ft.FontWeight.W_500,
            ))

        if visit.diagnosis:
            content_parts.append(ft.Text(
                f"Dx: {visit.diagnosis}",
                size=12,
                color=ft.Colors.BLUE_700,
            ))

        if visit.prescription_json:
            try:
                rx = json.loads(visit.prescription_json)
                meds = rx.get("medications", [])
                if meds:
                    med_names = [m.get("drug_name", "") for m in meds[:3]]
                    content_parts.append(ft.Text(
                        f"Rx: {', '.join(med_names)}{'...' if len(meds) > 3 else ''}",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ))
            except:
                pass

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        str(visit.visit_date) if visit.visit_date else "Unknown date",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            icon_size=16,
                            tooltip="Load this visit",
                            on_click=lambda e, v=visit: self._load_visit(v),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=16,
                            tooltip="Edit visit",
                            on_click=lambda e, v=visit: self._edit_visit(v),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=16,
                            tooltip="Delete visit",
                            icon_color=ft.Colors.RED_700,
                            on_click=lambda e, v=visit: self._delete_visit(e, v),
                        ),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                *content_parts,
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

    def _load_visit(self, visit: Visit):
        """Load a previous visit into the form."""
        self.complaint_field.value = visit.chief_complaint or ""
        self.notes_field.value = visit.clinical_notes or ""
        self.editing_visit_id = None  # Just loading, not editing

        if visit.prescription_json:
            try:
                rx_data = json.loads(visit.prescription_json)
                self.current_prescription = Prescription(**rx_data)
                self._display_prescription(self.current_prescription)
                self.save_btn.disabled = False
                self.print_btn.disabled = False
                self.whatsapp_btn.disabled = False
                self.save_template_btn.disabled = False
            except:
                pass

        self.tabs.selected_index = 0
        if self.tabs.page:
            self.tabs.page.update()

    def _edit_visit(self, visit: Visit):
        """Edit an existing visit."""
        self.editing_visit_id = visit.id
        self._load_visit(visit)
        self.save_btn.text = "Update Visit"
        self._show_snackbar(f"Editing visit from {visit.visit_date}")

    def _delete_visit(self, e, visit: Visit):
        """Delete a visit with confirmation."""
        def confirm_delete():
            if self.db.delete_visit(visit.id):
                self._show_snackbar("Visit deleted successfully")
                # Refresh visits
                if self.current_patient:
                    self.visits = self.db.get_patient_visits(self.current_patient.id)
                    self._refresh_history()
            else:
                self._show_snackbar("Failed to delete visit", error=True)

        ConfirmationDialog.show(
            e.page,
            "Delete Visit?",
            f"This will delete the visit from {visit.visit_date}. The record will be soft-deleted and can be recovered from backups.",
            confirm_delete
        )

    # ============== INVESTIGATIONS ==============

    def _refresh_investigations(self):
        """Refresh the investigations list."""
        self.investigations_list.controls.clear()

        if not self.investigations:
            self.investigations_list.controls.append(
                ft.Text("No investigations recorded", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for inv in self.investigations:
                inv_card = self._create_investigation_card(inv)
                self.investigations_list.controls.append(inv_card)

        if self.investigations_list.page:
            self.investigations_list.update()

    def _create_investigation_card(self, inv: Investigation) -> ft.Control:
        """Create a card for an investigation."""
        result_text = f"{inv.result} {inv.unit}" if inv.result else "Pending"
        if inv.is_abnormal:
            result_text += " (ABNORMAL)"

        # Calculate trend indicator
        trend_arrow = self._calculate_investigation_trend(inv.test_name)

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Text(inv.test_name, size=14, weight=ft.FontWeight.W_500),
                        ft.Text(trend_arrow, size=14) if trend_arrow != "→" else ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.SHOW_CHART,
                            icon_size=16,
                            tooltip="View trend chart",
                            icon_color=ft.Colors.BLUE_700,
                            on_click=lambda e, i=inv: self._show_trend_chart(e, i),
                        ),
                    ], spacing=5),
                    ft.Row([
                        ft.Text(
                            str(inv.test_date) if inv.test_date else "",
                            size=11,
                            color=ft.Colors.GREY_600
                        ),
                        ft.Text(
                            result_text,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_700 if inv.is_abnormal else ft.Colors.GREEN_700
                        ),
                    ], spacing=15),
                    ft.Text(
                        f"Ref: {inv.reference_range}" if inv.reference_range else "",
                        size=11,
                        color=ft.Colors.GREY_500
                    ),
                ], spacing=3, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_size=18,
                        tooltip="Edit investigation",
                        on_click=lambda e, i=inv: self._edit_investigation(e, i),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=18,
                        tooltip="Delete investigation",
                        icon_color=ft.Colors.RED_700,
                        on_click=lambda e, i=inv: self._delete_investigation(e, i),
                    ),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

    def _add_investigation(self, e):
        """Add a new investigation."""
        if not self.current_patient:
            return

        def save_investigation(inv_data):
            inv = Investigation(**inv_data)
            result = self.db.add_investigation(inv)
            if result:
                self._show_snackbar("Investigation added successfully")
                self.investigations = self.db.get_patient_investigations(self.current_patient.id)
                self._refresh_investigations()
                self._refresh_trends()
            else:
                self._show_snackbar("Failed to add investigation", error=True)

        EditInvestigationDialog.show(e.page, None, self.current_patient.id, save_investigation)

    def _edit_investigation(self, e, inv: Investigation):
        """Edit an investigation."""
        def save_investigation(inv_data):
            updated_inv = Investigation(**inv_data)
            if self.db.update_investigation(updated_inv):
                self._show_snackbar("Investigation updated successfully")
                self.investigations = self.db.get_patient_investigations(self.current_patient.id)
                self._refresh_investigations()
                self._refresh_trends()
            else:
                self._show_snackbar("Failed to update investigation", error=True)

        inv_dict = {
            "id": inv.id,
            "patient_id": inv.patient_id,
            "test_name": inv.test_name,
            "result": inv.result or "",
            "unit": inv.unit or "",
            "reference_range": inv.reference_range or "",
            "test_date": inv.test_date,
            "is_abnormal": inv.is_abnormal
        }
        EditInvestigationDialog.show(e.page, inv_dict, inv.patient_id, save_investigation)

    def _delete_investigation(self, e, inv: Investigation):
        """Delete an investigation with confirmation."""
        def confirm_delete():
            if self.db.delete_investigation(inv.id):
                self._show_snackbar("Investigation deleted successfully")
                self.investigations = self.db.get_patient_investigations(self.current_patient.id)
                self._refresh_investigations()
                self._refresh_trends()
            else:
                self._show_snackbar("Failed to delete investigation", error=True)

        ConfirmationDialog.show(
            e.page,
            "Delete Investigation?",
            f"This will delete {inv.test_name} from {inv.test_date}. The record will be soft-deleted and can be recovered from backups.",
            confirm_delete
        )

    def _calculate_investigation_trend(self, test_name: str) -> str:
        """Calculate trend for an investigation."""
        # Filter investigations for this test
        test_invs = [
            inv for inv in self.investigations
            if inv.test_name.lower() == test_name.lower() and inv.result
        ]

        if len(test_invs) < 2:
            return "→"

        # Extract numeric values
        try:
            values = [float(inv.result) for inv in test_invs[-3:]]
            return calculate_trend(values)
        except ValueError:
            return "→"

    def _show_trend_chart(self, e, inv: Investigation):
        """Show trend chart dialog for an investigation."""
        if not e.page or not self.current_patient:
            return

        # Get all investigations for this test
        test_investigations = [
            i for i in self.investigations
            if i.test_name.lower() == inv.test_name.lower()
        ]

        # Show dialog
        dialog = LabTrendsDialog(
            test_name=inv.test_name,
            investigations=test_investigations,
            all_investigations=self.investigations
        )
        dialog.show(e.page)

    # ============== PROCEDURES ==============

    def _refresh_procedures(self):
        """Refresh the procedures list."""
        self.procedures_list.controls.clear()

        if not self.procedures:
            self.procedures_list.controls.append(
                ft.Text("No procedures recorded", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for proc in self.procedures:
                proc_card = self._create_procedure_card(proc)
                self.procedures_list.controls.append(proc_card)

        if self.procedures_list.page:
            self.procedures_list.update()

    def _create_procedure_card(self, proc: Procedure) -> ft.Control:
        """Create a card for a procedure."""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(proc.procedure_name, size=14, weight=ft.FontWeight.W_500),
                    ft.Text(
                        str(proc.procedure_date) if proc.procedure_date else "",
                        size=11,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        proc.details if proc.details else "",
                        size=12,
                        color=ft.Colors.GREY_700,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ) if proc.details else ft.Container(),
                ], spacing=3, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_size=18,
                        tooltip="Edit procedure",
                        on_click=lambda e, p=proc: self._edit_procedure(e, p),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=18,
                        tooltip="Delete procedure",
                        icon_color=ft.Colors.RED_700,
                        on_click=lambda e, p=proc: self._delete_procedure(e, p),
                    ),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

    def _add_procedure(self, e):
        """Add a new procedure."""
        if not self.current_patient:
            return

        def save_procedure(proc_data):
            proc = Procedure(**proc_data)
            result = self.db.add_procedure(proc)
            if result:
                self._show_snackbar("Procedure added successfully")
                self.procedures = self.db.get_patient_procedures(self.current_patient.id)
                self._refresh_procedures()
            else:
                self._show_snackbar("Failed to add procedure", error=True)

        EditProcedureDialog.show(e.page, None, self.current_patient.id, save_procedure)

    def _edit_procedure(self, e, proc: Procedure):
        """Edit a procedure."""
        def save_procedure(proc_data):
            updated_proc = Procedure(**proc_data)
            if self.db.update_procedure(updated_proc):
                self._show_snackbar("Procedure updated successfully")
                self.procedures = self.db.get_patient_procedures(self.current_patient.id)
                self._refresh_procedures()
            else:
                self._show_snackbar("Failed to update procedure", error=True)

        proc_dict = {
            "id": proc.id,
            "patient_id": proc.patient_id,
            "procedure_name": proc.procedure_name,
            "details": proc.details or "",
            "procedure_date": proc.procedure_date,
            "notes": proc.notes or ""
        }
        EditProcedureDialog.show(e.page, proc_dict, proc.patient_id, save_procedure)

    def _delete_procedure(self, e, proc: Procedure):
        """Delete a procedure with confirmation."""
        def confirm_delete():
            if self.db.delete_procedure(proc.id):
                self._show_snackbar("Procedure deleted successfully")
                self.procedures = self.db.get_patient_procedures(self.current_patient.id)
                self._refresh_procedures()
            else:
                self._show_snackbar("Failed to delete procedure", error=True)

        ConfirmationDialog.show(
            e.page,
            "Delete Procedure?",
            f"This will delete {proc.procedure_name} from {proc.procedure_date}. The record will be soft-deleted and can be recovered from backups.",
            confirm_delete
        )

    # ============== PRESCRIPTION ==============
    # ============== VITALS ==============

    def _clear_vitals(self):
        """Clear all vitals fields."""
        if self.bp_systolic_field:
            self.bp_systolic_field.value = ""
            self.bp_systolic_field.border_color = None
        if self.bp_diastolic_field:
            self.bp_diastolic_field.value = ""
            self.bp_diastolic_field.border_color = None
        if self.pulse_field:
            self.pulse_field.value = ""
        if self.spo2_field:
            self.spo2_field.value = ""
            self.spo2_field.border_color = None
        if self.temperature_field:
            self.temperature_field.value = ""
            self.temperature_field.border_color = None
        if self.weight_field:
            self.weight_field.value = ""
        if self.height_field:
            self.height_field.value = ""
        if self.blood_sugar_field:
            self.blood_sugar_field.value = ""
        if self.sugar_type_dropdown:
            self.sugar_type_dropdown.value = "RBS"
        if self.bmi_text:
            self.bmi_text.value = "BMI: --"
            self.bmi_text.color = None
        if self.weight_change_text:
            self.weight_change_text.value = ""

    def _get_vitals_data(self) -> dict:
        """Get current vitals from form fields."""
        vitals_data = {
            'patient_id': self.current_patient.id if self.current_patient else None,
        }

        # Only include non-empty values
        try:
            if self.bp_systolic_field.value:
                vitals_data['bp_systolic'] = int(self.bp_systolic_field.value)
            if self.bp_diastolic_field.value:
                vitals_data['bp_diastolic'] = int(self.bp_diastolic_field.value)
            if self.pulse_field.value:
                vitals_data['pulse'] = int(self.pulse_field.value)
            if self.spo2_field.value:
                vitals_data['spo2'] = int(self.spo2_field.value)
            if self.temperature_field.value:
                vitals_data['temperature'] = float(self.temperature_field.value)
            if self.weight_field.value:
                vitals_data['weight'] = float(self.weight_field.value)
            if self.height_field.value:
                vitals_data['height'] = float(self.height_field.value)
            if self.blood_sugar_field.value:
                vitals_data['blood_sugar'] = float(self.blood_sugar_field.value)
                vitals_data['sugar_type'] = self.sugar_type_dropdown.value
        except (ValueError, AttributeError):
            pass

        return vitals_data

    def _refresh_vitals_history(self):
        """Refresh the vitals history list."""
        if not self.vitals_history_list:
            return

        self.vitals_history_list.controls.clear()

        if not self.current_patient:
            return

        vitals_list = self.db.get_patient_vitals(self.current_patient.id, limit=50)

        if not vitals_list:
            self.vitals_history_list.controls.append(
                ft.Text("No vitals recorded", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            # Add header row
            header = ft.Container(
                content=ft.Row([
                    ft.Text("Date", size=12, weight=ft.FontWeight.BOLD, width=120),
                    ft.Text("BP", size=12, weight=ft.FontWeight.BOLD, width=80),
                    ft.Text("Pulse", size=12, weight=ft.FontWeight.BOLD, width=60),
                    ft.Text("SpO2", size=12, weight=ft.FontWeight.BOLD, width=60),
                    ft.Text("Weight", size=12, weight=ft.FontWeight.BOLD, width=70),
                    ft.Text("BMI", size=12, weight=ft.FontWeight.BOLD, width=60),
                    ft.Text("Sugar", size=12, weight=ft.FontWeight.BOLD, width=100),
                ]),
                padding=10,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
            )
            self.vitals_history_list.controls.append(header)

            # Add vitals rows
            for v in vitals_list:
                bp_text = ""
                bp_color = ft.Colors.BLACK
                if v.get('bp_systolic') and v.get('bp_diastolic'):
                    bp_text = f"{v['bp_systolic']}/{v['bp_diastolic']}"
                    if v['bp_systolic'] >= 140 or v['bp_diastolic'] >= 90:
                        bp_color = ft.Colors.RED_700

                pulse_text = f"{v['pulse']}" if v.get('pulse') else ""
                spo2_text = f"{v['spo2']}%" if v.get('spo2') else ""
                spo2_color = ft.Colors.RED_700 if v.get('spo2') and v['spo2'] < 95 else ft.Colors.BLACK

                weight_text = f"{v['weight']} kg" if v.get('weight') else ""
                bmi_text = f"{v['bmi']}" if v.get('bmi') else ""
                bmi_color = ft.Colors.BLACK
                if v.get('bmi'):
                    if v['bmi'] >= 30:
                        bmi_color = ft.Colors.RED_700
                    elif v['bmi'] >= 25 or v['bmi'] < 18.5:
                        bmi_color = ft.Colors.ORANGE_700
                    else:
                        bmi_color = ft.Colors.GREEN_700

                sugar_text = ""
                if v.get('blood_sugar'):
                    sugar_text = f"{v['blood_sugar']} {v.get('sugar_type', '')}"

                # Format date
                date_text = v.get('recorded_at', '')[:16] if v.get('recorded_at') else ""

                row = ft.Container(
                    content=ft.Row([
                        ft.Text(date_text, size=11, width=120),
                        ft.Text(bp_text, size=11, width=80, color=bp_color),
                        ft.Text(pulse_text, size=11, width=60),
                        ft.Text(spo2_text, size=11, width=60, color=spo2_color),
                        ft.Text(weight_text, size=11, width=70),
                        ft.Text(bmi_text, size=11, width=60, color=bmi_color),
                        ft.Text(sugar_text, size=11, width=100),
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                )
                self.vitals_history_list.controls.append(row)

        if self.vitals_history_list.page:
            self.vitals_history_list.update()


    def _on_generate_click(self, e):
        """Handle generate prescription click."""
        clinical_notes = self.notes_field.value.strip()
        if not clinical_notes:
            self._show_snackbar("Please enter clinical notes first", error=True)
            return

        # Show loading
        self.loading_indicator.visible = True
        self.generate_btn.disabled = True
        e.page.update()

        def callback(success: bool, prescription: Optional[Prescription], raw: str):
            self.loading_indicator.visible = False
            self.generate_btn.disabled = False

            if success and prescription:
                self.current_prescription = prescription
                self._display_prescription(prescription)
                self.save_btn.disabled = False
                self.print_btn.disabled = False
                self.whatsapp_btn.disabled = False
                self.save_template_btn.disabled = False
            else:
                self.rx_display.controls.clear()
                self.rx_display.controls.append(
                    ft.Text(f"Error: {raw}", color=ft.Colors.RED_600)
                )

            if e.page:
                e.page.update()

        self.on_generate_rx(clinical_notes, callback)

    def _display_prescription(self, rx: Prescription):
        """Display the prescription in the UI."""
        self.rx_display.controls.clear()

        # Diagnosis
        if rx.diagnosis:
            self.rx_display.controls.append(
                ft.Text("DIAGNOSIS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLUE_700)
            )
            for dx in rx.diagnosis:
                self.rx_display.controls.append(ft.Text(f"  • {dx}", size=12))

        # Medications
        if rx.medications:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("Rx", weight=ft.FontWeight.BOLD, size=16)
            )
            for i, med in enumerate(rx.medications, 1):
                med_text = f"{i}. {med.drug_name}"
                if med.strength:
                    med_text += f" {med.strength}"

                dosage_text = f"   {med.dose} {med.frequency}"
                if med.duration:
                    dosage_text += f" x {med.duration}"
                if med.instructions:
                    dosage_text += f" ({med.instructions})"

                self.rx_display.controls.append(
                    ft.Text(med_text, weight=ft.FontWeight.W_500, size=13)
                )
                self.rx_display.controls.append(
                    ft.Text(dosage_text, size=12, color=ft.Colors.GREY_700)
                )

        # Investigations
        if rx.investigations:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("INVESTIGATIONS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.ORANGE_700)
            )
            for inv in rx.investigations:
                self.rx_display.controls.append(ft.Text(f"  • {inv}", size=12))

        # Advice
        if rx.advice:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("ADVICE:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.GREEN_700)
            )
            for adv in rx.advice:
                self.rx_display.controls.append(ft.Text(f"  • {adv}", size=12))

        # Follow-up
        if rx.follow_up:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text(f"FOLLOW-UP: {rx.follow_up}", weight=ft.FontWeight.W_500, size=12)
            )

        # Red flags
        if rx.red_flags:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("RED FLAGS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.RED_700),
                        *[ft.Text(f"  ⚠ {flag}", size=12, color=ft.Colors.RED_600) for flag in rx.red_flags]
                    ], spacing=2),
                    bgcolor=ft.Colors.RED_50,
                    padding=10,
                    border_radius=5,
                )
            )

        if self.rx_display.page:
            self.rx_display.update()

    def _on_save_click(self, e):
        """Handle save visit click."""
        if not self.current_patient or not self.current_prescription:
            return

        # Get diagnosis from prescription
        diagnosis = ", ".join(self.current_prescription.diagnosis) if self.current_prescription.diagnosis else ""

        visit_data = {
            "chief_complaint": self.complaint_field.value.strip(),
            "clinical_notes": self.notes_field.value.strip(),
            "diagnosis": diagnosis,
            "prescription_json": self.current_prescription.model_dump_json(),
        }

        # Save vitals if any are entered
        vitals_data = self._get_vitals_data()
        if vitals_data and vitals_data.get('patient_id'):
            # Check if at least one vital is entered
            has_vitals = any(key in vitals_data for key in [
                'bp_systolic', 'bp_diastolic', 'pulse', 'spo2',
                'temperature', 'weight', 'height', 'blood_sugar'
            ])
            if has_vitals:
                try:
                    self.db.add_vitals(vitals_data)
                    self._refresh_vitals_history()
                    self._clear_vitals()
                    # Re-populate last height
                    last_height = self.db.get_last_height(self.current_patient.id)
                    if last_height:
                        self.height_field.value = str(int(last_height))
                except Exception as ex:
                    self._show_snackbar(f"Warning: Failed to save vitals: {str(ex)}", error=True)

        # If editing, update the existing visit
        if self.editing_visit_id:
            visit = Visit(
                id=self.editing_visit_id,
                patient_id=self.current_patient.id,
                **visit_data
            )
            if self.db.update_visit(visit):
                self._show_snackbar("Visit updated successfully")
                self.editing_visit_id = None
                self.save_btn.text = "Save Visit"
                # Refresh visits
                self.visits = self.db.get_patient_visits(self.current_patient.id)
                self._refresh_history()
            else:
                self._show_snackbar("Failed to update visit", error=True)
        else:
            # Otherwise, create new visit
            success = self.on_save_visit(visit_data)
            if success:
                self._show_snackbar("Visit saved successfully")
                self.save_btn.disabled = True

                # Offer to schedule follow-up
                self._offer_schedule_followup(e.page)

        e.page.update()

    def _offer_schedule_followup(self, page):
        """Offer to schedule a follow-up after visit."""
        if not self.current_patient or not self.current_prescription:
            return

        # Parse follow-up days from prescription
        suggested_days = 14  # Default
        if self.current_prescription.follow_up:
            follow_up = self.current_prescription.follow_up.lower()
            if "1 week" in follow_up or "one week" in follow_up:
                suggested_days = 7
            elif "2 week" in follow_up or "two week" in follow_up:
                suggested_days = 14
            elif "3 week" in follow_up or "three week" in follow_up:
                suggested_days = 21
            elif "1 month" in follow_up or "one month" in follow_up:
                suggested_days = 30
            elif "2 month" in follow_up or "two month" in follow_up:
                suggested_days = 60
            elif "3 month" in follow_up or "three month" in follow_up:
                suggested_days = 90

        show_schedule_followup(
            page=page,
            db=self.db,
            patient=self.current_patient,
            suggested_days=suggested_days
        )

    def _on_print_click(self, e):
        """Handle print PDF click."""
        if not self.current_prescription:
            return

        filepath = self.on_print_pdf(
            self.current_prescription,
            self.complaint_field.value.strip()
        )

        if filepath:
            self._show_snackbar(f"PDF saved: {filepath}")
            # Store for WhatsApp sharing
            self._last_pdf_path = filepath
        else:
            self._show_snackbar("Failed to generate PDF", error=True)

    def _on_whatsapp_click(self, e):
        """Handle WhatsApp share click."""
        if not self.current_prescription or not self.current_patient:
            return

        # Get PDF path if available
        pdf_path = getattr(self, '_last_pdf_path', None)

        # Show share dialog
        show_whatsapp_share(
            page=e.page,
            patient=self.current_patient,
            prescription=self.current_prescription,
            pdf_path=pdf_path,
            on_shared=lambda: self._show_snackbar("Prescription shared via WhatsApp")
        )

    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar message."""
        if self.tabs and self.tabs.page:
            self.tabs.page.open(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
                )
            )

    def _on_templates_click(self, e):
        """Handle templates button click."""
        if e.page:
            self.template_browser.show(e.page)

    def _on_template_applied(self, prescription_data: dict):
        """Handle template application."""
        try:
            # Create Prescription object from template data
            self.current_prescription = Prescription(**prescription_data)

            # Display the prescription
            self._display_prescription(self.current_prescription)

            # Enable save, print, and share buttons
            self.save_btn.disabled = False
            self.print_btn.disabled = False
            self.whatsapp_btn.disabled = False
            self.save_template_btn.disabled = False

            if self.tabs and self.tabs.page:
                self.tabs.page.update()

            # Show success message
            self._show_snackbar("Template applied successfully")

        except Exception as ex:
            self._show_snackbar(f"Error applying template: {str(ex)}", error=True)

    def _on_save_template_click(self, e):
        """Handle save as template button click."""
        if not self.current_prescription:
            self._show_snackbar("No prescription to save", error=True)
            return

        # Convert prescription to dict
        prescription_dict = self.current_prescription.model_dump()

        # Show save template dialog
        save_dialog = SaveTemplateDialog(
            db=self.db,
            prescription_dict=prescription_dict,
            on_save=lambda template_id: self._show_snackbar(
                "Template saved successfully!"
            )
        )

        if e.page:
            save_dialog.show(e.page)
