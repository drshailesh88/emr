"""Template browser dialog for selecting clinical templates."""

import flet as ft
from typing import Callable, Optional
from ..services.database import DatabaseService
from ..models.schemas import Prescription


class TemplateBrowser:
    """Template browser dialog component."""

    def __init__(self, db: DatabaseService, on_apply: Callable[[dict], None]):
        """Initialize template browser.

        Args:
            db: Database service instance
            on_apply: Callback function when template is applied, receives prescription dict
        """
        self.db = db
        self.on_apply = on_apply
        self.dialog: Optional[ft.AlertDialog] = None
        self.search_field: Optional[ft.TextField] = None
        self.template_list: Optional[ft.ListView] = None
        self.preview_container: Optional[ft.Container] = None

        self.all_templates = []
        self.filtered_templates = []
        self.selected_template = None

    def show(self, page: ft.Page):
        """Show the template browser dialog."""
        # Load templates
        self.all_templates = self.db.get_all_templates()
        self.filtered_templates = self.all_templates.copy()

        # Build dialog content
        self.search_field = ft.TextField(
            hint_text="Search templates...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search,
            border_radius=8,
        )

        self.template_list = ft.ListView(
            spacing=5,
            padding=10,
            expand=True,
        )

        self.preview_container = ft.Container(
            content=ft.Text(
                "Select a template to preview",
                color=ft.Colors.GREY_500,
                italic=True,
            ),
            padding=15,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            expand=True,
        )

        # Build template list
        self._refresh_template_list()

        # Create dialog
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, size=28, color=ft.Colors.BLUE_700),
                ft.Text("Clinical Templates", size=20, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Row([
                    # Left panel - Template list
                    ft.Container(
                        content=ft.Column([
                            self.search_field,
                            ft.Container(
                                content=self.template_list,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=8,
                                expand=True,
                            ),
                        ], spacing=10, expand=True),
                        width=400,
                        expand=True,
                    ),
                    ft.VerticalDivider(width=1),
                    # Right panel - Preview
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Preview", size=16, weight=ft.FontWeight.BOLD),
                            ft.Divider(height=5),
                            self.preview_container,
                        ], spacing=10, expand=True),
                        width=400,
                        expand=True,
                    ),
                ], spacing=15, expand=True),
                width=850,
                height=600,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.ElevatedButton(
                    "Apply Template",
                    icon=ft.Icons.CHECK,
                    on_click=self._on_apply_click,
                    disabled=True,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.open(self.dialog)
        page.update()

    def _refresh_template_list(self):
        """Refresh the template list display."""
        self.template_list.controls.clear()

        if not self.filtered_templates:
            self.template_list.controls.append(
                ft.Text("No templates found", color=ft.Colors.GREY_500, italic=True)
            )
            return

        # Group by category
        templates_by_category = {}
        favorites = []

        for template in self.filtered_templates:
            if template.get('is_favorite'):
                favorites.append(template)

            category = template.get('category', 'Other')
            if category not in templates_by_category:
                templates_by_category[category] = []
            templates_by_category[category].append(template)

        # Show favorites first
        if favorites:
            self.template_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.STAR, color=ft.Colors.AMBER_700, size=18),
                        ft.Text("FAVORITES", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_700),
                    ], spacing=5),
                    padding=ft.padding.only(left=5, top=10, bottom=5),
                )
            )
            for template in favorites:
                self.template_list.controls.append(self._create_template_item(template))

            self.template_list.controls.append(ft.Divider(height=10))

        # Show templates by category
        for category in sorted(templates_by_category.keys()):
            # Category header
            self.template_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        category.upper(),
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                    ),
                    padding=ft.padding.only(left=5, top=10, bottom=5),
                )
            )

            # Templates in category
            for template in templates_by_category[category]:
                self.template_list.controls.append(self._create_template_item(template))

        # Custom templates section
        custom_templates = [t for t in self.filtered_templates if t.get('is_custom')]
        if custom_templates:
            self.template_list.controls.append(ft.Divider(height=10))
            self.template_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.FOLDER_SPECIAL, color=ft.Colors.PURPLE_700, size=18),
                        ft.Text("MY TEMPLATES", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ], spacing=5),
                    padding=ft.padding.only(left=5, top=10, bottom=5),
                )
            )
            for template in custom_templates:
                self.template_list.controls.append(self._create_template_item(template))

        if self.template_list.page:
            self.template_list.update()

    def _create_template_item(self, template: dict) -> ft.Control:
        """Create a template list item."""
        is_favorite = template.get('is_favorite', 0)
        is_custom = template.get('is_custom', 0)
        usage_count = template.get('usage_count', 0)

        # Build template info
        badges = []
        if is_custom:
            badges.append(ft.Container(
                content=ft.Text("Custom", size=9, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.PURPLE_700,
                padding=ft.padding.symmetric(horizontal=5, vertical=2),
                border_radius=3,
            ))
        if usage_count > 0:
            badges.append(ft.Container(
                content=ft.Text(f"Used {usage_count}x", size=9, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREY_600,
                padding=ft.padding.symmetric(horizontal=5, vertical=2),
                border_radius=3,
            ))

        # Favorite button
        favorite_btn = ft.IconButton(
            icon=ft.Icons.STAR if is_favorite else ft.Icons.STAR_BORDER,
            icon_color=ft.Colors.AMBER_700 if is_favorite else ft.Colors.GREY_400,
            icon_size=18,
            tooltip="Toggle favorite",
            on_click=lambda e, t=template: self._toggle_favorite(t),
        )

        item = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(template['name'], size=13, weight=ft.FontWeight.W_500),
                        ft.Row(badges, spacing=5) if badges else ft.Container(height=0),
                    ], spacing=3),
                    expand=True,
                ),
                favorite_btn,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            border_radius=5,
            border=ft.border.all(1, ft.Colors.GREY_300),
            bgcolor=ft.Colors.WHITE,
            on_click=lambda e, t=template: self._on_template_select(t),
        )

        return item

    def _on_template_select(self, template: dict):
        """Handle template selection."""
        self.selected_template = template

        # Update preview
        self._show_preview(template)

        # Enable apply button
        if self.dialog:
            self.dialog.actions[1].disabled = False
            if self.dialog.page:
                self.dialog.update()

    def _show_preview(self, template: dict):
        """Show template preview."""
        prescription = template.get('prescription', {})

        preview_controls = []

        # Template name and info
        preview_controls.append(
            ft.Text(template['name'], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
        )
        preview_controls.append(
            ft.Text(f"Category: {template.get('category', 'N/A')}", size=12, color=ft.Colors.GREY_600)
        )
        preview_controls.append(ft.Divider(height=10))

        # Diagnosis
        if prescription.get('diagnosis'):
            preview_controls.append(
                ft.Text("DIAGNOSIS:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
            )
            for dx in prescription['diagnosis']:
                preview_controls.append(ft.Text(f"  • {dx}", size=11))
            preview_controls.append(ft.Divider(height=5))

        # Medications
        if prescription.get('medications'):
            preview_controls.append(
                ft.Text("MEDICATIONS:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
            )
            for i, med in enumerate(prescription['medications'], 1):
                med_text = f"{i}. {med.get('drug_name', '')} {med.get('strength', '')}"
                dosage = f"   {med.get('dose', '')} {med.get('frequency', '')}"
                if med.get('duration'):
                    dosage += f" x {med['duration']}"
                if med.get('instructions'):
                    dosage += f" ({med['instructions']})"

                preview_controls.append(ft.Text(med_text, size=11, weight=ft.FontWeight.W_500))
                preview_controls.append(ft.Text(dosage, size=10, color=ft.Colors.GREY_700))
            preview_controls.append(ft.Divider(height=5))

        # Investigations
        if prescription.get('investigations'):
            preview_controls.append(
                ft.Text("INVESTIGATIONS:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)
            )
            for inv in prescription['investigations']:
                preview_controls.append(ft.Text(f"  • {inv}", size=11))
            preview_controls.append(ft.Divider(height=5))

        # Advice
        if prescription.get('advice'):
            preview_controls.append(
                ft.Text("ADVICE:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700)
            )
            for adv in prescription['advice']:
                preview_controls.append(ft.Text(f"  • {adv}", size=11))
            preview_controls.append(ft.Divider(height=5))

        # Follow-up
        if prescription.get('follow_up'):
            preview_controls.append(
                ft.Text(f"FOLLOW-UP: {prescription['follow_up']}", size=11, weight=ft.FontWeight.W_500)
            )

        # Red flags
        if prescription.get('red_flags'):
            preview_controls.append(ft.Divider(height=5))
            preview_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("RED FLAGS:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                        *[ft.Text(f"  ⚠ {flag}", size=10, color=ft.Colors.RED_600) for flag in prescription['red_flags']]
                    ], spacing=2),
                    bgcolor=ft.Colors.RED_50,
                    padding=8,
                    border_radius=5,
                )
            )

        self.preview_container.content = ft.Column(
            preview_controls,
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        )

        if self.preview_container.page:
            self.preview_container.update()

    def _on_search(self, e):
        """Handle search input."""
        query = self.search_field.value.lower().strip()

        if not query:
            self.filtered_templates = self.all_templates.copy()
        else:
            self.filtered_templates = [
                t for t in self.all_templates
                if query in t['name'].lower() or
                   query in t.get('category', '').lower() or
                   query in str(t.get('prescription', {}).get('diagnosis', [])).lower()
            ]

        self._refresh_template_list()

    def _toggle_favorite(self, template: dict):
        """Toggle template favorite status."""
        self.db.toggle_template_favorite(template['id'])

        # Reload templates
        self.all_templates = self.db.get_all_templates()

        # Reapply search filter
        if self.search_field.value:
            self._on_search(None)
        else:
            self.filtered_templates = self.all_templates.copy()

        self._refresh_template_list()

    def _on_apply_click(self, e):
        """Handle apply button click."""
        if self.selected_template:
            # Increment usage count
            self.db.increment_template_usage(self.selected_template['id'])

            # Call the callback with prescription data
            prescription_data = self.selected_template.get('prescription', {})
            self.on_apply(prescription_data)

            # Close dialog
            self._on_cancel(e)

    def _on_cancel(self, e):
        """Handle cancel button click."""
        if self.dialog and self.dialog.page:
            self.dialog.open = False
            self.dialog.page.update()


class SaveTemplateDialog:
    """Dialog for saving current prescription as a template."""

    def __init__(self, db: DatabaseService, prescription_dict: dict, on_save: Callable = None):
        """Initialize save template dialog.

        Args:
            db: Database service instance
            prescription_dict: Current prescription data to save
            on_save: Optional callback after successful save
        """
        self.db = db
        self.prescription_dict = prescription_dict
        self.on_save = on_save
        self.dialog: Optional[ft.AlertDialog] = None
        self.name_field: Optional[ft.TextField] = None
        self.category_field: Optional[ft.Dropdown] = None

    def show(self, page: ft.Page):
        """Show the save template dialog."""
        self.name_field = ft.TextField(
            label="Template Name",
            hint_text="e.g., My Custom Diabetes Protocol",
            border_radius=8,
            autofocus=True,
        )

        # Common categories
        categories = [
            "Metabolic",
            "Cardiac",
            "Respiratory",
            "GI",
            "Renal",
            "Neuro",
            "Musculoskeletal",
            "Hematology",
            "Psychiatry",
            "Dermatology",
            "Infectious",
            "Other",
        ]

        self.category_field = ft.Dropdown(
            label="Category",
            hint_text="Select category",
            options=[ft.dropdown.Option(cat) for cat in categories],
            border_radius=8,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SAVE, size=24, color=ft.Colors.BLUE_700),
                ft.Text("Save as Template", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Save this prescription as a reusable template for future use.",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=10),
                    self.name_field,
                    self.category_field,
                ], spacing=15, tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.ElevatedButton(
                    "Save Template",
                    icon=ft.Icons.CHECK,
                    on_click=self._on_save_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.open(self.dialog)
        page.update()

    def _on_save_click(self, e):
        """Handle save button click."""
        name = self.name_field.value.strip()
        category = self.category_field.value

        if not name:
            self.name_field.error_text = "Please enter a template name"
            self.name_field.update()
            return

        if not category:
            self.category_field.error_text = "Please select a category"
            self.category_field.update()
            return

        # Save template
        try:
            template_id = self.db.add_custom_template(name, category, self.prescription_dict)

            # Show success message
            if self.dialog and self.dialog.page:
                self.dialog.page.open(
                    ft.SnackBar(
                        content=ft.Text(f"Template '{name}' saved successfully!"),
                        bgcolor=ft.Colors.GREEN_700,
                    )
                )

            # Call callback
            if self.on_save:
                self.on_save(template_id)

            # Close dialog
            self._on_cancel(e)
        except Exception as ex:
            # Show error
            if self.dialog and self.dialog.page:
                self.dialog.page.open(
                    ft.SnackBar(
                        content=ft.Text(f"Error saving template: {str(ex)}"),
                        bgcolor=ft.Colors.RED_700,
                    )
                )

    def _on_cancel(self, e):
        """Handle cancel button click."""
        if self.dialog and self.dialog.page:
            self.dialog.open = False
            self.dialog.page.update()
