#!/usr/bin/env python3
"""
Demonstration of expanded symptom parser capabilities

Shows real-world clinical scenarios with the new symptom categories:
- Pediatric emergencies
- Obstetric emergencies
- Psychiatric conditions
- Ophthalmologic emergencies
- Dermatologic conditions
- Urologic emergencies
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.diagnosis.symptom_parser import parse_symptoms
from src.services.diagnosis.differential_engine import DifferentialEngine
from src.services.diagnosis.red_flag_detector import RedFlagDetector


def demo_pediatric_emergency():
    """Demonstrate pediatric meningitis recognition"""
    print("\n" + "=" * 80)
    print("PEDIATRIC EMERGENCY: Suspected Meningitis")
    print("=" * 80)

    clinical_note = """
    8 month old baby brought by parents
    C/o: High-pitched crying x 4 hours, not taking feeds, fever 103F
    O/E: Lethargic, bulging fontanelle, neck stiffness
    """

    print(f"\nClinical Note:\n{clinical_note}")

    # Parse symptoms
    symptoms = parse_symptoms(clinical_note)
    print(f"\nParsed Symptoms: {symptoms}")

    # Check red flags
    detector = RedFlagDetector()
    presentation = {sym: True for sym in symptoms}
    presentation["age"] = 0.67  # 8 months
    red_flags = detector.check(presentation)

    if red_flags:
        print(f"\n🚨 RED FLAGS DETECTED: {len(red_flags)}")
        for rf in red_flags:
            print(f"\n[{rf.urgency.value}] {rf.description}")
            print(f"Category: {rf.category}")
            print(f"Action: {rf.recommended_action}")
            print(f"Time Critical: {rf.time_critical}")


def demo_obstetric_emergency():
    """Demonstrate preeclampsia recognition"""
    print("\n" + "=" * 80)
    print("OBSTETRIC EMERGENCY: Severe Preeclampsia")
    print("=" * 80)

    clinical_note = """
    32F G2P1 at 34 weeks gestation
    C/o: Severe headache x 6 hours, blurred vision, epigastric pain
    H/o: Swelling of feet and face x 1 week
    O/E: BP 170/115, facial puffiness, pedal edema 2+
    Urine dipstick: Protein 3+
    """

    print(f"\nClinical Note:\n{clinical_note}")

    symptoms = parse_symptoms(clinical_note)
    print(f"\nParsed Symptoms: {symptoms}")

    # Check red flags
    detector = RedFlagDetector()
    presentation = {sym: True for sym in symptoms}
    presentation["pregnancy"] = True
    presentation["bp_systolic"] = 170
    presentation["bp_diastolic"] = 115

    red_flags = detector.check(presentation)

    if red_flags:
        print(f"\n🚨 RED FLAGS DETECTED: {len(red_flags)}")
        for rf in red_flags:
            print(f"\n[{rf.urgency.value}] {rf.description}")
            print(f"Action: {rf.recommended_action}")
            print(f"Time Critical: {rf.time_critical}")


def demo_ophthalmologic_emergency():
    """Demonstrate acute glaucoma recognition"""
    print("\n" + "=" * 80)
    print("OPHTHALMOLOGIC EMERGENCY: Acute Angle-Closure Glaucoma")
    print("=" * 80)

    clinical_note = """
    65F c/o severe eye pain in right eye x 3 hours
    Associated with: red eye, blurred vision, seeing halos around lights
    Also has: headache, nausea, vomiting
    O/E: Right eye - conjunctival injection, corneal edema, fixed mid-dilated pupil
    """

    print(f"\nClinical Note:\n{clinical_note}")

    symptoms = parse_symptoms(clinical_note)
    print(f"\nParsed Symptoms: {symptoms}")

    # Check red flags
    detector = RedFlagDetector()
    presentation = {sym: True for sym in symptoms}

    red_flags = detector.check(presentation)

    if red_flags:
        print(f"\n🚨 RED FLAGS DETECTED: {len(red_flags)}")
        for rf in red_flags:
            print(f"\n[{rf.urgency.value}] {rf.description}")
            print(f"Action: {rf.recommended_action}")
            print(f"Time Critical: {rf.time_critical}")


def demo_urologic_emergency():
    """Demonstrate testicular torsion recognition"""
    print("\n" + "=" * 80)
    print("UROLOGIC EMERGENCY: Testicular Torsion")
    print("=" * 80)

    clinical_note = """
    16M c/o sudden onset severe left testicular pain x 2 hours
    Pain started during sleep, 10/10 severity
    Associated with: nausea, vomiting
    O/E: Left testis high-riding, horizontal lie, exquisitely tender
    Cremasteric reflex: Absent on left
    """

    print(f"\nClinical Note:\n{clinical_note}")

    symptoms = parse_symptoms(clinical_note)
    print(f"\nParsed Symptoms: {symptoms}")

    # Check red flags
    detector = RedFlagDetector()
    presentation = {
        "testicular_pain": True,
        "sudden_onset": True,
        "nausea": True,
        "vomiting": True,
        "high_riding_testis": True,
        "absent_cremasteric_reflex": True,
    }

    red_flags = detector.check(presentation)

    if red_flags:
        print(f"\n🚨 RED FLAGS DETECTED: {len(red_flags)}")
        for rf in red_flags:
            print(f"\n[{rf.urgency.value}] {rf.description}")
            print(f"Action: {rf.recommended_action}")
            print(f"Time Critical: {rf.time_critical}")


def demo_psychiatric_emergency():
    """Demonstrate suicidal ideation recognition"""
    print("\n" + "=" * 80)
    print("PSYCHIATRIC EMERGENCY: High Suicide Risk")
    print("=" * 80)

    clinical_note = """
    28M brought by family
    C/o: Hearing voices telling him to kill himself
    States: Has plan to jump from building, wants to die
    H/o: Recent job loss, broke up with girlfriend
    O/E: Agitated, poor eye contact, evidence of self-harm (cutting marks on arms)
    """

    print(f"\nClinical Note:\n{clinical_note}")

    symptoms = parse_symptoms(clinical_note)
    print(f"\nParsed Symptoms: {symptoms}")

    # Check red flags
    detector = RedFlagDetector()
    presentation = {
        "suicidal_ideation": True,
        "suicide_plan": True,
        "hearing_voices": True,
        "self_harm": True,
        "recent_loss": True,
    }

    red_flags = detector.check(presentation)

    if red_flags:
        print(f"\n🚨 RED FLAGS DETECTED: {len(red_flags)}")
        for rf in red_flags:
            print(f"\n[{rf.urgency.value}] {rf.description}")
            print(f"Action: {rf.recommended_action}")
            print(f"Time Critical: {rf.time_critical}")


def demo_hinglish_parsing():
    """Demonstrate Hinglish symptom parsing"""
    print("\n" + "=" * 80)
    print("HINGLISH SYMPTOM PARSING")
    print("=" * 80)

    test_notes = [
        "Patient ko bukhar 3 din se, sir dard bhi hai, kamzori bahut",
        "Petdard 2 din se, ulti ho rahi hai, dast loose",
        "Peshab mein jalan, bar bar peshab aata hai, khoon bhi aa raha hai",
        "Neend nahi aati raat ko, bhookh nahi lagti, bahut thakan",
    ]

    for note in test_notes:
        symptoms = parse_symptoms(note)
        print(f"\nNote: {note}")
        print(f"Symptoms: {symptoms}")


def demo_complex_multi_system():
    """Demonstrate complex multi-system case"""
    print("\n" + "=" * 80)
    print("COMPLEX MULTI-SYSTEM CASE")
    print("=" * 80)

    clinical_note = """
    45M k/c HTN, DM
    C/o: Burning urination x 5 days, bar bar peshab (peshab mein jalan)
    Now: Fever 102F x 2 days, severe flank pain right side, nausea, vomiting
    O/E: Right CVA tenderness, BP 160/100, Temp 102.5F
    """

    print(f"\nClinical Note:\n{clinical_note}")

    symptoms = parse_symptoms(clinical_note)
    print(f"\nParsed Symptoms ({len(symptoms)}): {symptoms}")

    # Get differentials
    engine = DifferentialEngine()
    differentials = engine.calculate_differentials(symptoms, patient={"age": 45, "gender": "M"})

    if differentials:
        print(f"\nTop 5 Differential Diagnoses:")
        for i, diff in enumerate(differentials[:5], 1):
            print(f"{i}. {diff.diagnosis}: {diff.probability:.1%}")
            if diff.suggested_tests:
                print(f"   Suggested tests: {', '.join(diff.suggested_tests[:3])}")

    # Check red flags
    detector = RedFlagDetector()
    presentation = {sym: True for sym in symptoms}
    presentation["fever"] = True
    red_flags = detector.check(presentation)

    if red_flags:
        print(f"\n⚠️  WARNING SIGNS DETECTED:")
        for rf in red_flags:
            print(f"- [{rf.urgency.value}] {rf.description}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EXPANDED SYMPTOM PARSER DEMONSTRATION")
    print("Showcasing Pediatric, Obstetric, Psychiatric, Ophthalmologic, and Urologic")
    print("=" * 80)

    demo_pediatric_emergency()
    demo_obstetric_emergency()
    demo_ophthalmologic_emergency()
    demo_urologic_emergency()
    demo_psychiatric_emergency()
    demo_hinglish_parsing()
    demo_complex_multi_system()

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETED")
    print("=" * 80 + "\n")
