"""
Onboarding Page Component - Single page in onboarding flow.

Displays an icon/illustration, title, description, and optional action button.
Animates in when the page becomes active.
"""

import flet as ft
from typing import Optional, Callable

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations


class OnboardingPage(ft.Container):
    """
    Single onboarding page with icon, title, and description.

    Features:
    - Large icon/illustration area (top 40%)
    - Bold title text
    - Body description text
    - Optional action button
    - Entrance animations

    Usage:
        page = OnboardingPage(
            icon=ft.Icons.CLOUD_SYNC,
            title="Sync Seamlessly",
            description="Changes sync automatically between devices",
            icon_color=Colors.PRIMARY_500,
        )
    """

    def __init__(
        self,
        icon: Optional[str] = None,
        title: str = "",
        description: str = "",
        subdescription: Optional[str] = None,
        icon_color: str = Colors.PRIMARY_500,
        icon_size: int = 120,
        custom_illustration: Optional[ft.Control] = None,
        action_button: Optional[ft.Control] = None,
        on_appear: Optional[Callable] = None,
    ):
        self.icon = icon
        self.title = title
        self.description = description
        self.subdescription = subdescription
        self.icon_color = icon_color
        self.icon_size = icon_size
        self.custom_illustration = custom_illustration
        self.action_button = action_button
        self.on_appear = on_appear

        # Animation state
        self.is_visible = False

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            expand=True,
            padding=ft.padding.symmetric(
                horizontal=MobileSpacing.SCREEN_PADDING,
                vertical=MobileSpacing.XL,
            ),
            bgcolor=Colors.NEUTRAL_0,
        )

    def _build_content(self) -> ft.Column:
        """Build the page content."""
        controls = []

        # Top spacer
        controls.append(ft.Container(height=MobileSpacing.XXL))

        # Icon/Illustration area (top 40%)
        if self.custom_illustration:
            # Custom illustration provided
            illustration_container = ft.Container(
                content=self.custom_illustration,
                alignment=ft.alignment.center,
                animate_opacity=Animations.fade_in(),
                animate_scale=Animations.scale_in(),
                opacity=0,
                scale=0.8,
            )
        elif self.icon:
            # Standard icon
            illustration_container = ft.Container(
                content=ft.Icon(
                    self.icon,
                    size=self.icon_size,
                    color=self.icon_color,
                ),
                alignment=ft.alignment.center,
                animate_opacity=Animations.fade_in(),
                animate_scale=Animations.scale_in(),
                opacity=0,
                scale=0.8,
            )
        else:
            illustration_container = ft.Container()

        self.illustration_container = illustration_container
        controls.append(illustration_container)

        # Spacer
        controls.append(ft.Container(height=MobileSpacing.XXL))

        # Title
        self.title_container = ft.Container(
            content=ft.Text(
                self.title,
                size=MobileTypography.DISPLAY_MEDIUM,
                weight=ft.FontWeight.BOLD,
                color=Colors.NEUTRAL_900,
                text_align=ft.TextAlign.CENTER,
            ),
            animate_opacity=Animations.fade_in(duration=400),
            opacity=0,
        )
        controls.append(self.title_container)

        # Spacer
        controls.append(ft.Container(height=MobileSpacing.MD))

        # Description
        self.description_container = ft.Container(
            content=ft.Text(
                self.description,
                size=MobileTypography.BODY_LARGE,
                color=Colors.NEUTRAL_600,
                text_align=ft.TextAlign.CENTER,
            ),
            animate_opacity=Animations.fade_in(duration=400),
            opacity=0,
        )
        controls.append(self.description_container)

        # Subdescription (if provided)
        if self.subdescription:
            controls.append(ft.Container(height=MobileSpacing.SM))
            self.subdescription_container = ft.Container(
                content=ft.Text(
                    self.subdescription,
                    size=MobileTypography.BODY_MEDIUM,
                    color=Colors.NEUTRAL_500,
                    text_align=ft.TextAlign.CENTER,
                    italic=True,
                ),
                animate_opacity=Animations.fade_in(duration=400),
                opacity=0,
            )
            controls.append(self.subdescription_container)
        else:
            self.subdescription_container = None

        # Flexible spacer to push action button to bottom
        controls.append(ft.Container(expand=True))

        # Action button (if provided)
        if self.action_button:
            self.action_button_container = ft.Container(
                content=self.action_button,
                padding=ft.padding.only(bottom=MobileSpacing.LG),
                animate_opacity=Animations.fade_in(duration=400),
                opacity=0,
            )
            controls.append(self.action_button_container)
        else:
            self.action_button_container = None

        return ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    def animate_in(self):
        """
        Trigger entrance animations.

        Animates elements in sequence:
        1. Icon/illustration (scale + fade)
        2. Title (fade)
        3. Description (fade)
        4. Action button (fade)
        """
        if self.is_visible:
            return

        self.is_visible = True

        # Icon/illustration
        self.illustration_container.opacity = 1
        self.illustration_container.scale = 1.0

        # Title (slight delay)
        self.title_container.opacity = 1

        # Description
        self.description_container.opacity = 1

        # Subdescription
        if self.subdescription_container:
            self.subdescription_container.opacity = 1

        # Action button
        if self.action_button_container:
            self.action_button_container.opacity = 1

        # Update
        self.update()

        # Callback
        if self.on_appear:
            self.on_appear()

    def animate_out(self):
        """Trigger exit animations."""
        if not self.is_visible:
            return

        self.is_visible = False

        # Fade out all elements
        self.illustration_container.opacity = 0
        self.title_container.opacity = 0
        self.description_container.opacity = 0

        if self.subdescription_container:
            self.subdescription_container.opacity = 0

        if self.action_button_container:
            self.action_button_container.opacity = 0

        self.update()


