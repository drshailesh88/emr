"""
Red Flag Banner

Prominent banner for critical red flag alerts that require immediate attention.
Never auto-dismisses for safety.
"""

import flet as ft
from typing import Optional, Callable, List
from ...services.diagnosis.red_flag_detector import RedFlag, UrgencyLevel


class RedFlagBanner(ft.UserControl):
    """
    Prominent red flag alert banner for critical conditions.

    Features:
    - High visibility design (red/orange based on urgency)
    - Shows red flag condition clearly
    - Displays recommended action
    - Time-critical information
    - Requires explicit acknowledgment
    - Never auto-dismisses
    - Audit logs all acknowledgments
    """

    def __init__(
        self,
        on_acknowledged: Optional[Callable[[RedFlag], None]] = None,
        is_dark: bool = False,
    ):
        """Initialize red flag banner.

        Args:
            on_acknowledged: Callback when red flag is acknowledged
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_acknowledged = on_acknowledged
        self.is_dark = is_dark

        self.red_flags: List[RedFlag] = []
        self.container: Optional[ft.Container] = None
        self.banners_column: Optional[ft.Column] = None

    def build(self):
        """Build the red flag banner UI."""
        self.banners_column = ft.Column(
            controls=[],
            spacing=10,
        )

        self.container = ft.Container(
            content=self.banners_column,
            visible=False,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        return self.container

    def show_red_flags(self, red_flags: List[RedFlag]):
        """Show red flag alerts.

        Args:
            red_flags: List of RedFlag objects from RedFlagDetector
        """
        self.red_flags = red_flags
        self._rebuild_banners()

        if self.container:
            self.container.visible = len(red_flags) > 0
            if self.page:
                self.container.update()

    def _rebuild_banners(self):
        """Rebuild banner content with current red flags."""
        if not self.banners_column:
            return

        self.banners_column.controls.clear()

        for red_flag in self.red_flags:
            banner = self._create_red_flag_banner(red_flag)
            self.banners_column.controls.append(banner)

        if self.page:
            self.banners_column.update()

    def _create_red_flag_banner(self, red_flag: RedFlag) -> ft.Control:
        """Create a banner for a single red flag.

        Args:
            red_flag: RedFlag object

        Returns:
            Flet control for the banner
        """
        # Get colors based on urgency
        bg_color, border_color, icon_color, text_color = self._get_urgency_colors(red_flag.urgency)

        # Urgency indicator
        urgency_text = {
            UrgencyLevel.EMERGENCY: "🚨 EMERGENCY",
            UrgencyLevel.URGENT: "⚠️ URGENT",
            UrgencyLevel.WARNING: "⚡ WARNING",
        }.get(red_flag.urgency, "⚠️ ALERT")

        # Build content rows
        content_rows = [
            # Title row with urgency
            ft.Row([
                ft.Container(
                    content=ft.Text(
                        urgency_text,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=icon_color,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=4,
                ),
                ft.Text(
                    red_flag.description,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=text_color,
                ),
            ], spacing=10),
        ]

        # Matching features
        if red_flag.matching_features:
            features_text = ", ".join([
                self._format_feature_name(f) for f in red_flag.matching_features
            ])
            content_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.MEDICAL_SERVICES, size=16, color=icon_color),
                    ft.Text(
                        f"Present: {features_text}",
                        size=13,
                        color=text_color,
                        weight=ft.FontWeight.W_500,
                    ),
                ], spacing=6)
            )

        # Recommended action
        content_rows.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Recommended Action:",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=text_color,
                    ),
                    ft.Text(
                        red_flag.recommended_action,
                        size=12,
                        color=text_color,
                    ),
                ], spacing=4),
                padding=ft.padding.only(left=8, top=8),
                bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                border_radius=6,
            )
        )

        # Time critical information
        if red_flag.time_critical:
            content_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.TIMER, size=16, color=ft.Colors.ORANGE_700),
                    ft.Text(
                        f"⏱️ {red_flag.time_critical}",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_700,
                    ),
                ], spacing=6)
            )

        # Differential concerns
        if red_flag.differential_concerns:
            concerns_text = ", ".join(red_flag.differential_concerns)
            content_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, size=16, color=icon_color),
                    ft.Text(
                        f"Consider: {concerns_text}",
                        size=11,
                        italic=True,
                        color=text_color,
                    ),
                ], spacing=6)
            )

        # Acknowledge button
        acknowledge_btn = ft.ElevatedButton(
            text="Acknowledged",
            icon=ft.Icons.CHECK_CIRCLE,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=lambda e: self._acknowledge_red_flag(red_flag),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
        )

        # Create banner container
        return ft.Container(
            content=ft.Column([
                # Icon and content
                ft.Row([
                    # Large warning icon
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.WARNING_AMBER,
                            size=48,
                            color=icon_color,
                        ),
                        padding=15,
                    ),
                    # Content
                    ft.Container(
                        content=ft.Column(
                            content_rows,
                            spacing=8,
                        ),
                        expand=True,
                        padding=15,
                    ),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
                # Action button
                ft.Container(
                    content=ft.Row([
                        acknowledge_btn,
                    ], alignment=ft.MainAxisAlignment.END),
                    padding=ft.padding.only(right=15, bottom=15),
                ),
            ], spacing=0),
            bgcolor=bg_color,
            border=ft.border.all(3, border_color),
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.3, border_color),
                offset=ft.Offset(0, 4),
            ),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _get_urgency_colors(self, urgency: UrgencyLevel) -> tuple:
        """Get colors for urgency level.

        Args:
            urgency: UrgencyLevel enum

        Returns:
            Tuple of (bg_color, border_color, icon_color, text_color)
        """
        if urgency == UrgencyLevel.EMERGENCY:
            if self.is_dark:
                return ("#3D1414", ft.Colors.RED_700, ft.Colors.RED_500, ft.Colors.RED_100)
            else:
                return ("#FFEBEE", ft.Colors.RED_700, ft.Colors.RED_700, ft.Colors.RED_900)

        elif urgency == UrgencyLevel.URGENT:
            if self.is_dark:
                return ("#3D2E14", ft.Colors.ORANGE_700, ft.Colors.ORANGE_500, ft.Colors.ORANGE_100)
            else:
                return ("#FFF3E0", ft.Colors.ORANGE_700, ft.Colors.ORANGE_700, ft.Colors.ORANGE_900)

        else:  # WARNING
            if self.is_dark:
                return ("#3D3614", ft.Colors.YELLOW_700, ft.Colors.YELLOW_500, ft.Colors.YELLOW_100)
            else:
                return ("#FFFDE7", ft.Colors.YELLOW_800, ft.Colors.YELLOW_800, ft.Colors.YELLOW_900)

    def _format_feature_name(self, feature: str) -> str:
        """Format feature name for display.

        Args:
            feature: Raw feature key (e.g., "chest_pain")

        Returns:
            Formatted name (e.g., "Chest pain")
        """
        return feature.replace('_', ' ').capitalize()

    def _acknowledge_red_flag(self, red_flag: RedFlag):
        """Acknowledge a red flag and remove from display.

        Args:
            red_flag: RedFlag to acknowledge
        """
        # Remove from list
        if red_flag in self.red_flags:
            self.red_flags.remove(red_flag)

        # Rebuild banners
        self._rebuild_banners()

        # Hide container if no more red flags
        if not self.red_flags and self.container:
            self.container.visible = False

        # Callback
        if self.on_acknowledged:
            self.on_acknowledged(red_flag)

        # Log acknowledgment
        self._log_acknowledgment(red_flag)

        if self.page:
            self.update()

    def _log_acknowledgment(self, red_flag: RedFlag):
        """Log red flag acknowledgment for audit trail.

        Args:
            red_flag: RedFlag that was acknowledged
        """
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": red_flag.category,
            "description": red_flag.description,
            "urgency": red_flag.urgency.value,
            "action": "acknowledged",
        }

        # TODO: Save to audit database
        print(f"[AUDIT] Red flag acknowledged: {log_entry}")

    def clear(self):
        """Clear all red flags and hide banner."""
        self.red_flags = []
        if self.banners_column:
            self.banners_column.controls.clear()
        if self.container:
            self.container.visible = False
        if self.page:
            self.update()
