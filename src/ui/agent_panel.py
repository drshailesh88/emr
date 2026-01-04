"""Right panel - AI Agent for RAG queries."""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from ..models.schemas import Patient
from ..services.llm import LLMService
from ..services.rag import RAGService

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AgentPanel:
    """AI Assistant panel for RAG queries."""

    def __init__(
        self,
        on_query: Callable[[str, Callable], None],
        llm: LLMService,
        rag: RAGService
    ):
        self.on_query = on_query
        self.llm = llm
        self.rag = rag

        self.current_patient: Optional[Patient] = None
        self.messages: List[ChatMessage] = []

        # UI components
        self.chat_list: Optional[ft.ListView] = None
        self.query_field: Optional[ft.TextField] = None
        self.send_btn: Optional[ft.IconButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.patient_context: Optional[ft.Text] = None
        self.doc_count: Optional[ft.Text] = None

    def build(self) -> ft.Control:
        """Build the agent panel UI."""

        # Header with patient context
        self.patient_context = ft.Text(
            "No patient selected",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True,
        )

        self.doc_count = ft.Text(
            "",
            size=11,
            color=ft.Colors.GREY_500,
        )

        # Clear chat button
        clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_SWEEP,
            icon_size=18,
            tooltip="Clear chat (Ctrl+L)",
            on_click=lambda e: self.clear_chat(),
        )

        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.BLUE_700, size=20),
                    ft.Text("AI Assistant", size=14, weight=ft.FontWeight.BOLD),
                    clear_btn,
                ], spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.patient_context,
                self.doc_count,
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.BLUE_100,
        )

        # Chat history
        self.chat_list = ft.ListView(
            spacing=10,
            padding=10,
            expand=True,
            auto_scroll=True,
        )

        # Welcome message
        self._add_assistant_message(
            "Hello! I can help you query this patient's medical records. "
            "Try asking questions like:\n\n"
            "• What was his last creatinine?\n"
            "• When was his last echo done?\n"
            "• What medications is he on?\n"
            "• Summarize his cardiac history"
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(visible=False, width=16, height=16)

        # Query input
        self.query_field = ft.TextField(
            hint_text="Ask about this patient...",
            border_radius=20,
            text_size=13,
            min_lines=1,
            max_lines=3,
            expand=True,
            on_submit=self._on_send_click,
        )

        self.send_btn = ft.IconButton(
            icon=ft.Icons.SEND,
            icon_color=ft.Colors.BLUE_700,
            tooltip="Send message (Enter)",
            on_click=self._on_send_click,
        )

        input_row = ft.Container(
            content=ft.Row([
                self.query_field,
                self.loading_indicator,
                self.send_btn,
            ], spacing=5),
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

        # Quick action buttons
        quick_actions = ft.Container(
            content=ft.Row([
                ft.TextButton(
                    "Last labs",
                    style=ft.ButtonStyle(padding=5),
                    on_click=lambda e: self._quick_query("What are the most recent lab results?"),
                ),
                ft.TextButton(
                    "Medications",
                    style=ft.ButtonStyle(padding=5),
                    on_click=lambda e: self._quick_query("List all current medications"),
                ),
                ft.TextButton(
                    "Summary",
                    style=ft.ButtonStyle(padding=5),
                    on_click=lambda e: self._quick_query("Give me a brief summary of this patient"),
                ),
            ], spacing=5, wrap=True),
            padding=ft.padding.symmetric(horizontal=10),
        )

        return ft.Column([
            header,
            self.chat_list,
            quick_actions,
            input_row,
        ], spacing=0, expand=True)

    def set_patient(self, patient: Patient):
        """Set the current patient context."""
        logger.debug(f"Setting patient context in agent panel: {patient.name} (ID: {patient.id})")
        self.current_patient = patient

        # Update context display
        self.patient_context.value = f"Context: {patient.name}"
        self.patient_context.italic = False
        self.patient_context.color = ft.Colors.BLUE_700

        # Get document count
        try:
            doc_count = self.rag.get_patient_document_count(patient.id)
            self.doc_count.value = f"{doc_count} records indexed"
            logger.info(f"Patient {patient.id} has {doc_count} records indexed for RAG")
        except Exception as e:
            logger.error(f"Error getting document count for patient {patient.id}: {e}", exc_info=True)
            doc_count = 0
            self.doc_count.value = "Error loading records"

        # Clear chat history (keep welcome message)
        self.messages = []
        self.chat_list.controls.clear()
        self._add_assistant_message(
            f"Now viewing records for {patient.name}. "
            f"I have access to {doc_count} records. What would you like to know?"
        )

        if self.patient_context.page:
            self.patient_context.page.update()

    def _add_user_message(self, content: str):
        """Add a user message to the chat."""
        msg = ChatMessage(role="user", content=content)
        self.messages.append(msg)
        self._render_message(msg)

    def _add_assistant_message(self, content: str):
        """Add an assistant message to the chat."""
        msg = ChatMessage(role="assistant", content=content)
        self.messages.append(msg)
        self._render_message(msg)

    def _render_message(self, msg: ChatMessage):
        """Render a message in the chat list."""
        is_user = msg.role == "user"

        bubble = ft.Container(
            content=ft.Text(
                msg.content,
                size=13,
                color=ft.Colors.WHITE if is_user else ft.Colors.BLACK,
                selectable=True,
            ),
            bgcolor=ft.Colors.BLUE_700 if is_user else ft.Colors.WHITE,
            padding=ft.padding.all(12),
            border_radius=ft.border_radius.only(
                top_left=15,
                top_right=15,
                bottom_left=5 if is_user else 15,
                bottom_right=15 if is_user else 5,
            ),
            border=None if is_user else ft.border.all(1, ft.Colors.GREY_300),
        )

        row = ft.Row(
            [bubble],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
        )

        self.chat_list.controls.append(row)
        if self.chat_list.page:
            self.chat_list.update()

    def _quick_query(self, query: str):
        """Handle quick action button click."""
        logger.debug(f"Quick query selected: {query}")
        self.query_field.value = query
        if self.query_field.page:
            self.query_field.page.update()
        self._send_query(query)

    def _on_send_click(self, e):
        """Handle send button click."""
        query = self.query_field.value.strip()
        if not query:
            return
        self._send_query(query)

    def _send_query(self, query: str):
        """Send a query to the RAG system."""
        if not self.current_patient:
            logger.warning("Query attempted without patient context")
            self._add_assistant_message("Please select a patient first.")
            return

        logger.info(f"Sending RAG query from agent panel: {query}")
        # Add user message
        self._add_user_message(query)

        # Clear input
        self.query_field.value = ""

        # Show loading
        self.loading_indicator.visible = True
        self.send_btn.disabled = True
        if self.loading_indicator.page:
            self.loading_indicator.page.update()

        def callback(success: bool, response: str):
            self.loading_indicator.visible = False
            self.send_btn.disabled = False

            if success:
                logger.debug("RAG query successful, displaying response")
                self._add_assistant_message(response)
            else:
                logger.warning(f"RAG query failed: {response[:100]}")
                self._add_assistant_message(f"Sorry, I encountered an error: {response}")

            if self.loading_indicator.page:
                self.loading_indicator.page.update()

        self.on_query(query, callback)

    def clear_chat(self):
        """Clear the chat history."""
        # Keep only the welcome message for the current patient
        if self.current_patient:
            self.messages = []
            self.chat_list.controls.clear()

            # Get document count
            doc_count = self.rag.get_patient_document_count(self.current_patient.id)

            # Re-add welcome message
            self._add_assistant_message(
                f"Chat cleared. Still viewing records for {self.current_patient.name}. "
                f"I have access to {doc_count} records. What would you like to know?"
            )
        else:
            # No patient selected, just show default message
            self.messages = []
            self.chat_list.controls.clear()
            self._add_assistant_message(
                "Hello! I can help you query this patient's medical records. "
                "Try asking questions like:\n\n"
                "• What was his last creatinine?\n"
                "• When was his last echo done?\n"
                "• What medications is he on?\n"
                "• Summarize his cardiac history"
            )

        if self.chat_list.page:
            self.chat_list.page.update()
