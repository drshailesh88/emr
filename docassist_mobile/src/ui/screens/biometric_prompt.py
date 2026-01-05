"""
Biometric Prompt Screen - Face ID / Fingerprint authentication UI.

Premium biometric unlock screen with animated icons and haptic feedback.
"""

import flet as ft
from typing import Callable, Optional
import asyncio

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations
from ..haptics import HapticFeedback
from ...services.biometric_service import BiometricService


class BiometricPrompt(ft.Container):
    """
    Biometric authentication prompt screen.

    Shows Face ID or Fingerprint icon with pulsing animation.
    Provides fallback to password login.

    Usage:
        prompt = BiometricPrompt(
            biometric_type="face_id",
            user_name="Dr. Shailesh",
            on_authenticate=handle_biometric_auth,
            on_use_password=show_password_login,
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        biometric_type: str = "fingerprint",  # "face_id" or "fingerprint"
        user_name: str = "",
        user_email: str = "",
        on_authenticate: Optional[Callable] = None,
        on_use_password: Optional[Callable] = None,
        on_switch_account: Optional[Callable] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.biometric_type = biometric_type
        self.user_name = user_name
        self.user_email = user_email
        self.on_authenticate = on_authenticate
        self.on_use_password = on_use_password
        self.on_switch_account = on_switch_account
        self.haptic_feedback = haptic_feedback

        self._is_authenticating = False
        self._auth_failed = False

        # Biometric icon (animated)
        icon_name = ft.Icons.FACE if biometric_type == "face_id" else ft.Icons.FINGERPRINT
        icon_size = 120 if biometric_type == "face_id" else 100

        self.biometric_icon = ft.Container(
            content=ft.Icon(
                icon_name,
                size=icon_size,
                color=Colors.PRIMARY_500,
            ),
            animate_scale=Animations.scale_in(),
            animate_opacity=Animations.fade_in(),
            scale=1.0,
            opacity=1.0,
        )

        # Status text
        self.status_text = ft.Container(
            content=ft.Text(
                self._get_prompt_text(),
                size=MobileTypography.TITLE_LARGE,
                weight=ft.FontWeight.W_500,
                color=Colors.NEUTRAL_900,
                text_align=ft.TextAlign.CENTER,
            ),
            animate_opacity=Animations.fade_in(),
            opacity=1.0,
        )

        # Subtitle text
        self.subtitle_text = ft.Container(
            content=ft.Text(
                "Touch the sensor" if biometric_type == "fingerprint" else "Look at your device",
                size=MobileTypography.BODY_MEDIUM,
                color=Colors.NEUTRAL_600,
                text_align=ft.TextAlign.CENTER,
            ),
            animate_opacity=Animations.fade_in(),
            opacity=1.0,
        )

        # Error text (hidden by default)
        self.error_text = ft.Container(
            content=ft.Text(
                "Authentication failed. Try again.",
                size=MobileTypography.BODY_MEDIUM,
                color=Colors.ERROR_MAIN,
                text_align=ft.TextAlign.CENTER,
            ),
            visible=False,
            animate_opacity=Animations.fade_in(),
            opacity=0,
        )

        # Retry button (shown after failure)
        self.retry_button = ft.Container(
            content=ft.OutlinedButton(
                text="Try Again",
                icon=icon_name,
                style=ft.ButtonStyle(
                    color=Colors.PRIMARY_500,
                    side=ft.BorderSide(1.5, Colors.PRIMARY_500),
                    shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                ),
                width=200,
                height=MobileSpacing.TOUCH_TARGET,
                on_click=self._handle_retry,
            ),
            visible=False,
            animate_opacity=Animations.fade_in(),
            opacity=0,
        )

        # Use password button
        self.password_button = ft.TextButton(
            text="Use Password Instead",
            style=ft.ButtonStyle(color=Colors.NEUTRAL_600),
            on_click=self._handle_use_password,
        )

        # Switch account button
        self.switch_account_button = ft.TextButton(
            text=f"Not {user_name.split()[0]}? Switch account",
            style=ft.ButtonStyle(color=Colors.NEUTRAL_500),
            on_click=self._handle_switch_account,
        ) if user_name else None

        # Build content
        content_items = [
            # Top spacing
            ft.Container(height=80),

            # User info
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Welcome back,",
                            size=MobileTypography.BODY_MEDIUM,
                            color=Colors.NEUTRAL_600,
                        ),
                        ft.Text(
                            user_name or "User",
                            size=MobileTypography.HEADLINE_MEDIUM,
                            weight=ft.FontWeight.W_600,
                            color=Colors.NEUTRAL_900,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
            ),

            ft.Container(height=MobileSpacing.XXL),

            # Biometric icon with pulse animation
            self.biometric_icon,

            ft.Container(height=MobileSpacing.LG),

            # Status text
            self.status_text,

            ft.Container(height=MobileSpacing.XS),

            # Subtitle
            self.subtitle_text,

            ft.Container(height=MobileSpacing.MD),

            # Error message
            self.error_text,

            ft.Container(height=MobileSpacing.LG),

            # Retry button
            self.retry_button,

            ft.Container(expand=True),

            # Use password fallback
            self.password_button,
        ]

        # Add switch account button if provided
        if self.switch_account_button:
            content_items.append(ft.Container(height=MobileSpacing.XS))
            content_items.append(self.switch_account_button)

        content_items.append(ft.Container(height=MobileSpacing.XL))

        content = ft.Column(
            content_items,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_0,
            padding=MobileSpacing.SCREEN_PADDING,
        )

    def _get_prompt_text(self) -> str:
        """Get appropriate prompt text based on biometric type."""
        if self.biometric_type == "face_id":
            return "Unlock with Face ID"
        else:
            return "Unlock with Fingerprint"

    def _handle_retry(self, e):
        """Handle retry button click."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        self._reset_ui()
        self.authenticate()

    def _handle_use_password(self, e):
        """Handle use password button click."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        if self.on_use_password:
            self.on_use_password()

    def _handle_switch_account(self, e):
        """Handle switch account button click."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        if self.on_switch_account:
            self.on_switch_account()

    def _reset_ui(self):
        """Reset UI to initial state."""
        self._auth_failed = False

        # Hide error and retry button
        self.error_text.visible = False
        self.error_text.opacity = 0
        self.retry_button.visible = False
        self.retry_button.opacity = 0

        # Show subtitle
        self.subtitle_text.visible = True
        self.subtitle_text.opacity = 1.0

        # Reset icon color
        self.biometric_icon.content.color = Colors.PRIMARY_500

        self.update()

    def start_pulse_animation(self):
        """Start pulsing animation on biometric icon."""
        # Pulse animation: scale up and down repeatedly
        async def pulse():
            while self._is_authenticating and not self._auth_failed:
                # Scale up
                self.biometric_icon.scale = 1.1
                self.biometric_icon.update()
                await asyncio.sleep(0.8)

                # Scale down
                self.biometric_icon.scale = 1.0
                self.biometric_icon.update()
                await asyncio.sleep(0.8)

        # Note: This requires async support from the page
        # In practice, you'd call this via page.run_task
        return pulse()

    def authenticate(self):
        """
        Trigger biometric authentication.
        Should be called when screen is shown.
        """
        if self._is_authenticating:
            return

        self._is_authenticating = True
        self._reset_ui()

        # Start pulse animation (would need page.run_task in practice)
        # self.start_pulse_animation()

        # Trigger authentication
        if self.on_authenticate:
            self.on_authenticate()

    def show_success(self):
        """Show success state and trigger haptic feedback."""
        self._is_authenticating = False

        # Trigger success haptic
        if self.haptic_feedback:
            self.haptic_feedback.success()

        # Change icon to success color
        self.biometric_icon.content.color = Colors.SUCCESS_MAIN
        self.biometric_icon.scale = 1.2
        self.biometric_icon.update()

        # Update status text
        self.status_text.content.value = "Unlocked!"
        self.status_text.content.color = Colors.SUCCESS_MAIN
        self.status_text.update()

        # Hide subtitle
        self.subtitle_text.opacity = 0
        self.subtitle_text.update()

    def show_error(self, message: str = "Authentication failed. Try again."):
        """Show error state and trigger haptic feedback."""
        self._is_authenticating = False
        self._auth_failed = True

        # Trigger error haptic
        if self.haptic_feedback:
            self.haptic_feedback.error()

        # Change icon to error color and shake
        self.biometric_icon.content.color = Colors.ERROR_MAIN
        self.biometric_icon.scale = 0.9
        self.biometric_icon.update()

        # Reset scale
        import time
        time.sleep(0.1)
        self.biometric_icon.scale = 1.0
        self.biometric_icon.update()

        # Hide subtitle
        self.subtitle_text.opacity = 0
        self.subtitle_text.update()

        # Show error message
        self.error_text.content.value = message
        self.error_text.visible = True
        self.error_text.opacity = 1.0
        self.error_text.update()

        # Show retry button
        self.retry_button.visible = True
        self.retry_button.opacity = 1.0
        self.retry_button.update()

    def animate_in(self):
        """Trigger entrance animations."""
        # Animate icon with scale
        self.biometric_icon.scale = 0.5
        self.biometric_icon.opacity = 0
        self.biometric_icon.update()

        import time
        time.sleep(0.05)

        self.biometric_icon.scale = 1.0
        self.biometric_icon.opacity = 1.0
        self.biometric_icon.update()


