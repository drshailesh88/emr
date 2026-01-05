"""Trend Chart Component for visualizing vitals and lab results over time."""

import flet as ft
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class TrendChart(ft.UserControl):
    """Simple line/bar chart for vitals and labs with trend indicators."""

    def __init__(
        self,
        title: str,
        data_points: List[Dict],  # [{date: datetime, value: float, label: str}]
        unit: str = "",
        reference_range: Optional[Tuple[float, float]] = None,
        chart_type: str = "line",  # "line" or "bar"
        on_click=None,
        height: int = 200,
    ):
        super().__init__()
        self.title = title
        self.data_points = sorted(data_points, key=lambda x: x["date"])
        self.unit = unit
        self.reference_range = reference_range
        self.chart_type = chart_type
        self.on_click_handler = on_click
        self.chart_height = height

    def _calculate_trend(self) -> str:
        """Calculate trend indicator based on recent values."""
        if len(self.data_points) < 2:
            return "→"

        # Compare last value to average of previous values
        last_value = self.data_points[-1]["value"]
        previous_avg = sum(p["value"] for p in self.data_points[:-1]) / len(self.data_points[:-1])

        change_percent = ((last_value - previous_avg) / previous_avg) * 100 if previous_avg != 0 else 0

        if abs(change_percent) < 5:
            return "→"  # Stable
        elif change_percent > 0:
            return "↑"  # Increasing
        else:
            return "↓"  # Decreasing

    def _get_trend_color(self, trend: str) -> str:
        """Get color based on trend direction and clinical context."""
        # For most vitals, increasing is concerning
        # TODO: Make this context-aware (e.g., weight loss might be good)
        if trend == "↑":
            return ft.colors.RED_400
        elif trend == "↓":
            return ft.colors.GREEN_400
        else:
            return ft.colors.GREY_400

    def _is_out_of_range(self, value: float) -> Optional[str]:
        """Check if value is out of reference range."""
        if not self.reference_range:
            return None

        low, high = self.reference_range
        if value < low:
            return "low"
        elif value > high:
            return "high"
        return None

    def _normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range for visualization."""
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)

    def _render_line_chart(self) -> ft.Container:
        """Render as line chart."""
        if not self.data_points:
            return ft.Container(
                content=ft.Text("No data available", color=ft.colors.GREY_400),
                alignment=ft.alignment.center,
                height=self.chart_height,
            )

        # Calculate min/max for scaling
        values = [p["value"] for p in self.data_points]
        min_val = min(values)
        max_val = max(values)

        # Expand range to include reference range if provided
        if self.reference_range:
            min_val = min(min_val, self.reference_range[0])
            max_val = max(max_val, self.reference_range[1])

        # Add 10% padding
        value_range = max_val - min_val
        min_val -= value_range * 0.1
        max_val += value_range * 0.1

        # Create chart area
        chart_width = 600
        chart_height = self.chart_height - 60  # Reserve space for labels

        # Plot points
        points = []
        for i, point in enumerate(self.data_points):
            x = (i / (len(self.data_points) - 1)) * chart_width if len(self.data_points) > 1 else chart_width / 2
            y = chart_height - (self._normalize_value(point["value"], min_val, max_val) * chart_height)

            status = self._is_out_of_range(point["value"])
            color = ft.colors.RED_400 if status == "high" else ft.colors.BLUE_400 if status == "low" else ft.colors.GREEN_400

            points.append(
                ft.Container(
                    left=x - 4,
                    top=y - 4,
                    width=8,
                    height=8,
                    bgcolor=color,
                    border_radius=4,
                    tooltip=f"{point['label']}: {point['value']}{self.unit}",
                )
            )

        # Draw reference range if provided
        reference_overlay = []
        if self.reference_range:
            low_y = chart_height - (self._normalize_value(self.reference_range[0], min_val, max_val) * chart_height)
            high_y = chart_height - (self._normalize_value(self.reference_range[1], min_val, max_val) * chart_height)

            reference_overlay.append(
                ft.Container(
                    left=0,
                    top=high_y,
                    width=chart_width,
                    height=low_y - high_y,
                    bgcolor=ft.colors.GREEN_100 if ft.theme.ColorScheme else ft.colors.with_opacity(0.1, ft.colors.GREEN),
                    opacity=0.2,
                )
            )

        # Create stack with all elements
        return ft.Container(
            content=ft.Stack(
                controls=reference_overlay + points,
                width=chart_width,
                height=chart_height,
            ),
            padding=10,
        )

    def _render_bar_chart(self) -> ft.Container:
        """Render as bar chart."""
        if not self.data_points:
            return ft.Container(
                content=ft.Text("No data available", color=ft.colors.GREY_400),
                alignment=ft.alignment.center,
                height=self.chart_height,
            )

        # Calculate max for scaling
        values = [p["value"] for p in self.data_points]
        max_val = max(values) * 1.1  # 10% padding

        bars = []
        for i, point in enumerate(self.data_points):
            status = self._is_out_of_range(point["value"])
            color = ft.colors.RED_400 if status == "high" else ft.colors.BLUE_400 if status == "low" else ft.colors.GREEN_400

            bar_height = (point["value"] / max_val) * (self.chart_height - 60)

            bars.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                f"{point['value']}{self.unit}",
                                size=10,
                                weight=ft.FontWeight.BOLD,
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            width=40,
                            height=bar_height,
                            bgcolor=color,
                            border_radius=4,
                            tooltip=f"{point['label']}: {point['value']}{self.unit}",
                        ),
                        ft.Text(
                            point["label"],
                            size=10,
                            color=ft.colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                )
            )

        return ft.Container(
            content=ft.Row(
                controls=bars,
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                spacing=10,
            ),
            padding=10,
        )

    def build(self):
        trend = self._calculate_trend()
        trend_color = self._get_trend_color(trend)

        # Latest value
        latest_value = self.data_points[-1]["value"] if self.data_points else 0
        status = self._is_out_of_range(latest_value) if self.data_points else None

        # Status indicator
        status_text = ""
        status_color = ft.colors.GREY_600
        if status == "high":
            status_text = "HIGH"
            status_color = ft.colors.RED_400
        elif status == "low":
            status_text = "LOW"
            status_color = ft.colors.BLUE_400

        # Chart container
        chart = self._render_line_chart() if self.chart_type == "line" else self._render_bar_chart()

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Row(
                        controls=[
                            ft.Text(
                                self.title,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(expand=True),
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"{latest_value}{self.unit}" if self.data_points else "N/A",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=status_color if status else None,
                                    ),
                                    ft.Icon(
                                        name=ft.icons.TRENDING_UP if trend == "↑" else ft.icons.TRENDING_DOWN if trend == "↓" else ft.icons.TRENDING_FLAT,
                                        color=trend_color,
                                        size=20,
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Status badge
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    status_text,
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.WHITE,
                                ),
                                bgcolor=status_color,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=4,
                                visible=bool(status),
                            ),
                            ft.Text(
                                f"Reference: {self.reference_range[0]}-{self.reference_range[1]}{self.unit}" if self.reference_range else "",
                                size=10,
                                color=ft.colors.GREY_600,
                                visible=bool(self.reference_range),
                            ),
                        ],
                        spacing=8,
                    ),
                    # Chart
                    chart,
                ],
                spacing=8,
            ),
            padding=15,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            bgcolor=ft.colors.WHITE,
            on_click=lambda _: self.on_click_handler() if self.on_click_handler else None,
            ink=True if self.on_click_handler else False,
        )
