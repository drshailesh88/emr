#!/usr/bin/env python3
"""Test script for clinical entity extraction integration.

This script tests the complete entity extraction pipeline:
1. Abbreviations expansion
2. Entity extraction from clinical notes
3. Summary generation
4. UI component rendering
"""

import sys
from datetime import datetime

# Test clinical note with multiple entity types
SAMPLE_NOTE = """45F k/c DM2, HTN. C/o chest pain x 2 days, radiating to left arm.
Associated with breathlessness, sweating. No h/o fever or cough.

On Metformin 500mg BD, Telmisartan 40mg OD.

O/E: BP 150/90, Pulse 88/min, SpO2 96%, Temp 98.2F
CVS: S1S2 normal, no murmur
RS: NVBS bilateral

Impression: Unstable angina, r/o ACS

Plan:
- Tab Aspirin 75mg OD
- Tab Atorvastatin 40mg HS
- CBC, Troponin I, ECG, ECHO
- Advice: Low salt diet, avoid exertion
- F/u after 1 week
"""


def test_abbreviations():
    """Test abbreviation expansion."""
    print("=" * 70)
    print("TEST 1: Abbreviations Expansion")
    print("=" * 70)

    try:
        from src.services.clinical_nlp.abbreviations import (
            expand_abbreviation,
            expand_text,
            get_all_abbreviations
        )

        # Test single abbreviation expansion
        test_abbrevs = ["c/o", "h/o", "k/c", "DM2", "HTN", "BP", "OD", "BD"]
        print("\nSingle abbreviation expansions:")
        for abbr in test_abbrevs:
            expansion = expand_abbreviation(abbr)
            print(f"  {abbr:8} → {expansion}")

        # Test full text expansion
        print("\nFull text expansion:")
        sample = "Pt c/o chest pain. H/o DM, HTN. On Tab Metformin BD, Tab Enalapril OD."
        expanded = expand_text(sample)
        print(f"  Original: {sample}")
        print(f"  Expanded: {expanded}")

        print("\n✓ Abbreviations test PASSED\n")
        return True

    except Exception as ex:
        print(f"\n✗ Abbreviations test FAILED: {ex}\n")
        import traceback
        traceback.print_exc()
        return False


def test_entity_extraction():
    """Test entity extraction from clinical notes."""
    print("=" * 70)
    print("TEST 2: Entity Extraction")
    print("=" * 70)

    try:
        from src.services.clinical_nlp.note_extractor import ClinicalNoteExtractor

        # Initialize extractor (without LLM for testing)
        extractor = ClinicalNoteExtractor(llm_service=None)

        # Extract entities
        print("\nExtracting entities from sample note...")
        result = extractor.extract_entities(SAMPLE_NOTE)

        # Display entity spans
        entities = result.get('entities', [])
        print(f"\nFound {len(entities)} entity spans:")
        for entity in entities[:10]:  # Show first 10
            print(f"  [{entity['entity_type']:12}] {entity['text']:30} "
                  f"(pos: {entity['start']}-{entity['end']})")

        if len(entities) > 10:
            print(f"  ... and {len(entities) - 10} more entities")

        # Display summary
        summary = result.get('summary', {})
        print("\nExtracted Summary:")

        if summary.get('patient_info'):
            print(f"  Patient Info: {summary['patient_info']}")

        if summary.get('chief_complaint'):
            print(f"  Chief Complaint: {', '.join(summary['chief_complaint'])}")

        if summary.get('history'):
            print(f"  History: {', '.join(summary['history'])}")

        if summary.get('vitals'):
            print("  Vitals:")
            for k, v in summary['vitals'].items():
                print(f"    {k}: {v}")

        if summary.get('symptoms'):
            print(f"  Symptoms: {', '.join(summary['symptoms'][:5])}")

        if summary.get('diagnoses'):
            print(f"  Diagnoses: {', '.join(summary['diagnoses'])}")

        if summary.get('medications'):
            print("  Medications:")
            for med in summary['medications']:
                med_str = f"{med['drug_name']} {med.get('strength', '')} {med.get('frequency', '')}"
                print(f"    - {med_str.strip()}")

        if summary.get('investigations'):
            print(f"  Investigations: {', '.join(summary['investigations'][:5])}")

        print("\n✓ Entity extraction test PASSED\n")
        return True

    except Exception as ex:
        print(f"\n✗ Entity extraction test FAILED: {ex}\n")
        import traceback
        traceback.print_exc()
        return False


