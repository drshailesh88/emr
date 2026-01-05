"""
Workflow Engine for managing clinical consultation state machines.

Implements state transitions, validation, timeout handling, and
recovery mechanisms for clinical workflows.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from threading import Lock


logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    """Clinical consultation workflow states."""

    IDLE = "idle"
    CONSULTATION_ACTIVE = "consultation_active"
    LISTENING = "listening"
    PRESCRIBING = "prescribing"
    REVIEWING = "reviewing"
    SAVING = "saving"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class WorkflowTransition:
    """
    Represents a state transition in the workflow.

    Attributes:
        from_state: Source state
        to_state: Target state
        trigger: Trigger name
        condition: Optional validation function
        action: Optional action to execute during transition
    """

    from_state: WorkflowState
    to_state: WorkflowState
    trigger: str
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    action: Optional[Callable[[Dict[str, Any]], Any]] = None

    def can_transition(self, context: Dict[str, Any]) -> bool:
        """
        Check if transition is allowed.

        Args:
            context: Current context data

        Returns:
            True if transition is allowed
        """
        if self.condition is None:
            return True

        try:
            return self.condition(context)
        except Exception as e:
            logger.error(f"Error in transition condition: {e}")
            return False

    async def execute(self, context: Dict[str, Any]) -> None:
        """
        Execute transition action.

        Args:
            context: Current context data
        """
        if self.action is None:
            return

        try:
            if asyncio.iscoroutinefunction(self.action):
                await self.action(context)
            else:
                self.action(context)
        except Exception as e:
            logger.error(f"Error in transition action: {e}", exc_info=True)


class WorkflowEngine:
    """
    State machine engine for clinical workflows.

    Manages state transitions, validation, timeouts, and recovery.
    """

    def __init__(
        self,
        initial_state: WorkflowState = WorkflowState.IDLE,
        auto_save_interval: int = 300,  # 5 minutes
        idle_timeout: int = 1800  # 30 minutes
    ):
        """
        Initialize workflow engine.

        Args:
            initial_state: Starting state
            auto_save_interval: Seconds between auto-saves
            idle_timeout: Seconds before auto-save on idle
        """
        self._current_state = initial_state
        self._previous_state = initial_state
        self._state_history: List[Dict[str, Any]] = []
        self._transitions: Dict[WorkflowState, List[WorkflowTransition]] = {}
        self._state_entry_callbacks: Dict[WorkflowState, List[Callable]] = {}
        self._state_exit_callbacks: Dict[WorkflowState, List[Callable]] = {}
        self._lock = Lock()

        # Timeout management
        self._auto_save_interval = auto_save_interval
        self._idle_timeout = idle_timeout
        self._last_activity = datetime.now()
        self._auto_save_task: Optional[asyncio.Task] = None

        # Context
        self._context: Dict[str, Any] = {}

        # Define standard transitions
        self._define_standard_transitions()

        logger.info(f"WorkflowEngine initialized in state: {initial_state}")

    def _define_standard_transitions(self) -> None:
        """Define standard clinical workflow transitions."""

        # Start consultation
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.IDLE,
            to_state=WorkflowState.CONSULTATION_ACTIVE,
            trigger="start_consultation"
        ))

        # Begin listening
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.CONSULTATION_ACTIVE,
            to_state=WorkflowState.LISTENING,
            trigger="start_listening"
        ))

        # Stop listening, return to active
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.LISTENING,
            to_state=WorkflowState.CONSULTATION_ACTIVE,
            trigger="stop_listening"
        ))

        # Begin prescribing
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.CONSULTATION_ACTIVE,
            to_state=WorkflowState.PRESCRIBING,
            trigger="start_prescribing"
        ))

        # Continue prescribing from listening
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.LISTENING,
            to_state=WorkflowState.PRESCRIBING,
            trigger="start_prescribing"
        ))

        # Back to active from prescribing
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.PRESCRIBING,
            to_state=WorkflowState.CONSULTATION_ACTIVE,
            trigger="continue_consultation"
        ))

        # Review before completion
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.CONSULTATION_ACTIVE,
            to_state=WorkflowState.REVIEWING,
            trigger="start_review"
        ))

        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.PRESCRIBING,
            to_state=WorkflowState.REVIEWING,
            trigger="start_review"
        ))

        # Save from review
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.REVIEWING,
            to_state=WorkflowState.SAVING,
            trigger="save"
        ))

        # Complete after saving
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.SAVING,
            to_state=WorkflowState.COMPLETED,
            trigger="complete"
        ))

        # Cancel from any active state
        for state in [
            WorkflowState.CONSULTATION_ACTIVE,
            WorkflowState.LISTENING,
            WorkflowState.PRESCRIBING,
            WorkflowState.REVIEWING
        ]:
            self.add_transition(WorkflowTransition(
                from_state=state,
                to_state=WorkflowState.CANCELLED,
                trigger="cancel"
            ))

        # Error handling from any state
        for state in WorkflowState:
            if state != WorkflowState.ERROR:
                self.add_transition(WorkflowTransition(
                    from_state=state,
                    to_state=WorkflowState.ERROR,
                    trigger="error"
                ))

        # Recovery from error
        self.add_transition(WorkflowTransition(
            from_state=WorkflowState.ERROR,
            to_state=WorkflowState.CONSULTATION_ACTIVE,
            trigger="recover"
        ))

        # Reset from completed/cancelled to idle
        for state in [WorkflowState.COMPLETED, WorkflowState.CANCELLED]:
            self.add_transition(WorkflowTransition(
                from_state=state,
                to_state=WorkflowState.IDLE,
                trigger="reset"
            ))

    def add_transition(self, transition: WorkflowTransition) -> None:
        """
        Add a state transition.

        Args:
            transition: Transition to add
        """
        with self._lock:
            if transition.from_state not in self._transitions:
                self._transitions[transition.from_state] = []

            self._transitions[transition.from_state].append(transition)

            logger.debug(
                f"Added transition: {transition.from_state} -> {transition.to_state} "
                f"on '{transition.trigger}'"
            )

    def on_state_entry(
        self,
        state: WorkflowState,
        callback: Callable[[WorkflowState], Any]
    ) -> None:
        """
        Register callback for state entry.

        Args:
            state: State to monitor
            callback: Function to call on entry
        """
        if state not in self._state_entry_callbacks:
            self._state_entry_callbacks[state] = []

        self._state_entry_callbacks[state].append(callback)

    def on_state_exit(
        self,
        state: WorkflowState,
        callback: Callable[[WorkflowState], Any]
    ) -> None:
        """
        Register callback for state exit.

        Args:
            state: State to monitor
            callback: Function to call on exit
        """
        if state not in self._state_exit_callbacks:
            self._state_exit_callbacks[state] = []

        self._state_exit_callbacks[state].append(callback)

    async def trigger(
        self,
        trigger_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Trigger a state transition.

        Args:
            trigger_name: Name of trigger
            context: Optional context data

        Returns:
            True if transition successful
        """
        if context:
            self._context.update(context)

        with self._lock:
            current_state = self._current_state

            # Find matching transitions
            transitions = self._transitions.get(current_state, [])
            matching = [t for t in transitions if t.trigger == trigger_name]

            if not matching:
                logger.warning(
                    f"No transition found for trigger '{trigger_name}' "
                    f"in state {current_state}"
                )
                return False

            # Use first matching transition that passes condition
            transition = None
            for t in matching:
                if t.can_transition(self._context):
                    transition = t
                    break

            if transition is None:
                logger.warning(
                    f"No valid transition found for trigger '{trigger_name}' "
                    f"in state {current_state}"
                )
                return False

            # Execute exit callbacks
            await self._execute_callbacks(
                self._state_exit_callbacks.get(current_state, []),
                current_state
            )

            # Execute transition action
            await transition.execute(self._context)

            # Update state
            self._previous_state = current_state
            self._current_state = transition.to_state

            # Record in history
            self._state_history.append({
                "from_state": current_state.value,
                "to_state": transition.to_state.value,
                "trigger": trigger_name,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(
                f"Transition: {current_state} -> {transition.to_state} "
                f"(trigger: {trigger_name})"
            )

        # Execute entry callbacks (outside lock)
        await self._execute_callbacks(
            self._state_entry_callbacks.get(transition.to_state, []),
            transition.to_state
        )

        # Update activity timestamp
        self._last_activity = datetime.now()

        return True

    def trigger_sync(
        self,
        trigger_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Synchronous wrapper for trigger().

        Use this when calling from non-async contexts.
        For async contexts, use await trigger() directly.

        Args:
            trigger_name: Name of trigger
            context: Optional context data

        Returns:
            True if transition successful
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.trigger(trigger_name, context)
                    )
                    return future.result(timeout=5.0)
            else:
                # No running loop, we can use asyncio.run
                return asyncio.run(self.trigger(trigger_name, context))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.trigger(trigger_name, context))

    async def _execute_callbacks(
        self,
        callbacks: List[Callable],
        state: WorkflowState
    ) -> None:
        """
        Execute state callbacks.

        Args:
            callbacks: List of callbacks
            state: Current state
        """
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}", exc_info=True)

    def get_current_state(self) -> WorkflowState:
        """
        Get current state.

        Returns:
            Current WorkflowState
        """
        return self._current_state

    def get_previous_state(self) -> WorkflowState:
        """
        Get previous state.

        Returns:
            Previous WorkflowState
        """
        return self._previous_state

    def get_available_triggers(self) -> Set[str]:
        """
        Get available triggers from current state.

        Returns:
            Set of trigger names
        """
        transitions = self._transitions.get(self._current_state, [])
        return {t.trigger for t in transitions}

    def can_trigger(self, trigger_name: str) -> bool:
        """
        Check if a trigger is available.

        Args:
            trigger_name: Trigger name

        Returns:
            True if trigger is available
        """
        return trigger_name in self.get_available_triggers()

    def get_state_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get state transition history.

        Args:
            limit: Maximum number of entries

        Returns:
            List of state transitions
        """
        return self._state_history[-limit:]

    def is_idle(self) -> bool:
        """
        Check if workflow has been idle too long.

        Returns:
            True if idle timeout exceeded
        """
        idle_duration = (datetime.now() - self._last_activity).total_seconds()
        return idle_duration > self._idle_timeout

    def should_auto_save(self) -> bool:
        """
        Check if auto-save is needed.

        Returns:
            True if auto-save interval exceeded
        """
        time_since_activity = (datetime.now() - self._last_activity).total_seconds()
        return time_since_activity > self._auto_save_interval

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = datetime.now()

    def reset(self) -> None:
        """Reset workflow to initial state."""
        with self._lock:
            self._current_state = WorkflowState.IDLE
            self._previous_state = WorkflowState.IDLE
            self._state_history.clear()
            self._context.clear()
            self._last_activity = datetime.now()

            logger.info("WorkflowEngine reset")

    def get_context(self) -> Dict[str, Any]:
        """
        Get current workflow context.

        Returns:
            Context dictionary
        """
        return self._context.copy()

    def update_context(self, key: str, value: Any) -> None:
        """
        Update workflow context.

        Args:
            key: Context key
            value: Context value
        """
        self._context[key] = value
        self.update_activity()
