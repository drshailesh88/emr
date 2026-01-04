"""Metrics Card Component for displaying key practice metrics."""

import flet as ft
from typing import List, Optional, Callable


class MetricsCard(ft.UserControl):
    """
    Card displaying a single metric with trend indicator and optional sparkline.
    """

    def __init__(
        self,
        title: str,
        value: str,
        trend_percent: Optional[float] = None,
        trend_label: str = "vs last period",
        icon: str = ft.icons.ANALYTICS,
        icon_color: str = ft.colors.BLUE_600,
        sparkline_data: Optional[List[float]] = None,
        on_click: Optional[Callable] = None,
        loading: bool = False,
    ):
        super().__init__()
        self.title = title
        self.value = value
        self.trend_percent = trend_percent
        self.trend_label = trend_label
        self.icon = icon
        self.icon_color = icon_color
        self.sparkline_data = sparkline_data or []
        self.on_click_handler = on_click
        self.loading = loading

    def _render_sparkline(self) -> ft.Container:
        """Render mini sparkline chart."""
        if not self.sparkline_data or len(self.sparkline_data) < 2:
            return ft.Container()

        # Normalize data to 0-1 range
        min_val = min(self.sparkline_data)
        max_val = max(self.sparkline_data)
        value_range = max_val - min_val

        if value_range == 0:
            normalized = [0.5] * len(self.sparkline_data)
        else:
            normalized = [(v - min_val) / value_range for v in self.sparkline_data]

        # Create simple line visualization
        chart_height = 30
        chart_width = 100
        points = []

        for i, norm_val in enumerate(normalized):
            x = (i / (len(normalized) - 1)) * chart_width
            y = chart_height - (norm_val * chart_height)

            points.append(
                ft.Container(
                    left=x - 1,
                    top=y - 1,
                    width=2,
                    height=2,
                    bgcolor=self.icon_color,
                    border_radius=1,
                )
            )

        return ft.Container(
            content=ft.Stack(
                controls=points,
                width=chart_width,
                height=chart_height,
            ),
            padding=ft.padding.only(top=5),
        )

    def _render_skeleton(self) -> ft.Container:
        """Render skeleton loader."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=100,
                        height=12,
                        bgcolor=ft.colors.GREY_300,
                        border_radius=4,
                    ),
                    ft.Container(
                        width=150,
                        height=32,
                        bgcolor=ft.colors.GREY_300,
                        border_radius=4,
                    ),
                    ft.Container(
                        width=120,
                        height=10,
                        bgcolor=ft.colors.GREY_300,
                        border_radius=4,
                    ),
                ],
                spacing=10,
            ),
            padding=20,
        )

    def build(self):
        """Build the metrics card."""
        # Skeleton loader
        if self.loading:
            return ft.Container(
                content=self._render_skeleton(),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=12,
                bgcolor=ft.colors.WHITE,
                animate=ft.animation.Animation(300, "easeOut"),
            )

        # Trend indicator
        trend_color = ft.colors.GREY_600
        trend_icon = ft.icons.TRENDING_FLAT
        trend_text = ""

        if self.trend_percent is not None:
            if self.trend_percent > 0:
                trend_color = ft.colors.GREEN_600
                trend_icon = ft.icons.TRENDING_UP
                trend_text = f"+{self.trend_percent:.1f}%"
            elif self.trend_percent < 0:
                trend_color = ft.colors.RED_600
                trend_icon = ft.icons.TRENDING_DOWN
                trend_text = f"{self.trend_percent:.1f}%"
            else:
                trend_text = "0%"

        # Build content
        content = ft.Column(
            controls=[
                # Icon and title row
                ft.Row(
                    controls=[
                        ft.Icon(
                            self.icon,
                            color=self.icon_color,
                            size=24,
                        ),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Icon(
                                ft.icons.CHEVRON_RIGHT,
                                color=ft.colors.GREY_400,
                                size=20,
                            ),
                            visible=bool(self.on_click_handler),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # Title
                ft.Text(
                    self.title,
                    size=13,
                    color=ft.colors.GREY_600,
                    weight=ft.FontWeight.W_500,
                ),
                # Value
                ft.Text(
                    self.value,
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_900,
                ),
                # Trend indicator
                ft.Row(
                    controls=[
                        ft.Icon(
                            trend_icon,
                            color=trend_color,
                            size=16,
                        ),
                        ft.Text(
                            trend_text,
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=trend_color,
                        ),
                        ft.Text(
                            self.trend_label,
                            size=11,
                            color=ft.colors.GREY_600,
                        ),
                    ],
                    spacing=4,
                    visible=self.trend_percent is not None,
                ),
                # Sparkline
                self._render_sparkline(),
            ],
            spacing=8,
        )

        return ft.Container(
            content=content,
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=12,
            bgcolor=ft.colors.WHITE,
            ink=True if self.on_click_handler else False,
            on_click=lambda _: self.on_click_handler() if self.on_click_handler else None,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            animate=ft.animation.Animation(300, "easeOut"),
        )

    def update_value(self, new_value: str, new_trend: Optional[float] = None):
        """Update card value with animation."""
        self.value = new_value
        if new_trend is not None:
            self.trend_percent = new_trend
        self.update()
