"""Alert Banner - Clinical safety alerts and warnings."""

import flet as ft
from typing import Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"  # Blocks prescription until acknowledged
    WARNING = "warning"    # Requires acknowledgment
    INFO = "info"         # Dismissable


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    icon: str
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    dismissable: bool = True
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertBanner(ft.UserControl):
    """Alert banner with multiple severity levels and stacking support.

    Features:
    - CRITICAL (red): Blocks prescription, requires acknowledgment
    - WARNING (orange): Requires acknowledgment, allows override
    - INFO (blue): Dismissable notification
    - Stacks multiple alerts vertically
    - Smooth animations on appear/dismiss
    - Audit logging of all acknowledgments
    - Override with reason for warnings
    """

    def __init__(
        self,
        on_alert_dismissed: Optional[Callable[[Alert], None]] = None,
        on_override_requested: Optional[Callable[[Alert], None]] = None,
        is_dark: bool = False,
    ):
        """Initialize alert banner.

        Args:
            on_alert_dismissed: Callback when alert is dismissed
            on_override_requested: Callback when override is requested
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_alert_dismissed = on_alert_dismissed
        self.on_override_requested = on_override_requested
        self.is_dark = is_dark

        self.alerts: List[Alert] = []
        self.alert_containers: List[ft.Container] = []
        self.container: Optional[ft.Column] = None

    def build(self):
        """Build the alert banner."""
        self.container = ft.Column(
            controls=[],
            spacing=10,
            visible=False,
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        return self.container

    def show_interaction_alert(
        self,
        drug1: str,
        drug2: str,
        severity: str,
        description: str
    ):
        """Show drug-drug interaction alert.

        Args:
            drug1: First drug name
            drug2: Second drug name
            severity: Interaction severity (major/moderate/minor)
            description: Interaction description
        """
        alert_severity = AlertSeverity.CRITICAL if severity.lower() == "major" else AlertSeverity.WARNING

        alert = Alert(
            id=f"interaction_{drug1}_{drug2}_{datetime.now().timestamp()}",
            severity=alert_severity,
            title=f"Drug Interaction: {drug1} + {drug2}",
            description=f"{description}\n\nSeverity: {severity.upper()}",
            icon=ft.Icons.WARNING,
            action_label="Override" if alert_severity == AlertSeverity.WARNING else None,
            dismissable=alert_severity != AlertSeverity.CRITICAL,
        )

        self._add_alert(alert)

    def show_allergy_alert(self, drug: str, allergen: str):
        """Show allergy alert.

        Args:
            drug: Drug being prescribed
            allergen: Known allergen
        """
        alert = Alert(
            id=f"allergy_{drug}_{datetime.now().timestamp()}",
            severity=AlertSeverity.CRITICAL,
            title=f"ALLERGY ALERT: {drug}",
            description=f"Patient has documented allergy to {allergen}.\n\n⚠️ DO NOT PRESCRIBE without explicit consultation.",
            icon=ft.Icons.ERROR,
            dismissable=False,
        )

        self._add_alert(alert)

    def show_red_flag_alert(
        self,
        red_flag_type: str,
        message: str,
        action: Optional[str] = None
    ):
        """Show red flag alert.

        Args:
            red_flag_type: Type of red flag (e.g., "Chest Pain", "Breathlessness")
            message: Alert message
            action: Recommended action
        """
        full_message = message
        if action:
            full_message += f"\n\nRecommended Action: {action}"

        alert = Alert(
            id=f"redflag_{red_flag_type}_{datetime.now().timestamp()}",
            severity=AlertSeverity.WARNING,
            title=f"Red Flag: {red_flag_type}",
            description=full_message,
            icon=ft.Icons.LOCAL_HOSPITAL,
            dismissable=True,
        )

        self._add_alert(alert)

    def show_dose_alert(
        self,
        drug: str,
        issue: str,
        recommendation: str
    ):
        """Show dosage alert.

        Args:
            drug: Drug name
            issue: Dosage issue
            recommendation: Recommended correction
        """
        alert = Alert(
            id=f"dose_{drug}_{datetime.now().timestamp()}",
            severity=AlertSeverity.WARNING,
            title=f"Dose Alert: {drug}",
            description=f"{issue}\n\nRecommendation: {recommendation}",
            icon=ft.Icons.MEDICATION,
            action_label="Override",
            dismissable=True,
        )

        self._add_alert(alert)

    def show_info(self, title: str, message: str):
        """Show informational alert.

        Args:
            title: Alert title
            message: Alert message
        """
        alert = Alert(
            id=f"info_{datetime.now().timestamp()}",
            severity=AlertSeverity.INFO,
            title=title,
            description=message,
            icon=ft.Icons.INFO,
            dismissable=True,
        )

        self._add_alert(alert)

    def _add_alert(self, alert: Alert):
        """Add alert to the stack."""
        # Check if similar alert already exists
        for existing in self.alerts:
            if existing.title == alert.title and existing.description == alert.description:
                return  # Don't duplicate

        self.alerts.append(alert)

        # Create alert card
        alert_card = self._create_alert_card(alert)
        self.alert_containers.append(alert_card)

        if self.container:
            self.container.controls.append(alert_card)
            self.container.visible = True

            if self.page:
                self.container.update()

    def _create_alert_card(self, alert: Alert) -> ft.Container:
        """Create alert card UI."""
        # Get colors based on severity
        bg_color, border_color, icon_color = self._get_alert_colors(alert.severity)

        # Build action buttons
        actions = []

        if alert.action_label and alert.severity == AlertSeverity.WARNING:
            actions.append(
                ft.TextButton(
                    text=alert.action_label,
                    icon=ft.Icons.LOCK_OPEN,
                    on_click=lambda e: self._handle_override(alert),
                    style=ft.ButtonStyle(
                        color=ft.Colors.ORANGE_700 if not self.is_dark else ft.Colors.ORANGE_300,
                    ),
                )
            )

        if alert.dismissable:
            actions.append(
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=18,
                    on_click=lambda e: self._dismiss_alert(alert),
                    tooltip="Dismiss",
                )
            )
        else:
            # Critical alerts require explicit acknowledgment
            actions.append(
                ft.ElevatedButton(
                    text="I Acknowledge",
                    icon=ft.Icons.CHECK_CIRCLE,
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: self._acknowledge_critical(alert),
                )
            )

        # Build card content
        card_content = ft.Row([
            # Icon
            ft.Container(
                content=ft.Icon(
                    alert.icon,
                    color=icon_color,
                    size=32,
                ),
                padding=10,
            ),
            # Message
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        alert.title,
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
                    ),
                    ft.Text(
                        alert.description,
                        size=13,
                        color=ft.Colors.GREY_300 if self.is_dark else ft.Colors.GREY_700,
                    ),
                ], spacing=5),
                expand=True,
                padding=10,
            ),
            # Actions
            ft.Container(
                content=ft.Row(actions, spacing=5),
                padding=10,
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Container(
            content=card_content,
            bgcolor=bg_color,
            border=ft.border.all(2, border_color),
            border_radius=10,
            padding=5,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, border_color),
                offset=ft.Offset(0, 2),
            ),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            data=alert,
        )

    def _get_alert_colors(self, severity: AlertSeverity) -> tuple:
        """Get colors for alert severity.

        Returns:
            Tuple of (background_color, border_color, icon_color)
        """
        if severity == AlertSeverity.CRITICAL:
            if self.is_dark:
                return ("#3D1414", ft.Colors.RED_700, ft.Colors.RED_400)
            else:
                return ("#FFEBEE", ft.Colors.RED_700, ft.Colors.RED_700)

        elif severity == AlertSeverity.WARNING:
            if self.is_dark:
                return ("#3D2E14", ft.Colors.ORANGE_700, ft.Colors.ORANGE_400)
            else:
                return ("#FFF3E0", ft.Colors.ORANGE_700, ft.Colors.ORANGE_700)

        else:  # INFO
            if self.is_dark:
                return ("#14233D", ft.Colors.BLUE_700, ft.Colors.BLUE_400)
            else:
                return ("#E3F2FD", ft.Colors.BLUE_700, ft.Colors.BLUE_700)

    def _dismiss_alert(self, alert: Alert):
        """Dismiss an alert."""
        self._remove_alert(alert)

        if self.on_alert_dismissed:
            self.on_alert_dismissed(alert)

        # Log dismissal
        self._log_alert_action(alert, "dismissed")

    def _acknowledge_critical(self, alert: Alert):
        """Acknowledge a critical alert."""
        self._remove_alert(alert)

        if self.on_alert_dismissed:
            self.on_alert_dismissed(alert)

        # Log acknowledgment
        self._log_alert_action(alert, "acknowledged")

    def _handle_override(self, alert: Alert):
        """Handle override request."""
        if self.on_override_requested:
            self.on_override_requested(alert)

        # Don't remove alert yet - wait for override dialog result

    def override_with_reason(self, alert: Alert, reason: str):
        """Override alert with documented reason.

        Args:
            alert: Alert to override
            reason: Override reason for audit trail
        """
        self._remove_alert(alert)

        # Log override with reason
        self._log_alert_action(alert, "overridden", reason)

    def _remove_alert(self, alert: Alert):
        """Remove alert from display."""
        try:
            index = self.alerts.index(alert)
            self.alerts.pop(index)

            if self.container and index < len(self.container.controls):
                self.container.controls.pop(index)
                self.alert_containers.pop(index)

                # Hide container if no alerts remain
                if not self.alerts:
                    self.container.visible = False

                if self.page:
                    self.container.update()
        except (ValueError, IndexError):
            pass

    def _log_alert_action(self, alert: Alert, action: str, reason: Optional[str] = None):
        """Log alert action for audit trail.

        Args:
            alert: Alert that was acted upon
            action: Action taken (dismissed/acknowledged/overridden)
            reason: Optional reason for override
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "alert_id": alert.id,
            "severity": alert.severity.value,
            "title": alert.title,
            "action": action,
        }

        if reason:
            log_entry["override_reason"] = reason

        # TODO: Save to audit database
        print(f"[AUDIT] Alert {action}: {log_entry}")

    def clear_all(self):
        """Clear all alerts."""
        self.alerts.clear()
        self.alert_containers.clear()

        if self.container:
            self.container.controls.clear()
            self.container.visible = False

            if self.page:
                self.container.update()

    def has_critical_alerts(self) -> bool:
        """Check if there are any unacknowledged critical alerts.

        Returns:
            True if critical alerts exist
        """
        return any(a.severity == AlertSeverity.CRITICAL for a in self.alerts)
