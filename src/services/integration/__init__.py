"""
Integration Layer for DocAssist EMR.

This module provides the orchestration layer that connects all services
into a seamless clinical workflow.
"""

from .clinical_flow import ClinicalFlow
from .service_registry import ServiceRegistry
from .event_bus import EventBus, Event
from .workflow_engine import WorkflowEngine, WorkflowState, WorkflowTransition
from .context_manager import ConsultationContext, ContextManager

__all__ = [
    "ClinicalFlow",
    "ServiceRegistry",
    "EventBus",
    "Event",
    "WorkflowEngine",
    "WorkflowState",
    "WorkflowTransition",
    "ConsultationContext",
    "ContextManager",
]
