"""Phrase manager dialog for managing quick phrases."""

import flet as ft
from typing import Optional, Callable

from ..services.database import DatabaseService


class PhraseManager:
    """Dialog to view, add, edit, and delete quick phrases."""

    def __init__(self, db: DatabaseService, on_phrases_changed: Optional[Callable] = None):
        """Initialize phrase manager.

        Args:
            db: Database service instance
            on_phrases_changed: Callback when phrases are modified
        """
        self.db = db
        self.on_phrases_changed = on_phrases_changed

        # UI components
        self.dialog: Optional[ft.AlertDialog] = None
        self.search_field: Optional[ft.TextField] = None
        self.phrases_list: Optional[ft.ListView] = None
        self.add_dialog: Optional[ft.AlertDialog] = None
        self.edit_dialog: Optional[ft.AlertDialog] = None

        # State
        self.all_phrases = []
        self.filtered_phrases = []
        self.editing_phrase_id: Optional[int] = None

    def show(self, page: ft.Page):
        """Show the phrase manager dialog."""
        self._load_phrases()
        self._build_dialog()

        page.dialog = self.dialog
        self.dialog.open = True
        page.update()

    def _load_phrases(self):
        """Load phrases from database."""
        try:
            self.all_phrases = self.db.get_all_phrases()
            self.filtered_phrases = self.all_phrases.copy()
        except Exception as e:
            print(f"Error loading phrases: {e}")
            self.all_phrases = []
            self.filtered_phrases = []

    def _filter_phrases(self, search_query: str):
        """Filter phrases based on search query."""
        if not search_query:
            self.filtered_phrases = self.all_phrases.copy()
        else:
            query = search_query.lower()
            self.filtered_phrases = [
                p for p in self.all_phrases
                if query in p['shortcut'].lower() or query in p['expansion'].lower()
            ]
        self._refresh_phrases_list()

    def _refresh_phrases_list(self):
        """Refresh the phrases list view."""
        if not self.phrases_list:
            return

        self.phrases_list.controls.clear()

        if not self.filtered_phrases:
            self.phrases_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No phrases found",
                        color=ft.Colors.GREY_500,
                        italic=True
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for phrase in self.filtered_phrases:
                self.phrases_list.controls.append(
                    self._create_phrase_row(phrase)
                )

        if self.phrases_list.page:
            self.phrases_list.update()

    def _create_phrase_row(self, phrase: dict) -> ft.Control:
        """Create a row for a phrase."""
        # Determine if it's editable (only custom phrases can be edited/deleted)
        is_custom = phrase.get('is_custom', 0) == 1

        # Create shortcut badge
        shortcut_badge = ft.Container(
            content=ft.Text(
                phrase['shortcut'],
                size=12,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_700
            ),
            bgcolor=ft.Colors.BLUE_50,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=5,
        )

        # Create expansion text
        expansion_text = ft.Text(
            phrase['expansion'],
            size=12,
            color=ft.Colors.GREY_800,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=2,
            expand=True
        )

        # Create category badge if present
        category_badge = None
        if phrase.get('category'):
            category_badge = ft.Container(
                content=ft.Text(
                    phrase['category'],
                    size=10,
                    color=ft.Colors.GREY_600
                ),
                bgcolor=ft.Colors.GREY_100,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=3,
            )

        # Create action buttons
        actions = []
        if is_custom:
            actions.extend([
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_size=16,
                    tooltip="Edit phrase",
                    on_click=lambda e, p=phrase: self._show_edit_dialog(p)
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_size=16,
                    tooltip="Delete phrase",
                    icon_color=ft.Colors.RED_400,
                    on_click=lambda e, p=phrase: self._delete_phrase(p)
                )
            ])
        else:
            actions.append(
                ft.Text("Built-in", size=10, color=ft.Colors.GREY_400, italic=True)
            )

        # Usage count
        usage_text = ft.Text(
            f"Used {phrase.get('usage_count', 0)}x",
            size=10,
            color=ft.Colors.GREY_500
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    shortcut_badge,
                    expansion_text,
                    *([category_badge] if category_badge else []),
                    usage_text,
                    *actions
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_dialog(self):
        """Build the main phrase manager dialog."""
        # Search field
        self.search_field = ft.TextField(
            hint_text="Search phrases...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self._filter_phrases(e.control.value),
            border_radius=8,
            dense=True
        )

        # Add phrase button
        add_button = ft.ElevatedButton(
            text="Add Phrase",
            icon=ft.Icons.ADD,
            on_click=lambda e: self._show_add_dialog(),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE
            )
        )

        # Phrases list
        self.phrases_list = ft.ListView(
            spacing=10,
            padding=10,
            expand=True,
        )
        self._refresh_phrases_list()

        # Close button
        close_button = ft.TextButton(
            text="Close",
            on_click=lambda e: self._close_dialog()
        )

        # Hint text
        hint_text = ft.Container(
            content=ft.Text(
                "Type shortcut + Space to expand in any text field",
                size=11,
                color=ft.Colors.GREY_600,
                italic=True
            ),
            padding=10,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=5,
        )

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Text("Quick Phrases", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=self.search_field, expand=True),
                        add_button
                    ], spacing=10),
                    ft.Container(
                        content=self.phrases_list,
                        expand=True,
                        height=400
                    ),
                    hint_text
                ], spacing=15, expand=True),
                width=700,
                padding=10
            ),
            actions=[close_button],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def _show_add_dialog(self):
        """Show dialog to add a new phrase."""
        shortcut_field = ft.TextField(
            label="Shortcut",
            hint_text="e.g., htn",
            border_radius=8
        )

        expansion_field = ft.TextField(
            label="Expansion",
            hint_text="e.g., Hypertension",
            multiline=True,
            min_lines=2,
            max_lines=5,
            border_radius=8
        )

        category_field = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Common Abbreviations"),
                ft.dropdown.Option("Systems"),
                ft.dropdown.Option("Examination Templates"),
                ft.dropdown.Option("Prescriptions"),
                ft.dropdown.Option("Common Phrases"),
                ft.dropdown.Option("Medical Conditions"),
                ft.dropdown.Option("Procedures"),
                ft.dropdown.Option("Anatomy"),
                ft.dropdown.Option("Vitals"),
                ft.dropdown.Option("Investigations"),
                ft.dropdown.Option("Examination Findings"),
                ft.dropdown.Option("Custom"),
            ],
            value="Custom",
            border_radius=8
        )

        def save_phrase(e):
            if not shortcut_field.value or not expansion_field.value:
                self._show_snackbar("Please fill in all required fields", error=True)
                return

            try:
                self.db.add_phrase(
                    shortcut=shortcut_field.value,
                    expansion=expansion_field.value,
                    category=category_field.value
                )
                self._show_snackbar("Phrase added successfully")
                self.add_dialog.open = False
                self._load_phrases()
                self._refresh_phrases_list()

                # Notify parent to reload cache
                if self.on_phrases_changed:
                    self.on_phrases_changed()

                if self.dialog.page:
                    self.dialog.page.update()
            except Exception as e:
                self._show_snackbar(f"Error: {str(e)}", error=True)

        self.add_dialog = ft.AlertDialog(
            title=ft.Text("Add Quick Phrase"),
            content=ft.Container(
                content=ft.Column([
                    shortcut_field,
                    expansion_field,
                    category_field
                ], spacing=15),
                width=400,
                padding=10
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_add_dialog()),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_phrase,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        if self.dialog.page:
            self.dialog.page.dialog = self.add_dialog
            self.add_dialog.open = True
            self.dialog.page.update()

    def _show_edit_dialog(self, phrase: dict):
        """Show dialog to edit an existing phrase."""
        self.editing_phrase_id = phrase['id']

        shortcut_field = ft.TextField(
            label="Shortcut",
            value=phrase['shortcut'],
            border_radius=8
        )

        expansion_field = ft.TextField(
            label="Expansion",
            value=phrase['expansion'],
            multiline=True,
            min_lines=2,
            max_lines=5,
            border_radius=8
        )

        category_field = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Common Abbreviations"),
                ft.dropdown.Option("Systems"),
                ft.dropdown.Option("Examination Templates"),
                ft.dropdown.Option("Prescriptions"),
                ft.dropdown.Option("Common Phrases"),
                ft.dropdown.Option("Medical Conditions"),
                ft.dropdown.Option("Procedures"),
                ft.dropdown.Option("Anatomy"),
                ft.dropdown.Option("Vitals"),
                ft.dropdown.Option("Investigations"),
                ft.dropdown.Option("Examination Findings"),
                ft.dropdown.Option("Custom"),
            ],
            value=phrase.get('category', 'Custom'),
            border_radius=8
        )

        def update_phrase(e):
            if not shortcut_field.value or not expansion_field.value:
                self._show_snackbar("Please fill in all required fields", error=True)
                return

            try:
                self.db.update_phrase(
                    phrase_id=self.editing_phrase_id,
                    shortcut=shortcut_field.value,
                    expansion=expansion_field.value,
                    category=category_field.value
                )
                self._show_snackbar("Phrase updated successfully")
                self.edit_dialog.open = False
                self._load_phrases()
                self._refresh_phrases_list()

                # Notify parent to reload cache
                if self.on_phrases_changed:
                    self.on_phrases_changed()

                if self.dialog.page:
                    self.dialog.page.update()
            except Exception as e:
                self._show_snackbar(f"Error: {str(e)}", error=True)

        self.edit_dialog = ft.AlertDialog(
            title=ft.Text("Edit Quick Phrase"),
            content=ft.Container(
                content=ft.Column([
                    shortcut_field,
                    expansion_field,
                    category_field
                ], spacing=15),
                width=400,
                padding=10
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_edit_dialog()),
                ft.ElevatedButton(
                    "Update",
                    on_click=update_phrase,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        if self.dialog.page:
            self.dialog.page.dialog = self.edit_dialog
            self.edit_dialog.open = True
            self.dialog.page.update()

    def _delete_phrase(self, phrase: dict):
        """Delete a phrase after confirmation."""
        def confirm_delete(e):
            try:
                success = self.db.delete_phrase(phrase['id'])
                if success:
                    self._show_snackbar("Phrase deleted successfully")
                    self._load_phrases()
                    self._refresh_phrases_list()

                    # Notify parent to reload cache
                    if self.on_phrases_changed:
                        self.on_phrases_changed()
                else:
                    self._show_snackbar("Could not delete phrase (built-in phrases cannot be deleted)", error=True)

                confirm_dialog.open = False
                if self.dialog.page:
                    self.dialog.page.update()
            except Exception as e:
                self._show_snackbar(f"Error: {str(e)}", error=True)

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete '{phrase['shortcut']}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm_dialog(confirm_dialog)),
                ft.ElevatedButton(
                    "Delete",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_700,
                        color=ft.Colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        if self.dialog.page:
            self.dialog.page.dialog = confirm_dialog
            confirm_dialog.open = True
            self.dialog.page.update()

    def _close_dialog(self):
        """Close the main dialog."""
        if self.dialog:
            self.dialog.open = False
            if self.dialog.page:
                self.dialog.page.update()

    def _close_add_dialog(self):
        """Close the add dialog."""
        if self.add_dialog:
            self.add_dialog.open = False
            if self.dialog.page:
                self.dialog.page.update()

    def _close_edit_dialog(self):
        """Close the edit dialog."""
        if self.edit_dialog:
            self.edit_dialog.open = False
            if self.dialog.page:
                self.dialog.page.update()

    def _close_confirm_dialog(self, dialog):
        """Close a confirmation dialog."""
        dialog.open = False
        if self.dialog.page:
            self.dialog.page.update()

    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar message."""
        if self.dialog and self.dialog.page:
            self.dialog.page.open(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700
                )
            )
