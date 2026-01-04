"""Example usage of Clinical NLP Engine.

This file demonstrates how to use the Clinical NLP components
for extracting clinical information from natural language.
"""

from datetime import datetime
from typing import List

# Import LLM service (optional, for enhanced extraction)
from ..llm import LLMService

# Import Clinical NLP components
from .note_extractor import ClinicalNoteExtractor
from .medical_entity_recognition import MedicalNER
from .clinical_reasoning import ClinicalReasoning
from .entities import ClinicalContext, Symptom


def example_soap_extraction():
    """Example: Extract SOAP note from clinical transcript."""
    print("=" * 60)
    print("Example 1: SOAP Note Extraction")
    print("=" * 60)

    # Clinical transcript (Hinglish - common in India)
    transcript = """
    Patient c/o chest pain for 2 days. Dard seene ke beech mein hai,
    radiating to left arm. Associated breathlessness and sweating.
    h/o DM and HTN since 5 years. k/c/o IHD.

    On examination: BP 150/95, PR 88/min, temp 98.2F, SpO2 95%.
    CVS: S1 S2 normal, no murmur. RS: clear bilaterally.

    Impression: Acute coronary syndrome, rule out NSTEMI

    Plan:
    Tab. Aspirin 325mg stat
    Tab. Clopidogrel 300mg stat
    Tab. Atorvastatin 80mg OD

    Investigations: ECG stat, Troponin I, CK-MB, 2D Echo

    Advice: Bed rest, nil per oral
    Follow-up: Emergency department referral
    """

    # Initialize extractor (with LLM service for enhanced extraction)
    llm = LLMService()
    extractor = ClinicalNoteExtractor(llm_service=llm)

    # Extract SOAP note
    soap = extractor.extract_soap_note(transcript)

    # Display results
    print("\n📋 Chief Complaint:", soap.chief_complaint)
    print("⏱️  Duration:", soap.duration or "Not specified")
    print("\n💊 Vitals:")
    for vital, value in soap.vitals.items():
        print(f"   {vital}: {value}")

    print("\n🔍 Diagnoses:")
    for diagnosis in soap.diagnoses:
        print(f"   - {diagnosis}")

    print("\n💊 Medications:")
    for med in soap.medications:
        print(f"   - {med.drug_name} {med.strength} {med.frequency}")

    print("\n🔬 Investigations:")
    for inv in soap.investigations:
        print(f"   - {inv.name} ({inv.urgency})")

    print("\n" + "=" * 60)


def example_entity_recognition():
    """Example: Extract medical entities."""
    print("=" * 60)
    print("Example 2: Medical Entity Recognition")
    print("=" * 60)

    text = """
    Patient presented with severe headache since 3 days, associated with
    fever (high grade) and vomiting. On examination: BP 130/80, temp 102F.
    Diagnosed with viral meningitis. Started on IV antibiotics pending
    culture results. Prescribed Tab. Paracetamol 650mg TDS for fever.
    Investigations: CBC, blood culture, CSF analysis, CT brain.
    """

    # Initialize NER
    ner = MedicalNER()

    # Extract symptoms
    symptoms = ner.extract_symptoms(text)
    print("\n🤒 Symptoms:")
    for symptom in symptoms:
        print(f"   - {symptom.name.title()}")
        if symptom.duration:
            print(f"     Duration: {symptom.duration}")
        if symptom.severity:
            print(f"     Severity: {symptom.severity.value}")

    # Extract diagnoses
    diagnoses = ner.extract_diagnoses(text)
    print("\n🏥 Diagnoses:")
    for diagnosis in diagnoses:
        icd = f"(ICD-10: {diagnosis.icd10_code})" if diagnosis.icd10_code else ""
        print(f"   - {diagnosis.name} {icd}")

    # Extract medications
    medications = ner.extract_drugs(text)
    print("\n💊 Medications:")
    for med in medications:
        generic = f"({med.generic_name})" if med.generic_name else ""
        print(f"   - {med.name} {generic} {med.strength}")
        print(f"     {med.frequency} x {med.duration}")

    # Extract investigations
    investigations = ner.extract_investigations(text)
    print("\n🔬 Investigations:")
    for inv in investigations:
        print(f"   - {inv.name} [{inv.test_type}] ({inv.urgency})")

    print("\n" + "=" * 60)


