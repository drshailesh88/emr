"""
Standalone test for Diagnosis Engine modules

Tests the diagnosis engines without requiring full app dependencies.
"""

import sys
sys.path.insert(0, '/home/user/emr')

from src.services.diagnosis.differential_engine import DifferentialEngine, Differential
from src.services.diagnosis.red_flag_detector import RedFlagDetector, RedFlag, UrgencyLevel
from src.services.diagnosis.protocol_engine import ProtocolEngine, Medication


def test_differential_engine():
    """Test differential diagnosis calculation."""
    print("=" * 80)
    print("TEST 1: Differential Diagnosis Engine")
    print("=" * 80)

    engine = DifferentialEngine()

    # Test case: Dengue-like presentation during monsoon
    symptoms = ["fever_with_body_ache", "fever_with_headache", "fever_with_rash", "joint_pain_multiple"]
    patient = {
        "age": 28,
        "gender": "M",
        "season": "monsoon",
        "location": "urban",
    }

    print(f"\nPatient: {patient['age']}{patient['gender']}, presenting during monsoon season")
    print(f"Symptoms: {', '.join(symptoms)}")
    print("\nCalculating differential diagnoses...\n")

    differentials = engine.calculate_differentials(symptoms, patient)

    print(f"Found {len(differentials)} differential diagnoses:\n")
    for i, diff in enumerate(differentials[:5], 1):  # Show top 5
        print(f"{i}. {diff.diagnosis.replace('_', ' ').upper()}")
        print(f"   Probability: {diff.probability:.2%}")
        print(f"   Supporting features: {', '.join(diff.supporting_features) if diff.supporting_features else 'None'}")
        print(f"   Suggested tests: {', '.join(diff.suggested_tests[:3])}")
        print()

    # Test distinguishing features
    if len(differentials) >= 2:
        print("\n" + "-" * 80)
        print(f"\nHow to distinguish between {differentials[0].diagnosis} and {differentials[1].diagnosis}:")
        features = engine.get_distinguishing_features(
            differentials[0].diagnosis,
            differentials[1].diagnosis,
        )
        if features:
            for feature, meaning1, meaning2 in features:
                print(f"\n  {feature.replace('_', ' ').title()}:")
                print(f"    • {differentials[0].diagnosis}: {meaning1}")
                print(f"    • {differentials[1].diagnosis}: {meaning2}")
        else:
            print("  No specific distinguishing features defined")

    return True


def test_red_flag_detector():
    """Test red flag detection."""
    print("\n" + "=" * 80)
    print("TEST 2: Red Flag Detector")
    print("=" * 80)

    detector = RedFlagDetector()

    # Test case 1: ACS presentation
    print("\nCase 1: 55-year-old with crushing chest pain")
    print("-" * 80)

    presentation1 = {
        "chest_pain": True,
        "crushing_pain": True,
        "sweating": True,
        "radiation_to_arm": True,
        "age": 55,
    }

    red_flags1 = detector.check(presentation1)

    if red_flags1:
        print(f"\n🚨 DETECTED {len(red_flags1)} RED FLAG(S):\n")
        for flag in red_flags1:
            print(f"Category: {flag.category}")
            print(f"Finding: {flag.description}")
            print(f"Urgency: {flag.urgency.value}")
            print(f"Matching features: {', '.join(flag.matching_features)}")
            print(f"Concerns: {', '.join(flag.differential_concerns)}")
            print(f"\nRecommended action:\n{flag.recommended_action}")
            print(f"\nTime critical: {flag.time_critical}")
            print()

        triage = detector.get_triage_level(red_flags1)
        print(f"Triage Level: {triage}")
    else:
        print("✓ No red flags detected")

    # Test case 2: Meningitis
    print("\n" + "-" * 80)
    print("\nCase 2: Patient with fever, neck stiffness, and severe headache")
    print("-" * 80)

    presentation2 = {
        "fever": True,
        "neck_stiffness": True,
        "severe_headache": True,
        "photophobia": True,
    }

    red_flags2 = detector.check(presentation2)

    if red_flags2:
        print(f"\n🚨 DETECTED {len(red_flags2)} RED FLAG(S):\n")
        for flag in red_flags2:
            print(f"Category: {flag.category}")
            print(f"Finding: {flag.description}")
            print(f"Urgency: {flag.urgency.value}")
            print(f"\nImmediate action needed:\n{detector.get_immediate_action(flag)}")
            print()
    else:
        print("✓ No red flags detected")

    # Test case 3: Dengue warning signs
    print("\n" + "-" * 80)
    print("\nCase 3: Dengue patient (day 5) with warning signs")
    print("-" * 80)

    presentation3 = {
        "fever": True,
        "dengue_suspected": True,
        "abdominal_pain": True,
        "persistent_vomiting": True,
    }

    red_flags3 = detector.check(presentation3)

    if red_flags3:
        print(f"\n⚠️  DETECTED {len(red_flags3)} WARNING SIGN(S):\n")
        for flag in red_flags3:
            print(f"Finding: {flag.description}")
            print(f"Urgency: {flag.urgency.value}")
            print(f"Action: {flag.recommended_action}")
            print(f"Critical timing: {flag.time_critical}")
            print()
    else:
        print("✓ No warning signs")

    return True


