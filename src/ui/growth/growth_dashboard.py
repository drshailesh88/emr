"""Growth Dashboard Component - Practice analytics and actionable insights."""

import flet as ft
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from .metrics_card import MetricsCard


class GrowthDashboard(ft.UserControl):
    """
    Comprehensive practice growth dashboard with metrics, trends, and actionable recommendations.
    """

    def __init__(
        self,
        on_action_click: Optional[Callable] = None,
    ):
        super().__init__()
        self.on_action_click = on_action_click

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
        # TODO: Connect to actual analytics service
        # For now, using mock data
        self.metrics = {
            "today_patients": {"value": 24, "trend": 12.5, "sparkline": [18, 20, 22, 19, 24, 23, 24]},
            "week_revenue": {"value": "₹45,600", "trend": 8.3, "sparkline": [32000, 38000, 42000, 40000, 45600]},
            "new_patients": {"value": 8, "trend": -5.2, "sparkline": [10, 12, 9, 8, 11, 9, 8]},
            "avg_rating": {"value": "4.7", "trend": 2.1, "sparkline": [4.5, 4.6, 4.6, 4.7, 4.7]},
        }

        self.revenue_data = {
            "daily": [
                {"date": datetime.now() - timedelta(days=6), "amount": 5200},
                {"date": datetime.now() - timedelta(days=5), "amount": 6800},
                {"date": datetime.now() - timedelta(days=4), "amount": 7200},
                {"date": datetime.now() - timedelta(days=3), "amount": 6400},
                {"date": datetime.now() - timedelta(days=2), "amount": 8100},
                {"date": datetime.now() - timedelta(days=1), "amount": 6900},
                {"date": datetime.now(), "amount": 5000},
            ],
            "weekly": [
                {"date": datetime.now() - timedelta(weeks=4), "amount": 38000},
                {"date": datetime.now() - timedelta(weeks=3), "amount": 42000},
                {"date": datetime.now() - timedelta(weeks=2), "amount": 40000},
                {"date": datetime.now() - timedelta(weeks=1), "amount": 45600},
            ],
            "monthly": [
                {"date": datetime.now() - timedelta(days=150), "amount": 165000},
                {"date": datetime.now() - timedelta(days=120), "amount": 172000},
                {"date": datetime.now() - timedelta(days=90), "amount": 168000},
                {"date": datetime.now() - timedelta(days=60), "amount": 180000},
                {"date": datetime.now() - timedelta(days=30), "amount": 182400},
            ],
        }

        self.patient_sources = {
            "Referral": 45,
            "Google Search": 25,
            "Walk-in": 15,
            "Social Media": 10,
            "Other": 5,
        }

        self.followup_stats = {
            "total_due": 120,
            "completed": 72,
            "overdue": 15,
            "scheduled": 33,
        }

        self.reviews = [
            {
                "patient": "R***a S.",
                "rating": 5,
                "comment": "Excellent doctor, very attentive and thorough.",
                "date": datetime.now() - timedelta(days=1),
                "sentiment": "positive",
            },
            {
                "patient": "A***t K.",
                "rating": 4,
                "comment": "Good experience, but waiting time was long.",
                "date": datetime.now() - timedelta(days=3),
                "sentiment": "neutral",
            },
            {
                "patient": "P***a M.",
                "rating": 5,
                "comment": "Best cardiologist in the area. Highly recommend!",
                "date": datetime.now() - timedelta(days=5),
                "sentiment": "positive",
            },
        ]

        self.recommendations = [
            {
                "type": "followup",
                "priority": "high",
                "title": "15 patients overdue for follow-up",
                "description": "These patients haven't returned for scheduled follow-ups. Reaching out may prevent complications.",
                "action": "Send reminders",
                "icon": ft.icons.SCHEDULE,
                "color": ft.colors.ORANGE_600,
            },
            {
                "type": "rating",
                "priority": "medium",
                "title": "Rating dropped by 0.2 stars",
                "description": "Recent feedback mentions long waiting times. Consider optimizing scheduling.",
                "action": "View feedback",
                "icon": ft.icons.STAR_RATE,
                "color": ft.colors.AMBER_600,
            },
            {
                "type": "schedule",
                "priority": "low",
                "title": "Wednesdays are slow",
                "description": "Average only 12 patients on Wednesdays vs 22 on other days. Consider promotions or extending hours.",
                "action": "Analyze schedule",
                "icon": ft.icons.CALENDAR_TODAY,
                "color": ft.colors.BLUE_600,
            },
            {
                "type": "acquisition",
                "priority": "medium",
                "title": "45% patients from referrals",
                "description": "Your referral rate is excellent! Consider a referral rewards program to boost it further.",
                "action": "Set up rewards",
                "icon": ft.icons.PEOPLE,
                "color": ft.colors.GREEN_600,
            },
        ]

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
        """Revenue trend chart with period toggle."""
        # Get data for selected period
        data = self.revenue_data.get(self.selected_period.lower() + "ly", self.revenue_data["daily"])

        # Calculate max for scaling
        max_amount = max(d["amount"] for d in data) * 1.1
        chart_height = 200

        # Create bars
        bars = []
        for i, item in enumerate(data):
            bar_height = (item["amount"] / max_amount) * chart_height
            date_label = item["date"].strftime("%d %b") if self.selected_period == "day" else item["date"].strftime("%d %b")

            bars.append(
                ft.Column(
                    controls=[
                        ft.Text(
                            f"₹{item['amount']:,}",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY_700,
                        ),
                        ft.Container(
                            width=50,
                            height=bar_height,
                            bgcolor=ft.colors.GREEN_400,
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                            tooltip=f"{date_label}: ₹{item['amount']:,}",
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
                            ft.Text("Revenue Trend", size=18, weight=ft.FontWeight.BOLD),
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

    def _build_reviews_section(self) -> ft.Container:
        """Recent reviews with sentiment indicators."""
        review_items = []

        for review in self.reviews:
            # Sentiment color
            sentiment_color = ft.colors.GREEN_600 if review["sentiment"] == "positive" else ft.colors.ORANGE_600 if review["sentiment"] == "neutral" else ft.colors.RED_600

            # Stars
            stars = [
                ft.Icon(
                    ft.icons.STAR if i < review["rating"] else ft.icons.STAR_BORDER,
                    color=ft.colors.AMBER_600,
                    size=16,
                )
                for i in range(5)
            ]

            days_ago = (datetime.now() - review["date"]).days
            time_text = "Today" if days_ago == 0 else "Yesterday" if days_ago == 1 else f"{days_ago} days ago"

            review_items.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(review["patient"], size=13, weight=ft.FontWeight.BOLD),
                                    ft.Container(expand=True),
                                    ft.Text(time_text, size=11, color=ft.colors.GREY_600),
                                ],
                            ),
                            ft.Row(controls=stars, spacing=2),
                            ft.Text(
                                review["comment"],
                                size=12,
                                color=ft.colors.GREY_700,
                                italic=True,
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=12,
                    border=ft.border.all(1, ft.colors.with_opacity(0.3, sentiment_color)),
                    border_radius=8,
                    bgcolor=ft.colors.with_opacity(0.05, sentiment_color),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Recent Reviews", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=review_items,
                        spacing=10,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=12,
            bgcolor=ft.colors.WHITE,
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
                    # Patient sources and reviews
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                content=self._build_patient_acquisition_funnel(),
                                col={"sm": 12, "lg": 6},
                            ),
                            ft.Container(
                                content=self._build_reviews_section(),
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
