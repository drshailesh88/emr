"""
Skeleton Loading Components for DocAssist Mobile.

Provides premium skeleton screens with shimmer effect.
Used during data loading to show content structure.
"""

import flet as ft
from typing import Optional
from ..tokens import Colors, MobileSpacing, Radius
from ..animations import ShimmerEffect


class SkeletonBox(ft.Container):
    """
    Basic skeleton box with shimmer effect.

    Usage:
        skeleton = SkeletonBox(width=200, height=20)
    """

    def __init__(
        self,
        width: Optional[float] = None,
        height: Optional[float] = 20,
        border_radius: int = Radius.SM,
    ):
        super().__init__(
            width=width,
            height=height,
            border_radius=border_radius,
            bgcolor=Colors.NEUTRAL_200,
            animate_opacity=ft.Animation(1500, ft.AnimationCurve.LINEAR),
            opacity=1.0,
        )

        # Start shimmer animation
        self._shimmer_state = True

    def update_shimmer(self):
        """Toggle shimmer effect."""
        self.opacity = 0.5 if self._shimmer_state else 1.0
        self._shimmer_state = not self._shimmer_state
        self.update()


class SkeletonText(ft.Container):
    """
    Skeleton text line.

    Usage:
        skeleton = SkeletonText(width=150)
    """

    def __init__(
        self,
        width: Optional[float] = None,
        height: float = 16,
    ):
        super().__init__(
            content=SkeletonBox(
                width=width,
                height=height,
                border_radius=Radius.SM,
            ),
        )


class SkeletonAvatar(ft.Container):
    """
    Skeleton circular avatar.

    Usage:
        skeleton = SkeletonAvatar(size=48)
    """

    def __init__(self, size: float = 48):
        super().__init__(
            width=size,
            height=size,
            border_radius=Radius.FULL,
            bgcolor=Colors.NEUTRAL_200,
            animate_opacity=ft.Animation(1500, ft.AnimationCurve.LINEAR),
        )


class SkeletonPatientCard(ft.Container):
    """
    Skeleton for patient list card.
    Matches the structure of PatientCard.

    Usage:
        skeleton = SkeletonPatientCard()
    """

    def __init__(self):
        content = ft.Row(
            [
                # Avatar skeleton
                SkeletonAvatar(size=48),
                # Text skeletons
                ft.Column(
                    [
                        SkeletonBox(width=150, height=16),
                        ft.Container(height=4),
                        SkeletonBox(width=200, height=14),
                    ],
                    spacing=0,
                    expand=True,
                ),
                # Chevron space
                ft.Container(width=24),
            ],
            spacing=MobileSpacing.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )


class SkeletonAppointmentCard(ft.Container):
    """
    Skeleton for appointment card.
    Matches the structure of AppointmentCard.

    Usage:
        skeleton = SkeletonAppointmentCard()
    """

    def __init__(self):
        content = ft.Row(
            [
                # Time skeleton
                ft.Container(
                    content=SkeletonBox(width=60, height=16),
                    width=70,
                ),
                # Text skeletons
                ft.Column(
                    [
                        SkeletonBox(width=140, height=16),
                        ft.Container(height=4),
                        SkeletonBox(width=100, height=14),
                    ],
                    spacing=0,
                    expand=True,
                ),
                # Chevron space
                ft.Container(width=24),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )


class SkeletonVisitCard(ft.Container):
    """
    Skeleton for visit history card.

    Usage:
        skeleton = SkeletonVisitCard()
    """

    def __init__(self):
        content = ft.Column(
            [
                # Date and diagnosis
                ft.Row(
                    [
                        SkeletonBox(width=100, height=14),
                        ft.Container(expand=True),
                        SkeletonBox(width=60, height=14),
                    ],
                ),
                ft.Container(height=MobileSpacing.SM),
                # Chief complaint
                SkeletonBox(width=None, height=16),
                ft.Container(height=MobileSpacing.XS),
                # Prescription count
                SkeletonBox(width=120, height=14),
            ],
            spacing=0,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )


class SkeletonLabCard(ft.Container):
    """
    Skeleton for lab result card.

    Usage:
        skeleton = SkeletonLabCard()
    """

    def __init__(self):
        content = ft.Column(
            [
                # Test name and date
                ft.Row(
                    [
                        SkeletonBox(width=120, height=16),
                        ft.Container(expand=True),
                        SkeletonBox(width=80, height=14),
                    ],
                ),
                ft.Container(height=MobileSpacing.SM),
                # Result
                ft.Row(
                    [
                        SkeletonBox(width=80, height=20),
                        ft.Container(width=MobileSpacing.SM),
                        SkeletonBox(width=100, height=14),
                    ],
                ),
            ],
            spacing=0,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )


class SkeletonPatientHeader(ft.Container):
    """
    Skeleton for patient detail header.

    Usage:
        skeleton = SkeletonPatientHeader()
    """

    def __init__(self):
        content = ft.Column(
            [
                ft.Row(
                    [
                        # Avatar
                        SkeletonAvatar(size=64),
                        ft.Container(width=MobileSpacing.MD),
                        # Info
                        ft.Column(
                            [
                                SkeletonBox(width=150, height=20),
                                ft.Container(height=MobileSpacing.XS),
                                SkeletonBox(width=180, height=14),
                                ft.Container(height=MobileSpacing.XS),
                                SkeletonBox(width=200, height=14),
                            ],
                            spacing=0,
                        ),
                    ],
                ),
                ft.Container(height=MobileSpacing.MD),
                # Action buttons
                ft.Row(
                    [
                        SkeletonBox(width=80, height=40, border_radius=Radius.BUTTON),
                        ft.Container(width=MobileSpacing.SM),
                        SkeletonBox(width=100, height=40, border_radius=Radius.BUTTON),
                    ],
                ),
            ],
            spacing=0,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            padding=MobileSpacing.SCREEN_PADDING,
        )


class SkeletonList(ft.Container):
    """
    Skeleton for a list of items.
    Shows multiple skeleton cards.

    Usage:
        skeleton = SkeletonList(
            item_skeleton=SkeletonPatientCard,
            count=5,
        )
    """

    def __init__(
        self,
        item_skeleton: type,
        count: int = 5,
        spacing: int = MobileSpacing.XS,
    ):
        items = [item_skeleton() for _ in range(count)]

        content = ft.ListView(
            controls=items,
            spacing=spacing,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
            expand=True,
        )

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )


class SkeletonScreen(ft.Container):
    """
    Full screen skeleton with header and list.

    Usage:
        skeleton = SkeletonScreen(
            title_width=100,
            item_skeleton=SkeletonPatientCard,
            item_count=5,
        )
    """

    def __init__(
        self,
        title_width: float = 120,
        item_skeleton: type = SkeletonPatientCard,
        item_count: int = 5,
    ):
        content = ft.Column(
            [
                # Header
                ft.Container(
                    content=SkeletonBox(width=title_width, height=24),
                    padding=MobileSpacing.SCREEN_PADDING,
                ),
                # List
                SkeletonList(
                    item_skeleton=item_skeleton,
                    count=item_count,
                ),
            ],
            spacing=0,
            expand=True,
        )

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )


# Export all skeleton components
__all__ = [
    'SkeletonBox',
    'SkeletonText',
    'SkeletonAvatar',
    'SkeletonPatientCard',
    'SkeletonAppointmentCard',
    'SkeletonVisitCard',
    'SkeletonLabCard',
    'SkeletonPatientHeader',
    'SkeletonList',
    'SkeletonScreen',
]
