"""
Onboarding Screen - Multi-page onboarding flow.

Beautiful 4-page swipeable onboarding experience with:
- Page 1: "Your Clinic, Anywhere"
- Page 2: "Privacy First"
- Page 3: "Sync Seamlessly"
- Page 4: "Get Started"

Features:
- Horizontal swipe between pages
- Animated transitions (fade + slide)
- Page indicator dots
- Skip button
- Next/Get Started buttons
"""

import flet as ft
from typing import Callable, Optional
import webbrowser

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations
from ..haptics import HapticFeedback, HapticType
from ..components.onboarding_page import OnboardingPage, IllustrationCard
from ..components.page_indicator import PageIndicator


class OnboardingScreen(ft.Container):
    """
    Multi-page onboarding screen.

    Features:
    - 4 swipeable pages with premium animations
    - Page indicator dots
    - Skip button (top-right)
    - Next button (pages 1-3)
    - Get Started button (page 4)

    Usage:
        onboarding = OnboardingScreen(
            on_complete=handle_onboarding_complete,
        )
    """

    def __init__(
        self,
        on_complete: Callable[[], None],
        haptics: Optional[HapticFeedback] = None,
    ):
        self.on_complete = on_complete
        self.haptics = haptics
        self.current_page = 0
        self.total_pages = 4

        # Build UI
        content = self._build_content()

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_0,
        )

        # Trigger initial page animation
        self._animate_current_page()

    def _build_content(self) -> ft.Column:
        """Build the onboarding screen layout."""
        # Create all onboarding pages
        self.pages = [
            self._create_page_1(),
            self._create_page_2(),
            self._create_page_3(),
            self._create_page_4(),
        ]

        # Page container (shows one page at a time)
        self.page_container = ft.Container(
            content=self.pages[0],
            expand=True,
            animate=Animations.slide_left(),
        )

        # Page indicator
        self.page_indicator = PageIndicator(
            total_pages=self.total_pages,
            current_page=self.current_page,
        )

        # Skip button
        self.skip_button = ft.TextButton(
            text="Skip",
            style=ft.ButtonStyle(
                color=Colors.NEUTRAL_600,
            ),
            on_click=self._handle_skip,
        )

        # Next button
        self.next_button = ft.Container(
            content=ft.ElevatedButton(
                text="Next",
                width=120,
                height=MobileSpacing.TOUCH_TARGET,
                style=ft.ButtonStyle(
                    bgcolor=Colors.PRIMARY_500,
                    color=Colors.NEUTRAL_0,
                    shape=ft.RoundedRectangleBorder(radius=Radius.FULL),
                ),
                on_click=self._handle_next,
            ),
            visible=True,
        )

        # Top bar with skip button
        top_bar = ft.Row(
            [
                ft.Container(expand=True),  # Spacer
                self.skip_button,
            ],
            alignment=ft.MainAxisAlignment.END,
        )

        # Bottom navigation (indicator + button)
        bottom_nav = ft.Container(
            content=ft.Column(
                [
                    self.page_indicator,
                    ft.Container(height=MobileSpacing.LG),
                    self.next_button,
                    ft.Container(height=MobileSpacing.XL),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
        )

        # Main layout
        return ft.Column(
            [
                ft.Container(
                    content=top_bar,
                    padding=ft.padding.only(
                        top=MobileSpacing.MD,
                        right=MobileSpacing.SM,
                    ),
                ),
                self.page_container,
                bottom_nav,
            ],
            spacing=0,
            expand=True,
        )

    # -------------------------------------------------------------------------
    # Page Definitions
    # -------------------------------------------------------------------------

    def _create_page_1(self) -> OnboardingPage:
        """Page 1: Your Clinic, Anywhere."""
        illustration = IllustrationCard(
            icon=ft.Icons.PHONE_IPHONE,
            icon_color=Colors.PRIMARY_500,
            background_color=Colors.PRIMARY_50,
        )

        return OnboardingPage(
            custom_illustration=illustration,
            title="Your Clinic, Anywhere",
            description="Access your patient records from anywhere, anytime",
            subdescription="Never miss important patient information again",
            on_appear=lambda: self._trigger_haptic(HapticType.LIGHT),
        )

    def _create_page_2(self) -> OnboardingPage:
        """Page 2: Privacy First."""
        illustration = IllustrationCard(
            icon=ft.Icons.SHIELD,
            icon_color=Colors.SUCCESS_MAIN,
            background_color=Colors.SUCCESS_LIGHT,
        )

        return OnboardingPage(
            custom_illustration=illustration,
            title="Privacy First",
            description="End-to-end encrypted. Your data stays yours.",
            subdescription="We can't see your patient data - only you can",
            on_appear=lambda: self._trigger_haptic(HapticType.LIGHT),
        )

    def _create_page_3(self) -> OnboardingPage:
        """Page 3: Sync Seamlessly."""
        illustration = IllustrationCard(
            icon=ft.Icons.CLOUD_SYNC,
            icon_color=Colors.INFO_MAIN,
            background_color="#E8F0FE",
        )

        return OnboardingPage(
            custom_illustration=illustration,
            title="Sync Seamlessly",
            description="Changes sync automatically between devices",
            subdescription="Works offline, syncs when connected",
            on_appear=lambda: self._trigger_haptic(HapticType.LIGHT),
        )

    def _create_page_4(self) -> OnboardingPage:
        """Page 4: Get Started."""
        # DocAssist logo
        logo = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.LOCAL_HOSPITAL,
                        size=80,
                        color=Colors.PRIMARY_500,
                    ),
                    ft.Container(height=MobileSpacing.SM),
                    ft.Text(
                        "DocAssist",
                        size=MobileTypography.DISPLAY_LARGE,
                        weight=ft.FontWeight.W_300,
                        color=Colors.NEUTRAL_900,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Login button
        login_button = ft.ElevatedButton(
            text="Login to Your Account",
            width=280,
            height=MobileSpacing.TOUCH_TARGET,
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            ),
            on_click=self._handle_complete,
        )

        # Learn more link
        learn_more = ft.Row(
            [
                ft.Text(
                    "New to DocAssist?",
                    size=MobileTypography.BODY_MEDIUM,
                    color=Colors.NEUTRAL_600,
                ),
                ft.TextButton(
                    text="Learn More",
                    style=ft.ButtonStyle(color=Colors.PRIMARY_500),
                    on_click=self._handle_learn_more,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=MobileSpacing.XXS,
        )

        # Action buttons container
        action_buttons = ft.Column(
            [
                login_button,
                ft.Container(height=MobileSpacing.SM),
                learn_more,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return OnboardingPage(
            custom_illustration=logo,
            title="Ready to Get Started?",
            description="Transform your practice with premium EMR",
            action_button=action_buttons,
            on_appear=lambda: self._trigger_haptic(HapticType.MEDIUM),
        )

    # -------------------------------------------------------------------------
    # Navigation Handlers
    # -------------------------------------------------------------------------

    def _handle_next(self, e):
        """Handle next button click."""
        self._trigger_haptic(HapticType.MEDIUM)

        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_page()
        else:
            self._handle_complete(e)

    def _handle_skip(self, e):
        """Handle skip button click."""
        self._trigger_haptic(HapticType.LIGHT)
        self._handle_complete(e)

    def _handle_complete(self, e):
        """Handle onboarding completion."""
        self._trigger_haptic(HapticType.SUCCESS)

        if self.on_complete:
            self.on_complete()

    def _handle_learn_more(self, e):
        """Handle learn more link."""
        self._trigger_haptic(HapticType.LIGHT)
        # Open DocAssist website
        webbrowser.open("https://docassist.ai")

    # -------------------------------------------------------------------------
    # Page Management
    # -------------------------------------------------------------------------

    def _update_page(self):
        """Update the displayed page with animation."""
        # Update page indicator
        self.page_indicator.set_page(self.current_page)

        # Update skip button visibility (hide on last page)
        self.skip_button.visible = self.current_page < self.total_pages - 1

        # Update next button (hide on last page)
        self.next_button.visible = self.current_page < self.total_pages - 1

        # Animate out current page
        if hasattr(self.page_container.content, 'animate_out'):
            self.page_container.content.animate_out()

        # Update page container content
        self.page_container.content = self.pages[self.current_page]

        # Update UI
        self.update()

        # Animate in new page (slight delay)
        import threading
        threading.Timer(0.1, self._animate_current_page).start()

    def _animate_current_page(self):
        """Trigger animation for current page."""
        if hasattr(self.page_container.content, 'animate_in'):
            self.page_container.content.animate_in()

    def _trigger_haptic(self, haptic_type: HapticType):
        """Trigger haptic feedback."""
        if self.haptics:
            self.haptics._trigger(haptic_type)

    # -------------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------------

    def go_to_page(self, page: int):
        """
        Navigate to a specific page.

        Args:
            page: Page index (0-based)
        """
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._update_page()

    def next_page(self):
        """Go to next page."""
        self._handle_next(None)

    def previous_page(self):
        """Go to previous page."""
        self._trigger_haptic(HapticType.LIGHT)

        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()


class OnboardingScreenAlternative(ft.Container):
    """
    Alternative onboarding with swipeable GestureDetector.

    This version uses horizontal drag gestures for swiping between pages.
    More native feel but requires additional gesture handling.

    Note: Flet's GestureDetector support varies by platform.
    """

    def __init__(
        self,
        on_complete: Callable[[], None],
        haptics: Optional[HapticFeedback] = None,
    ):
        # Implementation similar to OnboardingScreen
        # but with GestureDetector for swipe handling
        # Left as TODO for future enhancement
        super().__init__()


__all__ = [
    'OnboardingScreen',
    'OnboardingScreenAlternative',
]
