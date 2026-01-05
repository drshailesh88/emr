#!/usr/bin/env python3
"""
Test/Demo script for specialty-specific clinical protocols.

Demonstrates usage of Cardiology, Pediatric, and OB/GYN protocols.
"""

from datetime import date
from src.services.diagnosis.specialty_protocols import (
    CardiologyProtocols,
    PediatricProtocols,
    OBGYNProtocols,
    ProtocolCalculator,
)


def demo_cardiology_protocols():
    """Demonstrate cardiology protocol usage."""
    print("=" * 80)
    print("CARDIOLOGY PROTOCOLS DEMO")
    print("=" * 80)

    cardio = CardiologyProtocols()

    # 1. Get STEMI protocol
    print("\n1. STEMI Protocol:")
    print("-" * 80)
    stemi = cardio.get_protocol("stemi")
    print(f"Diagnosis: {stemi.diagnosis}")
    print(f"ICD-10: {stemi.icd10_code}")
    print(f"\nFirst-line medications ({len(stemi.first_line_drugs)}):")
    for med in stemi.first_line_drugs[:3]:  # Show first 3
        print(f"  • {med.drug_name} {med.strength} - {med.indication}")
    print(f"\nKey investigations:")
    for inv in stemi.investigations[:5]:
        print(f"  • {inv}")

    # 2. Check compliance for a prescription
    print("\n2. Prescription Compliance Check:")
    print("-" * 80)
    sample_prescription = {
        "medications": [
            {"drug_name": "Aspirin", "strength": "150mg"},
            {"drug_name": "Clopidogrel", "strength": "75mg"},
            {"drug_name": "Atorvastatin", "strength": "80mg"},
        ]
    }
    compliance = cardio.check_compliance(sample_prescription, "stemi")
    print(f"Compliant: {compliance.is_compliant}")
    print(f"Score: {compliance.score}/100")
    if compliance.issues:
        print("Issues:")
        for issue in compliance.issues:
            print(f"  [{issue.severity.upper()}] {issue.description}")
            print(f"    → {issue.recommendation}")

    # 3. CHA2DS2-VASc calculator
    print("\n3. CHA2DS2-VASc Score (Atrial Fibrillation):")
    print("-" * 80)
    calc = ProtocolCalculator()
    cha2ds2vasc = calc.calculate_cha2ds2_vasc(
        age=72,
        gender="M",
        chf_history=True,
        hypertension=True,
        diabetes=True,
    )
    print(f"Score: {cha2ds2vasc['score']}")
    print(f"Annual stroke risk: {cha2ds2vasc['risk_percentage']}%")
    print(f"Recommendation: {cha2ds2vasc['recommendation']}")
    print(f"Treatment: {cha2ds2vasc['preferred_treatment']}")


def demo_pediatric_protocols():
    """Demonstrate pediatric protocol usage."""
    print("\n\n" + "=" * 80)
    print("PEDIATRIC PROTOCOLS DEMO")
    print("=" * 80)

    peds = PediatricProtocols()

    # 1. Gastroenteritis protocol
    print("\n1. Acute Gastroenteritis Protocol:")
    print("-" * 80)
    age = peds.get_protocol("acute_gastroenteritis")
    print(f"Diagnosis: {age.diagnosis}")
    print(f"\nFirst-line treatment:")
    for med in age.first_line_drugs:
        print(f"  • {med.drug_name}: {med.indication}")
    print(f"\nLifestyle advice:")
    for advice in age.lifestyle_advice[:3]:
        print(f"  • {advice}")

    # 2. Pediatric dosing calculator
    print("\n2. Pediatric Dose Calculator:")
    print("-" * 80)
    calc = ProtocolCalculator()
    paracetamol_dose = calc.calculate_pediatric_dose("Paracetamol", weight_kg=15)
    print(f"Paracetamol for 15kg child:")
    print(f"  Dose: {paracetamol_dose.amount}{paracetamol_dose.unit} {paracetamol_dose.frequency}")
    print(f"  Instructions: {paracetamol_dose.instructions}")

    amoxicillin_dose = calc.calculate_pediatric_dose("Amoxicillin", weight_kg=12)
    print(f"\nAmoxicillin for 12kg child:")
    print(f"  Dose: {amoxicillin_dose.amount}{amoxicillin_dose.unit} {amoxicillin_dose.frequency}")
    print(f"  Duration: {amoxicillin_dose.duration}")

    # 3. Red flags for pneumonia
    print("\n3. Pediatric Red Flags (Fast Breathing):")
    print("-" * 80)
    presentation = {
        "chief_complaint": "fever and cough",
        "respiratory_rate": 52,
    }
    red_flags = peds.get_red_flags(presentation, age_months=8)
    for flag in red_flags:
        print(f"  [{flag.urgency}] {flag.symptom}")
        print(f"    Action: {flag.action}")

    # 4. Immunization schedule
    print("\n4. India National Immunization Schedule (Sample):")
    print("-" * 80)
    schedule = peds.get_immunization_schedule()
    for age_point in ["Birth", "6 weeks", "9 months"]:
        print(f"\n{age_point}:")
        for vaccine in schedule[age_point]:
            print(f"  • {vaccine}")


