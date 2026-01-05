#!/usr/bin/env python3
"""Test script for drug interaction checker"""

import sys
sys.path.insert(0, '/home/user/emr')

from src.services.drugs import InteractionChecker, Severity

def test_interaction_checker():
    """Test the interaction checker with sample data"""

    print("=" * 70)
    print("Testing Drug Interaction Checker")
    print("=" * 70)

    # Initialize checker
    checker = InteractionChecker(data_path="/home/user/emr/data/interactions")

    print(f"\n✓ Loaded {len(checker.interactions)} drug-drug interactions")
    print(f"✓ Loaded {len(checker.contraindications)} contraindications")
    print(f"✓ Loaded {len(checker.cross_allergies)} cross-allergy patterns")
    print(f"✓ Loaded {len(checker.drug_classes)} drug class mappings")

    # Test 1: Check warfarin + aspirin interaction
    print("\n" + "=" * 70)
    print("Test 1: Warfarin + Aspirin Interaction")
    print("=" * 70)
    interaction = checker.check_pair("warfarin", "aspirin")
    if interaction:
        print(f"✓ Interaction detected!")
        print(f"  Severity: {interaction.severity.value}")
        print(f"  Effect: {interaction.clinical_effect}")
        print(f"  Management: {interaction.management}")
    else:
        print("✗ No interaction found (ERROR)")

    # Test 2: Check metformin + contrast interaction
    print("\n" + "=" * 70)
    print("Test 2: Metformin + Contrast Dye Interaction")
    print("=" * 70)
    interaction = checker.check_pair("metformin", "contrast dye")
    if interaction:
        print(f"✓ Interaction detected!")
        print(f"  Severity: {interaction.severity.value}")
        print(f"  Effect: {interaction.clinical_effect}")
        print(f"  Management: {interaction.management}")
    else:
        print("✗ No interaction found (ERROR)")

    # Test 3: Check multiple drug prescription
    print("\n" + "=" * 70)
    print("Test 3: Comprehensive Prescription Check")
    print("=" * 70)

    # Sample patient data
    new_drugs = ["warfarin", "ibuprofen", "metformin"]
    current_drugs = ["atorvastatin", "amlodipine"]
    patient_conditions = ["chronic kidney disease", "diabetes mellitus"]
    patient_allergies = ["penicillin"]
    patient_age = 70
    patient_gender = "M"
    egfr = 35.0

    print(f"\nPatient Profile:")
    print(f"  Age: {patient_age} years")
    print(f"  eGFR: {egfr} ml/min/1.73m²")
    print(f"  Conditions: {', '.join(patient_conditions)}")
    print(f"  Allergies: {', '.join(patient_allergies)}")
    print(f"  Current Meds: {', '.join(current_drugs)}")
    print(f"  New Prescription: {', '.join(new_drugs)}")

    alerts = checker.check_prescription(
        new_drugs=new_drugs,
        current_drugs=current_drugs,
        patient_conditions=patient_conditions,
        patient_allergies=patient_allergies,
        patient_age=patient_age,
        patient_gender=patient_gender,
        egfr=egfr
    )

    print(f"\n✓ Found {len(alerts)} alerts:")
    for i, alert in enumerate(alerts, 1):
        severity_color = {
            Severity.CRITICAL: "🔴",
            Severity.MAJOR: "🟠",
            Severity.MODERATE: "🟡",
            Severity.MINOR: "🟢"
        }
        icon = severity_color.get(alert.severity, "⚪")
        print(f"\n  {i}. {icon} {alert.title}")
        print(f"     Severity: {alert.severity.value.upper()}")
        print(f"     Message: {alert.message}")
        if alert.details:
            for key, value in alert.details.items():
                print(f"     {key.title()}: {value}")

    # Test 4: Check contraindication
    print("\n" + "=" * 70)
    print("Test 4: Drug-Disease Contraindication")
    print("=" * 70)
    contra_alert = checker.check_contraindication("metformin", "chronic kidney disease")
    if contra_alert:
        print(f"✓ Contraindication detected!")
        print(f"  Severity: {contra_alert.severity.value}")
        print(f"  Message: {contra_alert.message}")
        if contra_alert.alternatives:
            print(f"  Alternatives: {', '.join(contra_alert.alternatives)}")
    else:
        print("✗ No contraindication found (ERROR)")

    # Test 5: Check allergy cross-reactivity
    print("\n" + "=" * 70)
    print("Test 5: Allergy Cross-Reactivity")
    print("=" * 70)
    allergy_alert = checker.check_allergy("amoxicillin", ["penicillin"])
    if allergy_alert:
        print(f"✓ Allergy alert detected!")
        print(f"  Severity: {allergy_alert.severity.value}")
        print(f"  Message: {allergy_alert.message}")
    else:
        print("✗ No allergy alert found (this might be expected)")

    # Test 6: Check duplicate therapy
    print("\n" + "=" * 70)
    print("Test 6: Duplicate Therapy Detection")
    print("=" * 70)
    duplicate_alerts = checker.check_duplicate_therapy(["ibuprofen", "naproxen", "diclofenac"])
    if duplicate_alerts:
        print(f"✓ Duplicate therapy detected!")
        for alert in duplicate_alerts:
            print(f"  {alert.title}")
            print(f"  Message: {alert.message}")
    else:
        print("✗ No duplicate therapy found (ERROR)")

    print("\n" + "=" * 70)
    print("Testing Complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_interaction_checker()
