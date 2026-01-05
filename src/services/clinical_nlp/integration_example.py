"""Integration example: Clinical NLP Engine with DocAssist EMR.

This demonstrates how to integrate the Clinical NLP Engine
with the existing DocAssist EMR system components.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.llm import LLMService
from src.services.clinical_nlp import (
    ClinicalNoteExtractor,
    MedicalNER,
    ClinicalReasoning,
    ClinicalContext,
)
from src.models.schemas import Patient, Visit


def integrate_with_visit_creation(patient: Patient, clinical_notes: str) -> Visit:
    """
    Integrate Clinical NLP with visit creation workflow.

    Args:
        patient: Patient object
        clinical_notes: Raw clinical notes (can be Hinglish)

    Returns:
        Visit object with structured data
    """
    # Initialize services
    llm = LLMService()
    extractor = ClinicalNoteExtractor(llm_service=llm)
    ner = MedicalNER(llm_service=llm)
    reasoner = ClinicalReasoning(llm_service=llm)

    # Extract SOAP note
    soap = extractor.extract_soap_note(clinical_notes)

    # Extract structured entities
    symptoms = ner.extract_symptoms(clinical_notes)
    diagnoses = ner.extract_diagnoses(clinical_notes)

    # Build patient context
    context = ClinicalContext(
        patient_age=patient.age,
        patient_gender=patient.gender,
        # These would come from patient's history
        known_conditions=[],
        current_medications=[],
        allergies=[],
    )

    # Generate differentials
    differentials = reasoner.generate_differentials(symptoms, context)

    # Check for red flags
    presentation = {
        "symptoms": symptoms,
        "vitals": soap.vitals,
        "history": clinical_notes,
    }
    red_flags = reasoner.flag_red_flags(presentation)

    # Suggest investigations
    investigations = reasoner.suggest_investigations(differentials[:3])

    # Generate clinical summary
    summary = reasoner.generate_clinical_summary(soap)

    # Create Visit object
    visit = Visit(
        patient_id=patient.id,
        chief_complaint=soap.chief_complaint,
        clinical_notes=summary,
        diagnosis=", ".join(soap.diagnoses) if soap.diagnoses else
                  ", ".join([d.diagnosis for d in differentials[:3]]),
    )

    # Display red flags to doctor
    if red_flags:
        print("\n⚠️  RED FLAGS DETECTED:")
        for flag in red_flags:
            if flag.time_critical:
                print(f"🔴 {flag.category.upper()}: {flag.description}")
                print(f"   Action: {flag.action_required}")

    # Display suggested investigations
    if investigations:
        print("\n🔬 Suggested Investigations:")
        for inv in investigations[:5]:
            print(f"   - {inv.name} [{inv.urgency}]")

    return visit


def integrate_with_prescription_generation(clinical_notes: str, patient_context: dict):
    """
    Integrate Clinical NLP with prescription generation.

    Args:
        clinical_notes: Raw clinical notes
        patient_context: Patient context dictionary

    Returns:
        Enhanced prescription data
    """
    llm = LLMService()
    extractor = ClinicalNoteExtractor(llm_service=llm)
    reasoner = ClinicalReasoning(llm_service=llm)

    # Extract SOAP note
    soap = extractor.extract_soap_note(clinical_notes)

    # Convert medications to prescription format
    from src.models.schemas import Medication, Prescription

    medications = []
    for drug in soap.medications:
        medications.append(Medication(
            drug_name=drug.name,
            strength=drug.strength or "",
            form="tablet",  # Default, could be extracted
            dose=drug.dose or "1",
            frequency=drug.frequency or "OD",
            duration=drug.duration or "7 days",
            instructions=drug.instructions or "",
        ))

    # Build prescription
    prescription = Prescription(
        diagnosis=soap.diagnoses,
        medications=medications,
        investigations=[inv.name for inv in soap.investigations],
        advice=soap.advice,
        follow_up=soap.follow_up or "2 weeks",
        red_flags=[],
    )

    # Add red flags
    presentation = {
        "symptoms": [],  # Would extract symptoms here
        "vitals": soap.vitals,
        "history": clinical_notes,
    }
    red_flags = reasoner.flag_red_flags(presentation)

    if red_flags:
        prescription.red_flags = [
            f"{flag.category}: {flag.description}" for flag in red_flags
        ]

    return prescription


def integrate_with_rag_system(patient_id: int, query: str):
    """
    Integrate Clinical NLP with RAG system for intelligent querying.

    Args:
        patient_id: Patient ID
        query: Doctor's natural language query

    Returns:
        Structured answer with relevant entities
    """
    ner = MedicalNER()

    # Extract entities from query to improve RAG retrieval
    query_symptoms = ner.extract_symptoms(query)
    query_drugs = ner.extract_drugs(query)
    query_investigations = ner.extract_investigations(query)

    # Build enhanced search terms for RAG
    search_terms = [query]

    if query_symptoms:
        search_terms.extend([s.name for s in query_symptoms])

    if query_drugs:
        search_terms.extend([d.name for d in query_drugs])
        # Also search for generic names
        for drug in query_drugs:
            if drug.generic_name:
                search_terms.append(drug.generic_name)

    if query_investigations:
        search_terms.extend([i.name for i in query_investigations])

    # Return enhanced search terms for RAG system
    return {
        "original_query": query,
        "search_terms": search_terms,
        "entities": {
            "symptoms": [s.name for s in query_symptoms],
            "drugs": [d.name for d in query_drugs],
            "investigations": [i.name for i in query_investigations],
        }
    }


def demo_integration():
    """Demonstrate full integration with EMR workflow."""
    print("=" * 70)
    print("Clinical NLP Engine - Integration Demo")
    print("=" * 70)

    # Sample patient
    patient = Patient(
        id=1,
        uhid="EMR-2024-0001",
        name="Ram Kumar",
        age=58,
        gender="M",
    )

    # Sample clinical notes (Hinglish)
    clinical_notes = """
    Patient c/o chest pain for 4 hours. Dard seene mein hai, crushing type,
    radiating to left arm. Associated breathlessness and sweating.

    h/o DM since 10 years, HTN since 5 years. Currently on Glycomet 500mg BD
    and Telma 40mg OD. k/c/o IHD.

    On examination:
    BP 160/100, PR 110/min, temp 98.2F, SpO2 94% on room air
    CVS: S1 S2 normal, no murmur
    RS: bilateral clear
    PA: soft, non-tender

    Impression: Acute coronary syndrome, rule out NSTEMI

    Plan:
    Tab. Aspirin 325mg stat
    Tab. Clopidogrel 300mg stat
    Tab. Atorvastatin 80mg OD
    Inj. Enoxaparin 60mg SC BD

    Investigations:
    ECG stat - shows ST depression in V4-V6
    Troponin I stat
    CK-MB
    2D Echo
    Lipid profile

    Advice:
    Bed rest
    Nil per oral
    Monitor vitals q2h

    Immediate cardiology referral for possible PCI
    """

    print("\n📋 Creating visit with Clinical NLP...\n")

    # Create visit with NLP integration
    visit = integrate_with_visit_creation(patient, clinical_notes)

    print(f"\n✅ Visit Created:")
    print(f"   Patient: {patient.name} ({patient.uhid})")
    print(f"   Chief Complaint: {visit.chief_complaint}")
    print(f"   Diagnosis: {visit.diagnosis}")
    print(f"   Clinical Notes: {visit.clinical_notes[:100]}...")

    print("\n" + "=" * 70)

    # Generate prescription
    print("\n💊 Generating prescription with Clinical NLP...\n")

    prescription = integrate_with_prescription_generation(
        clinical_notes,
        {"age": patient.age, "gender": patient.gender}
    )

    print(f"✅ Prescription Generated:")
    print(f"   Diagnoses: {', '.join(prescription.diagnosis)}")
    print(f"   Medications: {len(prescription.medications)} prescribed")
    print(f"   Investigations: {len(prescription.investigations)} ordered")
    if prescription.red_flags:
        print(f"   ⚠️  Red Flags: {len(prescription.red_flags)} detected")

    print("\n" + "=" * 70)

    # RAG query enhancement
    print("\n🔍 Enhancing RAG query with Clinical NLP...\n")

    rag_query = "What was his last creatinine level? Any deterioration in kidney function?"

    enhanced = integrate_with_rag_system(patient.id, rag_query)

    print(f"Original Query: {enhanced['original_query']}")
    print(f"Enhanced Search Terms: {enhanced['search_terms']}")
    print(f"Extracted Entities: {enhanced['entities']}")

    print("\n" + "=" * 70)
    print("✅ Integration Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_integration()
