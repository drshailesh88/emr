"""Chart components for analytics visualization using Flet."""

import flet as ft
from typing import List, Dict, Tuple, Optional


class LineChart(ft.UserControl):
    """Simple line chart visualization."""

    def __init__(
        self,
        data: List[Dict],  # [{"label": "Jan", "value": 100}, ...]
        title: str = "",
        color: str = ft.colors.BLUE_600,
        height: int = 200,
    ):
        super().__init__()
        self.data = data
        self.title = title
        self.color = color
        self.chart_height = height

    def build(self):
        """Build line chart."""
        if not self.data:
            return ft.Container(
                content=ft.Text("No data available", color=ft.colors.GREY_600),
                padding=20,
            )

        # Find min/max for scaling
        values = [d["value"] for d in self.data]
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        value_range = max_val - min_val if max_val != min_val else 1

        # Create points
        chart_width = 600
        points = []
        labels = []

        for i, item in enumerate(self.data):
            # Calculate position
            x = (i / (len(self.data) - 1)) * chart_width if len(self.data) > 1 else chart_width / 2
            normalized = (item["value"] - min_val) / value_range
            y = self.chart_height - (normalized * self.chart_height)

            # Add point
            points.append(
                ft.Container(
                    left=x - 4,
                    top=y - 4,
                    width=8,
                    height=8,
                    bgcolor=self.color,
                    border_radius=4,
                    tooltip=f"{item['label']}: {item['value']}",
                )
            )

            # Add label
            labels.append(
                ft.Container(
                    left=x - 30,
                    top=self.chart_height + 5,
                    width=60,
                    content=ft.Text(
                        item["label"],
                        size=10,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREY_600,
                    ),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD) if self.title else ft.Container(),
                    ft.Container(
                        content=ft.Stack(
                            controls=points + labels,
                            width=chart_width,
                            height=self.chart_height + 30,
                        ),
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    ),
                ],
                spacing=10,
            ),
        )


class BarChart(ft.UserControl):
    """Simple bar chart visualization."""

    def __init__(
        self,
        data: List[Dict],  # [{"label": "Category", "value": 100}, ...]
        title: str = "",
        color: str = ft.colors.GREEN_600,
        height: int = 200,
        horizontal: bool = False,
    ):
        super().__init__()
        self.data = data
        self.title = title
        self.color = color
        self.chart_height = height
        self.horizontal = horizontal

    def build(self):
        """Build bar chart."""
        if not self.data:
            return ft.Container(
                content=ft.Text("No data available", color=ft.colors.GREY_600),
                padding=20,
            )

        # Find max for scaling
        max_val = max(d["value"] for d in self.data) if self.data else 1

        bars = []
        for item in self.data:
            bar_height = (item["value"] / max_val) * self.chart_height if max_val > 0 else 0

            bars.append(
                ft.Column(
                    controls=[
                        ft.Text(
                            str(item["value"]),
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY_700,
                        ),
                        ft.Container(
                            width=80,
                            height=bar_height,
                            bgcolor=self.color,
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                            tooltip=f"{item['label']}: {item['value']}",
                        ),
                        ft.Text(
                            item["label"],
                            size=10,
                            color=ft.colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                            width=80,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD) if self.title else ft.Container(),
                    ft.Container(
                        content=ft.Row(
                            controls=bars,
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            spacing=10,
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=10),
                    ),
                ],
                spacing=10,
            ),
        )


class PieChart(ft.UserControl):
    """Simple pie chart visualization (shown as horizontal bars with percentages)."""

    def __init__(
        self,
        data: List[Dict],  # [{"label": "Category", "value": 100, "color": ft.colors.BLUE_400}, ...]
        title: str = "",
    ):
        super().__init__()
        self.data = data
        self.title = title

    def build(self):
        """Build pie chart (as horizontal bars)."""
        if not self.data:
            return ft.Container(
                content=ft.Text("No data available", color=ft.colors.GREY_600),
                padding=20,
            )

        # Calculate total and percentages
        total = sum(d["value"] for d in self.data)

        items = []
        colors = [
            ft.colors.BLUE_400,
            ft.colors.GREEN_400,
            ft.colors.PURPLE_400,
            ft.colors.ORANGE_400,
            ft.colors.RED_400,
            ft.colors.TEAL_400,
            ft.colors.PINK_400,
        ]

        for i, item in enumerate(self.data):
            percentage = (item["value"] / total * 100) if total > 0 else 0
            color = item.get("color", colors[i % len(colors)])

            items.append(
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
                                ft.Text(
                                    item["label"],
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(expand=True),
                                ft.Text(
                                    f"{item['value']} ({percentage:.0f}%)",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.GREY_700,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            width=400,
                            height=8,
                            bgcolor=ft.colors.GREY_200,
                            border_radius=4,
                            content=ft.Container(
                                width=400 * (percentage / 100),
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
                    ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD) if self.title else ft.Container(),
                    ft.Column(
                        controls=items,
                        spacing=12,
                    ),
                ],
                spacing=15,
            ),
        )


class GaugeChart(ft.UserControl):
    """Circular gauge chart for showing percentages."""

    def __init__(
        self,
        value: float,  # 0-100
        label: str = "",
        color: Optional[str] = None,
    ):
        super().__init__()
        self.value = min(100, max(0, value))  # Clamp to 0-100
        self.label = label

        # Auto-color based on value
        if color:
            self.color = color
        elif self.value >= 80:
            self.color = ft.colors.GREEN_600
        elif self.value >= 60:
            self.color = ft.colors.ORANGE_600
        else:
            self.color = ft.colors.RED_600

    def build(self):
        """Build gauge chart."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Main value display
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    f"{self.value:.0f}%",
                                    size=48,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.color,
                                ),
                                ft.Text(
                                    self.label,
                                    size=13,
                                    color=ft.colors.GREY_600,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                    ),
                    # Progress bar
                    ft.ProgressBar(
                        value=self.value / 100,
                        color=self.color,
                        bgcolor=ft.colors.GREY_200,
                        height=8,
                        width=200,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        )


class SparklineChart(ft.UserControl):
    """Tiny sparkline chart for showing trends."""

    def __init__(
        self,
        data: List[float],
        color: str = ft.colors.BLUE_600,
        width: int = 100,
        height: int = 30,
    ):
        super().__init__()
        self.data = data
        self.color = color
        self.width = width
        self.height = height

    def build(self):
        """Build sparkline."""
        if not self.data or len(self.data) < 2:
            return ft.Container()

        # Normalize data to 0-1 range
        min_val = min(self.data)
        max_val = max(self.data)
        value_range = max_val - min_val

        if value_range == 0:
            normalized = [0.5] * len(self.data)
        else:
            normalized = [(v - min_val) / value_range for v in self.data]

        # Create points
        points = []
        for i, norm_val in enumerate(normalized):
            x = (i / (len(normalized) - 1)) * self.width
            y = self.height - (norm_val * self.height)

            points.append(
                ft.Container(
                    left=x - 1,
                    top=y - 1,
                    width=2,
                    height=2,
                    bgcolor=self.color,
                    border_radius=1,
                )
            )

        return ft.Container(
            content=ft.Stack(
                controls=points,
                width=self.width,
                height=self.height,
            ),
        )
