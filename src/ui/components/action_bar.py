"""Premium Action Bar Component.

Action buttons for prescription workflow with premium styling.
"""

import flet as ft
from typing import Optional, Callable

from ..tokens import Colors, Typography, Spacing, Radius, Motion


class ActionBar:
    """Premium action bar with styled buttons."""

    def __init__(
        self,
        on_templates: Optional[Callable] = None,
        on_generate: Optional[Callable] = None,
        on_save: Optional[Callable] = None,
        on_print: Optional[Callable] = None,
        on_whatsapp: Optional[Callable] = None,
        on_save_template: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        self.on_templates = on_templates
        self.on_generate = on_generate
        self.on_save = on_save
        self.on_print = on_print
        self.on_whatsapp = on_whatsapp
        self.on_save_template = on_save_template
        self.is_dark = is_dark

        # Button references
        self.templates_btn: Optional[ft.ElevatedButton] = None
        self.generate_btn: Optional[ft.ElevatedButton] = None
        self.save_btn: Optional[ft.ElevatedButton] = None
        self.print_btn: Optional[ft.ElevatedButton] = None
        self.whatsapp_btn: Optional[ft.ElevatedButton] = None
        self.save_template_btn: Optional[ft.ElevatedButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None

    def build_top_row(self) -> ft.Row:
        """Build the top action row (Templates, Generate)."""
        self.templates_btn = ft.ElevatedButton(
            text="Templates",
            icon=ft.Icons.DESCRIPTION,
            tooltip="Use clinical template",
            style=self._button_style("primary"),
            on_click=self._handle_templates,
            disabled=True,
        )

        self.generate_btn = ft.ElevatedButton(
            text="Generate Rx",
            icon=ft.Icons.AUTO_AWESOME,
            tooltip="Generate prescription with AI (Ctrl+G)",
            style=self._button_style("success"),
            on_click=self._handle_generate,
            disabled=True,
        )

        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=20,
            height=20,
            stroke_width=2,
            color=Colors.PRIMARY_500,
        )

        return ft.Row([
            self.templates_btn,
            self.generate_btn,
            self.loading_indicator,
        ], spacing=Spacing.SM)

    def build_bottom_row(self) -> ft.Row:
        """Build the bottom action row (Save, Print, Share, Template)."""
        self.save_btn = ft.ElevatedButton(
            text="Save Visit",
            icon=ft.Icons.SAVE,
            tooltip="Save current visit (Ctrl+S)",
            style=self._button_style("default"),
            on_click=self._handle_save,
            disabled=True,
        )

        self.print_btn = ft.ElevatedButton(
            text="Print PDF",
            icon=ft.Icons.PRINT,
            tooltip="Print prescription as PDF (Ctrl+P)",
            style=self._button_style("default"),
            on_click=self._handle_print,
            disabled=True,
        )

        self.whatsapp_btn = ft.ElevatedButton(
            text="Share WhatsApp",
            icon=ft.Icons.CHAT,
            tooltip="Share prescription via WhatsApp",
            style=self._button_style("success"),
            on_click=self._handle_whatsapp,
            disabled=True,
        )

        self.save_template_btn = ft.ElevatedButton(
            text="Save as Template",
            icon=ft.Icons.BOOKMARK_ADD,
            tooltip="Save this prescription as a template",
            style=self._button_style("secondary"),
            on_click=self._handle_save_template,
            disabled=True,
        )

        return ft.Row([
            self.save_btn,
            self.print_btn,
            self.whatsapp_btn,
            self.save_template_btn,
        ], spacing=Spacing.SM, wrap=True)

    def _button_style(self, variant: str) -> ft.ButtonStyle:
        """Get button style by variant."""
        base = {
            "shape": ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            "animation_duration": Motion.FAST,
            "padding": ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
        }

        if variant == "primary":
            return ft.ButtonStyle(
                **base,
                bgcolor=Colors.PRIMARY_600,
                color=Colors.NEUTRAL_0,
            )
        elif variant == "success":
            return ft.ButtonStyle(
                **base,
                bgcolor=Colors.SUCCESS_MAIN,
                color=Colors.NEUTRAL_0,
            )
        elif variant == "secondary":
            return ft.ButtonStyle(
                **base,
                bgcolor=Colors.NEUTRAL_100 if not self.is_dark else Colors.NEUTRAL_700,
                color=Colors.NEUTRAL_800 if not self.is_dark else Colors.NEUTRAL_100,
            )
        else:
            return ft.ButtonStyle(**base)

    # Event handlers
    def _handle_templates(self, e):
        if self.on_templates:
            self.on_templates(e)

    def _handle_generate(self, e):
        if self.on_generate:
            self.on_generate(e)

    def _handle_save(self, e):
        if self.on_save:
            self.on_save(e)

    def _handle_print(self, e):
        if self.on_print:
            self.on_print(e)

    def _handle_whatsapp(self, e):
        if self.on_whatsapp:
            self.on_whatsapp(e)

    def _handle_save_template(self, e):
        if self.on_save_template:
            self.on_save_template(e)

    # State management
    def enable_patient_actions(self):
        """Enable actions when patient is selected."""
        self.templates_btn.disabled = False
        self.generate_btn.disabled = False

    def enable_prescription_actions(self):
        """Enable actions when prescription is ready."""
        self.save_btn.disabled = False
        self.print_btn.disabled = False
        self.whatsapp_btn.disabled = False
        self.save_template_btn.disabled = False

    def disable_all(self):
        """Disable all action buttons."""
        self.templates_btn.disabled = True
        self.generate_btn.disabled = True
        self.save_btn.disabled = True
        self.print_btn.disabled = True
        self.whatsapp_btn.disabled = True
        self.save_template_btn.disabled = True

    def set_loading(self, loading: bool):
        """Set loading state for generate button."""
        self.loading_indicator.visible = loading
        self.generate_btn.disabled = loading
        if self.loading_indicator.page:
            self.loading_indicator.page.update()

    def set_save_mode(self, is_update: bool):
        """Set save button mode."""
        self.save_btn.text = "Update Visit" if is_update else "Save Visit"
        if self.save_btn.page:
            self.save_btn.update()

    def disable_save(self):
        """Disable save button after successful save."""
        self.save_btn.disabled = True
        if self.save_btn.page:
            self.save_btn.update()
