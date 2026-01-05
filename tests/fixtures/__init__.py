"""Test fixtures for DocAssist EMR.

This module provides comprehensive test data for various clinical scenarios,
including patients, visits, prescriptions, lab results, and more.
"""

# Patient fixtures
from .patients import (
    PATIENTS,
    generate_patients,
    generate_indian_name,
    generate_phone_number,
    generate_address,
    get_patient_by_condition,
)

# Visit fixtures
from .visits import (
    VISITS,
    generate_visit_history,
    create_routine_visit,
    create_emergency_visit,
)

# Prescription fixtures
from .sample_prescriptions_extended import (
    get_prescription_by_scenario,
    get_prescriptions_with_interactions,
    get_emergency_prescriptions,
    get_all_sample_prescriptions,
)

# Lab result fixtures
from .lab_results import (
    LAB_RESULTS,
    generate_lab_history,
    create_lab_result,
    get_critical_lab_results,
)

# Transcript fixtures
from .sample_transcripts import (
    get_transcript_by_language,
    get_all_transcripts,
)

# Drug interaction fixtures
from .interactions import (
    INTERACTION_SCENARIOS,
    get_interaction_by_severity,
    get_all_interactions,
    get_critical_interactions,
    get_pregnancy_contraindications,
    get_renal_contraindications,
)

# Red flag fixtures
from .red_flags import (
    RED_FLAG_SCENARIOS,
    get_red_flags_by_urgency,
    get_all_red_flag_scenarios,
    get_cardiac_emergencies,
    get_neurological_emergencies,
    get_respiratory_emergencies,
)

# Factory functions
from .factories import (
    create_patient,
    create_visit,
    create_prescription,
    create_investigation,
    create_clinic_data,
    create_emergency_case,
    create_diabetic_patient_with_history,
)

# Complete clinic scenarios
from .scenarios import (
    SCENARIOS,
    generate_clinic_day,
    get_scenario_by_type,
    generate_weekly_schedule,
)

__all__ = [
    # Patient
    "PATIENTS",
    "generate_patients",
    "generate_indian_name",
    "generate_phone_number",
    "generate_address",
    "get_patient_by_condition",
    # Visits
    "VISITS",
    "generate_visit_history",
    "create_routine_visit",
    "create_emergency_visit",
    # Prescriptions
    "get_prescription_by_scenario",
    "get_prescriptions_with_interactions",
    "get_emergency_prescriptions",
    "get_all_sample_prescriptions",
    # Lab results
    "LAB_RESULTS",
    "generate_lab_history",
    "create_lab_result",
    "get_critical_lab_results",
    # Transcripts
    "get_transcript_by_language",
    "get_all_transcripts",
    # Interactions
    "INTERACTION_SCENARIOS",
    "get_interaction_by_severity",
    "get_all_interactions",
    "get_critical_interactions",
    "get_pregnancy_contraindications",
    "get_renal_contraindications",
    # Red flags
    "RED_FLAG_SCENARIOS",
    "get_red_flags_by_urgency",
    "get_all_red_flag_scenarios",
    "get_cardiac_emergencies",
    "get_neurological_emergencies",
    "get_respiratory_emergencies",
    # Factories
    "create_patient",
    "create_visit",
    "create_prescription",
    "create_investigation",
    "create_clinic_data",
    "create_emergency_case",
    "create_diabetic_patient_with_history",
    # Scenarios
    "SCENARIOS",
    "generate_clinic_day",
    "get_scenario_by_type",
    "generate_weekly_schedule",
]
