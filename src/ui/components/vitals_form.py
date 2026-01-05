"""Premium Vitals Form Component.

Collapsible vitals entry section with auto-calculation and color-coding.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any

from ..tokens import Colors, Typography, Spacing, Radius
from ...services.database import DatabaseService


class VitalsForm:
    """Premium collapsible vitals entry form."""

    def __init__(
        self,
        db: DatabaseService,
        is_dark: bool = False,
    ):
        self.db = db
        self.is_dark = is_dark
        self.expanded = True
        self.current_patient_id: Optional[int] = None

        # Field references
        self.bp_systolic_field: Optional[ft.TextField] = None
        self.bp_diastolic_field: Optional[ft.TextField] = None
        self.pulse_field: Optional[ft.TextField] = None
        self.spo2_field: Optional[ft.TextField] = None
        self.temperature_field: Optional[ft.TextField] = None
        self.weight_field: Optional[ft.TextField] = None
        self.height_field: Optional[ft.TextField] = None
        self.blood_sugar_field: Optional[ft.TextField] = None
        self.sugar_type_dropdown: Optional[ft.Dropdown] = None
        self.bmi_text: Optional[ft.Text] = None
        self.weight_change_text: Optional[ft.Text] = None

        # Container refs
        self._content_container: Optional[ft.Container] = None
        self._expand_icon: Optional[ft.IconButton] = None

    def build(self) -> ft.Container:
        """Build the vitals form section."""
        # Create all fields
        self._create_fields()

        # Vitals content
        vitals_content = ft.Column([
            # Row 1: BP, Pulse, SpO2
            ft.Row([
                self.bp_systolic_field,
                ft.Text("/", size=20, weight=ft.FontWeight.BOLD),
                self.bp_diastolic_field,
                ft.Text("mmHg", size=11, color=Colors.NEUTRAL_500),
                ft.Container(width=Spacing.LG),
                self.pulse_field,
                ft.Container(width=Spacing.LG),
                self.spo2_field,
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            # Row 2: Temp, Weight, Height
            ft.Row([
                self.temperature_field,
                ft.Container(width=Spacing.LG),
                self.weight_field,
                ft.Container(width=Spacing.LG),
                self.height_field,
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            # Row 3: BMI and Weight Change
            ft.Row([
                self.bmi_text,
                ft.Container(width=Spacing.LG),
                self.weight_change_text,
            ], spacing=5),
            # Row 4: Blood Sugar
            ft.Row([
                self.blood_sugar_field,
                self.sugar_type_dropdown,
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
        ], spacing=10)

        # Collapsible container
        self._content_container = ft.Container(
            content=vitals_content,
            padding=Spacing.MD,
            bgcolor=Colors.INFO_LIGHT if not self.is_dark else "rgba(66, 133, 244, 0.1)",
            border_radius=ft.border_radius.only(bottom_left=Radius.MD, bottom_right=Radius.MD),
            visible=self.expanded,
        )

        # Header
        self._expand_icon = ft.IconButton(
            icon=ft.Icons.EXPAND_LESS if self.expanded else ft.Icons.EXPAND_MORE,
            icon_size=20,
            on_click=self._toggle_expand,
        )

        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.FAVORITE, size=16, color=Colors.PRIMARY_700),
                    ft.Text(
                        "VITALS",
                        size=Typography.LABEL_MEDIUM.size,
                        weight=ft.FontWeight.W_600,
                        color=Colors.PRIMARY_800 if not self.is_dark else Colors.PRIMARY_200,
                    ),
                ], spacing=Spacing.XS),
                self._expand_icon,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(left=Spacing.MD, right=4, top=4, bottom=4),
            bgcolor=Colors.PRIMARY_100 if not self.is_dark else Colors.PRIMARY_900,
            border_radius=ft.border_radius.only(top_left=Radius.MD, top_right=Radius.MD),
        )

        return ft.Container(
            content=ft.Column([header, self._content_container], spacing=0),
            border=ft.border.all(1, Colors.PRIMARY_200 if not self.is_dark else Colors.PRIMARY_800),
            border_radius=Radius.MD,
        )

    def _create_fields(self):
        """Create all vitals fields."""
        field_style = {
            "text_size": 13,
            "border_radius": Radius.SM,
        }

        self.bp_systolic_field = ft.TextField(
            label="BP Sys",
            hint_text="120",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_vitals_change,
            **field_style,
        )
        self.bp_diastolic_field = ft.TextField(
            label="BP Dia",
            hint_text="80",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_vitals_change,
            **field_style,
        )
        self.pulse_field = ft.TextField(
            label="Pulse",
            hint_text="72",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="/min",
            **field_style,
        )
        self.spo2_field = ft.TextField(
            label="SpO2",
            hint_text="98",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="%",
            on_change=self._on_vitals_change,
            **field_style,
        )
        self.temperature_field = ft.TextField(
            label="Temp",
            hint_text="98.6",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="°F",
            on_change=self._on_vitals_change,
            **field_style,
        )
        self.weight_field = ft.TextField(
            label="Weight",
            hint_text="70",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="kg",
            on_change=self._on_weight_height_change,
            **field_style,
        )
        self.height_field = ft.TextField(
            label="Height",
            hint_text="170",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="cm",
            on_change=self._on_weight_height_change,
            **field_style,
        )
        self.blood_sugar_field = ft.TextField(
            label="Blood Sugar",
            hint_text="100",
            width=110,
            keyboard_type=ft.KeyboardType.NUMBER,
            suffix_text="mg/dL",
            **field_style,
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
        self.bmi_text = ft.Text(
            "BMI: --",
            size=Typography.BODY_SMALL.size,
            weight=ft.FontWeight.W_500,
        )
        self.weight_change_text = ft.Text(
            "",
            size=Typography.BODY_SMALL.size - 1,
            italic=True,
        )

    def _toggle_expand(self, e):
        """Toggle vitals section expansion."""
        self.expanded = not self.expanded
        self._content_container.visible = self.expanded
        self._expand_icon.icon = ft.Icons.EXPAND_LESS if self.expanded else ft.Icons.EXPAND_MORE
        if self._content_container.page:
            self._content_container.page.update()

    def _on_weight_height_change(self, e):
        """Auto-calculate BMI when weight or height changes."""
        try:
            weight = float(self.weight_field.value) if self.weight_field.value else None
            height = float(self.height_field.value) if self.height_field.value else None

            if weight and height:
                height_m = height / 100
                bmi = round(weight / (height_m ** 2), 1)

                # Determine category
                if bmi < 18.5:
                    category, color = "Underweight", Colors.WARNING_MAIN
                elif bmi < 25:
                    category, color = "Normal", Colors.SUCCESS_MAIN
                elif bmi < 30:
                    category, color = "Overweight", Colors.WARNING_MAIN
                else:
                    category, color = "Obese", Colors.ERROR_MAIN

                self.bmi_text.value = f"BMI: {bmi} ({category})"
                self.bmi_text.color = color
            else:
                self.bmi_text.value = "BMI: --"
                self.bmi_text.color = None

            # Weight change from last visit
            if weight and self.current_patient_id:
                last_vitals = self.db.get_latest_vitals(self.current_patient_id)
                if last_vitals and last_vitals.get('weight'):
                    last_weight = last_vitals['weight']
                    weight_change = round(weight - last_weight, 1)
                    if weight_change > 0:
                        self.weight_change_text.value = f"↑ +{weight_change} kg from last visit"
                        self.weight_change_text.color = Colors.WARNING_MAIN
                    elif weight_change < 0:
                        self.weight_change_text.value = f"↓ {weight_change} kg from last visit"
                        self.weight_change_text.color = Colors.INFO_MAIN
                    else:
                        self.weight_change_text.value = "No change from last visit"
                        self.weight_change_text.color = Colors.NEUTRAL_500
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
                    self.bp_systolic_field.border_color = Colors.ERROR_MAIN
                else:
                    self.bp_systolic_field.border_color = None

            # BP Diastolic
            if self.bp_diastolic_field.value:
                bp_dia = int(self.bp_diastolic_field.value)
                if bp_dia >= 90 or bp_dia < 60:
                    self.bp_diastolic_field.border_color = Colors.ERROR_MAIN
                else:
                    self.bp_diastolic_field.border_color = None

            # SpO2
            if self.spo2_field.value:
                spo2 = int(self.spo2_field.value)
                if spo2 < 95:
                    self.spo2_field.border_color = Colors.ERROR_MAIN
                else:
                    self.spo2_field.border_color = None

            # Temperature
            if self.temperature_field.value:
                temp = float(self.temperature_field.value)
                if temp > 100.4 or temp < 96:
                    self.temperature_field.border_color = Colors.ERROR_MAIN
                else:
                    self.temperature_field.border_color = None

            if e.page:
                e.page.update()
        except (ValueError, AttributeError):
            pass

    def set_patient(self, patient_id: int, last_height: Optional[float] = None):
        """Set current patient for weight comparison."""
        self.current_patient_id = patient_id
        self.clear()
        if last_height:
            self.height_field.value = str(int(last_height))

    def clear(self):
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

    def get_data(self) -> Dict[str, Any]:
        """Get vitals data from form fields."""
        vitals_data = {
            'patient_id': self.current_patient_id,
        }

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

    def has_data(self) -> bool:
        """Check if any vitals are entered."""
        return any([
            self.bp_systolic_field.value,
            self.bp_diastolic_field.value,
            self.pulse_field.value,
            self.spo2_field.value,
            self.temperature_field.value,
            self.weight_field.value,
            self.height_field.value,
            self.blood_sugar_field.value,
        ])
