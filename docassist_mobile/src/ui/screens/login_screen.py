"""
Login Screen - Authentication UI

Premium login screen with DocAssist branding.
"""

import flet as ft
from typing import Callable, Optional

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations
from ..haptics import HapticFeedback
from ...services.biometric_service import get_biometric_icon


class LoginScreen(ft.Container):
    """
    Login screen with email/password authentication.

    Usage:
        login = LoginScreen(on_login=handle_login)
        page.add(login)
    """

    def __init__(
        self,
        on_login: Callable[[str, str], None],
        on_forgot_password: Optional[Callable] = None,
        on_enable_biometric: Optional[Callable[[bool], None]] = None,
        biometric_available: bool = False,
        biometric_type: str = "fingerprint",  # "face_id" or "fingerprint"
        show_biometric_toggle: bool = False,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.on_login = on_login
        self.on_forgot_password = on_forgot_password
        self.on_enable_biometric = on_enable_biometric
        self.biometric_available = biometric_available
        self.biometric_type = biometric_type
        self.show_biometric_toggle = show_biometric_toggle
        self.haptic_feedback = haptic_feedback

        # Form fields
        self.email_field = ft.TextField(
            label="Email",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_radius=Radius.MD,
            height=56,
            keyboard_type=ft.KeyboardType.EMAIL,
            autofocus=True,
        )

        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            border_radius=Radius.MD,
            height=56,
            on_submit=self._handle_login,
        )

        self.error_text = ft.Text(
            "",
            size=MobileTypography.BODY_SMALL,
            color=Colors.ERROR_MAIN,
            visible=False,
        )

        self.login_button = ft.ElevatedButton(
            text="Login",
            width=float("inf"),
            height=MobileSpacing.TOUCH_TARGET,
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            ),
            on_click=self._handle_login,
        )

        self.loading_indicator = ft.ProgressRing(
            width=20,
            height=20,
            stroke_width=2,
            visible=False,
        )

        # Biometric toggle (shown after first successful login)
        biometric_icon = get_biometric_icon(biometric_type)
        biometric_display_name = "Face ID" if biometric_type == "face_id" else "Fingerprint"

        self.biometric_toggle = ft.Container(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            biometric_icon,
                            color=Colors.PRIMARY_500,
                            size=24,
                        ),
                        ft.Container(width=MobileSpacing.SM),
                        ft.Column(
                            [
                                ft.Text(
                                    f"Enable {biometric_display_name}",
                                    size=MobileTypography.BODY_LARGE,
                                    color=Colors.NEUTRAL_900,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    f"Use {biometric_display_name} to unlock next time",
                                    size=MobileTypography.BODY_SMALL,
                                    color=Colors.NEUTRAL_600,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Switch(
                            value=False,
                            on_change=self._handle_biometric_toggle,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=Colors.PRIMARY_50,
                padding=MobileSpacing.MD,
                border_radius=Radius.CARD,
                border=ft.border.all(1, Colors.PRIMARY_200),
            ),
            visible=show_biometric_toggle and biometric_available,
            animate_opacity=Animations.fade_in(),
            opacity=0 if show_biometric_toggle else 1,
        )

        # Logo with animation
        self.logo_icon = ft.Container(
            content=ft.Icon(
                ft.Icons.LOCAL_HOSPITAL,
                size=64,
                color=Colors.PRIMARY_500,
            ),
            animate_scale=Animations.scale_in(),
            animate_opacity=Animations.fade_in(),
            scale=0.5,
            opacity=0,
        )

        self.title_text = ft.Container(
            content=ft.Text(
                "DocAssist",
                size=MobileTypography.DISPLAY_LARGE,
                weight=ft.FontWeight.W_300,
                color=Colors.NEUTRAL_900,
            ),
            animate_opacity=Animations.fade_in(),
            opacity=0,
        )

        self.subtitle_text = ft.Container(
            content=ft.Text(
                "Your clinic in your pocket",
                size=MobileTypography.BODY_MEDIUM,
                color=Colors.NEUTRAL_600,
            ),
            animate_opacity=Animations.fade_in(),
            opacity=0,
        )

        # Build content
        content = ft.Column(
            [
                # Logo section
                ft.Container(height=60),
                self.logo_icon,
                ft.Container(height=MobileSpacing.MD),
                self.title_text,
                self.subtitle_text,
                ft.Container(height=MobileSpacing.XXL),

                # Form section
                ft.Container(
                    content=ft.Column(
                        [
                            self.email_field,
                            ft.Container(height=MobileSpacing.MD),
                            self.password_field,
                            ft.Container(height=MobileSpacing.XS),
                            self.error_text,
                            ft.Container(height=MobileSpacing.LG),
                            ft.Stack(
                                [
                                    self.login_button,
                                    ft.Container(
                                        content=self.loading_indicator,
                                        alignment=ft.alignment.center,
                                        height=MobileSpacing.TOUCH_TARGET,
                                    ),
                                ],
                            ),
                            ft.Container(height=MobileSpacing.LG),
                            self.biometric_toggle,
                            ft.Container(height=MobileSpacing.MD),
                            ft.TextButton(
                                text="Forgot password?",
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY_500,
                                ),
                                on_click=self._handle_forgot_password,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=MobileSpacing.SCREEN_PADDING,
                ),

                ft.Container(expand=True),

                # Footer
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.LOCK,
                                    size=14,
                                    color=Colors.NEUTRAL_500,
                                ),
                                ft.Text(
                                    "Privacy-first. Your data stays yours.",
                                    size=MobileTypography.CAPTION,
                                    color=Colors.NEUTRAL_500,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=MobileSpacing.XXS,
                        ),
                        ft.Container(height=MobileSpacing.XS),
                        ft.Text(
                            "End-to-end encrypted",
                            size=MobileTypography.CAPTION,
                            color=Colors.NEUTRAL_400,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=MobileSpacing.XL),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_0,
        )

    def _handle_login(self, e):
        """Handle login button click."""
        email = self.email_field.value or ""
        password = self.password_field.value or ""

        # Validate
        if not email:
            self._show_error("Please enter your email")
            return
        if not password:
            self._show_error("Please enter your password")
            return

        # Show loading
        self._set_loading(True)
        self._hide_error()

        # Call login handler
        if self.on_login:
            self.on_login(email, password)

    def _handle_forgot_password(self, e):
        """Handle forgot password click."""
        if self.on_forgot_password:
            self.on_forgot_password()

    def _handle_biometric_toggle(self, e):
        """Handle biometric toggle change."""
        enabled = e.control.value

        # Trigger haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.selection()

        # Call handler
        if self.on_enable_biometric:
            self.on_enable_biometric(enabled)

    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.error_text.update()

    def _hide_error(self):
        """Hide error message."""
        self.error_text.visible = False
        self.error_text.update()

    def _set_loading(self, loading: bool):
        """Set loading state."""
        self.login_button.visible = not loading
        self.loading_indicator.visible = loading
        self.email_field.disabled = loading
        self.password_field.disabled = loading
        self.update()

    def show_login_error(self, message: str = "Invalid email or password"):
        """Show login error and reset loading state."""
        self._set_loading(False)
        self._show_error(message)

    def reset(self):
        """Reset form to initial state."""
        self.email_field.value = ""
        self.password_field.value = ""
        self._hide_error()
        self._set_loading(False)
        self.update()

    def show_biometric_toggle(self):
        """Show biometric toggle after successful login."""
        if self.biometric_available and not self.biometric_toggle.visible:
            self.biometric_toggle.visible = True
            self.biometric_toggle.opacity = 1.0
            self.biometric_toggle.update()

    def hide_biometric_toggle(self):
        """Hide biometric toggle."""
        if self.biometric_toggle.visible:
            self.biometric_toggle.opacity = 0
            self.biometric_toggle.update()
            import time
            time.sleep(0.25)
            self.biometric_toggle.visible = False
            self.biometric_toggle.update()

    def animate_in(self):
        """Trigger entrance animations."""
        # Animate logo
        self.logo_icon.scale = 1.0
        self.logo_icon.opacity = 1.0
        self.logo_icon.update()

        # Animate title (delayed)
        import time
        time.sleep(0.1)
        self.title_text.opacity = 1.0
        self.title_text.update()

        # Animate subtitle (delayed)
        time.sleep(0.05)
        self.subtitle_text.opacity = 1.0
        self.subtitle_text.update()
