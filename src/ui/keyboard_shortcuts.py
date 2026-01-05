"""Keyboard shortcuts system for DocAssist EMR.

Provides global keyboard shortcuts, shortcut registry, and help overlay.
"""

import flet as ft
from typing import Callable, Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import logging
import platform

logger = logging.getLogger(__name__)


class ShortcutCategory(Enum):
    """Categories for organizing shortcuts."""
    GENERAL = "General"
    NAVIGATION = "Navigation"
    PATIENT = "Patient Management"
    PRESCRIPTION = "Prescription"
    AI = "AI Assistant"
    SYSTEM = "System"


@dataclass
class Shortcut:
    """Represents a keyboard shortcut."""
    key: str  # The key to press (e.g., "s", "n", "F1")
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    meta: bool = False  # Command key on Mac
    description: str = ""
    category: ShortcutCategory = ShortcutCategory.GENERAL
    action: Optional[Callable] = None
    enabled: bool = True

    def matches(self, e: ft.KeyboardEvent) -> bool:
        """Check if keyboard event matches this shortcut."""
        return (
            e.key.lower() == self.key.lower() and
            e.ctrl == self.ctrl and
            e.alt == self.alt and
            e.shift == self.shift and
            e.meta == self.meta
        )

    def get_display_string(self) -> str:
        """Get human-readable shortcut string."""
        # Use Cmd on Mac, Ctrl on others
        is_mac = platform.system() == "Darwin"

        parts = []
        if self.ctrl:
            parts.append("Cmd" if is_mac else "Ctrl")
        if self.alt:
            parts.append("Alt")
        if self.shift:
            parts.append("Shift")
        if self.meta and not is_mac:  # Only show Meta explicitly on non-Mac
            parts.append("Meta")

        # Format key nicely
        key_display = self.key
        if len(self.key) == 1:
            key_display = self.key.upper()
        elif self.key.startswith("F") and len(self.key) <= 3:  # Function keys
            key_display = self.key.upper()
        elif self.key == "Escape":
            key_display = "Esc"
        elif self.key == "Enter":
            key_display = "Enter"
        elif self.key == "ArrowLeft":
            key_display = "←"
        elif self.key == "ArrowRight":
            key_display = "→"
        elif self.key == "ArrowUp":
            key_display = "↑"
        elif self.key == "ArrowDown":
            key_display = "↓"

        parts.append(key_display)
        return "+".join(parts)


class KeyboardShortcutRegistry:
    """Registry for managing keyboard shortcuts."""

    def __init__(self):
        self.shortcuts: List[Shortcut] = []
        self._initialized = False

    def register(self, shortcut: Shortcut):
        """Register a new shortcut."""
        # Check for conflicts
        for existing in self.shortcuts:
            if (existing.key.lower() == shortcut.key.lower() and
                existing.ctrl == shortcut.ctrl and
                existing.alt == shortcut.alt and
                existing.shift == shortcut.shift and
                existing.meta == shortcut.meta):
                logger.warning(
                    f"Shortcut conflict: {shortcut.get_display_string()} "
                    f"already registered for '{existing.description}'"
                )
                return False

        self.shortcuts.append(shortcut)
        logger.debug(f"Registered shortcut: {shortcut.get_display_string()} - {shortcut.description}")
        return True

    def unregister(self, key: str, ctrl: bool = False, alt: bool = False,
                   shift: bool = False, meta: bool = False):
        """Unregister a shortcut."""
        self.shortcuts = [
            s for s in self.shortcuts
            if not (s.key.lower() == key.lower() and
                   s.ctrl == ctrl and s.alt == alt and
                   s.shift == shift and s.meta == meta)
        ]

    def get_shortcut(self, e: ft.KeyboardEvent) -> Optional[Shortcut]:
        """Find shortcut matching the keyboard event."""
        for shortcut in self.shortcuts:
            if shortcut.enabled and shortcut.matches(e):
                return shortcut
        return None

    def get_shortcuts_by_category(self) -> Dict[ShortcutCategory, List[Shortcut]]:
        """Get shortcuts grouped by category."""
        by_category: Dict[ShortcutCategory, List[Shortcut]] = {}
        for shortcut in self.shortcuts:
            if shortcut.category not in by_category:
                by_category[shortcut.category] = []
            by_category[shortcut.category].append(shortcut)
        return by_category

    def enable_shortcut(self, key: str, ctrl: bool = False):
        """Enable a specific shortcut."""
        for shortcut in self.shortcuts:
            if shortcut.key.lower() == key.lower() and shortcut.ctrl == ctrl:
                shortcut.enabled = True

    def disable_shortcut(self, key: str, ctrl: bool = False):
        """Disable a specific shortcut."""
        for shortcut in self.shortcuts:
            if shortcut.key.lower() == key.lower() and shortcut.ctrl == ctrl:
                shortcut.enabled = False