def demo_obgyn_protocols():
    """Demonstrate OB/GYN protocol usage."""
    print("\n\n" + "=" * 80)
    print("OB/GYN PROTOCOLS DEMO")
    print("=" * 80)

    obgyn = OBGYNProtocols()

    # 1. Antenatal care protocol
    print("\n1. Antenatal Care Protocol:")
    print("-" * 80)
    anc = obgyn.get_protocol("antenatal_care")
    print(f"Diagnosis: {anc.diagnosis}")
    print(f"\nEssential medications:")
    for med in anc.first_line_drugs[:3]:
        print(f"  • {med.drug_name} {med.strength} - {med.indication}")

    # 2. ANC visit schedule
    print("\n2. ANC Visit Schedule:")
    print("-" * 80)
    visit_schedule = obgyn.get_anc_visit_schedule()
    for visit in visit_schedule:
        print(f"\nVisit {visit.visit_number} ({visit.timing}):")
        print(f"  Key investigations: {', '.join(visit.key_investigations[:2])}")

    # 3. Gestational age calculator
    print("\n3. Gestational Age Calculator:")
    print("-" * 80)
    calc = ProtocolCalculator()
    lmp = date(2024, 10, 1)
    ga = calc.calculate_gestational_age(lmp)
    print(f"LMP: {lmp}")
    print(f"Gestational Age: {ga['gestational_age']}")
    print(f"Trimester: {ga['trimester']}")
    print(f"Status: {ga['term_status']}")

    edd = calc.calculate_edd(lmp)
    print(f"Expected Delivery Date: {edd}")

    # 4. GDM protocol compliance
    print("\n4. Gestational Diabetes Management:")
    print("-" * 80)
    gdm = obgyn.get_protocol("gestational_diabetes")
    print(f"Diagnosis: {gdm.diagnosis}")
    print(f"First-line treatment: {gdm.first_line_drugs[0].indication}")
    print(f"\nLifestyle advice:")
    for advice in gdm.lifestyle_advice[:4]:
        print(f"  • {advice}")

    # 5. Pregnancy safety check
    print("\n5. Pregnancy Drug Safety Check:")
    print("-" * 80)
    unsafe_prescription = {
        "medications": [
            {"drug_name": "Enalapril", "strength": "5mg"},  # ACE-I - teratogenic!
        ]
    }
    compliance = obgyn.check_compliance(
        unsafe_prescription,
        "antenatal_care",
        is_pregnant=True,
        trimester=2,
    )
    print(f"Compliant: {compliance.is_compliant}")
    print(f"Score: {compliance.score}/100")
    if compliance.issues:
        print("SAFETY ISSUES:")
        for issue in compliance.issues:
            print(f"  [{issue.severity.upper()}] {issue.description}")
            print(f"    → {issue.recommendation}")


def demo_clinical_calculators():
    """Demonstrate clinical calculator usage."""
    print("\n\n" + "=" * 80)
    print("CLINICAL CALCULATORS DEMO")
    print("=" * 80)

    calc = ProtocolCalculator()

    # 1. Framingham CVD risk
    print("\n1. Framingham 10-Year CVD Risk (Indian population):")
    print("-" * 80)
    cvd_risk = calc.calculate_framingham(
        age=55,
        gender="M",
        total_cholesterol=220,
        hdl=35,
        systolic_bp=150,
        on_bp_medication=True,
        smoker=True,
        diabetic=True,
    )
    print(f"10-year CVD risk: {cvd_risk.risk_percentage}% ({cvd_risk.risk_category})")
    print(f"Target LDL: <{cvd_risk.target_ldl} mg/dL")
    print(f"Recommendations:")
    for rec in cvd_risk.recommendations[:3]:
        print(f"  • {rec}")

    # 2. eGFR calculation
    print("\n2. eGFR Calculation (Adult):")
    print("-" * 80)
    egfr = calc.calculate_egfr_adult(
        creatinine_mg_dl=1.5,
        age=65,
        gender="M",
        race="non-black",
    )
    print(f"Creatinine: 1.5 mg/dL")
    print(f"eGFR: {egfr} mL/min/1.73m²")
    if egfr < 60:
        print(f"  → CKD Stage 3 or higher")

    # 3. Pediatric eGFR
    print("\n3. Pediatric eGFR (Schwartz formula):")
    print("-" * 80)
    ped_egfr = calc.calculate_egfr_pediatric(
        creatinine_mg_dl=0.8,
        height_cm=120,
    )
    print(f"Creatinine: 0.8 mg/dL, Height: 120cm")
    print(f"eGFR: {ped_egfr} mL/min/1.73m²")

    # 4. HAS-BLED score
    print("\n4. HAS-BLED Bleeding Risk (on anticoagulation):")
    print("-" * 80)
    hasbled = calc.calculate_hasbled(
        age=70,
        hypertension_uncontrolled=True,
        abnormal_renal_function=True,
        bleeding_history=False,
    )
    print(f"Score: {hasbled['score']}")
    print(f"Annual bleeding risk: {hasbled['bleeding_risk_percentage']}%")
    print(f"Interpretation: {hasbled['interpretation']}")
    print(f"Recommendation: {hasbled['recommendation']}")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("SPECIALTY-SPECIFIC CLINICAL PROTOCOLS - DEMONSTRATION")
    print("DocAssist EMR - Evidence-Based Medicine for Indian Practice")
    print("=" * 80)

    demo_cardiology_protocols()
    demo_pediatric_protocols()
    demo_obgyn_protocols()
    demo_clinical_calculators()

    print("\n\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nThese protocols provide:")
    print("  ✓ Evidence-based treatment guidelines")
    print("  ✓ India-specific recommendations")
    print("  ✓ Prescription compliance checking")
    print("  ✓ Clinical risk calculators")
    print("  ✓ Red flag detection")
    print("  ✓ Referral criteria")
    print("\nAll protocols follow WHO, ICMR, IAP, FOGSI, CSI, and international guidelines.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