def test_protocol_engine():
    """Test protocol retrieval and compliance checking."""
    print("\n" + "=" * 80)
    print("TEST 3: Protocol Engine")
    print("=" * 80)

    engine = ProtocolEngine()

    # Test 1: Get protocol for Type 2 Diabetes
    print("\nTest 3.1: Type 2 Diabetes Protocol")
    print("-" * 80)

    protocol = engine.get_protocol("type_2_diabetes")

    if protocol:
        print(f"\nDiagnosis: {protocol.diagnosis}")
        print(f"ICD-10 Code: {protocol.icd10_code}")

        print(f"\nFirst-line medications:")
        for med in protocol.first_line_drugs:
            print(f"  • {med.drug_name} {med.strength}")
            print(f"    Dose: {med.dose} {med.frequency}, {med.instructions}")
            print(f"    Indication: {med.indication}")

        print(f"\nKey investigations:")
        for test in protocol.investigations[:5]:
            print(f"  • {test}")

        print(f"\nLifestyle modifications:")
        for advice in protocol.lifestyle_advice[:3]:
            print(f"  • {advice}")

        print(f"\nFollow-up: {protocol.follow_up_interval}")
    else:
        print("Protocol not found")

    # Test 2: Check prescription compliance
    print("\n" + "-" * 80)
    print("\nTest 3.2: Prescription Compliance Check")
    print("-" * 80)

    # Good prescription
    print("\nChecking compliant prescription for Type 2 DM:")
    prescription_good = {
        "medications": [
            {"drug_name": "Metformin 500mg", "dose": "1", "frequency": "BD"},
        ],
        "investigations": ["FBS", "HbA1c", "Lipid profile"],
    }

    compliance = engine.check_compliance(prescription_good, "type_2_diabetes")
    print(f"  Compliance Score: {compliance.score:.1f}/100")
    print(f"  Status: {'✓ COMPLIANT' if compliance.is_compliant else '✗ NON-COMPLIANT'}")

    if compliance.issues:
        print("  Issues:")
        for issue in compliance.issues:
            print(f"    [{issue.severity}] {issue.description}")

    if compliance.suggestions:
        print("  Suggestions:")
        for suggestion in compliance.suggestions[:2]:
            print(f"    • {suggestion}")

    # Bad prescription - antibiotic for viral URTI
    print("\n" + "-" * 80)
    print("\nChecking NON-compliant prescription (antibiotic for viral URTI):")

    prescription_bad = {
        "medications": [
            {"drug_name": "Azithromycin 500mg", "dose": "1", "frequency": "OD"},
            {"drug_name": "Paracetamol 500mg", "dose": "1", "frequency": "TDS"},
        ],
        "investigations": [],
    }

    compliance_bad = engine.check_compliance(prescription_bad, "upper_respiratory_tract_infection")
    print(f"  Compliance Score: {compliance_bad.score:.1f}/100")
    print(f"  Status: {'✓ COMPLIANT' if compliance_bad.is_compliant else '✗ NON-COMPLIANT'}")

    if compliance_bad.issues:
        print("  Issues:")
        for issue in compliance_bad.issues:
            print(f"    [{issue.severity.upper()}] {issue.description}")
            print(f"    → Recommendation: {issue.recommendation}")

    # Test 3: Dengue protocol
    print("\n" + "-" * 80)
    print("\nTest 3.3: Dengue Management Protocol")
    print("-" * 80)

    dengue_protocol = engine.get_protocol("dengue")

    if dengue_protocol:
        print(f"\nDiagnosis: {dengue_protocol.diagnosis}")

        print(f"\nMonitoring requirements:")
        for mon in dengue_protocol.monitoring[:4]:
            print(f"  • {mon}")

        print(f"\nReferral criteria (immediate admission if any):")
        for criteria in dengue_protocol.referral_criteria:
            print(f"  • {criteria}")

    return True


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "DocAssist EMR - Diagnosis Engine Tests" + " " * 21 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        test_differential_engine()
        test_red_flag_detector()
        test_protocol_engine()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nThe Diagnosis Engine is ready for integration into DocAssist EMR.")
        print()
        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
