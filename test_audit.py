#!/usr/bin/env python3
"""Test script for audit trail functionality."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import directly to avoid loading all services
import sqlite3
import json
from datetime import datetime, date
from typing import List, Optional, Tuple
from contextlib import contextmanager

# Import Pydantic models
from models.schemas import Patient, Visit, Investigation, Procedure

# Import database class directly
from services.database import DatabaseService

def test_audit_trail():
    """Test audit trail functionality."""
    print("Testing Audit Trail System...")
    print("=" * 60)

    # Use a test database
    test_db_path = "data/test_clinic.db"

    # Remove existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Initialize database
    db = DatabaseService(test_db_path)
    print("✓ Database initialized")

    # Test 1: Create patient (INSERT)
    print("\nTest 1: Creating patient...")
    patient = Patient(
        name="Test Patient",
        age=45,
        gender="M",
        phone="9876543210",
        address="123 Test St"
    )
    saved_patient = db.add_patient(patient)
    print(f"✓ Patient created: {saved_patient.uhid}")

    # Check audit log
    audit_history = db.get_audit_history(table_name="patients", record_id=saved_patient.id)
    assert len(audit_history) == 1, "Should have 1 audit entry for INSERT"
    assert audit_history[0]['operation'] == 'INSERT', "Should be INSERT operation"
    print(f"✓ Audit log created for INSERT: {audit_history[0]['new_value']}")

    # Test 2: Update patient (UPDATE)
    print("\nTest 2: Updating patient...")
    saved_patient.phone = "9999999999"
    saved_patient.age = 46
    db.update_patient(saved_patient)
    print(f"✓ Patient updated")

    # Check audit log
    audit_history = db.get_audit_history(table_name="patients", record_id=saved_patient.id)
    assert len(audit_history) == 2, "Should have 2 audit entries (INSERT + UPDATE)"
    update_entry = audit_history[0]  # Most recent first
    assert update_entry['operation'] == 'UPDATE', "Should be UPDATE operation"
    assert 'phone' in update_entry['old_value'], "Should track phone change"
    assert update_entry['old_value']['phone'] == "9876543210", "Should have old phone"
    assert update_entry['new_value']['phone'] == "9999999999", "Should have new phone"
    print(f"✓ Audit log created for UPDATE:")
    print(f"  Old: {update_entry['old_value']}")
    print(f"  New: {update_entry['new_value']}")

    # Test 3: Add visit (INSERT)
    print("\nTest 3: Creating visit...")
    visit = Visit(
        patient_id=saved_patient.id,
        visit_date=date.today(),
        chief_complaint="Fever",
        clinical_notes="Patient has fever for 2 days",
        diagnosis="Viral fever"
    )
    saved_visit = db.add_visit(visit)
    print(f"✓ Visit created: ID {saved_visit.id}")

    # Check audit log
    audit_history = db.get_audit_history(table_name="visits", record_id=saved_visit.id)
    assert len(audit_history) == 1, "Should have 1 audit entry for visit INSERT"
    print(f"✓ Audit log created for visit INSERT")

    # Test 4: Update visit (UPDATE)
    print("\nTest 4: Updating visit...")
    saved_visit.diagnosis = "Bacterial fever"
    db.update_visit(saved_visit)
    print(f"✓ Visit updated")

    # Check audit log
    audit_history = db.get_audit_history(table_name="visits", record_id=saved_visit.id)
    assert len(audit_history) == 2, "Should have 2 audit entries for visit"
    print(f"✓ Audit log created for visit UPDATE")

    # Test 5: Add investigation (INSERT)
    print("\nTest 5: Creating investigation...")
    investigation = Investigation(
        patient_id=saved_patient.id,
        test_name="CBC",
        result="Normal",
        test_date=date.today()
    )
    saved_inv = db.add_investigation(investigation)
    print(f"✓ Investigation created: ID {saved_inv.id}")

    # Test 6: Add procedure (INSERT)
    print("\nTest 6: Creating procedure...")
    procedure = Procedure(
        patient_id=saved_patient.id,
        procedure_name="ECG",
        details="Normal sinus rhythm",
        procedure_date=date.today()
    )
    saved_proc = db.add_procedure(procedure)
    print(f"✓ Procedure created: ID {saved_proc.id}")

    # Test 7: Get patient audit history
    print("\nTest 7: Getting patient audit history...")
    patient_audit = db.get_patient_audit_history(saved_patient.id)
    print(f"✓ Found {len(patient_audit)} audit entries for patient")
    expected_count = 6  # 2 patient + 2 visit + 1 investigation + 1 procedure
    assert len(patient_audit) == expected_count, f"Should have {expected_count} total audit entries"

    # Print audit history
    print("\nFull Audit History:")
    print("-" * 60)
    for i, entry in enumerate(patient_audit, 1):
        print(f"{i}. {entry['timestamp']} | {entry['table_name']} | {entry['operation']}")
        if entry['operation'] == 'INSERT':
            print(f"   Created: {entry['new_value']}")
        elif entry['operation'] == 'UPDATE':
            print(f"   Changed: {entry['old_value']} → {entry['new_value']}")

    # Test 8: Soft delete
    print("\nTest 8: Testing soft delete...")
    db.delete_patient(saved_patient.id)
    print(f"✓ Patient soft deleted")

    # Verify patient is not returned in get_patient
    deleted_patient = db.get_patient(saved_patient.id)
    assert deleted_patient is None, "Deleted patient should not be returned"
    print(f"✓ Deleted patient not returned in queries")

    # Check audit log for DELETE
    audit_history = db.get_audit_history(table_name="patients", record_id=saved_patient.id)
    delete_entry = audit_history[0]  # Most recent
    assert delete_entry['operation'] == 'DELETE', "Should have DELETE entry"
    print(f"✓ Audit log created for DELETE: {delete_entry['old_value']}")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)

    # Cleanup
    os.remove(test_db_path)
    print("✓ Test database cleaned up")

if __name__ == "__main__":
    test_audit_trail()
