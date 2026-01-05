"""
Premium Animation System for DocAssist Mobile.

Provides consistent, smooth animations throughout the app.
All animations are designed for 60fps performance.
"""

import flet as ft
from typing import Optional, Callable
from enum import Enum


class AnimationDuration(Enum):
    """Standard animation durations (in milliseconds)."""
    INSTANT = 0
    FAST = 150
    NORMAL = 250
    SLOW = 400
    VERY_SLOW = 600


class AnimationCurve(Enum):
    """Standard animation curves."""
    LINEAR = ft.AnimationCurve.LINEAR
    EASE = ft.AnimationCurve.EASE
    EASE_IN = ft.AnimationCurve.EASE_IN
    EASE_OUT = ft.AnimationCurve.EASE_OUT
    EASE_IN_OUT = ft.AnimationCurve.EASE_IN_OUT
    BOUNCE_OUT = ft.AnimationCurve.BOUNCE_OUT
    ELASTIC_OUT = ft.AnimationCurve.ELASTIC_OUT


class Animations:
    """
    Collection of premium animation presets.

    Usage:
        container.animate_scale = Animations.scale_tap()
        container.animate_opacity = Animations.fade_in()
    """

    @staticmethod
    def fade_in(duration: int = AnimationDuration.NORMAL.value) -> ft.Animation:
        """Smooth fade in animation."""
        return ft.Animation(duration, ft.AnimationCurve.EASE_OUT)

    @staticmethod
    def fade_out(duration: int = AnimationDuration.FAST.value) -> ft.Animation:
        """Quick fade out animation."""
        return ft.Animation(duration, ft.AnimationCurve.EASE_IN)

    @staticmethod
    def scale_tap() -> ft.Animation:
        """Quick scale animation for tap feedback (scale down then up)."""
        return ft.Animation(AnimationDuration.FAST.value, ft.AnimationCurve.EASE_IN_OUT)

    @staticmethod
    def scale_in() -> ft.Animation:
        """Scale up animation for appearing elements."""
        return ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT)

    @staticmethod
    def slide_up() -> ft.Animation:
        """Slide up from bottom animation."""
        return ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT)

    @staticmethod
    def slide_down() -> ft.Animation:
        """Slide down animation."""
        return ft.Animation(AnimationDuration.FAST.value, ft.AnimationCurve.EASE_IN)

    @staticmethod
    def slide_left() -> ft.Animation:
        """Slide left animation (screen transition)."""
        return ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_IN_OUT)

    @staticmethod
    def slide_right() -> ft.Animation:
        """Slide right animation (back navigation)."""
        return ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_IN_OUT)

    @staticmethod
    def bounce() -> ft.Animation:
        """Bouncy animation for playful feedback."""
        return ft.Animation(AnimationDuration.SLOW.value, ft.AnimationCurve.BOUNCE_OUT)

    @staticmethod
    def elastic() -> ft.Animation:
        """Elastic animation for pull-to-refresh."""
        return ft.Animation(AnimationDuration.SLOW.value, ft.AnimationCurve.ELASTIC_OUT)

    @staticmethod
    def shimmer(duration: int = 1500) -> ft.Animation:
        """Shimmer animation for skeleton loading screens."""
        return ft.Animation(duration, ft.AnimationCurve.LINEAR)


