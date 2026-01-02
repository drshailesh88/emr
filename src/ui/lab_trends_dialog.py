"""Lab trends dialog for viewing investigation trends over time."""

import flet as ft
from typing import List, Optional
from datetime import date

from ..models.schemas import Investigation
from ..services.reference_ranges import get_reference_range
from ..services.trend_calculator import prepare_chart_data, calculate_trend, get_trend_summary
from .components.lab_trend_chart import LabTrendChart


class LabTrendsDialog:
    """Dialog for viewing lab trends with time range controls."""

    def __init__(
        self,
        test_name: str,
        investigations: List[Investigation],
        all_investigations: List[Investigation] = None,
    ):
        """
        Initialize lab trends dialog.

        Args:
            test_name: Name of the test to show
            investigations: List of investigations for this test
            all_investigations: All investigations for the patient (for comparison)
        """
        self.test_name = test_name
        self.investigations = investigations
        self.all_investigations = all_investigations or investigations
        self.time_range = "All"
        self.dialog: Optional[ft.AlertDialog] = None
        self.chart_container: Optional[ft.Container] = None

    def show(self, page: ft.Page):
        """Show the dialog."""
        # Get reference range
        normal_min, normal_max, unit = get_reference_range(self.test_name)

        # Prepare initial data
        data_points, min_val, max_val = prepare_chart_data(
            self.investigations,
            self.test_name,
            self.time_range
        )

        # Calculate trend
        values = [p["value"] for p in data_points]
        dates = [p["date"] for p in data_points]
        trend_arrow = calculate_trend(values, dates)

        # Get current value
        current_value = values[-1] if values else None
        current_str = f"{current_value:.2f} {unit}" if current_value is not None else "N/A"

        # Create trend summary
        trend_summary = ""
        if values:
            trend_summary = get_trend_summary(
                self.test_name,
                values,
                dates,
                normal_min,
                normal_max
            )

        # Time range buttons
        time_range_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    "6M",
                    on_click=lambda e: self._change_time_range("6M"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700 if self.time_range == "6M" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.time_range == "6M" else ft.Colors.BLACK,
                    ),
                ),
                ft.ElevatedButton(
                    "1Y",
                    on_click=lambda e: self._change_time_range("1Y"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700 if self.time_range == "1Y" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.time_range == "1Y" else ft.Colors.BLACK,
                    ),
                ),
                ft.ElevatedButton(
                    "All",
                    on_click=lambda e: self._change_time_range("All"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700 if self.time_range == "All" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.time_range == "All" else ft.Colors.BLACK,
                    ),
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.END,
        )

        # Create chart
        chart = LabTrendChart(
            test_name=self.test_name,
            data_points=data_points,
            normal_min=normal_min,
            normal_max=normal_max,
            unit=unit,
            width=700,
            height=350,
        )

        # Chart container (for updates)
        self.chart_container = ft.Container(
            content=chart,
            expand=True,
        )

        # Summary header
        summary_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Current Value", size=11, color=ft.Colors.GREY_600),
                        ft.Text(current_str, size=16, weight=ft.FontWeight.BOLD),
                    ], spacing=2),
                    ft.Container(width=20),
                    ft.Column([
                        ft.Text("Normal Range", size=11, color=ft.Colors.GREY_600),
                        ft.Text(
                            self._format_normal_range(normal_min, normal_max, unit),
                            size=14,
                            color=ft.Colors.GREEN_700
                        ),
                    ], spacing=2),
                    ft.Container(width=20),
                    ft.Column([
                        ft.Text("Trend", size=11, color=ft.Colors.GREY_600),
                        ft.Text(
                            f"{trend_arrow} {self._trend_text(trend_arrow)}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=self._trend_color(trend_arrow)
                        ),
                    ], spacing=2),
                ], alignment=ft.MainAxisAlignment.START, spacing=30),
                ft.Divider(height=10),
                ft.Text(trend_summary, size=12, color=ft.Colors.GREY_700, italic=True),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
        )

        # Dialog content
        content = ft.Container(
            content=ft.Column(
                [
                    summary_header,
                    time_range_buttons,
                    self.chart_container,
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=800,
            height=600,
        )

        # Create dialog
        self.dialog = ft.AlertDialog(
            title=ft.Text(f"Lab Trends: {self.test_name}", size=18, weight=ft.FontWeight.BOLD),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(page)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.open(self.dialog)
        page.update()

    def _change_time_range(self, new_range: str):
        """Change the time range filter."""
        self.time_range = new_range

        # Refresh chart
        normal_min, normal_max, unit = get_reference_range(self.test_name)
        data_points, min_val, max_val = prepare_chart_data(
            self.investigations,
            self.test_name,
            self.time_range
        )

        # Update chart
        chart = LabTrendChart(
            test_name=self.test_name,
            data_points=data_points,
            normal_min=normal_min,
            normal_max=normal_max,
            unit=unit,
            width=700,
            height=350,
        )

        self.chart_container.content = chart

        # Update dialog
        if self.dialog and hasattr(self.dialog, 'page') and self.dialog.page:
            self.dialog.page.update()

    def _close_dialog(self, page: ft.Page):
        """Close the dialog."""
        if self.dialog:
            page.close(self.dialog)
            page.update()

    def _format_normal_range(self, min_val, max_val, unit):
        """Format normal range for display."""
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val} {unit}"
        elif min_val is not None:
            return f">{min_val} {unit}"
        elif max_val is not None:
            return f"<{max_val} {unit}"
        else:
            return "Not defined"

    def _trend_text(self, arrow: str) -> str:
        """Convert trend arrow to text."""
        if arrow == "↑":
            return "Rising"
        elif arrow == "↓":
            return "Falling"
        else:
            return "Stable"

    def _trend_color(self, arrow: str) -> str:
        """Get color for trend arrow."""
        if arrow == "↑":
            return ft.Colors.ORANGE_700
        elif arrow == "↓":
            return ft.Colors.BLUE_700
        else:
            return ft.Colors.GREY_600
