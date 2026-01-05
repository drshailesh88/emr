#!/usr/bin/env python3
"""
Test script for expanded symptom parser

Tests parsing of complex clinical notes including:
- Pediatric symptoms
- Obstetric symptoms
- Psychiatric symptoms
- Ophthalmologic symptoms
- Dermatologic symptoms
- Urologic symptoms
- Hinglish patterns
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.diagnosis.symptom_parser import parse_symptoms
from src.services.diagnosis.differential_engine import DifferentialEngine
from src.services.diagnosis.red_flag_detector import RedFlagDetector


def test_pediatric_symptoms():
    """Test pediatric symptom parsing"""
    print("\n" + "=" * 80)
    print("PEDIATRIC SYMPTOM TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "6 month old baby c/o high pitched cry x 2 hours, not feeding well, bulging fontanelle o/e",
            "expected": ["crying_excessively", "not_feeding", "bulging_fontanelle"],
        },
        {
            "note": "2 year old child p/w barking cough, stridor, difficulty breathing",
            "expected": ["barking_cough", "stridor", "breathlessness"],
        },
        {
            "note": "8 month infant w/ fever, loose stools x 3 days, sunken eyes, dry mouth - dehydration",
            "expected": ["fever", "loose_stools", "dehydration_signs"],
        },
        {
            "note": "4 year old h/o fever with fits, jerking movements both sides",
            "expected": ["fever", "seizure_child"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        # Check if all expected symptoms were found
        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_obstetric_symptoms():
    """Test obstetric symptom parsing"""
    print("\n" + "=" * 80)
    print("OBSTETRIC SYMPTOM TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "32 weeks pregnant, c/o vaginal bleeding, severe abdominal pain, BP 160/110",
            "expected": ["vaginal_bleeding", "abdominal_pain"],
        },
        {
            "note": "G2P1 at 38 weeks p/w water leaking PV, contractions every 5 minutes",
            "expected": ["leaking_pv", "contractions"],
        },
        {
            "note": "28 weeks pregnancy, decreased fetal movements since yesterday, worried",
            "expected": ["decreased_fetal_movements"],
        },
        {
            "note": "Pregnant lady c/o severe headache, blurred vision, swelling of feet and face, BP high",
            "expected": ["headache_severe_sudden", "visual_disturbances", "swelling_feet_face"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_psychiatric_symptoms():
    """Test psychiatric symptom parsing"""
    print("\n" + "=" * 80)
    print("PSYCHIATRIC SYMPTOM TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "Patient c/o hearing voices telling him to hurt himself, suicidal thoughts",
            "expected": ["hearing_voices", "suicidal_ideation"],
        },
        {
            "note": "35F p/w excessive worry, panic attacks, can't sleep at night, neend nahi aati",
            "expected": ["excessive_worry", "panic_attacks", "insomnia"],
        },
        {
            "note": "Young man seeing things that others can't see, confused, disoriented",
            "expected": ["seeing_things", "confusion"],
        },
        {
            "note": "H/o racing thoughts, not sleeping for 3 days, very agitated",
            "expected": ["racing_thoughts", "insomnia"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_ophthalmologic_symptoms():
    """Test ophthalmologic symptom parsing"""
    print("\n" + "=" * 80)
    print("OPHTHALMOLOGIC SYMPTOM TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "60M c/o sudden vision loss in right eye, painless, since this morning",
            "expected": ["sudden_vision_loss"],
        },
        {
            "note": "Patient p/w red eye, severe eye pain, photophobia, headache",
            "expected": ["red_eye", "eye_pain", "photophobia", "headache"],
        },
        {
            "note": "Seeing floaters and flashing lights in left eye since yesterday",
            "expected": ["floaters"],
        },
        {
            "note": "Double vision, seeing double objects, difficulty focusing",
            "expected": ["double_vision"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_dermatologic_symptoms():
    """Test dermatologic symptom parsing"""
    print("\n" + "=" * 80)
    print("DERMATOLOGIC SYMPTOM TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "Patient c/o severe itching all over body, khujli bahut zyada hai, rash on hands",
            "expected": ["itching", "rash"],
        },
        {
            "note": "H/o blisters on chest and back, fluid-filled lesions, painful",
            "expected": ["blisters"],
        },
        {
            "note": "Complaining of hair loss, baal gir rahe hain, patchy bald areas",
            "expected": ["hair_loss"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_urologic_symptoms():
    """Test urologic symptom parsing"""
    print("\n" + "=" * 80)
    print("UROLOGIC SYMPTOM TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "45F c/o burning urination, peshab mein jalan, bar bar peshab aata hai",
            "expected": ["burning_urination", "urinary_frequency"],
        },
        {
            "note": "Patient p/w blood in urine, red colored urine since morning",
            "expected": ["blood_in_urine"],
        },
        {
            "note": "60M c/o can't pass urine, suprapubic pain, bladder distended",
            "expected": ["urinary_retention"],
        },
        {
            "note": "Severe flank pain on right side, radiating to groin, colicky",
            "expected": ["flank_pain"],
        },
        {
            "note": "Young male c/o sudden testicular pain, nausea, vomiting",
            "expected": ["testicular_pain", "vomiting"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_hinglish_patterns():
    """Test Hinglish pattern parsing"""
    print("\n" + "=" * 80)
    print("HINGLISH PATTERN TESTS")
    print("=" * 80)

    test_cases = [
        {
            "note": "Patient ko bukhar 5 din se, sir dard bhi hai, kamzori aur thakan",
            "expected": ["fever", "headache", "fatigue"],
        },
        {
            "note": "Petdard 2 din se, ulti bhi ho rahi hai, dast loose",
            "expected": ["abdominal_pain", "vomiting", "diarrhea"],
        },
        {
            "note": "Seene mein dard, saans phoolna, chakkar aa raha hai",
            "expected": ["chest_pain", "breathlessness"],
        },
        {
            "note": "Neend nahi aati, bhookh nahi lagti, bahut kamzori",
            "expected": ["insomnia", "fatigue"],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nTest {i}: {case['note']}")
        print(f"Parsed symptoms: {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"✓ PASS" if found else f"✗ FAIL")


def test_differential_diagnosis():
    """Test differential diagnosis with new symptoms"""
    print("\n" + "=" * 80)
    print("DIFFERENTIAL DIAGNOSIS TESTS")
    print("=" * 80)

    engine = DifferentialEngine()

    test_cases = [
        {
            "description": "Child with meningitis symptoms",
            "symptoms": ["fever", "not_feeding", "lethargy_child", "bulging_fontanelle"],
            "expected_dx": "meningitis",
        },
        {
            "description": "Pregnant woman with preeclampsia",
            "symptoms": ["headache_with_high_bp", "visual_disturbances", "swelling_feet_face"],
            "expected_dx": "preeclampsia",
        },
        {
            "description": "Acute angle-closure glaucoma",
            "symptoms": ["eye_pain", "red_eye", "photophobia"],
            "expected_dx": "acute_angle_closure_glaucoma",
        },
        {
            "description": "Testicular torsion",
            "symptoms": ["testicular_pain"],
            "expected_dx": "testicular_torsion",
        },
    ]

    for case in test_cases:
        print(f"\n{case['description']}:")
        print(f"Symptoms: {case['symptoms']}")

        differentials = engine.calculate_differentials(case["symptoms"])

        if differentials:
            print("\nTop 5 differentials:")
            for i, diff in enumerate(differentials[:5], 1):
                print(f"{i}. {diff.diagnosis}: {diff.probability:.1%}")

            # Check if expected diagnosis is in top 3
            top_3_diagnoses = [d.diagnosis for d in differentials[:3]]
            if case["expected_dx"] in top_3_diagnoses:
                print(f"\n✓ PASS: '{case['expected_dx']}' found in top 3")
            else:
                print(f"\n✗ FAIL: '{case['expected_dx']}' not in top 3")
        else:
            print("✗ FAIL: No differentials generated")


def test_red_flags():
    """Test red flag detection with new patterns"""
    print("\n" + "=" * 80)
    print("RED FLAG DETECTION TESTS")
    print("=" * 80)

    detector = RedFlagDetector()

    test_cases = [
        {
            "description": "Acute angle-closure glaucoma",
            "presentation": {
                "eye_pain": True,
                "red_eye": True,
                "blurred_vision": True,
                "headache": True,
                "nausea": True,
            },
            "expected_category": "OPHTHALMIC",
        },
        {
            "description": "Testicular torsion",
            "presentation": {
                "testicular_pain": True,
                "sudden_onset": True,
                "nausea": True,
                "vomiting": True,
            },
            "expected_category": "UROLOGIC",
        },
        {
            "description": "Suicidal patient with plan",
            "presentation": {
                "suicidal_ideation": True,
                "suicide_plan": True,
            },
            "expected_category": "PSYCHIATRIC",
        },
        {
            "description": "Eclampsia",
            "presentation": {
                "pregnancy": True,
                "seizure": True,
                "hypertension": True,
                "headache": True,
            },
            "expected_category": "OBSTETRIC",
        },
        {
            "description": "Epiglottitis in child",
            "presentation": {
                "stridor": True,
                "drooling": True,
                "tripod_position": True,
                "fever": True,
            },
            "expected_category": "PEDIATRIC",
        },
    ]

    for case in test_cases:
        print(f"\n{case['description']}:")
        print(f"Presentation: {case['presentation']}")

        red_flags = detector.check(case["presentation"])

        if red_flags:
            print(f"\n{len(red_flags)} red flag(s) detected:")
            for rf in red_flags:
                print(f"  - [{rf.urgency.value}] {rf.description} ({rf.category})")
                print(f"    Action: {rf.recommended_action[:80]}...")

            # Check if expected category is present
            categories = [rf.category for rf in red_flags]
            if case["expected_category"] in categories:
                print(f"\n✓ PASS: {case['expected_category']} red flag detected")
            else:
                print(f"\n✗ FAIL: {case['expected_category']} red flag not detected")
        else:
            print("\n✗ FAIL: No red flags detected")


def test_complex_clinical_notes():
    """Test parsing of complex, realistic clinical notes"""
    print("\n" + "=" * 80)
    print("COMPLEX CLINICAL NOTES TESTS")
    print("=" * 80)

    complex_notes = [
        {
            "note": """
            32F G2P1 at 34 weeks gestation p/w c/o severe headache x 6 hours,
            blurred vision, epigastric pain. H/o swelling of feet and face x 1 week.
            O/E: BP 170/115, facial puffiness present, pedal edema 2+.
            Urine dipstick: Protein 3+
            """,
            "expected": ["headache_severe_sudden", "visual_disturbances", "epigastric_pain_pregnancy", "swelling_feet_face"],
        },
        {
            "note": """
            8 month old baby brought by mother c/o high-pitched crying x 4 hours,
            not taking feeds, fever 102F. O/E: lethargic, fontanelle bulging and tense,
            neck stiffness present.
            """,
            "expected": ["crying_excessively", "not_feeding", "fever", "lethargy_child", "bulging_fontanelle"],
        },
        {
            "note": """
            65M k/c DM, HTN p/w sudden vision loss in right eye since morning, painless.
            No trauma. O/E: RAPD present, fundus shows cherry red spot.
            """,
            "expected": ["sudden_vision_loss"],
        },
        {
            "note": """
            28M c/o sudden onset severe testicular pain on left side x 2 hours,
            associated with nausea and vomiting. Pain 10/10. O/E: left testis high-riding,
            horizontal lie, cremasteric reflex absent.
            """,
            "expected": ["testicular_pain", "vomiting"],
        },
    ]

    for i, case in enumerate(complex_notes, 1):
        symptoms = parse_symptoms(case["note"])
        print(f"\nComplex Note {i}:")
        print(f"Note: {case['note'][:100]}...")
        print(f"\nParsed symptoms ({len(symptoms)}): {symptoms}")
        print(f"Expected (at least): {case['expected']}")

        found = all(exp in symptoms for exp in case["expected"])
        print(f"\n✓ PASS" if found else f"✗ FAIL")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SYMPTOM PARSER TEST SUITE")
    print("=" * 80)

    test_pediatric_symptoms()
    test_obstetric_symptoms()
    test_psychiatric_symptoms()
    test_ophthalmologic_symptoms()
    test_dermatologic_symptoms()
    test_urologic_symptoms()
    test_hinglish_patterns()
    test_differential_diagnosis()
    test_red_flags()
    test_complex_clinical_notes()

    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80 + "\n")