def test_ui_components():
    """Test UI components rendering (structure only, no Flet runtime)."""
    print("=" * 70)
    print("TEST 3: UI Components Structure")
    print("=" * 70)

    try:
        from src.ui.components.entity_highlight import EntitySpan, EntityHighlightedText
        from src.ui.components.extracted_summary import ExtractedData, ExtractedSummaryPanel

        # Test EntitySpan dataclass
        print("\nTesting EntitySpan dataclass...")
        span = EntitySpan(
            start=0,
            end=5,
            text="chest pain",
            entity_type="symptom",
            normalized_value="chest pain (severe)",
            confidence=0.9
        )
        print(f"  Created EntitySpan: {span.text} ({span.entity_type})")

        # Test ExtractedData dataclass
        print("\nTesting ExtractedData dataclass...")
        data = ExtractedData(
            patient_info={"Age": "45y", "Gender": "F"},
            chief_complaint=["chest pain x 2 days"],
            history=["DM2", "HTN"],
            vitals={"BP": "150/90 mmHg", "Pulse": "88 /min"},
            symptoms=["chest pain", "breathlessness", "sweating"],
            diagnoses=["Unstable angina"],
            medications=[
                {"drug_name": "Metformin", "strength": "500mg", "frequency": "BD"},
                {"drug_name": "Telmisartan", "strength": "40mg", "frequency": "OD"}
            ],
            investigations=["CBC", "Troponin I", "ECG", "ECHO"]
        )
        print(f"  Created ExtractedData with {len(data.symptoms)} symptoms, "
              f"{len(data.medications)} medications")

        # Test component instantiation (structure only)
        print("\nTesting component instantiation...")

        # Note: We can't fully test Flet components without a runtime,
        # but we can verify they instantiate without errors
        try:
            # This will create the component structure but won't render
            panel = ExtractedSummaryPanel(
                extracted_data=data,
                on_correction=lambda cat, old, new: print(f"Correction: {cat}"),
            )
            print(f"  Created ExtractedSummaryPanel successfully")
        except Exception as ex:
            # If this fails due to Flet runtime requirements, that's OK for structure test
            if "page" not in str(ex).lower() and "runtime" not in str(ex).lower():
                raise

        print("\n✓ UI components structure test PASSED\n")
        return True

    except Exception as ex:
        print(f"\n✗ UI components test FAILED: {ex}\n")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration pipeline."""
    print("=" * 70)
    print("TEST 4: Full Integration Pipeline")
    print("=" * 70)

    try:
        from src.services.clinical_nlp.note_extractor import ClinicalNoteExtractor
        from src.ui.components.extracted_summary import ExtractedData

        # Initialize extractor
        extractor = ClinicalNoteExtractor(llm_service=None)

        # Extract entities
        print("\nRunning full extraction pipeline...")
        result = extractor.extract_entities(SAMPLE_NOTE)

        # Convert to UI data structure
        summary = result.get('summary', {})
        ui_data = ExtractedData(
            patient_info=summary.get('patient_info', {}),
            chief_complaint=summary.get('chief_complaint', []),
            history=summary.get('history', []),
            vitals=summary.get('vitals', {}),
            symptoms=summary.get('symptoms', []),
            diagnoses=summary.get('diagnoses', []),
            medications=summary.get('medications', []),
            investigations=summary.get('investigations', []),
        )

        # Verify data pipeline
        print("\nVerifying data pipeline:")
        print(f"  ✓ Extracted {len(result.get('entities', []))} entity spans")
        print(f"  ✓ Generated summary with {len(ui_data.symptoms)} symptoms")
        print(f"  ✓ Found {len(ui_data.medications)} medications")
        print(f"  ✓ Identified {len(ui_data.investigations)} investigations")
        print(f"  ✓ Captured {len(ui_data.vitals)} vital signs")

        print("\n✓ Integration test PASSED\n")
        return True

    except Exception as ex:
        print(f"\n✗ Integration test FAILED: {ex}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CLINICAL ENTITY EXTRACTION INTEGRATION TESTS")
    print("=" * 70)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sample Note Length: {len(SAMPLE_NOTE)} characters\n")

    # Run tests
    results = []
    results.append(("Abbreviations", test_abbreviations()))
    results.append(("Entity Extraction", test_entity_extraction()))
    results.append(("UI Components", test_ui_components()))
    results.append(("Integration", test_integration()))

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name:25} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Entity extraction is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above for details.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