class AnimatedContainer(ft.Container):
    """
    Container with pre-configured tap animation.
    Scales down slightly on tap, then bounces back.

    Usage:
        card = AnimatedContainer(
            content=...,
            on_click=handler,
        )
    """

    def __init__(
        self,
        *args,
        tap_scale: float = 0.95,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tap_scale = tap_scale
        self._original_on_click = self.on_click

        # Set up animations
        self.animate_scale = Animations.scale_tap()
        self.scale = 1.0

        # Override on_click to add animation
        if self.on_click:
            self.on_click = self._animated_click

    def _animated_click(self, e):
        """Handle click with animation."""
        # Scale down
        self.scale = self.tap_scale
        self.update()

        # Call original handler
        if self._original_on_click:
            self._original_on_click(e)

        # Scale back up (happens automatically via animation)
        # Use a small delay to ensure scale down is visible
        import time
        time.sleep(0.05)
        self.scale = 1.0
        self.update()


class StaggeredAnimation:
    """
    Creates staggered animation effect for list items.
    Items appear one by one with a small delay.

    Usage:
        stagger = StaggeredAnimation(delay=50)
        for i, item in enumerate(items):
            animated_item = stagger.wrap(item, index=i)
            list.controls.append(animated_item)
    """

    def __init__(self, delay_ms: int = 50, max_items: int = 20):
        self.delay_ms = delay_ms
        self.max_items = max_items

    def wrap(self, control: ft.Control, index: int) -> ft.Container:
        """
        Wrap a control with staggered fade-in animation.

        Args:
            control: The control to animate
            index: Item index (determines delay)

        Returns:
            Animated container wrapping the control
        """
        # Cap the delay to prevent very long waits
        effective_index = min(index, self.max_items)

        container = ft.Container(
            content=control,
            animate_opacity=ft.Animation(
                AnimationDuration.NORMAL.value,
                ft.AnimationCurve.EASE_OUT,
            ),
            opacity=0,  # Start invisible
        )

        # We'll trigger the animation after adding to page
        # This needs to be done by the caller
        return container

    def trigger(self, containers: list[ft.Container]):
        """
        Trigger staggered animation for a list of containers.
        Call this after adding all containers to the page.

        Args:
            containers: List of containers to animate
        """
        import asyncio

        async def animate():
            for i, container in enumerate(containers):
                if i < self.max_items:
                    await asyncio.sleep(self.delay_ms / 1000)
                container.opacity = 1
                container.update()

        # Note: This requires async context
        # In practice, you'd use page.run_task or similar
        return animate()


class PullToRefresh(ft.Container):
    """
    Pull-to-refresh component with custom animation.

    Usage:
        ptr = PullToRefresh(
            content=scrollable_list,
            on_refresh=handle_refresh,
        )
    """

    def __init__(
        self,
        content: ft.Control,
        on_refresh: Optional[Callable] = None,
        refresh_threshold: int = 80,
    ):
        self.on_refresh = on_refresh
        self.refresh_threshold = refresh_threshold
        self._is_refreshing = False
        self._pull_distance = 0

        # Refresh indicator
        self.refresh_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=24, height=24, stroke_width=2),
                    ft.Text("Refreshing...", size=12),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            height=0,
            animate=ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT),
            alignment=ft.alignment.center,
        )

        # Build pull-to-refresh container
        super().__init__(
            content=ft.Column(
                [
                    self.refresh_indicator,
                    content,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )

    def start_refresh(self):
        """Start refresh animation."""
        if self._is_refreshing:
            return

        self._is_refreshing = True
        self.refresh_indicator.height = 60
        self.update()

        # Call refresh handler
        if self.on_refresh:
            self.on_refresh()

    def end_refresh(self):
        """End refresh animation."""
        self._is_refreshing = False
        self.refresh_indicator.height = 0
        self.update()


class ShimmerEffect(ft.Container):
    """
    Shimmer loading effect for skeleton screens.
    Creates a moving gradient highlight effect.

    Usage:
        shimmer = ShimmerEffect(width=200, height=20)
    """

    def __init__(
        self,
        width: Optional[float] = None,
        height: Optional[float] = None,
        border_radius: int = 8,
    ):
        from ..tokens import Colors

        # Create shimmer gradient using opacity animation
        self.shimmer_box = ft.Container(
            width=width,
            height=height,
            border_radius=border_radius,
            bgcolor=Colors.NEUTRAL_200,
            animate_opacity=Animations.shimmer(),
            opacity=0.5,
        )

        super().__init__(
            content=self.shimmer_box,
            width=width,
            height=height,
        )

    def start_shimmer(self):
        """Start shimmer animation."""
        # Toggle opacity to create shimmer effect
        # This would need to be called repeatedly
        self.shimmer_box.opacity = 1.0 if self.shimmer_box.opacity == 0.5 else 0.5
        self.shimmer_box.update()


class PageTransition:
    """
    Page transition animations.
    Provides consistent screen transitions throughout the app.
    """

    @staticmethod
    def slide_left_enter() -> dict:
        """New screen slides in from right."""
        return {
            "animate": ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT),
            "offset": ft.transform.Offset(1, 0),  # Start off-screen right
        }

    @staticmethod
    def slide_left_exit() -> dict:
        """Old screen slides out to left."""
        return {
            "animate": ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT),
            "offset": ft.transform.Offset(-0.3, 0),  # Slide slightly left
            "opacity": 0.7,
        }

    @staticmethod
    def slide_right_enter() -> dict:
        """Screen slides in from left (back navigation)."""
        return {
            "animate": ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT),
            "offset": ft.transform.Offset(-0.3, 0),
        }

    @staticmethod
    def slide_right_exit() -> dict:
        """Screen slides out to right (back navigation)."""
        return {
            "animate": ft.Animation(AnimationDuration.NORMAL.value, ft.AnimationCurve.EASE_OUT),
            "offset": ft.transform.Offset(1, 0),
        }

    @staticmethod
    def fade_in() -> dict:
        """Screen fades in."""
        return {
            "animate_opacity": Animations.fade_in(),
            "opacity": 0,
        }

    @staticmethod
    def fade_out() -> dict:
        """Screen fades out."""
        return {
            "animate_opacity": Animations.fade_out(),
            "opacity": 0,
        }


# Export all animation utilities
__all__ = [
    'AnimationDuration',
    'AnimationCurve',
    'Animations',
    'AnimatedContainer',
    'StaggeredAnimation',
    'PullToRefresh',
    'ShimmerEffect',
    'PageTransition',
]
