"""Chronic disease flowsheet panel for patient management."""

import flet as ft
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class FlowsheetPanel(ft.UserControl):
    """Display flowsheet for a chronic condition."""

    def __init__(
        self,
        db,
        patient_id: int,
        condition_code: str,
        condition_name: str,
        on_add_value: callable = None
    ):
        super().__init__()
        self.db = db
        self.patient_id = patient_id
        self.condition_code = condition_code
        self.condition_name = condition_name
        self.on_add_value = on_add_value
        self.flowsheet_def = self._load_flowsheet_definition()

    def _load_flowsheet_definition(self) -> Dict:
        """Load flowsheet definition from JSON."""
        try:
            json_path = Path(__file__).parent.parent / "data" / "flowsheet_definitions.json"
            with open(json_path, 'r') as f:
                definitions = json.load(f)
                return definitions.get(self.condition_code, {})
        except Exception:
            return {}

    def _get_parameter_status(self, param: Dict) -> Dict:
        """Get current status of a flowsheet parameter."""
        source = param.get('source')
        result = {
            'name': param['name'],
            'last_value': None,
            'last_date': None,
            'status': 'unknown',  # on_target, borderline, off_target, overdue, no_data
            'due_date': None,
            'is_overdue': False,
            'target': param.get('target', ''),
            'unit': param.get('unit', ''),
            'category': param.get('category', 'Other')
        }

        frequency_months = param.get('frequency_months', 12)

        if source == 'investigation':
            # Get latest investigation matching this test
            test_name = param.get('test_name', '')
            investigations = self.db.get_patient_investigations(self.patient_id)

            for inv in investigations:
                if test_name.lower() in inv['test_name'].lower():
                    result['last_value'] = inv.get('result', '')
                    result['last_date'] = inv.get('test_date', '')
                    result['is_abnormal'] = inv.get('is_abnormal', False)
                    break

        elif source == 'vitals':
            field = param.get('field', '')
            latest_vitals = self.db.get_latest_vitals(self.patient_id)

            if latest_vitals:
                if field == 'bp':
                    sys = latest_vitals.get('bp_systolic')
                    dia = latest_vitals.get('bp_diastolic')
                    if sys and dia:
                        result['last_value'] = f"{sys}/{dia}"
                        result['last_date'] = latest_vitals.get('recorded_at', '')[:10]
                elif field == 'weight':
                    weight = latest_vitals.get('weight')
                    if weight:
                        result['last_value'] = f"{weight}"
                        result['last_date'] = latest_vitals.get('recorded_at', '')[:10]

        elif source == 'procedure':
            procedure_name = param.get('procedure_name', '')
            procedures = self.db.get_patient_procedures(self.patient_id)

            for proc in procedures:
                if procedure_name.lower() in proc['procedure_name'].lower():
                    result['last_value'] = 'Done'
                    result['last_date'] = proc.get('procedure_date', '')
                    break

        # Calculate due date and overdue status
        if result['last_date']:
            try:
                last_date = datetime.strptime(result['last_date'][:10], "%Y-%m-%d")
                due_date = last_date + timedelta(days=frequency_months * 30)
                result['due_date'] = due_date.strftime("%Y-%m-%d")
                result['is_overdue'] = datetime.now() > due_date
            except ValueError:
                pass

        # Determine status
        if not result['last_value']:
            result['status'] = 'no_data'
        elif result['is_overdue']:
            result['status'] = 'overdue'
        else:
            # Check if on target (simplified logic)
            result['status'] = 'on_target'
            if result.get('is_abnormal'):
                result['status'] = 'off_target'

        return result

    def build(self):
        if not self.flowsheet_def:
            return ft.Container(
                content=ft.Text(f"No flowsheet defined for {self.condition_code}"),
                padding=20
            )

        parameters = self.flowsheet_def.get('parameters', [])

        # Group by category
        categories = {}
        for param in parameters:
            status = self._get_parameter_status(param)
            cat = status['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(status)

        # Build category sections
        sections = []

        # Summary counts
        overdue_count = sum(
            1 for cat_params in categories.values()
            for p in cat_params if p['is_overdue']
        )
        off_target_count = sum(
            1 for cat_params in categories.values()
            for p in cat_params if p['status'] == 'off_target'
        )

        # Header
        sections.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.MONITOR_HEART, color=ft.colors.BLUE_700, size=24),
                        ft.Text(
                            self.flowsheet_def.get('name', self.condition_name),
                            weight=ft.FontWeight.BOLD,
                            size=16
                        )
                    ]),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                f"{overdue_count} overdue",
                                color=ft.colors.WHITE,
                                size=11
                            ),
                            bgcolor=ft.colors.RED_600 if overdue_count > 0 else ft.colors.GREY_400,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=10
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{off_target_count} off target",
                                color=ft.colors.WHITE,
                                size=11
                            ),
                            bgcolor=ft.colors.ORANGE_600 if off_target_count > 0 else ft.colors.GREY_400,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=10
                        )
                    ], spacing=8)
                ], spacing=4),
                padding=ft.padding.all(12),
                bgcolor=ft.colors.BLUE_50,
                border_radius=8
            )
        )

        # Category sections
        for cat_name, cat_params in categories.items():
            rows = []
            for param in cat_params:
                rows.append(self._build_parameter_row(param))

            sections.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(cat_name, weight=ft.FontWeight.BOLD, size=12, color=ft.colors.GREY_700),
                        ft.Column(rows, spacing=4)
                    ], spacing=8),
                    padding=ft.padding.all(8),
                    margin=ft.margin.only(top=8)
                )
            )

        return ft.Container(
            content=ft.Column(sections, spacing=0, scroll=ft.ScrollMode.AUTO),
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            padding=ft.padding.all(8)
        )

    def _build_parameter_row(self, param: Dict) -> ft.Container:
        """Build a single parameter row."""
        status = param['status']

        # Status indicator
        if status == 'on_target':
            status_icon = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_600, size=16)
            bg_color = ft.colors.GREEN_50
        elif status == 'off_target':
            status_icon = ft.Icon(ft.icons.WARNING, color=ft.colors.ORANGE_600, size=16)
            bg_color = ft.colors.ORANGE_50
        elif status == 'overdue':
            status_icon = ft.Icon(ft.icons.ACCESS_TIME, color=ft.colors.RED_600, size=16)
            bg_color = ft.colors.RED_50
        else:
            status_icon = ft.Icon(ft.icons.HELP_OUTLINE, color=ft.colors.GREY_400, size=16)
            bg_color = ft.colors.GREY_50

        # Value display
        value_text = param['last_value'] or "No data"
        if param['unit'] and param['last_value']:
            value_text = f"{param['last_value']} {param['unit']}"

        # Date display
        date_text = ""
        if param['last_date']:
            try:
                dt = datetime.strptime(param['last_date'][:10], "%Y-%m-%d")
                date_text = dt.strftime("%d-%b-%y")
            except ValueError:
                date_text = param['last_date']

        # Overdue badge
        overdue_badge = None
        if param['is_overdue']:
            overdue_badge = ft.Container(
                content=ft.Text("OVERDUE", size=9, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=ft.colors.RED_600,
                padding=ft.padding.symmetric(horizontal=4, vertical=1),
                border_radius=3
            )

        return ft.Container(
            content=ft.Row([
                status_icon,
                ft.Container(
                    content=ft.Text(param['name'], size=12),
                    expand=True
                ),
                ft.Column([
                    ft.Text(value_text, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(date_text, size=10, color=ft.colors.GREY_600) if date_text else ft.Container()
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                overdue_badge if overdue_badge else ft.Container(width=0),
                ft.Text(f"Target: {param['target']}", size=10, color=ft.colors.GREY_500, width=100)
            ], spacing=8, alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            bgcolor=bg_color,
            border_radius=4
        )


class ConditionManager(ft.UserControl):
    """Manage patient's chronic conditions and display flowsheets."""

    AVAILABLE_CONDITIONS = [
        ("DM2", "Type 2 Diabetes"),
        ("HTN", "Hypertension"),
        ("CKD", "Chronic Kidney Disease"),
        ("CAD", "Coronary Artery Disease")
    ]

    def __init__(self, db, patient_id: int):
        super().__init__()
        self.db = db
        self.patient_id = patient_id
        self.conditions = []

    def _load_patient_conditions(self):
        """Load patient's chronic conditions from database."""
        # For now, we'll use a simple approach - check if conditions table exists
        # In a full implementation, this would query patient_conditions table
        self.conditions = []

        # Check for common chronic conditions based on diagnoses
        visits = self.db.get_patient_visits(self.patient_id)
        condition_keywords = {
            'DM2': ['diabetes', 'dm', 'type 2', 'diabetic', 't2dm'],
            'HTN': ['hypertension', 'htn', 'high blood pressure', 'bp high'],
            'CKD': ['ckd', 'chronic kidney', 'renal failure', 'nephropathy'],
            'CAD': ['cad', 'coronary', 'ihd', 'ischemic heart', 'mi', 'angina']
        }

        found_conditions = set()
        for visit in visits:
            diagnosis = (visit.get('diagnosis', '') or '').lower()
            for code, keywords in condition_keywords.items():
                if any(kw in diagnosis for kw in keywords):
                    found_conditions.add(code)

        self.conditions = list(found_conditions)

    def build(self):
        self._load_patient_conditions()

        if not self.conditions:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.GREY_400, size=32),
                    ft.Text(
                        "No chronic conditions detected",
                        color=ft.colors.GREY_600,
                        size=14
                    ),
                    ft.Text(
                        "Conditions are auto-detected from visit diagnoses",
                        color=ft.colors.GREY_500,
                        size=11
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                padding=ft.padding.all(20),
                alignment=ft.alignment.center
            )

        # Build flowsheet for each condition
        flowsheets = []
        for code in self.conditions:
            name = next((n for c, n in self.AVAILABLE_CONDITIONS if c == code), code)
            flowsheet = FlowsheetPanel(
                db=self.db,
                patient_id=self.patient_id,
                condition_code=code,
                condition_name=name
            )
            flowsheets.append(
                ft.Container(
                    content=flowsheet,
                    margin=ft.margin.only(bottom=12)
                )
            )

        return ft.Container(
            content=ft.Column(flowsheets, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(8)
        )
