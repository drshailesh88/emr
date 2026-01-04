"""
Demonstration script for Diagnosis Engine

Shows how to use DifferentialEngine, RedFlagDetector, and ProtocolEngine
"""

from src.services.diagnosis import (
    DifferentialEngine,
    RedFlagDetector,
    ProtocolEngine,
    UrgencyLevel,
)


def demo_differential_engine():
    """Demo: Calculate differential diagnosis for dengue-like presentation."""
    print("=" * 80)
    print("DEMO 1: Differential Diagnosis Engine")
    print("=" * 80)

    engine = DifferentialEngine()

    # Case: Young patient with fever, body ache, headache
    symptoms = ["fever_with_body_ache", "fever_with_headache", "fever_with_rash"]
    patient = {
        "age": 28,
        "gender": "M",
        "season": "monsoon",
        "location": "urban",
    }

    print("\nPatient: 28M, presenting during monsoon")
    print(f"Symptoms: {', '.join(symptoms)}")
    print("\nCalculating differential diagnoses...\n")

    differentials = engine.calculate_differentials(symptoms, patient)

    print(f"Top {len(differentials)} differential diagnoses:\n")
    for i, diff in enumerate(differentials, 1):
        print(f"{i}. {diff.diagnosis.replace('_', ' ').title()}")
        print(f"   Probability: {diff.probability:.1%}")
        print(f"   Supporting: {', '.join(diff.supporting_features)}")
        print(f"   Suggested tests: {', '.join(diff.suggested_tests)}")
        print()

    # Show distinguishing features between top 2 diagnoses
    if len(differentials) >= 2:
        print("\nDistinguishing features between top 2 diagnoses:")
        features = engine.get_distinguishing_features(
            differentials[0].diagnosis,
            differentials[1].diagnosis,
        )
        for feature, meaning1, meaning2 in features:
            print(f"  {feature}:")
            print(f"    - {differentials[0].diagnosis}: {meaning1}")
            print(f"    - {differentials[1].diagnosis}: {meaning2}")


def demo_red_flag_detector():
    """Demo: Detect red flags in emergency presentations."""
    print("\n" + "=" * 80)
    print("DEMO 2: Red Flag Detector")
    print("=" * 80)

    detector = RedFlagDetector()

    # Case 1: Chest pain with cardiac features
    print("\nCase 1: 55-year-old man with chest pain")
    presentation1 = {
        "chest_pain": True,
        "sweating": True,
        "radiation_to_arm": True,
        "age": 55,
    }

    red_flags1 = detector.check(presentation1)

    if red_flags1:
        print(f"\n🚨 {len(red_flags1)} RED FLAG(S) DETECTED:\n")
        for flag in red_flags1:
            print(f"Category: {flag.category}")
            print(f"Finding: {flag.description}")
            print(f"Urgency: {flag.urgency.value}")
            print(f"\nImmediate Action:")
            print(detector.get_immediate_action(flag))
            print(f"\nTriage Level: {detector.get_triage_level(red_flags1)}")
    else:
        print("No red flags detected")

    # Case 2: Fever with meningitis signs
    print("\n" + "-" * 80)
    print("\nCase 2: Patient with fever and neck stiffness")
    presentation2 = {
        "fever": True,
        "neck_stiffness": True,
        "severe_headache": True,
        "photophobia": True,
    }

    red_flags2 = detector.check(presentation2)

    if red_flags2:
        print(f"\n🚨 {len(red_flags2)} RED FLAG(S) DETECTED:\n")
        for flag in red_flags2:
            print(f"Category: {flag.category}")
            print(f"Finding: {flag.description}")
            print(f"Urgency: {flag.urgency.value}")
            print(f"\nImmediate Action:")
            print(detector.get_immediate_action(flag))
            print(f"\nTriage Level: {detector.get_triage_level(red_flags2)}")
    else:
        print("No red flags detected")


