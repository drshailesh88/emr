"""
Welcome Back Screen - Quick welcome for returning users.

Shows a personalized welcome message with:
- User greeting
- Last sync status
- Today's appointment preview
- Quick biometric authentication

Appears briefly before transitioning to home screen.
"""

import flet as ft
from typing import Callable, Optional
from datetime import datetime

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations
from ..haptics import HapticFeedback, HapticType


class WelcomeBackScreen(ft.Container):
    """
    Welcome back screen for returning users.

    Shows personalized greeting and app status.
    Optionally prompts for biometric authentication.

    Usage:
        welcome = WelcomeBackScreen(
            user_name="Dr. Sharma",
            last_sync="2 hours ago",
            appointments_today=3,
            on_continue=handle_continue,
            biometrics_enabled=True,
        )
    """

    def __init__(
        self,
        user_name: str,
        last_sync: Optional[str] = None,
        appointments_today: int = 0,
        on_continue: Optional[Callable[[], None]] = None,
        on_biometric_auth: Optional[Callable[[bool], None]] = None,
        biometrics_enabled: bool = False,
        haptics: Optional[HapticFeedback] = None,
        auto_continue_delay: int = 2000,  # ms
    ):
        self.user_name = user_name
        self.last_sync = last_sync
        self.appointments_today = appointments_today
        self.on_continue = on_continue
        self.on_biometric_auth = on_biometric_auth
        self.biometrics_enabled = biometrics_enabled
        self.haptics = haptics
        self.auto_continue_delay = auto_continue_delay

        # Build UI
        content = self._build_content()

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_0,
        )

        # Auto-continue if biometrics not enabled
        if not self.biometrics_enabled and self.auto_continue_delay > 0:
            import threading
            threading.Timer(
                self.auto_continue_delay / 1000,
                self._auto_continue
            ).start()

        # Trigger entrance animations
        self._animate_in()

    def _build_content(self) -> ft.Column:
        """Build the welcome screen layout."""
        # Get greeting based on time of day
        greeting = self._get_greeting()

        # Welcome icon
        self.icon_container = ft.Container(
            content=ft.Icon(
                ft.Icons.WAVING_HAND,
                size=80,
                color=Colors.PRIMARY_500,
            ),
            animate_scale=Animations.scale_in(),
            animate_opacity=Animations.fade_in(),
            scale=0.5,
            opacity=0,
        )

        # Greeting text
        self.greeting_container = ft.Container(
            content=ft.Text(
                greeting,
                size=MobileTypography.HEADLINE_LARGE,
                color=Colors.NEUTRAL_600,
                text_align=ft.TextAlign.CENTER,
            ),
            animate_opacity=Animations.fade_in(),
            opacity=0,
        )

        # User name
        self.name_container = ft.Container(
            content=ft.Text(
                self.user_name,
                size=MobileTypography.DISPLAY_LARGE,
                weight=ft.FontWeight.BOLD,
                color=Colors.NEUTRAL_900,
                text_align=ft.TextAlign.CENTER,
            ),
            animate_opacity=Animations.fade_in(),
            opacity=0,
        )

        # Status cards
        status_cards = []

        # Last sync status
        if self.last_sync:
            sync_card = self._create_status_card(
                icon=ft.Icons.CLOUD_DONE,
                label="Last synced",
                value=self.last_sync,
                color=Colors.SUCCESS_MAIN,
            )
            status_cards.append(sync_card)

        # Today's appointments
        if self.appointments_today > 0:
            appt_text = f"{self.appointments_today} appointment{'s' if self.appointments_today > 1 else ''}"
            appt_card = self._create_status_card(
                icon=ft.Icons.CALENDAR_TODAY,
                label="Today",
                value=appt_text,
                color=Colors.PRIMARY_500,
            )
            status_cards.append(appt_card)

        # Status row
        if status_cards:
            self.status_row = ft.Container(
                content=ft.Row(
                    status_cards,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=MobileSpacing.MD,
                ),
                animate_opacity=Animations.fade_in(),
                opacity=0,
            )
        else:
            self.status_row = ft.Container()

        # Biometric prompt (if enabled)
        if self.biometrics_enabled:
            self.biometric_button = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.FINGERPRINT,
                            size=64,
                            color=Colors.PRIMARY_500,
                        ),
                        ft.Container(height=MobileSpacing.SM),
                        ft.Text(
                            "Touch to unlock",
                            size=MobileTypography.BODY_MEDIUM,
                            color=Colors.NEUTRAL_600,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                on_click=self._handle_biometric_tap,
                ink=True,
                border_radius=Radius.LG,
                padding=MobileSpacing.LG,
                animate_opacity=Animations.fade_in(),
                opacity=0,
            )
        else:
            self.biometric_button = ft.Container()

        # Loading indicator (shown during biometric auth)
        self.loading_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(
                        width=40,
                        height=40,
                        stroke_width=3,
                        color=Colors.PRIMARY_500,
                    ),
                    ft.Container(height=MobileSpacing.SM),
                    ft.Text(
                        "Authenticating...",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            visible=False,
            animate_opacity=Animations.fade_in(),
        )

        # Main layout
        return ft.Column(
            [
                ft.Container(height=MobileSpacing.XXL * 2),
                self.icon_container,
                ft.Container(height=MobileSpacing.LG),
                self.greeting_container,
                ft.Container(height=MobileSpacing.XS),
                self.name_container,
                ft.Container(height=MobileSpacing.XXL),
                self.status_row,
                ft.Container(expand=True),
                self.biometric_button,
                self.loading_indicator,
                ft.Container(height=MobileSpacing.XXL * 2),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    def _create_status_card(
        self,
        icon: str,
        label: str,
        value: str,
        color: str,
    ) -> ft.Container:
        """Create a status info card."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=24, color=color),
                    ft.Container(height=MobileSpacing.XXS),
                    ft.Text(
                        label,
                        size=MobileTypography.CAPTION,
                        color=Colors.NEUTRAL_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        value,
                        size=MobileTypography.BODY_MEDIUM,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.NEUTRAL_900,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=MobileSpacing.MD,
            border_radius=Radius.LG,
            bgcolor=Colors.NEUTRAL_50,
            width=140,
        )

    def _get_greeting(self) -> str:
        """Get time-appropriate greeting."""
        hour = datetime.now().hour

        if hour < 12:
            return "Good morning,"
        elif hour < 17:
            return "Good afternoon,"
        else:
            return "Good evening,"

    def _animate_in(self):
        """Trigger entrance animations."""
        # Icon
        self.icon_container.scale = 1.0
        self.icon_container.opacity = 1.0

        # Greeting
        self.greeting_container.opacity = 1.0

        # Name
        self.name_container.opacity = 1.0

        # Status row
        if hasattr(self, 'status_row'):
            self.status_row.opacity = 1.0

        # Biometric button
        if self.biometrics_enabled:
            self.biometric_button.opacity = 1.0

        # Update
        self.update()

        # Haptic feedback
        if self.haptics:
            self.haptics.light()

    def _handle_biometric_tap(self, e):
        """Handle biometric button tap."""
        # Trigger haptic
        if self.haptics:
            self.haptics.medium()

        # Show loading
        self.biometric_button.visible = False
        self.loading_indicator.visible = True
        self.update()

        # Simulate biometric auth (in real app, this would call platform API)
        import threading

        def authenticate():
            # Simulate delay
            import time
            time.sleep(1.5)

            # Call biometric auth handler
            success = True  # In real app, this comes from biometric API

            # Update UI on main thread
            if hasattr(self, 'page') and self.page:
                self.page.run_task(lambda: self._handle_auth_result(success))
            else:
                self._handle_auth_result(success)

        threading.Thread(target=authenticate, daemon=True).start()

    def _handle_auth_result(self, success: bool):
        """Handle biometric authentication result."""
        if success:
            # Success haptic
            if self.haptics:
                self.haptics.success()

            # Call callback
            if self.on_biometric_auth:
                self.on_biometric_auth(True)

            # Continue to app
            if self.on_continue:
                self.on_continue()
        else:
            # Error haptic
            if self.haptics:
                self.haptics.error()

            # Show error
            self.loading_indicator.visible = False
            self.biometric_button.visible = True

            # Show error message
            error_text = ft.Text(
                "Authentication failed. Try again.",
                size=MobileTypography.BODY_SMALL,
                color=Colors.ERROR_MAIN,
            )

            # Add error to UI
            # (In production, would show a snackbar or alert)

            self.update()

    def _auto_continue(self):
        """Auto-continue to main app."""
        if self.on_continue and hasattr(self, 'page') and self.page:
            self.page.run_task(self.on_continue)
        elif self.on_continue:
            self.on_continue()


class QuickStatsCard(ft.Container):
    """
    Quick stats card for welcome screen.

    Shows a single stat with icon and label.

    Usage:
        stat = QuickStatsCard(
            icon=ft.Icons.PEOPLE,
            value="247",
            label="Patients",
        )
    """

    def __init__(
        self,
        icon: str,
        value: str,
        label: str,
        color: str = Colors.PRIMARY_500,
    ):
        super().__init__(
            content=ft.Row(
                [
                    ft.Icon(icon, size=32, color=color),
                    ft.Container(width=MobileSpacing.SM),
                    ft.Column(
                        [
                            ft.Text(
                                value,
                                size=MobileTypography.HEADLINE_MEDIUM,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.NEUTRAL_900,
                            ),
                            ft.Text(
                                label,
                                size=MobileTypography.BODY_SMALL,
                                color=Colors.NEUTRAL_600,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=0,
            ),
            padding=MobileSpacing.MD,
            border_radius=Radius.LG,
            bgcolor=Colors.NEUTRAL_50,
            border=ft.border.all(1, Colors.NEUTRAL_200),
        )


__all__ = [
    'WelcomeBackScreen',
    'QuickStatsCard',
]
