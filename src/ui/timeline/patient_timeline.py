"""Patient Timeline Component - Comprehensive view of patient history."""

import flet as ft
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from .trend_chart import TrendChart


class PatientTimeline(ft.UserControl):
    """
    Comprehensive patient timeline with AI summary, vitals, medications, visits, labs, and care gaps.
    """

    def __init__(
        self,
        patient_id: Optional[int] = None,
        on_visit_click: Optional[Callable] = None,
        on_care_gap_action: Optional[Callable] = None,
    ):
        super().__init__()
        self.patient_id = patient_id
        self.on_visit_click = on_visit_click
        self.on_care_gap_action = on_care_gap_action

        # Filter state
        self.selected_date_range = "all"  # "all", "1month", "3months", "6months", "1year"
        self.selected_category = "all"  # "all", "visits", "labs", "medications", "vitals"

        # Data (will be loaded from services)
        self.ai_summary = None
        self.vitals_data = {}
        self.medications = []
        self.visits = []
        self.lab_results = []
        self.care_gaps = []

        # UI components
        self.loading_indicator = ft.ProgressRing(visible=True)
        self.content_container = ft.Column(visible=False)

    def load_data(self):
        """Load patient data from database/services."""
        # TODO: Connect to actual services
        # For now, using mock data
        self.ai_summary = {
            "summary": "65-year-old male with long-standing hypertension and Type 2 diabetes. Recent concern: rising HbA1c (7.2% -> 8.1% in 3 months). Current medications include Metformin 1000mg BD, Ramipril 5mg OD. Last visit 2 weeks ago with chief complaint of fatigue.",
            "key_diagnoses": ["Type 2 Diabetes Mellitus", "Hypertension", "Dyslipidemia"],
            "current_medications": ["Metformin 1000mg BD", "Ramipril 5mg OD", "Atorvastatin 20mg OD"],
            "recent_trends": [
                {"metric": "HbA1c", "trend": "worsening", "detail": "7.2% → 8.1%"},
                {"metric": "Blood Pressure", "trend": "stable", "detail": "130/85 mmHg"},
                {"metric": "Weight", "trend": "increasing", "detail": "75kg → 78kg"},
            ],
            "alerts": [
                {"type": "critical", "message": "HbA1c above target (>7%)"},
                {"type": "warning", "message": "Overdue for lipid panel (last done 8 months ago)"},
            ],
        }

        self.vitals_data = {
            "blood_pressure": [
                {"date": datetime.now() - timedelta(days=180), "value": 140, "label": "6mo ago"},
                {"date": datetime.now() - timedelta(days=120), "value": 135, "label": "4mo ago"},
                {"date": datetime.now() - timedelta(days=60), "value": 130, "label": "2mo ago"},
                {"date": datetime.now() - timedelta(days=14), "value": 130, "label": "2wk ago"},
            ],
            "weight": [
                {"date": datetime.now() - timedelta(days=180), "value": 75, "label": "6mo ago"},
                {"date": datetime.now() - timedelta(days=120), "value": 76, "label": "4mo ago"},
                {"date": datetime.now() - timedelta(days=60), "value": 77, "label": "2mo ago"},
                {"date": datetime.now() - timedelta(days=14), "value": 78, "label": "2wk ago"},
            ],
            "hba1c": [
                {"date": datetime.now() - timedelta(days=180), "value": 7.2, "label": "6mo ago"},
                {"date": datetime.now() - timedelta(days=90), "value": 7.8, "label": "3mo ago"},
                {"date": datetime.now() - timedelta(days=14), "value": 8.1, "label": "2wk ago"},
            ],
        }

        self.medications = [
            {
                "name": "Metformin",
                "strength": "1000mg",
                "frequency": "BD",
                "start_date": datetime.now() - timedelta(days=730),
                "end_date": None,
                "status": "active",
            },
            {
                "name": "Ramipril",
                "strength": "5mg",
                "frequency": "OD",
                "start_date": datetime.now() - timedelta(days=730),
                "end_date": None,
                "status": "active",
            },
            {
                "name": "Atorvastatin",
                "strength": "20mg",
                "frequency": "OD",
                "start_date": datetime.now() - timedelta(days=365),
                "end_date": None,
                "status": "active",
            },
            {
                "name": "Glimepiride",
                "strength": "2mg",
                "frequency": "OD",
                "start_date": datetime.now() - timedelta(days=180),
                "end_date": datetime.now() - timedelta(days=90),
                "status": "discontinued",
            },
        ]

        self.visits = [
            {
                "id": 1,
                "date": datetime.now() - timedelta(days=14),
                "chief_complaint": "Fatigue, increased thirst",
                "diagnosis": "Uncontrolled Type 2 DM",
                "notes": "Patient reports poor dietary compliance. HbA1c increased to 8.1%. Counseled on diet and exercise. Continue current medications.",
            },
            {
                "id": 2,
                "date": datetime.now() - timedelta(days=90),
                "chief_complaint": "Routine follow-up",
                "diagnosis": "Type 2 DM, HTN - stable",
                "notes": "BP well controlled. HbA1c slightly elevated at 7.8%. Advised to increase physical activity.",
            },
            {
                "id": 3,
                "date": datetime.now() - timedelta(days=180),
                "chief_complaint": "Medication refill",
                "diagnosis": "Type 2 DM, HTN - stable",
                "notes": "No new complaints. All parameters stable. Continue same treatment.",
            },
        ]

        self.lab_results = [
            {"test": "HbA1c", "value": 8.1, "unit": "%", "reference": "4.0-6.0", "date": datetime.now() - timedelta(days=14), "abnormal": True, "direction": "high"},
            {"test": "Fasting Blood Sugar", "value": 145, "unit": "mg/dL", "reference": "70-100", "date": datetime.now() - timedelta(days=14), "abnormal": True, "direction": "high"},
            {"test": "Creatinine", "value": 1.1, "unit": "mg/dL", "reference": "0.7-1.3", "date": datetime.now() - timedelta(days=14), "abnormal": False, "direction": None},
            {"test": "Total Cholesterol", "value": 195, "unit": "mg/dL", "reference": "<200", "date": datetime.now() - timedelta(days=240), "abnormal": False, "direction": None},
            {"test": "LDL", "value": 115, "unit": "mg/dL", "reference": "<100", "date": datetime.now() - timedelta(days=240), "abnormal": True, "direction": "high"},
        ]

        self.care_gaps = [
            {
                "type": "overdue_test",
                "title": "Lipid Panel Overdue",
                "description": "Last done 8 months ago. Recommended annually for diabetic patients.",
                "priority": "medium",
                "action": "Order lipid panel",
            },
            {
                "type": "preventive",
                "title": "Diabetic Eye Exam Due",
                "description": "No record of retinal exam in past 12 months.",
                "priority": "high",
                "action": "Refer to ophthalmology",
            },
            {
                "type": "medication",
                "title": "Consider SGLT2 Inhibitor",
                "description": "HbA1c >8% despite dual therapy. Guidelines suggest adding SGLT2i.",
                "priority": "medium",
                "action": "Review medication options",
            },
        ]

        # Hide loading, show content
        self.loading_indicator.visible = False
        self.content_container.visible = True
        self.update()

    def _build_ai_summary_card(self) -> ft.Container:
        """30-second AI summary card."""
        if not self.ai_summary:
            return ft.Container()

        # Key diagnoses chips
        diagnosis_chips = [
            ft.Container(
                content=ft.Text(dx, size=12, color=ft.colors.WHITE),
                bgcolor=ft.colors.BLUE_700,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
            )
            for dx in self.ai_summary["key_diagnoses"]
        ]

        # Current medications
        med_list = [
            ft.Text(f"• {med}", size=12, color=ft.colors.GREY_800)
            for med in self.ai_summary["current_medications"]
        ]

        # Recent trends
        trend_rows = []
        for trend in self.ai_summary["recent_trends"]:
            icon_name = ft.icons.TRENDING_UP if trend["trend"] == "worsening" else ft.icons.TRENDING_DOWN if trend["trend"] == "improving" else ft.icons.TRENDING_FLAT
            icon_color = ft.colors.RED_400 if trend["trend"] == "worsening" else ft.colors.GREEN_400 if trend["trend"] == "improving" else ft.colors.GREY_400

            trend_rows.append(
                ft.Row(
                    controls=[
                        ft.Icon(icon_name, color=icon_color, size=16),
                        ft.Text(trend["metric"], size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(trend["detail"], size=12, color=ft.colors.GREY_600),
                    ],
                    spacing=8,
                )
            )

        # Alerts
        alert_items = []
        for alert in self.ai_summary["alerts"]:
            bg_color = ft.colors.RED_100 if alert["type"] == "critical" else ft.colors.ORANGE_100
            text_color = ft.colors.RED_900 if alert["type"] == "critical" else ft.colors.ORANGE_900
            icon = ft.icons.ERROR if alert["type"] == "critical" else ft.icons.WARNING

            alert_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icon, color=text_color, size=16),
                            ft.Text(alert["message"], size=12, color=text_color),
                        ],
                        spacing=8,
                    ),
                    bgcolor=bg_color,
                    padding=8,
                    border_radius=4,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.AUTO_AWESOME, color=ft.colors.PURPLE_400, size=20),
                            ft.Text("AI Summary (30-second snapshot)", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=1),
                    # Summary text
                    ft.Text(self.ai_summary["summary"], size=13, color=ft.colors.GREY_800),
                    ft.Divider(height=1),
                    # Key diagnoses
                    ft.Row(
                        controls=[ft.Text("Key Diagnoses:", size=12, weight=ft.FontWeight.BOLD)] + diagnosis_chips,
                        spacing=8,
                        wrap=True,
                    ),
                    # Current medications
                    ft.Column(
                        controls=[ft.Text("Current Medications:", size=12, weight=ft.FontWeight.BOLD)] + med_list,
                        spacing=2,
                    ),
                    # Recent trends
                    ft.Column(
                        controls=[ft.Text("Recent Trends:", size=12, weight=ft.FontWeight.BOLD)] + trend_rows,
                        spacing=4,
                    ),
                    # Alerts
                    ft.Column(
                        controls=alert_items,
                        spacing=8,
                    ) if alert_items else ft.Container(),
                ],
                spacing=12,
            ),
            padding=15,
            bgcolor=ft.colors.PURPLE_50,
            border=ft.border.all(2, ft.colors.PURPLE_200),
            border_radius=8,
        )

    def _build_vitals_section(self) -> ft.Container:
        """Vital signs trend charts."""
        charts = []

        if "blood_pressure" in self.vitals_data:
            charts.append(
                TrendChart(
                    title="Systolic Blood Pressure",
                    data_points=self.vitals_data["blood_pressure"],
                    unit=" mmHg",
                    reference_range=(90, 130),
                    chart_type="line",
                )
            )

        if "weight" in self.vitals_data:
            charts.append(
                TrendChart(
                    title="Weight",
                    data_points=self.vitals_data["weight"],
                    unit=" kg",
                    chart_type="bar",
                )
            )

        if "hba1c" in self.vitals_data:
            charts.append(
                TrendChart(
                    title="HbA1c",
                    data_points=self.vitals_data["hba1c"],
                    unit="%",
                    reference_range=(4.0, 7.0),
                    chart_type="line",
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Vital Signs & Key Parameters", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=charts,
                        spacing=15,
                    ),
                ],
                spacing=10,
            ),
        )

    def _build_medication_timeline(self) -> ft.Container:
        """Medication timeline with start/end dates."""
        med_items = []

        # Separate active and discontinued
        active_meds = [m for m in self.medications if m["status"] == "active"]
        discontinued_meds = [m for m in self.medications if m["status"] == "discontinued"]

        # Active medications
        if active_meds:
            med_items.append(
                ft.Text("Active Medications", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700)
            )
            for med in active_meds:
                duration = (datetime.now() - med["start_date"]).days
                duration_text = f"{duration // 365}+ years" if duration >= 365 else f"{duration // 30}+ months" if duration >= 30 else f"{duration} days"

                med_items.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.MEDICATION, color=ft.colors.GREEN_600, size=20),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"{med['name']} {med['strength']} {med['frequency']}",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"Started: {med['start_date'].strftime('%d-%b-%Y')} ({duration_text})",
                                            size=11,
                                            color=ft.colors.GREY_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREEN_200),
                        border_radius=6,
                        bgcolor=ft.colors.GREEN_50,
                    )
                )

        # Discontinued medications
        if discontinued_meds:
            med_items.append(
                ft.Text("Discontinued Medications", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_600)
            )
            for med in discontinued_meds:
                duration = (med["end_date"] - med["start_date"]).days
                duration_text = f"{duration // 30} months" if duration >= 30 else f"{duration} days"

                med_items.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.BLOCK, color=ft.colors.GREY_400, size=20),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"{med['name']} {med['strength']} {med['frequency']}",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.GREY_700,
                                        ),
                                        ft.Text(
                                            f"{med['start_date'].strftime('%d-%b-%Y')} to {med['end_date'].strftime('%d-%b-%Y')} ({duration_text})",
                                            size=11,
                                            color=ft.colors.GREY_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=6,
                        bgcolor=ft.colors.GREY_50,
                    )
                )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Medication Timeline", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=med_items,
                        spacing=10,
                    ),
                ],
                spacing=10,
            ),
        )

    def _build_visit_card(self, visit: Dict, expanded: bool = False) -> ft.Container:
        """Expandable visit history card."""
        # Visit preview
        days_ago = (datetime.now() - visit["date"]).days
        time_text = f"Today" if days_ago == 0 else f"Yesterday" if days_ago == 1 else f"{days_ago} days ago"

        card_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(visit["date"].strftime("%d %b %Y"), size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(time_text, size=11, color=ft.colors.GREY_600),
                            ],
                            spacing=2,
                        ),
                        ft.Container(expand=True),
                        ft.Icon(
                            ft.icons.EXPAND_MORE if not expanded else ft.icons.EXPAND_LESS,
                            color=ft.colors.GREY_600,
                        ),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.ASSIGNMENT, color=ft.colors.BLUE_600, size=18),
                        ft.Text(visit["chief_complaint"], size=13, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.LOCAL_HOSPITAL, color=ft.colors.RED_600, size=18),
                        ft.Text(visit["diagnosis"], size=13, color=ft.colors.GREY_700),
                    ],
                    spacing=8,
                ),
            ],
            spacing=8,
        )

        # Add expanded details if needed
        if expanded:
            card_content.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Divider(height=1),
                            ft.Text("Clinical Notes:", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(visit["notes"], size=12, color=ft.colors.GREY_700),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.only(top=10),
                )
            )

        return ft.Container(
            content=card_content,
            padding=15,
            border=ft.border.all(1, ft.colors.BLUE_200),
            border_radius=8,
            bgcolor=ft.colors.BLUE_50,
            ink=True,
            on_click=lambda _: self.on_visit_click(visit["id"]) if self.on_visit_click else None,
        )

    def _build_visits_section(self) -> ft.Container:
        """Visit history as expandable cards."""
        visit_cards = [self._build_visit_card(visit) for visit in self.visits]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Visit History", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=visit_cards,
                        spacing=10,
                    ),
                ],
                spacing=10,
            ),
        )

    def _build_lab_results_section(self) -> ft.Container:
        """Lab results with abnormal highlighting."""
        lab_rows = []

        for lab in self.lab_results:
            # Determine color based on abnormality
            bg_color = ft.colors.WHITE
            text_color = ft.colors.GREY_900
            border_color = ft.colors.GREY_300

            if lab["abnormal"]:
                if lab["direction"] == "high":
                    bg_color = ft.colors.RED_50
                    text_color = ft.colors.RED_900
                    border_color = ft.colors.RED_300
                elif lab["direction"] == "low":
                    bg_color = ft.colors.BLUE_50
                    text_color = ft.colors.BLUE_900
                    border_color = ft.colors.BLUE_300

            lab_rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(lab["test"], size=13, weight=ft.FontWeight.BOLD, color=text_color),
                                    ft.Text(
                                        lab["date"].strftime("%d-%b-%Y"),
                                        size=10,
                                        color=ft.colors.GREY_600,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"{lab['value']} {lab['unit']}",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=text_color,
                                    ),
                                    ft.Text(
                                        f"Ref: {lab['reference']}",
                                        size=10,
                                        color=ft.colors.GREY_600,
                                    ),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                            ft.Icon(
                                ft.icons.ARROW_UPWARD if lab.get("direction") == "high" else ft.icons.ARROW_DOWNWARD if lab.get("direction") == "low" else ft.icons.CHECK,
                                color=text_color if lab["abnormal"] else ft.colors.GREEN_600,
                                size=20,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=12,
                    border=ft.border.all(1, border_color),
                    border_radius=6,
                    bgcolor=bg_color,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Laboratory Results", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=lab_rows,
                        spacing=8,
                    ),
                ],
                spacing=10,
            ),
        )

    def _build_care_gaps_section(self) -> ft.Container:
        """Care gaps section with actionable items."""
        gap_items = []

        for gap in self.care_gaps:
            # Color based on priority
            if gap["priority"] == "high":
                bg_color = ft.colors.RED_50
                border_color = ft.colors.RED_300
                icon_color = ft.colors.RED_600
                icon = ft.icons.PRIORITY_HIGH
            elif gap["priority"] == "medium":
                bg_color = ft.colors.ORANGE_50
                border_color = ft.colors.ORANGE_300
                icon_color = ft.colors.ORANGE_600
                icon = ft.icons.WARNING
            else:
                bg_color = ft.colors.BLUE_50
                border_color = ft.colors.BLUE_300
                icon_color = ft.colors.BLUE_600
                icon = ft.icons.INFO

            gap_items.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icon, color=icon_color, size=20),
                                    ft.Text(gap["title"], size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8,
                            ),
                            ft.Text(gap["description"], size=12, color=ft.colors.GREY_700),
                            ft.ElevatedButton(
                                text=gap["action"],
                                icon=ft.icons.PLAY_ARROW,
                                on_click=lambda _, g=gap: self.on_care_gap_action(g) if self.on_care_gap_action else None,
                                style=ft.ButtonStyle(
                                    color=ft.colors.WHITE,
                                    bgcolor=icon_color,
                                ),
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=12,
                    border=ft.border.all(2, border_color),
                    border_radius=8,
                    bgcolor=bg_color,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.HEALTH_AND_SAFETY, color=ft.colors.ORANGE_600, size=24),
                            ft.Text("Care Gaps & Recommendations", size=18, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Column(
                        controls=gap_items,
                        spacing=12,
                    ),
                ],
                spacing=10,
            ),
        )

    def _build_filters(self) -> ft.Container:
        """Date range and category filters."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Filter:", size=13, weight=ft.FontWeight.BOLD),
                    ft.Dropdown(
                        options=[
                            ft.dropdown.Option("all", "All Time"),
                            ft.dropdown.Option("1month", "Last Month"),
                            ft.dropdown.Option("3months", "Last 3 Months"),
                            ft.dropdown.Option("6months", "Last 6 Months"),
                            ft.dropdown.Option("1year", "Last Year"),
                        ],
                        value=self.selected_date_range,
                        width=150,
                        height=40,
                        text_size=12,
                    ),
                    ft.Dropdown(
                        options=[
                            ft.dropdown.Option("all", "All Categories"),
                            ft.dropdown.Option("visits", "Visits"),
                            ft.dropdown.Option("labs", "Lab Results"),
                            ft.dropdown.Option("medications", "Medications"),
                            ft.dropdown.Option("vitals", "Vital Signs"),
                        ],
                        value=self.selected_category,
                        width=180,
                        height=40,
                        text_size=12,
                    ),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.only(bottom=15),
        )

    def build(self):
        """Build the timeline UI."""
        # Main content
        self.content_container = ft.Column(
            controls=[
                # Filters
                self._build_filters(),
                # AI Summary
                self._build_ai_summary_card(),
                ft.Divider(height=20),
                # Care Gaps
                self._build_care_gaps_section(),
                ft.Divider(height=20),
                # Vitals
                self._build_vitals_section(),
                ft.Divider(height=20),
                # Medications
                self._build_medication_timeline(),
                ft.Divider(height=20),
                # Visits
                self._build_visits_section(),
                ft.Divider(height=20),
                # Lab Results
                self._build_lab_results_section(),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        # Load data
        self.load_data()

        return ft.Container(
            content=ft.Stack(
                controls=[
                    self.content_container,
                    ft.Container(
                        content=self.loading_indicator,
                        alignment=ft.alignment.center,
                        visible=self.loading_indicator.visible,
                    ),
                ],
            ),
            expand=True,
        )
