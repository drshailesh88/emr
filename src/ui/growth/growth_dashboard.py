"""Growth Dashboard Component - Practice analytics and actionable insights."""

import flet as ft
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta, date
from .metrics_card import MetricsCard
from .charts import BarChart, PieChart, LineChart
from ...services.analytics.practice_analytics import PracticeAnalytics
from ...services.analytics.patient_acquisition import PatientAcquisition
from ...services.analytics.retention_tracker import RetentionTracker


class GrowthDashboard(ft.UserControl):
    """
    Comprehensive practice growth dashboard with metrics, trends, and actionable recommendations.
    """

    def __init__(
        self,
        db_service,
        on_action_click: Optional[Callable] = None,
    ):
        super().__init__()
        self.db_service = db_service
        self.on_action_click = on_action_click

        # Initialize analytics services
        self.practice_analytics = PracticeAnalytics(db_service)
        self.patient_acquisition = PatientAcquisition(db_service)
        self.retention_tracker = RetentionTracker(db_service)

        # Time period selection
        self.selected_period = "week"  # "day", "week", "month"

        # Data (will be loaded from analytics service)
        self.metrics = {}
        self.revenue_data = []
        self.patient_sources = {}
        self.followup_stats = {}
        self.reviews = []
        self.recommendations = []

        # UI components
        self.loading = True

    def load_data(self):
        """Load analytics data from services."""
        try:
            # Get real metrics from database
            total_patients = self.practice_analytics.get_total_patients()
            patients_this_month = self.practice_analytics.get_patients_this_month()
            visits_today = self.practice_analytics.get_visits_today()
            visits_this_week = self.practice_analytics.get_visits_this_week()

            # Calculate trends (simplified - comparing to previous periods)
            # For a real implementation, you'd compare to last week/month
            today_trend = 0.0  # Placeholder
            week_trend = 0.0  # Placeholder
            new_patients_trend = self.patient_acquisition.get_growth_rate()

            # Build metrics
            self.metrics = {
                "today_patients": {
                    "value": visits_today,
                    "trend": today_trend,
                    "sparkline": [visits_today] * 7  # Simplified
                },
                "week_revenue": {
                    "value": f"₹0",  # Revenue tracking not implemented yet
                    "trend": week_trend,
                    "sparkline": [0] * 5
                },
                "new_patients": {
                    "value": patients_this_month,
                    "trend": new_patients_trend,
                    "sparkline": [patients_this_month] * 7
                },
                "avg_rating": {
                    "value": "N/A",  # Rating tracking not implemented yet
                    "trend": 0.0,
                    "sparkline": [4.5] * 5
                },
            }
        except Exception as e:
            # Fallback to mock data if real data fails
            self.metrics = {
                "today_patients": {"value": 0, "trend": 0, "sparkline": [0]},
                "week_revenue": {"value": "₹0", "trend": 0, "sparkline": [0]},
                "new_patients": {"value": 0, "trend": 0, "sparkline": [0]},
                "avg_rating": {"value": "N/A", "trend": 0, "sparkline": [0]},
            }

        # Load visit data for revenue chart (using visits as proxy since no revenue tracking yet)
        try:
            # Get visits for last 7 days
            daily_visits = []
            for i in range(6, -1, -1):
                target_date = date.today() - timedelta(days=i)
                visits = self.db_service.get_visits_by_date(target_date)
                daily_visits.append({
                    "date": datetime.combine(target_date, datetime.min.time()),
                    "amount": len(visits)  # Using visit count as proxy
                })

            # Get visits for last 4 weeks
            weekly_visits = []
            for i in range(3, -1, -1):
                week_start = date.today() - timedelta(weeks=i+1)
                week_end = date.today() - timedelta(weeks=i)
                visits = self.db_service.get_visits_by_date_range(week_start, week_end)
                weekly_visits.append({
                    "date": datetime.combine(week_start, datetime.min.time()),
                    "amount": len(visits)
                })

            self.revenue_data = {
                "daily": daily_visits,
                "weekly": weekly_visits,
                "monthly": weekly_visits,  # Using weekly for now
            }
        except:
            # Fallback
            self.revenue_data = {
                "daily": [{"date": datetime.now(), "amount": 0}],
                "weekly": [{"date": datetime.now(), "amount": 0}],
                "monthly": [{"date": datetime.now(), "amount": 0}],
            }

        # Patient sources (placeholder - source tracking not implemented yet)
        self.patient_sources = {
            "Walk-in": total_patients,  # Default all to walk-in for now
        }

        # Follow-up stats
        try:
            returning = self.retention_tracker.get_returning_patients()
            self.followup_stats = {
                "total_due": total_patients,
                "completed": returning,
                "overdue": 0,  # Not tracked yet
                "scheduled": total_patients - returning,
            }
        except:
            self.followup_stats = {
                "total_due": 0,
                "completed": 0,
                "overdue": 0,
                "scheduled": 0,
            }

        # Reviews (not implemented yet - placeholder)
        self.reviews = []

        # Generate recommendations based on real data
        self.recommendations = []
        try:
            # Recommendation 1: Churned patients
            churned = self.retention_tracker.get_patient_churn(180)
            if churned:
                self.recommendations.append({
                    "type": "followup",
                    "priority": "high",
                    "title": f"{len(churned)} patients haven't visited in 6 months",
                    "description": "These patients may have churned. Reaching out could win them back.",
                    "action": "View list",
                    "icon": ft.icons.SCHEDULE,
                    "color": ft.colors.ORANGE_600,
                })

            # Recommendation 2: Patient growth
            if new_patients_trend > 0:
                self.recommendations.append({
                    "type": "acquisition",
                    "priority": "medium",
                    "title": f"Patient growth up {new_patients_trend:.1f}%",
                    "description": "Your practice is growing! Keep up the momentum.",
                    "action": "View details",
                    "icon": ft.icons.TRENDING_UP,
                    "color": ft.colors.GREEN_600,
                })
            elif new_patients_trend < -10:
                self.recommendations.append({
                    "type": "acquisition",
                    "priority": "high",
                    "title": f"Patient growth down {abs(new_patients_trend):.1f}%",
                    "description": "New patient acquisition is declining. Consider marketing efforts.",
                    "action": "View details",
                    "icon": ft.icons.TRENDING_DOWN,
                    "color": ft.colors.RED_600,
                })

            # Recommendation 3: Today's visits
            if visits_today == 0:
                self.recommendations.append({
                    "type": "schedule",
                    "priority": "low",
                    "title": "No visits recorded today",
                    "description": "Make sure to log all patient visits for accurate analytics.",
                    "action": "Add visit",
                    "icon": ft.icons.CALENDAR_TODAY,
                    "color": ft.colors.BLUE_600,
                })
            elif visits_today > 20:
                self.recommendations.append({
                    "type": "schedule",
                    "priority": "medium",
                    "title": "Busy day - excellent!",
                    "description": f"{visits_today} visits today. Your practice is thriving!",
                    "action": "View today",
                    "icon": ft.icons.CELEBRATION,
                    "color": ft.colors.GREEN_600,
                })

            # Add default recommendation if none generated
            if not self.recommendations:
                self.recommendations.append({
                    "type": "info",
                    "priority": "low",
                    "title": "Start tracking your practice",
                    "description": "Add patients and visits to get personalized insights.",
                    "action": "Add patient",
                    "icon": ft.icons.INFO,
                    "color": ft.colors.BLUE_600,
                })
        except:
            pass

        self.loading = False
        self.update()

    def _build_metrics_grid(self) -> ft.Container:
        """Grid of key metrics cards."""
        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=MetricsCard(
                            title="Today's Patients",
                            value=str(self.metrics["today_patients"]["value"]),
                            trend_percent=self.metrics["today_patients"]["trend"],
                            trend_label="vs yesterday",
                            icon=ft.icons.PEOPLE,
                            icon_color=ft.colors.BLUE_600,
                            sparkline_data=self.metrics["today_patients"]["sparkline"],
                            loading=self.loading,
                        ),
                        col={"sm": 12, "md": 6, "lg": 3},
                    ),
                    ft.Container(
                        content=MetricsCard(
                            title="This Week Revenue",
                            value=self.metrics["week_revenue"]["value"],
                            trend_percent=self.metrics["week_revenue"]["trend"],
                            trend_label="vs last week",
                            icon=ft.icons.CURRENCY_RUPEE,
                            icon_color=ft.colors.GREEN_600,
                            sparkline_data=self.metrics["week_revenue"]["sparkline"],
                            loading=self.loading,
                        ),
                        col={"sm": 12, "md": 6, "lg": 3},
                    ),
                    ft.Container(
                        content=MetricsCard(
                            title="New Patients",
                            value=str(self.metrics["new_patients"]["value"]),
                            trend_percent=self.metrics["new_patients"]["trend"],
                            trend_label="vs last week",
                            icon=ft.icons.PERSON_ADD,
                            icon_color=ft.colors.PURPLE_600,
                            sparkline_data=self.metrics["new_patients"]["sparkline"],
                            loading=self.loading,
                        ),
                        col={"sm": 12, "md": 6, "lg": 3},
                    ),
                    ft.Container(
                        content=MetricsCard(
                            title="Average Rating",
                            value=self.metrics["avg_rating"]["value"],
                            trend_percent=self.metrics["avg_rating"]["trend"],
                            trend_label="vs last month",
                            icon=ft.icons.STAR,
                            icon_color=ft.colors.AMBER_600,
                            sparkline_data=self.metrics["avg_rating"]["sparkline"],
                            loading=self.loading,
                        ),
                        col={"sm": 12, "md": 6, "lg": 3},
                    ),
                ],
            ),
        )

    def _build_revenue_chart(self) -> ft.Container:
        """Visits trend chart with period toggle."""
        # Get data for selected period
        data = self.revenue_data.get(self.selected_period.lower() + "ly", self.revenue_data["daily"])

        if not data or len(data) == 0:
            return ft.Container(
                content=ft.Text("No visit data available", color=ft.colors.GREY_600),
                padding=20,
            )

        # Calculate max for scaling
        max_amount = max(d["amount"] for d in data) * 1.1 if data else 1
        if max_amount == 0:
            max_amount = 1
        chart_height = 200

        # Create bars
        bars = []
        for i, item in enumerate(data):
            bar_height = (item["amount"] / max_amount) * chart_height if max_amount > 0 else 0
            date_label = item["date"].strftime("%d %b")

            bars.append(
                ft.Column(
                    controls=[
                        ft.Text(
                            f"{item['amount']}",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY_700,
                        ),
                        ft.Container(
                            width=50,
                            height=max(bar_height, 5),  # Minimum height for visibility
                            bgcolor=ft.colors.BLUE_400,
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                            tooltip=f"{date_label}: {item['amount']} visits",
                        ),
                        ft.Text(
                            date_label,
                            size=10,
                            color=ft.colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header with period toggle
                    ft.Row(
                        controls=[
                            ft.Text("Visits Trend", size=18, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.SegmentedButton(
                                selected={"day"} if self.selected_period == "day" else {"week"} if self.selected_period == "week" else {"month"},
                                segments=[
                                    ft.Segment(value="day", label=ft.Text("Daily")),
                                    ft.Segment(value="week", label=ft.Text("Weekly")),
                                    ft.Segment(value="month", label=ft.Text("Monthly")),
                                ],
                                on_change=lambda e: self._change_period(e.control.selected.pop()),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Chart
                    ft.Container(
                        content=ft.Row(
                            controls=bars,
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            spacing=10,
                        ),
                        padding=ft.padding.only(top=20, bottom=10),
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=12,
            bgcolor=ft.colors.WHITE,
        )

    def _change_period(self, period: str):
        """Change revenue chart period."""
        self.selected_period = period
        self.update()

    def _build_patient_acquisition_funnel(self) -> ft.Container:
        """Patient acquisition source visualization."""
        # Calculate total
        total = sum(self.patient_sources.values())

        # Create bars
        source_items = []
        colors = [ft.colors.BLUE_400, ft.colors.GREEN_400, ft.colors.PURPLE_400, ft.colors.ORANGE_400, ft.colors.GREY_400]

        for i, (source, count) in enumerate(self.patient_sources.items()):
            percentage = (count / total) * 100
            color = colors[i % len(colors)]

            source_items.append(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=12,
                                    height=12,
                                    bgcolor=color,
                                    border_radius=6,
                                ),
                                ft.Text(source, size=13, weight=ft.FontWeight.W_500),
                                ft.Container(expand=True),
                                ft.Text(f"{count} ({percentage:.0f}%)", size=13, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            width=300,
                            height=8,
                            bgcolor=ft.colors.GREY_200,
                            border_radius=4,
                            content=ft.Container(
                                width=300 * (percentage / 100),
                                height=8,
                                bgcolor=color,
                                border_radius=4,
                            ),
                        ),
                    ],
                    spacing=6,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Patient Acquisition Sources", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=source_items,
                        spacing=12,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=12,
            bgcolor=ft.colors.WHITE,
        )

    def _build_followup_compliance(self) -> ft.Container:
        """Follow-up compliance gauge/pie chart."""
        total = self.followup_stats["total_due"]
        completed = self.followup_stats["completed"]
        overdue = self.followup_stats["overdue"]
        scheduled = self.followup_stats["scheduled"]

        compliance_rate = (completed / total) * 100 if total > 0 else 0

        # Determine color based on compliance
        gauge_color = ft.colors.GREEN_600 if compliance_rate >= 80 else ft.colors.ORANGE_600 if compliance_rate >= 60 else ft.colors.RED_600

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Follow-up Compliance", size=18, weight=ft.FontWeight.BOLD),
                    # Gauge visualization (simplified)
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    f"{compliance_rate:.0f}%",
                                    size=48,
                                    weight=ft.FontWeight.BOLD,
                                    color=gauge_color,
                                ),
                                ft.Text(
                                    "Compliance Rate",
                                    size=13,
                                    color=ft.colors.GREY_600,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                    ),
                    # Stats breakdown
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_600, size=20),
                                    ft.Text(f"Completed: {completed}", size=13),
                                ],
                                spacing=8,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.icons.SCHEDULE, color=ft.colors.BLUE_600, size=20),
                                    ft.Text(f"Scheduled: {scheduled}", size=13),
                                ],
                                spacing=8,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.icons.WARNING, color=ft.colors.RED_600, size=20),
                                    ft.Text(f"Overdue: {overdue}", size=13),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=12,
            bgcolor=ft.colors.WHITE,
        )

    def _build_top_diagnoses(self) -> ft.Container:
        """Top diagnoses chart."""
        try:
            # Get top diagnoses from database
            top_diagnoses = self.practice_analytics.get_top_diagnoses(5)

            if not top_diagnoses:
                return ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Top Diagnoses", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("No diagnosis data available yet", color=ft.colors.GREY_600, size=13),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=12,
                    bgcolor=ft.colors.WHITE,
                )

            # Convert to chart data
            chart_data = [
                {"label": diagnosis[:20], "value": count}
                for diagnosis, count in top_diagnoses
            ]

            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Top Diagnoses", size=18, weight=ft.FontWeight.BOLD),
                        BarChart(data=chart_data, color=ft.colors.PURPLE_400, height=150),
                    ],
                    spacing=15,
                ),
                padding=20,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=12,
                bgcolor=ft.colors.WHITE,
            )
        except Exception as e:
            return ft.Container(
                content=ft.Text(f"Error loading diagnoses: {str(e)}", color=ft.colors.RED_600),
                padding=20,
            )

    def _build_recommendations_section(self) -> ft.Container:
        """Actionable recommendations."""
        recommendation_items = []

        for rec in self.recommendations:
            # Priority badge
            priority_color = ft.colors.RED_600 if rec["priority"] == "high" else ft.colors.ORANGE_600 if rec["priority"] == "medium" else ft.colors.BLUE_600

            recommendation_items.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(rec["icon"], color=rec["color"], size=24),
                                    ft.Column(
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text(rec["title"], size=14, weight=ft.FontWeight.BOLD),
                                                    ft.Container(
                                                        content=ft.Text(
                                                            rec["priority"].upper(),
                                                            size=9,
                                                            weight=ft.FontWeight.BOLD,
                                                            color=ft.colors.WHITE,
                                                        ),
                                                        bgcolor=priority_color,
                                                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                                        border_radius=4,
                                                    ),
                                                ],
                                                spacing=8,
                                            ),
                                            ft.Text(
                                                rec["description"],
                                                size=12,
                                                color=ft.colors.GREY_700,
                                            ),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                ],
                                spacing=12,
                            ),
                            ft.ElevatedButton(
                                text=rec["action"],
                                icon=ft.icons.PLAY_ARROW,
                                on_click=lambda _, r=rec: self.on_action_click(r) if self.on_action_click else None,
                                style=ft.ButtonStyle(
                                    color=ft.colors.WHITE,
                                    bgcolor=rec["color"],
                                ),
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=15,
                    border=ft.border.all(2, ft.colors.with_opacity(0.3, rec["color"])),
                    border_radius=10,
                    bgcolor=ft.colors.with_opacity(0.05, rec["color"]),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.AMBER_600, size=24),
                            ft.Text("Actionable Recommendations", size=18, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Column(
                        controls=recommendation_items,
                        spacing=12,
                    ),
                ],
                spacing=15,
            ),
        )

    def build(self):
        """Build the growth dashboard UI."""
        # Load data
        self.load_data()

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Page header
                    ft.Row(
                        controls=[
                            ft.Text("Practice Growth Dashboard", size=24, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                tooltip="Refresh data",
                                on_click=lambda _: self.load_data(),
                            ),
                        ],
                    ),
                    ft.Divider(height=20),
                    # Metrics grid
                    self._build_metrics_grid(),
                    ft.Divider(height=20),
                    # Recommendations (top priority)
                    self._build_recommendations_section(),
                    ft.Divider(height=20),
                    # Revenue and analytics
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                content=self._build_revenue_chart(),
                                col={"sm": 12, "lg": 8},
                            ),
                            ft.Container(
                                content=self._build_followup_compliance(),
                                col={"sm": 12, "lg": 4},
                            ),
                        ],
                    ),
                    ft.Divider(height=20),
                    # Patient sources and top diagnoses
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                content=self._build_patient_acquisition_funnel(),
                                col={"sm": 12, "lg": 6},
                            ),
                            ft.Container(
                                content=self._build_top_diagnoses(),
                                col={"sm": 12, "lg": 6},
                            ),
                        ],
                    ),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )
