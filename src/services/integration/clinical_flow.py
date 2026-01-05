"""
Clinical Flow Orchestrator - Main integration layer for DocAssist EMR.

Coordinates all services into a seamless clinical consultation workflow,
managing the entire lifecycle from patient selection to prescription delivery.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from .context_manager import ConsultationContext, ContextManager
from .event_bus import EventBus, EventType
from .service_registry import ServiceRegistry
from .workflow_engine import WorkflowEngine, WorkflowState


logger = logging.getLogger(__name__)


class ClinicalFlow:
    """
    Orchestrates the entire clinical consultation workflow.

    Integrates all services and manages the consultation lifecycle:
    1. Patient selection and timeline loading
    2. Ambient listening and note-taking
    3. Clinical decision support (alerts, drug checks)
    4. Prescription generation and delivery
    5. Follow-up scheduling and analytics
    """

    def __init__(
        self,
        services: Optional[Dict[str, Any]] = None,
        context_manager: Optional[ContextManager] = None,
        event_bus: Optional[EventBus] = None,
        service_registry: Optional[ServiceRegistry] = None
    ):
        """
        Initialize clinical flow orchestrator.

        Args:
            services: Optional dict of service instances
            context_manager: Optional ContextManager instance
            event_bus: Optional EventBus instance
            service_registry: Optional ServiceRegistry instance
        """
        # Core infrastructure
        self.context_manager = context_manager or ContextManager()
        self.event_bus = event_bus or EventBus()
        self.service_registry = service_registry or ServiceRegistry()
        self.workflow = WorkflowEngine()

        # Register services if provided
        if services:
            for name, service in services.items():
                self.service_registry.register(name, service)

        # Set up workflow callbacks
        self._setup_workflow_callbacks()

        # Set up event subscriptions
        self._setup_event_subscriptions()

        logger.info("ClinicalFlow orchestrator initialized")

    def _setup_workflow_callbacks(self) -> None:
        """Set up workflow state callbacks."""

        # On entering consultation active state
        self.workflow.on_state_entry(
            WorkflowState.CONSULTATION_ACTIVE,
            self._on_consultation_active
        )

        # On entering completed state
        self.workflow.on_state_entry(
            WorkflowState.COMPLETED,
            self._on_consultation_completed
        )

        # On entering error state
        self.workflow.on_state_entry(
            WorkflowState.ERROR,
            self._on_error
        )

    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions."""

        # Subscribe to red flag events
        self.event_bus.subscribe(
            EventType.RED_FLAG_DETECTED,
            self._handle_red_flag,
            priority=100  # High priority
        )

        # Subscribe to drug interaction events
        self.event_bus.subscribe(
            EventType.DRUG_INTERACTION_DETECTED,
            self._handle_drug_interaction,
            priority=100
        )

        # Subscribe to care gap events
        self.event_bus.subscribe(
            EventType.CARE_GAP_DETECTED,
            self._handle_care_gap,
            priority=50
        )

    async def _on_consultation_active(self, state: WorkflowState) -> None:
        """
        Callback for entering consultation active state.

        Args:
            state: Current workflow state
        """
        logger.info("Consultation became active")

        await self.event_bus.publish(
            EventType.CONSULTATION_STARTED,
            {"timestamp": datetime.now().isoformat()},
            source="clinical_flow"
        )

    async def _on_consultation_completed(self, state: WorkflowState) -> None:
        """
        Callback for entering completed state.

        Args:
            state: Current workflow state
        """
        logger.info("Consultation completed")

        context = self.context_manager.get_current_context()
        if context:
            await self.event_bus.publish(
                EventType.CONSULTATION_COMPLETED,
                {
                    "consultation_id": context.consultation_id,
                    "patient_id": context.patient_id,
                    "duration": (datetime.now() - context.started_at).total_seconds()
                },
                source="clinical_flow"
            )

    async def _on_error(self, state: WorkflowState) -> None:
        """
        Callback for entering error state.

        Args:
            state: Current workflow state
        """
        logger.error("Workflow entered error state")

        context = self.context_manager.get_current_context()
        if context:
            await self.event_bus.publish(
                EventType.ERROR_OCCURRED,
                {
                    "consultation_id": context.consultation_id,
                    "workflow_state": state.value
                },
                source="clinical_flow"
            )

    async def _handle_red_flag(self, event) -> None:
        """
        Handle red flag detection event.

        Args:
            event: Red flag event
        """
        logger.warning(f"Red flag detected: {event.data}")

        context = self.context_manager.get_current_context()
        if context:
            context.add_alert(
                alert_type="red_flag",
                severity="high",
                message=event.data.get("message", "Red flag detected"),
                metadata=event.data
            )

    async def _handle_drug_interaction(self, event) -> None:
        """
        Handle drug interaction event.

        Args:
            event: Drug interaction event
        """
        logger.warning(f"Drug interaction detected: {event.data}")

        context = self.context_manager.get_current_context()
        if context:
            context.add_alert(
                alert_type="drug_interaction",
                severity=event.data.get("severity", "medium"),
                message=event.data.get("message", "Drug interaction detected"),
                metadata=event.data
            )

    async def _handle_care_gap(self, event) -> None:
        """
        Handle care gap event.

        Args:
            event: Care gap event
        """
        logger.info(f"Care gap detected: {event.data}")

        context = self.context_manager.get_current_context()
        if context:
            context.add_alert(
                alert_type="care_gap",
                severity="low",
                message=event.data.get("message", "Care gap identified"),
                metadata=event.data
            )

    async def start_consultation(
        self,
        patient_id: int,
        doctor_id: str
    ) -> ConsultationContext:
        """
        Start a new consultation session.

        Workflow:
        1. Load patient timeline (patient_summarizer)
        2. Check for alerts (care_gap_detector, pending_reminders)
        3. Initialize consultation context
        4. Start ambient listening (voice_capture)
        5. Log consultation start (audit_logger)

        Args:
            patient_id: Patient ID
            doctor_id: Doctor ID

        Returns:
            ConsultationContext for this session

        Raises:
            Exception: If consultation cannot be started
        """
        try:
            # Generate consultation ID
            consultation_id = f"CONSULT-{uuid.uuid4().hex[:12]}"

            logger.info(
                f"Starting consultation {consultation_id} "
                f"for patient {patient_id} with doctor {doctor_id}"
            )

            # Transition workflow state
            await self.workflow.trigger("start_consultation")

            # Create consultation context
            context = self.context_manager.create_context(
                consultation_id=consultation_id,
                patient_id=patient_id,
                doctor_id=doctor_id
            )

            # === INTEGRATION POINT: Patient Summarizer ===
            # Load patient timeline and summary
            if self.service_registry.has("patient_summarizer"):
                try:
                    summarizer = self.service_registry.get("patient_summarizer")
                    timeline = await summarizer.get_patient_timeline(patient_id)
                    context.patient_timeline = timeline
                    logger.info(f"Loaded patient timeline: {len(timeline)} events")
                except Exception as e:
                    logger.error(f"Failed to load patient timeline: {e}")

            # === INTEGRATION POINT: Care Gap Detector ===
            # Check for care gaps
            if self.service_registry.has("care_gap_detector"):
                try:
                    detector = self.service_registry.get("care_gap_detector")
                    care_gaps = await detector.check_patient_gaps(patient_id)
                    context.care_gaps = care_gaps

                    # Publish care gap events
                    for gap in care_gaps:
                        await self.event_bus.publish(
                            EventType.CARE_GAP_DETECTED,
                            gap,
                            source="clinical_flow",
                            correlation_id=consultation_id
                        )

                    logger.info(f"Found {len(care_gaps)} care gaps")
                except Exception as e:
                    logger.error(f"Failed to check care gaps: {e}")

            # === INTEGRATION POINT: Reminder Service ===
            # Check for pending reminders
            if self.service_registry.has("reminder_service"):
                try:
                    reminder_service = self.service_registry.get("reminder_service")
                    pending = await reminder_service.get_pending_reminders(patient_id)
                    context.pending_reminders = pending
                    logger.info(f"Found {len(pending)} pending reminders")
                except Exception as e:
                    logger.error(f"Failed to load reminders: {e}")

            # === INTEGRATION POINT: Voice Capture ===
            # Start ambient listening
            if self.service_registry.has("voice_capture"):
                try:
                    voice_capture = self.service_registry.get("voice_capture")
                    await voice_capture.start_listening(consultation_id)
                    logger.info("Started ambient listening")
                except Exception as e:
                    logger.error(f"Failed to start voice capture: {e}")

            # === INTEGRATION POINT: Audit Logger ===
            # Log consultation start
            if self.service_registry.has("audit_logger"):
                try:
                    audit_logger = self.service_registry.get("audit_logger")
                    await audit_logger.log_event(
                        event_type="consultation_started",
                        user_id=doctor_id,
                        patient_id=patient_id,
                        metadata={
                            "consultation_id": consultation_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log audit event: {e}")

            # Update workflow state
            context.workflow_state = self.workflow.get_current_state().value

            logger.info(f"Consultation started successfully: {consultation_id}")

            return context

        except Exception as e:
            logger.error(f"Failed to start consultation: {e}", exc_info=True)
            await self.workflow.trigger("error")
            raise

    async def process_speech(self, audio: bytes) -> Dict[str, Any]:
        """
        Process speech audio from ambient listening.

        Workflow:
        1. Transcribe audio (speech_to_text)
        2. Extract clinical entities (clinical_nlp)
        3. Check for red flags (red_flag_detector)
        4. Update live note display
        5. Update consultation context

        Args:
            audio: Audio bytes to process

        Returns:
            Dict with transcription and extracted entities

        Raises:
            ValueError: If no active consultation
        """
        context = self.context_manager.get_current_context()
        if not context:
            raise ValueError("No active consultation")

        try:
            result = {
                "transcription": "",
                "entities": {},
                "red_flags": [],
                "timestamp": datetime.now().isoformat()
            }

            # === INTEGRATION POINT: Speech to Text ===
            if self.service_registry.has("speech_to_text"):
                try:
                    stt_service = self.service_registry.get("speech_to_text")
                    transcription = await stt_service.transcribe(audio)
                    result["transcription"] = transcription
                    context.add_transcription(transcription)

                    await self.event_bus.publish(
                        EventType.SPEECH_TRANSCRIBED,
                        {"text": transcription},
                        source="clinical_flow",
                        correlation_id=context.consultation_id
                    )

                    logger.info(f"Transcribed: {transcription[:50]}...")
                except Exception as e:
                    logger.error(f"Failed to transcribe audio: {e}")

            # === INTEGRATION POINT: Clinical NLP ===
            if result["transcription"] and self.service_registry.has("clinical_nlp"):
                try:
                    nlp_service = self.service_registry.get("clinical_nlp")
                    entities = await nlp_service.extract_entities(result["transcription"])
                    result["entities"] = entities

                    # Update context with extracted entities
                    if "symptoms" in entities:
                        context.symptoms.extend(entities["symptoms"])
                    if "medications" in entities:
                        context.medications_mentioned.extend(entities["medications"])
                    if "investigations" in entities:
                        context.investigations_mentioned.extend(entities["investigations"])

                    logger.info(f"Extracted entities: {entities}")
                except Exception as e:
                    logger.error(f"Failed to extract entities: {e}")

            # === INTEGRATION POINT: Red Flag Detector ===
            if result["transcription"] and self.service_registry.has("red_flag_detector"):
                try:
                    detector = self.service_registry.get("red_flag_detector")
                    red_flags = await detector.check_text(
                        result["transcription"],
                        context.patient_data
                    )
                    result["red_flags"] = red_flags

                    # Publish red flag events
                    for flag in red_flags:
                        await self.event_bus.publish(
                            EventType.RED_FLAG_DETECTED,
                            flag,
                            source="clinical_flow",
                            correlation_id=context.consultation_id
                        )
                        context.red_flags.append(flag.get("message", "Unknown red flag"))

                    if red_flags:
                        logger.warning(f"Red flags detected: {len(red_flags)}")
                except Exception as e:
                    logger.error(f"Failed to check red flags: {e}")

            # Update clinical notes
            if result["transcription"]:
                if context.clinical_notes:
                    context.clinical_notes += " " + result["transcription"]
                else:
                    context.clinical_notes = result["transcription"]

                await self.event_bus.publish(
                    EventType.CLINICAL_NOTE_UPDATED,
                    {"notes": context.clinical_notes},
                    source="clinical_flow",
                    correlation_id=context.consultation_id
                )

            return result

        except Exception as e:
            logger.error(f"Failed to process speech: {e}", exc_info=True)
            raise

    async def generate_prescription(
        self,
        medications: List[Dict[str, Any]],
        patient_id: int
    ) -> Dict[str, Any]:
        """
        Generate prescription with clinical decision support.

        Workflow:
        1. Check drug interactions (interaction_checker)
        2. Calculate appropriate doses (dose_calculator)
        3. Generate alerts if needed
        4. Create prescription record
        5. Log with all warnings shown (audit_logger)

        Args:
            medications: List of medication dicts
            patient_id: Patient ID

        Returns:
            Prescription dict with any warnings

        Raises:
            ValueError: If no active consultation
        """
        context = self.context_manager.get_current_context()
        if not context:
            raise ValueError("No active consultation")

        try:
            # Transition to prescribing state
            await self.workflow.trigger("start_prescribing")

            prescription = {
                "medications": medications,
                "interactions": [],
                "dose_warnings": [],
                "alerts": [],
                "timestamp": datetime.now().isoformat()
            }

            # === INTEGRATION POINT: Interaction Checker ===
            if self.service_registry.has("interaction_checker"):
                try:
                    checker = self.service_registry.get("interaction_checker")
                    interactions = await checker.check_interactions(
                        medications,
                        patient_id
                    )
                    prescription["interactions"] = interactions

                    # Publish interaction events
                    for interaction in interactions:
                        await self.event_bus.publish(
                            EventType.DRUG_INTERACTION_DETECTED,
                            interaction,
                            source="clinical_flow",
                            correlation_id=context.consultation_id
                        )

                        context.drug_interactions.append(interaction)

                    if interactions:
                        logger.warning(f"Drug interactions found: {len(interactions)}")
                except Exception as e:
                    logger.error(f"Failed to check interactions: {e}")

            # === INTEGRATION POINT: Dose Calculator ===
            if self.service_registry.has("dose_calculator"):
                try:
                    calculator = self.service_registry.get("dose_calculator")

                    # Calculate doses for each medication
                    for i, med in enumerate(medications):
                        dose_check = await calculator.check_dose(
                            medication=med,
                            patient_data=context.patient_data
                        )

                        if dose_check.get("warnings"):
                            prescription["dose_warnings"].append({
                                "medication": med.get("drug_name"),
                                "warnings": dose_check["warnings"]
                            })

                        # Update medication with recommended dose if needed
                        if dose_check.get("recommended_dose"):
                            medications[i]["recommended_dose"] = dose_check["recommended_dose"]

                    if prescription["dose_warnings"]:
                        logger.warning(f"Dose warnings: {len(prescription['dose_warnings'])}")
                except Exception as e:
                    logger.error(f"Failed to calculate doses: {e}")

            # Create prescription record
            context.current_prescription = prescription
            context.medications = medications

            # === INTEGRATION POINT: Audit Logger ===
            if self.service_registry.has("audit_logger"):
                try:
                    audit_logger = self.service_registry.get("audit_logger")
                    await audit_logger.log_event(
                        event_type="prescription_created",
                        user_id=context.doctor_id,
                        patient_id=patient_id,
                        metadata={
                            "consultation_id": context.consultation_id,
                            "medication_count": len(medications),
                            "interactions": len(prescription["interactions"]),
                            "warnings": len(prescription["dose_warnings"])
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log prescription: {e}")

            # Publish prescription created event
            await self.event_bus.publish(
                EventType.PRESCRIPTION_CREATED,
                prescription,
                source="clinical_flow",
                correlation_id=context.consultation_id
            )

            logger.info(f"Prescription generated with {len(medications)} medications")

            return prescription

        except Exception as e:
            logger.error(f"Failed to generate prescription: {e}", exc_info=True)
            await self.workflow.trigger("error")
            raise

    async def complete_consultation(
        self,
        visit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete and finalize the consultation.

        Workflow:
        1. Finalize clinical documentation
        2. Create audit record (audit_logger)
        3. Schedule follow-up reminders (reminder_service)
        4. Queue prescription for WhatsApp (whatsapp_client)
        5. Update analytics (practice_analytics)
        6. Check if review request appropriate (retention_tracker)

        Args:
            visit_data: Visit data to save

        Returns:
            Completion summary

        Raises:
            ValueError: If no active consultation
        """
        context = self.context_manager.get_current_context()
        if not context:
            raise ValueError("No active consultation")

        try:
            # Transition to reviewing state
            await self.workflow.trigger("start_review")

            summary = {
                "consultation_id": context.consultation_id,
                "patient_id": context.patient_id,
                "visit_id": None,
                "reminders_scheduled": [],
                "prescription_sent": False,
                "analytics_updated": False,
                "timestamp": datetime.now().isoformat()
            }

            # === INTEGRATION POINT: Database Service ===
            # Save visit data
            if self.service_registry.has("database"):
                try:
                    db = self.service_registry.get("database")

                    # Merge context data into visit_data
                    visit_data.update({
                        "patient_id": context.patient_id,
                        "chief_complaint": context.chief_complaint,
                        "clinical_notes": context.clinical_notes,
                        "diagnosis": context.diagnosis,
                        "prescription_json": context.current_prescription
                    })

                    visit_id = await db.create_visit(visit_data)
                    context.visit_id = visit_id
                    summary["visit_id"] = visit_id

                    logger.info(f"Saved visit: {visit_id}")
                except Exception as e:
                    logger.error(f"Failed to save visit: {e}")
                    raise

            # Transition to saving state
            await self.workflow.trigger("save")

            # === INTEGRATION POINT: Audit Logger ===
            if self.service_registry.has("audit_logger"):
                try:
                    audit_logger = self.service_registry.get("audit_logger")
                    await audit_logger.log_event(
                        event_type="consultation_completed",
                        user_id=context.doctor_id,
                        patient_id=context.patient_id,
                        metadata={
                            "consultation_id": context.consultation_id,
                            "visit_id": context.visit_id,
                            "duration": (datetime.now() - context.started_at).total_seconds(),
                            "alerts_shown": len(context.active_alerts),
                            "red_flags": len(context.red_flags)
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log completion: {e}")

            # === INTEGRATION POINT: Reminder Service ===
            if context.follow_up and self.service_registry.has("reminder_service"):
                try:
                    reminder_service = self.service_registry.get("reminder_service")
                    reminder = await reminder_service.schedule_reminder(
                        patient_id=context.patient_id,
                        reminder_type="follow_up",
                        scheduled_date=context.follow_up,
                        message=f"Follow-up appointment for {context.chief_complaint}"
                    )
                    summary["reminders_scheduled"].append(reminder)

                    await self.event_bus.publish(
                        EventType.REMINDER_CREATED,
                        reminder,
                        source="clinical_flow",
                        correlation_id=context.consultation_id
                    )

                    logger.info(f"Scheduled follow-up reminder: {context.follow_up}")
                except Exception as e:
                    logger.error(f"Failed to schedule reminder: {e}")

            # === INTEGRATION POINT: WhatsApp Client ===
            if self.service_registry.has("whatsapp_client"):
                try:
                    whatsapp = self.service_registry.get("whatsapp_client")

                    # Send prescription if phone number available
                    if context.patient_data.get("phone"):
                        await whatsapp.send_prescription(
                            phone=context.patient_data["phone"],
                            prescription=context.current_prescription,
                            patient_name=context.patient_data.get("name")
                        )
                        summary["prescription_sent"] = True

                        await self.event_bus.publish(
                            EventType.PRESCRIPTION_SENT,
                            {"phone": context.patient_data["phone"]},
                            source="clinical_flow",
                            correlation_id=context.consultation_id
                        )

                        logger.info("Prescription sent via WhatsApp")
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp: {e}")

            # === INTEGRATION POINT: Practice Analytics ===
            if self.service_registry.has("practice_analytics"):
                try:
                    analytics = self.service_registry.get("practice_analytics")
                    await analytics.record_consultation(
                        consultation_id=context.consultation_id,
                        patient_id=context.patient_id,
                        doctor_id=context.doctor_id,
                        duration=(datetime.now() - context.started_at).total_seconds(),
                        medications_count=len(context.medications),
                        alerts_count=len(context.active_alerts)
                    )
                    summary["analytics_updated"] = True

                    await self.event_bus.publish(
                        EventType.METRIC_RECORDED,
                        {"type": "consultation_completed"},
                        source="clinical_flow",
                        correlation_id=context.consultation_id
                    )

                    logger.info("Analytics updated")
                except Exception as e:
                    logger.error(f"Failed to update analytics: {e}")

            # === INTEGRATION POINT: Retention Tracker ===
            if self.service_registry.has("retention_tracker"):
                try:
                    tracker = self.service_registry.get("retention_tracker")
                    should_request = await tracker.should_request_review(
                        doctor_id=context.doctor_id,
                        patient_id=context.patient_id
                    )

                    if should_request:
                        # Trigger review request flow
                        summary["review_request"] = True
                        logger.info("Review request triggered")
                except Exception as e:
                    logger.error(f"Failed to check review request: {e}")

            # Transition to completed state
            await self.workflow.trigger("complete")

            # Save and close context
            self.context_manager.save_context()
            self.context_manager.close_context()

            logger.info(f"Consultation completed: {context.consultation_id}")

            return summary

        except Exception as e:
            logger.error(f"Failed to complete consultation: {e}", exc_info=True)
            await self.workflow.trigger("error")
            raise

    async def cancel_consultation(self, reason: Optional[str] = None) -> None:
        """
        Cancel the current consultation.

        Args:
            reason: Optional cancellation reason
        """
        context = self.context_manager.get_current_context()
        if not context:
            return

        try:
            await self.workflow.trigger("cancel")

            # Log cancellation
            if self.service_registry.has("audit_logger"):
                try:
                    audit_logger = self.service_registry.get("audit_logger")
                    await audit_logger.log_event(
                        event_type="consultation_cancelled",
                        user_id=context.doctor_id,
                        patient_id=context.patient_id,
                        metadata={
                            "consultation_id": context.consultation_id,
                            "reason": reason,
                            "duration": (datetime.now() - context.started_at).total_seconds()
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log cancellation: {e}")

            # Publish cancellation event
            await self.event_bus.publish(
                EventType.CONSULTATION_CANCELLED,
                {"reason": reason},
                source="clinical_flow",
                correlation_id=context.consultation_id
            )

            # Close context
            self.context_manager.close_context()

            logger.info(f"Consultation cancelled: {context.consultation_id}")

        except Exception as e:
            logger.error(f"Failed to cancel consultation: {e}", exc_info=True)

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current workflow and context state.

        Returns:
            Dict with current state information
        """
        context = self.context_manager.get_current_context()

        return {
            "workflow_state": self.workflow.get_current_state().value,
            "has_active_consultation": context is not None,
            "consultation_id": context.consultation_id if context else None,
            "patient_id": context.patient_id if context else None,
            "active_alerts": len(context.active_alerts) if context else 0,
            "available_triggers": list(self.workflow.get_available_triggers())
        }

    def get_service_health(self) -> Dict[str, bool]:
        """
        Get health status of all registered services.

        Returns:
            Dict mapping service names to health status
        """
        return self.service_registry.check_health()