class KeyboardShortcutHandler:
    """Global keyboard shortcut handler for DocAssist EMR."""

    def __init__(self, page: ft.Page):
        """Initialize the keyboard shortcut handler.

        Args:
            page: The Flet page to attach handlers to
        """
        self.page = page
        self.registry = KeyboardShortcutRegistry()
        self.help_overlay: Optional[ft.Container] = None
        self.help_dialog_open = False

        # Callbacks (set by app)
        self.on_new_patient: Optional[Callable] = None
        self.on_save: Optional[Callable] = None
        self.on_focus_search: Optional[Callable] = None
        self.on_print_pdf: Optional[Callable] = None
        self.on_toggle_voice: Optional[Callable] = None
        self.on_submit: Optional[Callable] = None
        self.on_switch_tab: Optional[Callable[[int], None]] = None
        self.on_backup: Optional[Callable] = None
        self.on_refresh_patients: Optional[Callable] = None
        self.on_navigate_patient: Optional[Callable[[str], None]] = None
        self.on_generate_rx: Optional[Callable] = None
        self.on_settings: Optional[Callable] = None
        self.on_help: Optional[Callable] = None

        # Initialize shortcuts
        self._register_default_shortcuts()

        # Attach keyboard handler to page
        self.page.on_keyboard_event = self._handle_keyboard_event
        logger.info("Keyboard shortcut handler initialized")

    def _register_default_shortcuts(self):
        """Register all default shortcuts."""

        # GENERAL SHORTCUTS
        self.registry.register(Shortcut(
            key="n", ctrl=True,
            description="New patient",
            category=ShortcutCategory.PATIENT,
            action=self._action_new_patient
        ))

        self.registry.register(Shortcut(
            key="s", ctrl=True,
            description="Save current form",
            category=ShortcutCategory.GENERAL,
            action=self._action_save
        ))

        self.registry.register(Shortcut(
            key="f", ctrl=True,
            description="Focus search box",
            category=ShortcutCategory.NAVIGATION,
            action=self._action_focus_search
        ))

        self.registry.register(Shortcut(
            key="p", ctrl=True,
            description="Print/Generate PDF",
            category=ShortcutCategory.PRESCRIPTION,
            action=self._action_print_pdf
        ))

        self.registry.register(Shortcut(
            key="m", ctrl=True,
            description="Toggle voice recording",
            category=ShortcutCategory.GENERAL,
            action=self._action_toggle_voice
        ))

        self.registry.register(Shortcut(
            key="Enter", ctrl=True,
            description="Submit/Save and continue",
            category=ShortcutCategory.GENERAL,
            action=self._action_submit
        ))

        self.registry.register(Shortcut(
            key="Escape",
            description="Close dialog/Cancel",
            category=ShortcutCategory.GENERAL,
            action=self._action_escape
        ))

        self.registry.register(Shortcut(
            key="g", ctrl=True,
            description="Generate prescription",
            category=ShortcutCategory.PRESCRIPTION,
            action=self._action_generate_rx
        ))

        # NAVIGATION SHORTCUTS
        self.registry.register(Shortcut(
            key="1", ctrl=True,
            description="Switch to Patients tab",
            category=ShortcutCategory.NAVIGATION,
            action=lambda: self._action_switch_tab(0)
        ))

        self.registry.register(Shortcut(
            key="2", ctrl=True,
            description="Switch to Prescription tab",
            category=ShortcutCategory.NAVIGATION,
            action=lambda: self._action_switch_tab(1)
        ))

        self.registry.register(Shortcut(
            key="3", ctrl=True,
            description="Switch to History tab",
            category=ShortcutCategory.NAVIGATION,
            action=lambda: self._action_switch_tab(2)
        ))

        self.registry.register(Shortcut(
            key="4", ctrl=True,
            description="Switch to Labs tab",
            category=ShortcutCategory.NAVIGATION,
            action=lambda: self._action_switch_tab(3)
        ))

        # SYSTEM SHORTCUTS
        self.registry.register(Shortcut(
            key="b", ctrl=True,
            description="Create backup",
            category=ShortcutCategory.SYSTEM,
            action=self._action_backup
        ))

        self.registry.register(Shortcut(
            key="/", ctrl=True,
            description="Show shortcuts help",
            category=ShortcutCategory.SYSTEM,
            action=self._action_show_help
        ))

        self.registry.register(Shortcut(
            key="F1",
            description="Show shortcuts help",
            category=ShortcutCategory.SYSTEM,
            action=self._action_show_help
        ))

        self.registry.register(Shortcut(
            key="F5",
            description="Refresh patient list",
            category=ShortcutCategory.PATIENT,
            action=self._action_refresh_patients
        ))

        self.registry.register(Shortcut(
            key="ArrowLeft", alt=True,
            description="Previous patient",
            category=ShortcutCategory.NAVIGATION,
            action=lambda: self._action_navigate_patient("previous")
        ))

        self.registry.register(Shortcut(
            key="ArrowRight", alt=True,
            description="Next patient",
            category=ShortcutCategory.NAVIGATION,
            action=lambda: self._action_navigate_patient("next")
        ))

        self.registry.register(Shortcut(
            key=",", ctrl=True,
            description="Open settings",
            category=ShortcutCategory.SYSTEM,
            action=self._action_settings
        ))

        logger.info(f"Registered {len(self.registry.shortcuts)} default shortcuts")

    def _handle_keyboard_event(self, e: ft.KeyboardEvent):
        """Handle keyboard events from Flet.

        Args:
            e: Keyboard event from Flet
        """
        # Don't handle events if user is typing in an input field
        # (except for global shortcuts like Escape, F1, etc.)
        if self._is_typing_in_field(e):
            # Still allow escape and F1 in input fields
            if e.key not in ["Escape", "F1"]:
                return

        # Find matching shortcut
        shortcut = self.registry.get_shortcut(e)

        if shortcut and shortcut.action:
            logger.debug(f"Triggered shortcut: {shortcut.get_display_string()} - {shortcut.description}")
            try:
                # Prevent default browser behavior for shortcuts
                if hasattr(e, 'prevent_default'):
                    e.prevent_default()

                # Execute action
                shortcut.action()
            except Exception as ex:
                logger.error(f"Error executing shortcut action: {ex}", exc_info=True)

    def _is_typing_in_field(self, e: ft.KeyboardEvent) -> bool:
        """Check if user is typing in an input field.

        Args:
            e: Keyboard event

        Returns:
            True if user is typing in input field
        """
        # In Flet, we need to check if the focused control is an input
        # This is a simplified check - in production might need more sophistication
        # For now, we'll allow global shortcuts to work everywhere except during
        # certain key combinations

        # Always handle these shortcuts regardless of focus
        global_keys = ["Escape", "F1", "F5"]
        if e.key in global_keys:
            return False

        # Ctrl combinations should generally work
        if e.ctrl or e.alt or e.meta:
            return False

        # Otherwise, assume user might be typing
        return False  # For now, allow all shortcuts - Flet will handle focus

    # Action handlers
    def _action_new_patient(self):
        """Handle new patient shortcut."""
        if self.on_new_patient:
            self.on_new_patient()

    def _action_save(self):
        """Handle save shortcut."""
        if self.on_save:
            self.on_save()

    def _action_focus_search(self):
        """Handle focus search shortcut."""
        if self.on_focus_search:
            self.on_focus_search()

    def _action_print_pdf(self):
        """Handle print PDF shortcut."""
        if self.on_print_pdf:
            self.on_print_pdf()

    def _action_toggle_voice(self):
        """Handle toggle voice shortcut."""
        if self.on_toggle_voice:
            self.on_toggle_voice()

    def _action_submit(self):
        """Handle submit shortcut."""
        if self.on_submit:
            self.on_submit()

    def _action_escape(self):
        """Handle escape key - close dialogs."""
        # Close help overlay if open
        if self.help_dialog_open:
            self._close_help_overlay()
            return

        # Close any open dialogs
        if self.page.overlay:
            for item in self.page.overlay:
                if isinstance(item, ft.AlertDialog) and item.open:
                    item.open = False
                    self.page.update()
                    return

    def _action_switch_tab(self, tab_index: int):
        """Handle tab switch shortcut."""
        if self.on_switch_tab:
            self.on_switch_tab(tab_index)

    def _action_backup(self):
        """Handle backup shortcut."""
        if self.on_backup:
            self.on_backup()

    def _action_show_help(self):
        """Show shortcuts help overlay."""
        if self.help_dialog_open:
            self._close_help_overlay()
        else:
            self._show_help_overlay()

    def _action_refresh_patients(self):
        """Handle refresh patients shortcut."""
        if self.on_refresh_patients:
            self.on_refresh_patients()

    def _action_navigate_patient(self, direction: str):
        """Handle patient navigation shortcut."""
        if self.on_navigate_patient:
            self.on_navigate_patient(direction)

    def _action_generate_rx(self):
        """Handle generate prescription shortcut."""
        if self.on_generate_rx:
            self.on_generate_rx()

    def _action_settings(self):
        """Handle settings shortcut."""
        if self.on_settings:
            self.on_settings()

    def _action_help(self):
        """Handle help shortcut."""
        if self.on_help:
            self.on_help()

    def _show_help_overlay(self):
        """Show the keyboard shortcuts help overlay."""
        self.help_dialog_open = True

        # Build shortcuts list grouped by category
        shortcuts_by_category = self.registry.get_shortcuts_by_category()

        # Create columns for each category
        category_columns = []

        # Define order for categories
        category_order = [
            ShortcutCategory.GENERAL,
            ShortcutCategory.PATIENT,
            ShortcutCategory.PRESCRIPTION,
            ShortcutCategory.NAVIGATION,
            ShortcutCategory.AI,
            ShortcutCategory.SYSTEM,
        ]

        for category in category_order:
            if category not in shortcuts_by_category:
                continue

            shortcuts = shortcuts_by_category[category]

            # Category header
            category_items = [
                ft.Container(
                    content=ft.Text(
                        category.value.upper(),
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                    ),
                    padding=ft.padding.only(bottom=8),
                )
            ]

            # Shortcuts in this category
            for shortcut in shortcuts:
                category_items.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                shortcut.get_display_string(),
                                size=12,
                                weight=ft.FontWeight.W_500,
                                font_family="monospace",
                            ),
                            width=120,
                        ),
                        ft.Text(
                            shortcut.description,
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                    ], spacing=10)
                )

            category_columns.append(
                ft.Container(
                    content=ft.Column(category_items, spacing=6, tight=True),
                    padding=10,
                )
            )

        # Create help dialog
        help_content = ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.KEYBOARD, size=24, color=ft.Colors.BLUE_700),
                        ft.Text(
                            "Keyboard Shortcuts",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(expand=True),  # Spacer
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=20,
                            tooltip="Close (Esc)",
                            on_click=lambda e: self._close_help_overlay(),
                        ),
                    ], spacing=10),
                    padding=ft.padding.only(left=20, right=10, top=15, bottom=10),
                    bgcolor=ft.Colors.BLUE_50,
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                # Shortcuts grid
                ft.Container(
                    content=ft.Row(
                        category_columns,
                        spacing=20,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=20,
                    expand=True,
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                # Footer
                ft.Container(
                    content=ft.Text(
                        "💡 Tip: Press F1 or Ctrl+/ anytime to show this help",
                        size=11,
                        italic=True,
                        color=ft.Colors.GREY_600,
                    ),
                    padding=ft.padding.only(left=20, bottom=15, top=10),
                    bgcolor=ft.Colors.GREY_50,
                ),
            ], spacing=0),
            width=900,
            height=600,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            ),
        )

        # Overlay background
        self.help_overlay = ft.Container(
            content=ft.Stack([
                # Semi-transparent background
                ft.Container(
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                    expand=True,
                    on_click=lambda e: self._close_help_overlay(),
                ),
                # Help dialog centered
                ft.Container(
                    content=help_content,
                    alignment=ft.alignment.center,
                ),
            ]),
            expand=True,
        )

        # Add to page overlay
        self.page.overlay.append(self.help_overlay)
        self.page.update()

        logger.info("Keyboard shortcuts help overlay displayed")

    def _close_help_overlay(self):
        """Close the help overlay."""
        if self.help_overlay and self.help_overlay in self.page.overlay:
            self.page.overlay.remove(self.help_overlay)
            self.help_overlay = None
            self.help_dialog_open = False
            self.page.update()
            logger.debug("Help overlay closed")


def create_shortcut_handler(page: ft.Page) -> KeyboardShortcutHandler:
    """Create and initialize a keyboard shortcut handler.

    Args:
        page: The Flet page

    Returns:
        KeyboardShortcutHandler instance
    """
    return KeyboardShortcutHandler(page)
