"""Right panel - AI Agent for RAG queries."""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..models.schemas import Patient
from ..services.context_builder import ContextBuilder
from ..services.app_mode import ModeCapabilities

# Optional imports
try:
    from ..services.llm import LLMService
except ImportError:
    LLMService = None

try:
    from ..services.rag import RAGService
except ImportError:
    RAGService = None


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
        llm=None,
        rag=None,
        context_builder: Optional[ContextBuilder] = None,
        capabilities: Optional[ModeCapabilities] = None,
    ):
        self.on_query = on_query
        self.llm = llm
        self.rag = rag
        self.context_builder = context_builder
        self.capabilities = capabilities

        self.current_patient: Optional[Patient] = None
        self.messages: List[ChatMessage] = []

        # UI components
        self.chat_list: Optional[ft.ListView] = None
        self.query_field: Optional[ft.TextField] = None
        self.send_btn: Optional[ft.IconButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.patient_context: Optional[ft.Text] = None
        self.mode_indicator: Optional[ft.Container] = None

    def build(self) -> ft.Control:
        """Build the agent panel UI."""

        # Determine mode text
        if self.capabilities and self.capabilities.llm_query_answering:
            if self.capabilities.semantic_search:
                mode_text = "Full AI"
                mode_color = ft.Colors.GREEN_700
            else:
                mode_text = "SQL + LLM"
                mode_color = ft.Colors.BLUE_700
        else:
            mode_text = "SQL Only"
            mode_color = ft.Colors.GREY_700

        # Mode indicator
        self.mode_indicator = ft.Container(
            content=ft.Text(mode_text, size=9, color=ft.Colors.WHITE),
            bgcolor=mode_color,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=8,
        )

        # Header with patient context
        self.patient_context = ft.Text(
            "No patient selected",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True,
        )

        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.BLUE_700, size=20),
                    ft.Text("AI Assistant", size=14, weight=ft.FontWeight.BOLD),
                    self.mode_indicator,
                ], spacing=8),
                self.patient_context,
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

        # Welcome message based on mode
        if self.capabilities and self.capabilities.llm_query_answering:
            welcome = (
                "Hello! I can help you query this patient's medical records. "
                "Try asking questions like:\n\n"
                "- What was his last creatinine?\n"
                "- When was his last echo done?\n"
                "- What did nephrology recommend?\n"
                "- Summarize his cardiac history"
            )
        else:
            welcome = (
                "Hello! I can search this patient's records for you. "
                "(AI interpretation is disabled in Lite mode)\n\n"
                "Try asking:\n"
                "- Show lab results\n"
                "- Show consultations\n"
                "- Show recent visits"
            )

        self._add_assistant_message(welcome)

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

        # Quick action buttons - adapt based on mode
        quick_actions_list = [
            ("Labs", "What are the most recent lab results?"),
            ("Meds", "List all current medications"),
        ]

        if self.capabilities and self.capabilities.llm_query_answering:
            quick_actions_list.append(("Summary", "Give me a brief summary of this patient"))
        else:
            quick_actions_list.append(("Visits", "Show recent visits"))

        quick_actions = ft.Container(
            content=ft.Row([
                ft.TextButton(
                    label,
                    style=ft.ButtonStyle(padding=5),
                    on_click=lambda e, q=query: self._quick_query(q),
                )
                for label, query in quick_actions_list
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
        self.current_patient = patient

        # Update context display
        self.patient_context.value = f"Context: {patient.name}"
        self.patient_context.italic = False
        self.patient_context.color = ft.Colors.BLUE_700

        # Clear chat history (keep welcome message)
        self.messages = []
        self.chat_list.controls.clear()

        # Get record count info
        if self.capabilities and self.capabilities.llm_query_answering:
            self._add_assistant_message(
                f"Now viewing records for {patient.name}. "
                f"What would you like to know?"
            )
        else:
            self._add_assistant_message(
                f"Now viewing records for {patient.name}. "
                f"I can search records for you (AI interpretation not available in this mode)."
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
            self._add_assistant_message("Please select a patient first.")
            return

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
                self._add_assistant_message(response)
            else:
                self._add_assistant_message(f"Sorry, I encountered an error: {response}")

            if self.loading_indicator.page:
                self.loading_indicator.page.update()

        self.on_query(query, callback)