class IllustrationCard(ft.Container):
    """
    Illustration card for onboarding pages.

    Creates a card with an icon and decorative background.
    Can be used as custom_illustration in OnboardingPage.

    Usage:
        illustration = IllustrationCard(
            icon=ft.Icons.LOCK,
            background_color=Colors.PRIMARY_50,
            icon_color=Colors.PRIMARY_500,
        )
    """

    def __init__(
        self,
        icon: str,
        icon_size: int = 80,
        icon_color: str = Colors.PRIMARY_500,
        background_color: str = Colors.PRIMARY_50,
        card_size: int = 160,
    ):
        super().__init__(
            content=ft.Icon(
                icon,
                size=icon_size,
                color=icon_color,
            ),
            width=card_size,
            height=card_size,
            bgcolor=background_color,
            border_radius=card_size // 4,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=f"{background_color}80",
                offset=ft.Offset(0, 4),
            ),
        )


class FeatureList(ft.Column):
    """
    Feature list for onboarding pages.

    Displays a list of features with icons.

    Usage:
        features = FeatureList(
            features=[
                ("Bank-grade encryption", ft.Icons.SHIELD),
                ("Zero-knowledge architecture", ft.Icons.LOCK),
                ("Your data stays on your device", ft.Icons.PHONE_IPHONE),
            ]
        )
    """

    def __init__(
        self,
        features: list[tuple[str, str]],  # List of (text, icon)
        icon_color: str = Colors.PRIMARY_500,
    ):
        feature_controls = []

        for text, icon in features:
            feature_item = ft.Row(
                [
                    ft.Icon(
                        icon,
                        size=24,
                        color=icon_color,
                    ),
                    ft.Container(width=MobileSpacing.SM),
                    ft.Text(
                        text,
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_700,
                        expand=True,
                    ),
                ],
                spacing=0,
            )
            feature_controls.append(feature_item)
            feature_controls.append(ft.Container(height=MobileSpacing.MD))

        super().__init__(
            controls=feature_controls,
            spacing=0,
        )


__all__ = [
    'OnboardingPage',
    'IllustrationCard',
    'FeatureList',
]
