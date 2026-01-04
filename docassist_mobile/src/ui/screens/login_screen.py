"""
Login Screen - Authentication UI

Premium login screen with DocAssist branding.
"""

import flet as ft
from typing import Callable, Optional

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


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
    ):
        self.on_login = on_login
        self.on_forgot_password = on_forgot_password

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

        # Build content
        content = ft.Column(
            [
                # Logo section
                ft.Container(height=60),
                ft.Icon(
                    ft.Icons.LOCAL_HOSPITAL,
                    size=64,
                    color=Colors.PRIMARY_500,
                ),
                ft.Container(height=MobileSpacing.MD),
                ft.Text(
                    "DocAssist",
                    size=MobileTypography.DISPLAY_LARGE,
                    weight=ft.FontWeight.W_300,
                    color=Colors.NEUTRAL_900,
                ),
                ft.Text(
                    "Your clinic in your pocket",
                    size=MobileTypography.BODY_MEDIUM,
                    color=Colors.NEUTRAL_600,
                ),
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