def demo_protocol_engine():
    """Demo: Get evidence-based treatment protocols."""
    print("\n" + "=" * 80)
    print("DEMO 3: Protocol Engine")
    print("=" * 80)

    engine = ProtocolEngine()

    # Get protocol for Type 2 Diabetes
    print("\nCase: Newly diagnosed Type 2 Diabetes\n")

    protocol = engine.get_protocol("type_2_diabetes")

    if protocol:
        print(f"Diagnosis: {protocol.diagnosis}")
        print(f"ICD-10: {protocol.icd10_code}\n")

        print("First-line medications:")
        for med in protocol.first_line_drugs:
            print(f"  • {med.drug_name} {med.strength} - {med.dose} {med.frequency}")
            print(f"    {med.instructions} ({med.indication})")

        print(f"\nInvestigations:")
        for test in protocol.investigations[:5]:
            print(f"  • {test}")

        print(f"\nLifestyle advice:")
        for advice in protocol.lifestyle_advice[:3]:
            print(f"  • {advice}")

        print(f"\nFollow-up: {protocol.follow_up_interval}")

    # Check compliance for a prescription
    print("\n" + "-" * 80)
    print("\nChecking prescription compliance...")

    # Good prescription
    prescription_good = {
        "medications": [
            {"drug_name": "Metformin 500mg", "dose": "1", "frequency": "BD"},
        ],
        "investigations": ["FBS", "HbA1c"],
    }

    compliance = engine.check_compliance(prescription_good, "type_2_diabetes")

    print(f"\nCompliance Score: {compliance.score:.1f}/100")
    print(f"Status: {'✓ COMPLIANT' if compliance.is_compliant else '✗ NON-COMPLIANT'}")

    if compliance.issues:
        print("\nIssues found:")
        for issue in compliance.issues:
            print(f"  [{issue.severity.upper()}] {issue.description}")
            print(f"  → {issue.recommendation}")

    if compliance.suggestions:
        print("\nSuggestions:")
        for suggestion in compliance.suggestions:
            print(f"  • {suggestion}")

    # Bad prescription (antibiotic for viral URTI)
    print("\n" + "-" * 80)
    print("\nChecking inappropriate prescription...")

    prescription_bad = {
        "medications": [
            {"drug_name": "Azithromycin 500mg", "dose": "1", "frequency": "OD"},
            {"drug_name": "Paracetamol 500mg", "dose": "1", "frequency": "TDS"},
        ],
        "investigations": [],
    }

    compliance_bad = engine.check_compliance(
        prescription_bad, "upper_respiratory_tract_infection"
    )

    print(f"\nCompliance Score: {compliance_bad.score:.1f}/100")
    print(
        f"Status: {'✓ COMPLIANT' if compliance_bad.is_compliant else '✗ NON-COMPLIANT'}"
    )

    if compliance_bad.issues:
        print("\nIssues found:")
        for issue in compliance_bad.issues:
            print(f"  [{issue.severity.upper()}] {issue.description}")
            print(f"  → {issue.recommendation}")


def demo_dengue_protocol():
    """Demo: Dengue-specific protocol and red flags."""
    print("\n" + "=" * 80)
    print("DEMO 4: Dengue Management (India-specific)")
    print("=" * 80)

    detector = RedFlagDetector()
    protocol_engine = ProtocolEngine()

    print("\nCase: 32-year-old with fever for 5 days, suspected dengue")
    print("Day 5 (critical phase)\n")

    # Check for dengue warning signs
    presentation = {
        "fever": True,
        "dengue_suspected": True,
        "abdominal_pain": True,
        "persistent_vomiting": True,
    }

    red_flags = detector.check(presentation)

    if red_flags:
        print(f"⚠️  {len(red_flags)} WARNING SIGN(S) DETECTED:\n")
        for flag in red_flags:
            print(f"Finding: {flag.description}")
            print(f"Action: {flag.recommended_action}")
            print(f"Critical timing: {flag.time_critical}\n")

    # Get dengue protocol
    protocol = protocol_engine.get_protocol("dengue")

    if protocol:
        print("Dengue Management Protocol:\n")

        print("Medications:")
        for med in protocol.first_line_drugs:
            print(f"  • {med.drug_name} - {med.indication}")

        print(f"\nCritical monitoring (daily):")
        for mon in protocol.monitoring[:4]:
            print(f"  • {mon}")

        print(f"\nReferral criteria (immediate admission if any):")
        for criteria in protocol.referral_criteria:
            print(f"  • {criteria}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DocAssist EMR - Diagnosis Engine Demo" + " " * 21 + "║")
    print("╚" + "=" * 78 + "╝")

    demo_differential_engine()
    demo_red_flag_detector()
    demo_protocol_engine()
    demo_dengue_protocol()

    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80 + "\n")
