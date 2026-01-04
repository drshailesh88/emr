"""Lab trend chart component using Flet LineChart."""

import flet as ft
from typing import List, Dict, Optional
from datetime import datetime


class LabTrendChart(ft.UserControl):
    """
    A line chart component showing lab values over time.
    Highlights abnormal values and shows normal range as reference.
    """

    def __init__(
        self,
        test_name: str,
        data_points: List[Dict],  # [{date, value, is_abnormal}]
        normal_min: Optional[float] = None,
        normal_max: Optional[float] = None,
        unit: str = "",
        width: int = 600,
        height: int = 300,
    ):
        """
        Initialize lab trend chart.

        Args:
            test_name: Name of the test
            data_points: List of data points with date, value, is_abnormal
            normal_min: Lower bound of normal range
            normal_max: Upper bound of normal range
            unit: Unit of measurement
            width: Chart width in pixels
            height: Chart height in pixels
        """
        super().__init__()
        self.test_name = test_name
        self.data_points = data_points
        self.normal_min = normal_min
        self.normal_max = normal_max
        self.unit = unit
        self.width = width
        self.height = height

    def build(self):
        """Build the chart control."""
        if not self.data_points:
            return ft.Container(
                content=ft.Text(
                    "No data available for this test",
                    size=14,
                    color=ft.Colors.GREY_600,
                    italic=True
                ),
                padding=20,
                alignment=ft.alignment.center,
            )

        # Prepare chart data
        chart_data_points = []
        min_val = float('inf')
        max_val = float('-inf')

        # Convert dates to X-axis indices
        for i, point in enumerate(self.data_points):
            value = point["value"]
            chart_data_points.append(
                ft.LineChartDataPoint(
                    x=i,
                    y=value,
                    tooltip=self._format_tooltip(point),
                    selected_point_color=ft.Colors.RED if point.get("is_abnormal") else ft.Colors.BLUE,
                )
            )
            min_val = min(min_val, value)
            max_val = max(max_val, value)

        # Add padding to Y-axis
        y_padding = (max_val - min_val) * 0.15 if max_val > min_val else 1
        chart_min = min_val - y_padding
        chart_max = max_val + y_padding

        # Adjust min/max if we have normal range
        if self.normal_min is not None:
            chart_min = min(chart_min, self.normal_min - y_padding)
        if self.normal_max is not None:
            chart_max = max(chart_max, self.normal_max + y_padding)

        # Create line chart data series
        line_series = ft.LineChartData(
            data_points=chart_data_points,
            color=ft.Colors.BLUE_700,
            stroke_width=3,
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_700),
            below_line_fill=True,
        )

        # Create horizontal lines for normal range
        extra_lines = []
        if self.normal_min is not None:
            extra_lines.append(
                ft.ChartGridLines(
                    interval=chart_max - chart_min,  # Only one line
                    color=ft.Colors.GREEN_400,
                    width=2,
                    dash_pattern=[5, 5],
                )
            )
        if self.normal_max is not None:
            extra_lines.append(
                ft.ChartGridLines(
                    interval=chart_max - chart_min,
                    color=ft.Colors.GREEN_400,
                    width=2,
                    dash_pattern=[5, 5],
                )
            )

        # Create X-axis labels (dates)
        x_labels = []
        num_labels = min(len(self.data_points), 6)  # Show max 6 labels
        step = len(self.data_points) // num_labels if num_labels > 0 else 1
        step = max(1, step)

        for i in range(0, len(self.data_points), step):
            date_val = self.data_points[i]["date"]
            if isinstance(date_val, str):
                try:
                    date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
                except:
                    pass
            label = date_val.strftime("%d-%b") if hasattr(date_val, 'strftime') else str(date_val)
            x_labels.append(
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(label, size=10, color=ft.Colors.GREY_700)
                )
            )

        # Create Y-axis labels
        y_interval = (chart_max - chart_min) / 5
        y_labels = []
        for i in range(6):
            val = chart_min + (i * y_interval)
            y_labels.append(
                ft.ChartAxisLabel(
                    value=val,
                    label=ft.Text(f"{val:.1f}", size=10, color=ft.Colors.GREY_700)
                )
            )

        # Build the chart
        chart = ft.LineChart(
            data_series=[line_series],
            border=ft.border.all(1, ft.Colors.GREY_300),
            horizontal_grid_lines=ft.ChartGridLines(
                interval=(chart_max - chart_min) / 5,
                color=ft.Colors.with_opacity(0.2, ft.Colors.GREY_400),
                width=1,
            ),
            vertical_grid_lines=ft.ChartGridLines(
                interval=1,
                color=ft.Colors.with_opacity(0.2, ft.Colors.GREY_400),
                width=1,
            ),
            left_axis=ft.ChartAxis(
                labels=y_labels,
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels=x_labels,
                labels_size=30,
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
            min_y=chart_min,
            max_y=chart_max,
            min_x=0,
            max_x=len(self.data_points) - 1 if len(self.data_points) > 1 else 1,
            expand=True,
        )

        # Create normal range indicator
        normal_range_text = ""
        if self.normal_min is not None and self.normal_max is not None:
            normal_range_text = f"Normal: {self.normal_min}-{self.normal_max} {self.unit}"
        elif self.normal_min is not None:
            normal_range_text = f"Normal: >{self.normal_min} {self.unit}"
        elif self.normal_max is not None:
            normal_range_text = f"Normal: <{self.normal_max} {self.unit}"

        # Build the complete chart container
        return ft.Container(
            content=ft.Column(
                [
                    # Normal range indicator
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.GREEN_700),
                                ft.Text(normal_range_text, size=12, color=ft.Colors.GREEN_700),
                            ],
                            spacing=5,
                        ),
                        padding=ft.padding.only(bottom=10),
                    ) if normal_range_text else ft.Container(),
                    # Chart
                    ft.Container(
                        content=chart,
                        width=self.width,
                        height=self.height,
                        padding=10,
                    ),
                    # Legend
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(width=20, height=3, bgcolor=ft.Colors.BLUE_700),
                                    ft.Text("Values", size=11),
                                ], spacing=5),
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.CIRCLE, size=10, color=ft.Colors.RED),
                                    ft.Text("Abnormal", size=11),
                                ], spacing=5),
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(width=20, height=2, bgcolor=ft.Colors.GREEN_400),
                                    ft.Text("Normal range", size=11),
                                ], spacing=5),
                            ) if normal_range_text else ft.Container(),
                        ],
                        spacing=15,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
            ),
            padding=10,
        )

    def _format_tooltip(self, point: Dict) -> str:
        """Format tooltip text for a data point."""
        date_val = point["date"]
        if isinstance(date_val, str):
            try:
                date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
            except:
                pass

        date_str = date_val.strftime("%d %b %Y") if hasattr(date_val, 'strftime') else str(date_val)
        value_str = f"{point['value']:.2f} {self.unit}"

        tooltip = f"{date_str}\n{value_str}"
        if point.get("is_abnormal"):
            tooltip += "\n(ABNORMAL)"

        return tooltip
