"""
Premium Widget Library for DocAssist EMR

This module exports all premium UI components built on the design token system.
"""

from .buttons import (
    PrimaryButton,
    SecondaryButton,
    DangerButton,
    GhostButton,
    IconActionButton,
)

from .cards import (
    PremiumCard,
    PatientCard,
    SelectableCard,
)

from .text_fields import (
    PremiumTextField,
    PremiumSearchField,
    PremiumTextArea,
    ChatInputField,
)

from .dialogs import (
    PremiumDialog,
    ConfirmDialog,
    FormDialog,
    SuccessDialog,
    InfoDialog,
)

__all__ = [
    # Buttons
    'PrimaryButton',
    'SecondaryButton',
    'DangerButton',
    'GhostButton',
    'IconActionButton',

    # Cards
    'PremiumCard',
    'PatientCard',
    'SelectableCard',

    # Text Fields
    'PremiumTextField',
    'PremiumSearchField',
    'PremiumTextArea',
    'ChatInputField',

    # Dialogs
    'PremiumDialog',
    'ConfirmDialog',
    'FormDialog',
    'SuccessDialog',
    'InfoDialog',
]