def example_differential_diagnosis():
    """Example: Generate differential diagnoses."""
    print("=" * 60)
    print("Example 3: Differential Diagnosis Generation")
    print("=" * 60)

    # Patient presentation
    symptoms = [
        Symptom(
            name="chest pain",
            duration="4 hours",
            severity="severe",
            onset="sudden",
            location="central",
            radiation="left arm",
            associated_symptoms=["sweating", "breathlessness"],
        ),
        Symptom(
            name="breathlessness",
            duration="4 hours",
            severity="moderate",
        ),
    ]

    # Patient context
    context = ClinicalContext(
        patient_age=58,
        patient_gender="M",
        known_conditions=["Diabetes Mellitus", "Hypertension"],
        current_medications=["Metformin", "Amlodipine"],
    )

    # Initialize reasoning engine
    reasoner = ClinicalReasoning()

    # Generate differentials
    differentials = reasoner.generate_differentials(symptoms, context)

    print("\n🎯 Differential Diagnoses (ranked by probability):\n")
    for i, diff in enumerate(differentials[:5], 1):
        print(f"{i}. {diff.diagnosis}")
        print(f"   Probability: {diff.probability * 100:.1f}%")
        print(f"   Prior (India): {diff.prior_probability * 100:.2f}%")
        print(f"   Supporting: {', '.join(diff.supporting_features)}")
        print(f"   Urgency: {diff.treatment_urgency.upper()}")

        if diff.recommended_investigations:
            print(f"   Investigations: {', '.join(diff.recommended_investigations[:3])}")

        if diff.red_flags:
            print(f"   ⚠️  Red Flags: {', '.join(diff.red_flags)}")
        print()

    # Suggest investigations
    investigations = reasoner.suggest_investigations(differentials)

    print("\n🔬 Recommended Investigations (prioritized):\n")
    for inv in investigations[:8]:
        urgency_marker = "🔴" if inv.urgency == "stat" else "🟡" if inv.urgency == "urgent" else "🟢"
        print(f"{urgency_marker} {inv.name} [{inv.test_type.upper()}] - {inv.reason}")

    print("\n" + "=" * 60)


def example_red_flag_detection():
    """Example: Detect clinical red flags."""
    print("=" * 60)
    print("Example 4: Red Flag Detection")
    print("=" * 60)

    # Critical presentation
    presentation = {
        "symptoms": [
            Symptom(
                name="chest pain",
                severity="severe",
                description="crushing chest pain radiating to jaw",
            ),
            Symptom(
                name="breathlessness",
                severity="severe",
            ),
        ],
        "vitals": {
            "BP": "160/100",
            "SpO2": "88%",
            "Pulse": "110 bpm",
        },
        "history": "sudden onset severe chest pain with sweating and breathlessness at rest",
    }

    # Initialize reasoning
    reasoner = ClinicalReasoning()

    # Flag red flags
    red_flags = reasoner.flag_red_flags(presentation)

    print("\n⚠️  RED FLAGS DETECTED:\n")
    for flag in red_flags:
        severity_marker = "🔴" if flag.severity == "critical" else "🟠"
        time_marker = "⏰ TIME CRITICAL" if flag.time_critical else ""

        print(f"{severity_marker} [{flag.category.upper()}] {flag.description}")
        print(f"   System: {flag.system}")
        print(f"   Action: {flag.action_required}")
        if time_marker:
            print(f"   {time_marker}")
        print()

    print("=" * 60)


def example_clinical_summary():
    """Example: Generate clinical summary."""
    print("=" * 60)
    print("Example 5: Clinical Summary Generation")
    print("=" * 60)

    # Mock SOAP note
    from .entities import SOAPNote, Investigation

    soap = SOAPNote(
        chief_complaint="fever and cough",
        duration="5 days",
        history_of_present_illness="Gradual onset fever with productive cough",
        associated_symptoms=["breathlessness", "chest pain"],
        vitals={
            "BP": "120/80",
            "Pulse": "88 bpm",
            "Temperature": "101.2°F",
            "SpO2": "94%",
        },
        examination_findings=["Bilateral crepitations on chest examination"],
        diagnoses=["Community Acquired Pneumonia"],
        investigations=[
            Investigation(name="Chest X-ray", test_type="imaging"),
            Investigation(name="CBC", test_type="lab"),
            Investigation(name="CRP", test_type="lab"),
        ],
        advice=["Bed rest", "Adequate hydration", "Monitor temperature"],
        follow_up="3 days",
    )

    # Initialize reasoning
    llm = LLMService()
    reasoner = ClinicalReasoning(llm_service=llm)

    # Generate summary
    summary = reasoner.generate_clinical_summary(soap)

    print("\n📄 Clinical Summary:\n")
    print(summary)
    print("\n" + "=" * 60)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print(" Clinical NLP Engine - Examples")
    print("=" * 60 + "\n")

    try:
        example_soap_extraction()
        print("\n")

        example_entity_recognition()
        print("\n")

        example_differential_diagnosis()
        print("\n")

        example_red_flag_detection()
        print("\n")

        example_clinical_summary()

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