class BiometricPromptDialog(ft.AlertDialog):
    """
    Biometric prompt as a modal dialog (alternative to full-screen).

    Usage:
        dialog = BiometricPromptDialog(
            biometric_type="face_id",
            on_authenticate=handle_auth,
            on_cancel=close_dialog,
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    """

    def __init__(
        self,
        biometric_type: str = "fingerprint",
        on_authenticate: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.biometric_type = biometric_type
        self.on_authenticate = on_authenticate
        self.on_cancel = on_cancel
        self.haptic_feedback = haptic_feedback

        # Icon
        icon_name = ft.Icons.FACE if biometric_type == "face_id" else ft.Icons.FINGERPRINT

        # Build dialog content
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        icon_name,
                        size=80,
                        color=Colors.PRIMARY_500,
                    ),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "Unlock with Face ID" if biometric_type == "face_id" else "Unlock with Fingerprint",
                        size=MobileTypography.TITLE_MEDIUM,
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=MobileSpacing.XS),
                    ft.Text(
                        "Authenticate to continue",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=MobileSpacing.LG,
        )

        super().__init__(
            modal=True,
            title=None,
            content=content,
            actions=[
                ft.TextButton(
                    text="Cancel",
                    on_click=self._handle_cancel,
                ),
                ft.ElevatedButton(
                    text="Authenticate",
                    style=ft.ButtonStyle(
                        bgcolor=Colors.PRIMARY_500,
                        color=Colors.NEUTRAL_0,
                    ),
                    on_click=self._handle_authenticate,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_authenticate(self, e):
        """Handle authenticate button click."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        if self.on_authenticate:
            self.on_authenticate()

    def _handle_cancel(self, e):
        """Handle cancel button click."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if self.on_cancel:
            self.on_cancel()


# Export biometric prompt components
__all__ = [
    'BiometricPrompt',
    'BiometricPromptDialog',
]
