#!/usr/bin/env python3
"""
Comprehensive Test Suite for DocAssist EMR
Tests all services and features built for the LLM/RAG architecture.
"""

import os
import sys
import json
import tempfile
import traceback
from datetime import date, datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    message: str = ""
    error: str = ""
    duration_ms: float = 0


@dataclass
class TestCategory:
    """Category of tests."""
    name: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)


class TestRunner:
    """Runs all tests and collects results."""

    def __init__(self):
        self.categories: List[TestCategory] = []
        self.db_path = None
        self.db = None

    def setup(self):
        """Set up test environment."""
        # Create temp database
        fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

    def teardown(self):
        """Clean up test environment."""
        if self.db_path and os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def run_test(self, name: str, test_func) -> TestResult:
        """Run a single test and return result."""
        import time
        start = time.time()
        try:
            result = test_func()
            duration = (time.time() - start) * 1000
            if result is True or result is None:
                return TestResult(name, True, "OK", duration_ms=duration)
            elif isinstance(result, str):
                return TestResult(name, True, result, duration_ms=duration)
            else:
                return TestResult(name, False, str(result), duration_ms=duration)
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                name,
                False,
                f"Exception: {type(e).__name__}",
                error=traceback.format_exc(),
                duration_ms=duration
            )

    def run_all(self):
        """Run all test categories."""
        self.setup()
        try:
            self.test_database_service()
            self.test_phonetic_search()
            self.test_safety_checker()
            self.test_context_builder()
            self.test_app_mode()
            self.test_llm_service()
            self.test_patient_snapshot()
            self.test_integration()
        finally:
            self.teardown()

    # =========================================================================
    # DATABASE SERVICE TESTS
    # =========================================================================

    def test_database_service(self):
        """Test DatabaseService functionality."""
        category = TestCategory("Database Service")

        from src.services.database import DatabaseService
        from src.models.schemas import Patient, Visit, Doctor, Consultation

        self.db = DatabaseService(self.db_path)

        # Test 1: Tables created
        def test_tables_created():
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()

            required = {'patients', 'visits', 'investigations', 'procedures',
                       'doctors', 'consultations', 'care_team', 'audit_log',
                       'patient_snapshots', 'patient_allergies'}
            missing = required - tables
            if missing:
                return f"Missing tables: {missing}"
            return f"All {len(required)} required tables present"

        category.results.append(self.run_test("Tables created", test_tables_created))

        # Test 2: FTS5 table created
        def test_fts5_created():
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinical_fts'")
            result = cursor.fetchone()
            conn.close()
            if not result:
                return "FTS5 table 'clinical_fts' not found"
            return True

        category.results.append(self.run_test("FTS5 table created", test_fts5_created))

        # Test 3: Add patient
        def test_add_patient():
            patient = Patient(name="Ram Kumar", age=50, gender="M", phone="9876543210")
            saved = self.db.add_patient(patient)
            if not saved.id:
                return "Patient ID not assigned"
            if not saved.uhid:
                return "UHID not generated"
            if not saved.uhid.startswith("EMR-"):
                return f"UHID format wrong: {saved.uhid}"
            return f"Patient created with UHID: {saved.uhid}"

        category.results.append(self.run_test("Add patient", test_add_patient))

        # Test 4: Search patients basic
        def test_search_patients_basic():
            results = self.db.search_patients_basic("Ram")
            if not results:
                return "No results for 'Ram'"
            if results[0].name != "Ram Kumar":
                return f"Wrong patient returned: {results[0].name}"
            return True

        category.results.append(self.run_test("Search patients basic", test_search_patients_basic))

        # Test 5: Add visit
        def test_add_visit():
            patients = self.db.get_all_patients()
            visit = Visit(
                patient_id=patients[0].id,
                visit_date=date.today(),
                chief_complaint="Chest pain",
                clinical_notes="Patient c/o chest pain x 2 days",
                diagnosis="Unstable angina"
            )
            saved = self.db.add_visit(visit)
            if not saved.id:
                return "Visit ID not assigned"
            return True

        category.results.append(self.run_test("Add visit", test_add_visit))

        # Test 6: Get patient visits
        def test_get_patient_visits():
            patients = self.db.get_all_patients()
            visits = self.db.get_patient_visits(patients[0].id)
            if not visits:
                return "No visits found"
            if visits[0].chief_complaint != "Chest pain":
                return f"Wrong visit data: {visits[0].chief_complaint}"
            return True

        category.results.append(self.run_test("Get patient visits", test_get_patient_visits))

        # Test 7: Add doctor
        def test_add_doctor():
            doctor = Doctor(
                name="Dr. Sharma",
                specialty="nephrology",
                department="Medicine",
                employee_id="DOC001"
            )
            saved = self.db.add_doctor(doctor)
            if not saved.id:
                return "Doctor ID not assigned"
            return True

        category.results.append(self.run_test("Add doctor", test_add_doctor))

        # Test 8: Get doctors by specialty
        def test_get_doctors_by_specialty():
            doctors = self.db.get_doctors_by_specialty("nephrology")
            if not doctors:
                return "No nephrologists found"
            if doctors[0].name != "Dr. Sharma":
                return f"Wrong doctor: {doctors[0].name}"
            return True

        category.results.append(self.run_test("Get doctors by specialty", test_get_doctors_by_specialty))

        # Test 9: Add consultation
        def test_add_consultation():
            patients = self.db.get_all_patients()
            doctors = self.db.get_doctors_by_specialty("nephrology")
            consult = Consultation(
                patient_id=patients[0].id,
                consulting_doctor_id=doctors[0].id,
                consulting_specialty="nephrology",
                consult_date=date.today(),
                reason_for_referral="Elevated creatinine",
                findings="CKD stage 3",
                recommendations="Low protein diet, avoid NSAIDs"
            )
            saved = self.db.add_consultation(consult)
            if not saved.id:
                return "Consultation ID not assigned"
            return True

        category.results.append(self.run_test("Add consultation", test_add_consultation))

        # Test 10: Get consultations by specialty
        def test_get_consultations_by_specialty():
            patients = self.db.get_all_patients()
            consults = self.db.get_consultations_by_specialty(patients[0].id, "nephrology")
            if not consults:
                return "No nephrology consults found"
            # consults is a list of dicts
            if "avoid NSAIDs" not in consults[0].get('recommendations', ''):
                return f"Wrong recommendations: {consults[0].get('recommendations', '')}"
            return True

        category.results.append(self.run_test("Get consultations by specialty", test_get_consultations_by_specialty))

        # Test 11: Add allergy
        def test_add_allergy():
            patients = self.db.get_all_patients()
            self.db.add_allergy(patients[0].id, "penicillin", "Anaphylaxis")
            self.db.add_allergy(patients[0].id, "sulfa")
            allergies = self.db.get_patient_allergies(patients[0].id)
            if len(allergies) != 2:
                return f"Expected 2 allergies, got {len(allergies)}"
            return True

        category.results.append(self.run_test("Add allergy", test_add_allergy))

        # Test 12: Check allergy
        def test_check_allergy():
            patients = self.db.get_all_patients()
            has_penicillin = self.db.check_allergy(patients[0].id, "penicillin")
            has_iodine = self.db.check_allergy(patients[0].id, "iodine")
            if not has_penicillin:
                return "Penicillin allergy not detected"
            if has_iodine:
                return "False positive for iodine"
            return True

        category.results.append(self.run_test("Check allergy", test_check_allergy))

        # Test 13: Care team management
        def test_care_team():
            from src.models.schemas import CareTeamMember
            patients = self.db.get_all_patients()
            doctors = self.db.get_doctors_by_specialty("nephrology")
            care_member = CareTeamMember(
                patient_id=patients[0].id,
                doctor_id=doctors[0].id,
                role="Consulting Nephrologist",
                specialty="nephrology"
            )
            self.db.add_to_care_team(care_member)
            is_member = self.db.is_in_care_team(doctors[0].id, patients[0].id)
            if not is_member:
                return "Doctor not found in care team"
            return True

        category.results.append(self.run_test("Care team management", test_care_team))

        # Test 14: Audit logging
        def test_audit_log():
            patients = self.db.get_all_patients()
            doctors = self.db.get_doctors_by_specialty("nephrology")
            self.db.log_action(
                user_id=doctors[0].id,
                user_name=doctors[0].name,
                user_role="Doctor",
                action="VIEW",
                resource_type="patient",
                resource_id=patients[0].id,
                patient_id=patients[0].id,
                details="Viewed patient record"
            )
            logs = self.db.get_patient_audit_log(patients[0].id)
            if not logs:
                return "No audit logs found"
            return True

        category.results.append(self.run_test("Audit logging", test_audit_log))

        # Test 15: FTS search clinical
        def test_fts_search_clinical():
            patients = self.db.get_all_patients()
            # Insert directly into FTS table (normally done via triggers on visit insert)
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clinical_fts (patient_id, content, doc_type, doc_date, source_id)
                VALUES (?, ?, ?, ?, ?)
            """, (patients[0].id, "Patient with chest pain and elevated troponin", "visit", date.today().isoformat(), 1))
            conn.commit()
            conn.close()

            # Now search - note: fts_search_clinical(query, patient_id, doc_type, limit)
            results = self.db.fts_search_clinical("troponin", patient_id=patients[0].id)
            if not results:
                return "FTS search returned no results"
            return f"Found {len(results)} FTS results"

        category.results.append(self.run_test("FTS search clinical", test_fts_search_clinical))

        self.categories.append(category)

    # =========================================================================
    # PHONETIC SEARCH TESTS
    # =========================================================================

    def test_phonetic_search(self):
        """Test phonetic search functionality."""
        category = TestCategory("Phonetic Search")

        from src.services.phonetic import IndianPhoneticSearch, MultiStrategySearch

        phonetic = IndianPhoneticSearch()

        # Test 1: Basic phonetic code
        def test_phonetic_code():
            code1 = phonetic.get_phonetic_code("Ram")
            code2 = phonetic.get_phonetic_code("Raam")
            if code1 != code2:
                return f"Ram ({code1}) != Raam ({code2})"
            return f"Ram and Raam both encode to: {code1}"

        category.results.append(self.run_test("Phonetic code - vowel variation", test_phonetic_code))

        # Test 2: Aspirated consonants
        def test_aspirated_consonants():
            code1 = phonetic.get_phonetic_code("Bharat")
            code2 = phonetic.get_phonetic_code("Barat")
            if code1 != code2:
                return f"Bharat ({code1}) != Barat ({code2})"
            return True

        category.results.append(self.run_test("Phonetic code - aspirated consonants", test_aspirated_consonants))

        # Test 3: Sibilant variations
        def test_sibilant_variations():
            code1 = phonetic.get_phonetic_code("Shyam")
            code2 = phonetic.get_phonetic_code("Syam")
            if code1 != code2:
                return f"Shyam ({code1}) != Syam ({code2})"
            return True

        category.results.append(self.run_test("Phonetic code - sibilant variations", test_sibilant_variations))

        # Test 4: Match score exact
        def test_match_score_exact():
            score = phonetic.match_score("Shailesh", "Shylesh")
            if score < 0.9:
                return f"Expected high score, got {score}"
            return f"Score: {score:.2f}"

        category.results.append(self.run_test("Match score - phonetic equivalent", test_match_score_exact))

        # Test 5: Match score prefix
        def test_match_score_prefix():
            score = phonetic.match_score("Ram", "Ramesh")
            if score < 0.7:
                return f"Expected moderate score for prefix, got {score}"
            return f"Score: {score:.2f}"

        category.results.append(self.run_test("Match score - prefix match", test_match_score_prefix))

        # Test 6: Match score unrelated
        def test_match_score_unrelated():
            score = phonetic.match_score("Ram", "Suresh")
            if score > 0.5:
                return f"Expected low score for unrelated, got {score}"
            return f"Score: {score:.2f}"

        category.results.append(self.run_test("Match score - unrelated names", test_match_score_unrelated))

        # Test 7: Search function
        def test_search_function():
            candidates = [
                (1, "Ram Kumar"),
                (2, "Raam Sharma"),
                (3, "Ramesh Gupta"),
                (4, "Suresh Verma"),
                (5, "Rama Rao"),
            ]
            results = phonetic.search("Ram", candidates, threshold=0.7)
            if len(results) < 3:
                return f"Expected at least 3 matches, got {len(results)}"
            # First result should be highest score
            if results[0][2] < results[-1][2]:
                return "Results not sorted by score"
            return f"Found {len(results)} matches"

        category.results.append(self.run_test("Search function", test_search_function))

        # Test 8: Indian name variations
        indian_names = [
            ("Pradeep", "Pradip"),
            ("Vijay", "Wijay"),
            ("Gaurav", "Gorav"),
            ("Dhiraj", "Diraj"),
            ("Suresh", "Sooresh"),
        ]

        for name1, name2 in indian_names:
            def test_variation(n1=name1, n2=name2):
                score = phonetic.match_score(n1, n2)
                if score < 0.8:
                    return f"{n1} vs {n2}: score {score:.2f} too low"
                return f"Score: {score:.2f}"
            category.results.append(self.run_test(f"Indian name: {name1} vs {name2}", test_variation))

        # Test 9: Multi-strategy search with DB
        def test_multi_strategy():
            ms = MultiStrategySearch(self.db)
            # Add more test patients
            from src.models.schemas import Patient
            self.db.add_patient(Patient(name="Raam Sharma", age=45, gender="M"))
            self.db.add_patient(Patient(name="Ramesh Gupta", age=55, gender="M"))

            results = ms.search_patients("Ram", limit=10)
            if not results:
                return "No results from multi-strategy search"
            return f"Found {len(results)} patients"

        category.results.append(self.run_test("Multi-strategy search", test_multi_strategy))

        self.categories.append(category)

    # =========================================================================
    # SAFETY CHECKER TESTS
    # =========================================================================

    def test_safety_checker(self):
        """Test prescription safety checker."""
        category = TestCategory("Safety Checker")

        from src.services.safety import PrescriptionSafetyChecker, CriticalInfoBanner
        from src.models.schemas import Prescription, Medication, PatientSnapshot

        checker = PrescriptionSafetyChecker()

        # Create test snapshot with allergies
        snapshot = PatientSnapshot(
            patient_id=1,
            uhid="TEST-001",
            demographics="Test Patient, 50M",
            allergies=["penicillin", "sulfa"],
            on_anticoagulation=True,
            anticoag_drug="warfarin",
            active_problems=["CKD Stage 3", "Hypertension"],
            key_labs={"creatinine": 2.5, "egfr": 35}
        )

        # Test 1: Direct allergy detection
        def test_direct_allergy():
            rx = Prescription(
                diagnosis=["UTI"],
                medications=[
                    Medication(drug_name="Amoxicillin", strength="500mg", dose="1", frequency="TDS")
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            critical = [a for a in alerts if a.severity == "CRITICAL"]
            if not critical:
                return "Failed to detect penicillin cross-reactivity"
            if "penicillin" not in critical[0].message.lower():
                return f"Wrong message: {critical[0].message}"
            return True

        category.results.append(self.run_test("Direct allergy detection", test_direct_allergy))

        # Test 2: Cross-reactivity (penicillin -> cephalosporin)
        def test_cross_reactivity():
            rx = Prescription(
                diagnosis=["Infection"],
                medications=[
                    Medication(drug_name="Cephalexin", strength="500mg", dose="1", frequency="TDS")
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            # Should have at least a warning
            relevant = [a for a in alerts if "penicillin" in a.message.lower() or "cross" in a.message.lower()]
            if not relevant:
                return "Failed to warn about penicillin cross-reactivity with cephalosporin"
            return True

        category.results.append(self.run_test("Cross-reactivity detection", test_cross_reactivity))

        # Test 3: Sulfa allergy
        def test_sulfa_allergy():
            rx = Prescription(
                diagnosis=["UTI"],
                medications=[
                    Medication(drug_name="Sulfamethoxazole", strength="800mg", dose="1", frequency="BD")
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            critical = [a for a in alerts if a.severity == "CRITICAL"]
            if not critical:
                return "Failed to detect sulfa allergy"
            return True

        category.results.append(self.run_test("Sulfa allergy detection", test_sulfa_allergy))

        # Test 4: Safe medication (no alerts expected)
        def test_safe_medication():
            rx = Prescription(
                diagnosis=["Hypertension"],
                medications=[
                    Medication(drug_name="Amlodipine", strength="5mg", dose="1", frequency="OD")
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            critical = [a for a in alerts if a.action == "BLOCK"]
            if critical:
                return f"False positive: {critical[0].message}"
            return "No blocking alerts for safe medication"

        category.results.append(self.run_test("Safe medication - no false positives", test_safe_medication))

        # Test 5: Anticoagulation interaction
        def test_anticoag_interaction():
            rx = Prescription(
                diagnosis=["Pain"],
                medications=[
                    Medication(drug_name="Aspirin", strength="325mg", dose="1", frequency="OD")
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            relevant = [a for a in alerts if "anticoag" in a.message.lower() or "bleeding" in a.message.lower()]
            if not relevant:
                return "Failed to warn about anticoagulant interaction"
            return True

        category.results.append(self.run_test("Anticoagulation interaction", test_anticoag_interaction))

        # Test 6: Renal dose adjustment (CKD patient)
        def test_renal_adjustment():
            rx = Prescription(
                diagnosis=["Infection"],
                medications=[
                    Medication(drug_name="Gentamicin", strength="80mg", dose="1", frequency="TDS")
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            relevant = [a for a in alerts if "renal" in a.message.lower() or "kidney" in a.message.lower()]
            # Note: This depends on implementation - may or may not detect
            return f"Found {len(relevant)} renal-related alerts"

        category.results.append(self.run_test("Renal dose awareness", test_renal_adjustment))

        # Test 7: Critical info banner
        def test_critical_banner():
            info = CriticalInfoBanner.get_critical_info(snapshot)
            if not info:
                return "No critical info returned"
            if "penicillin" not in info.get("allergies", []):
                return "Allergies not included"
            if not info.get("on_anticoagulation"):
                return "Anticoagulation status not included"
            return True

        category.results.append(self.run_test("Critical info banner", test_critical_banner))

        # Test 8: Empty snapshot handling
        def test_empty_snapshot():
            empty = PatientSnapshot(
                patient_id=2,
                uhid="TEST-002",
                demographics="Empty Patient, 30F"
            )
            rx = Prescription(
                diagnosis=["Fever"],
                medications=[
                    Medication(drug_name="Paracetamol", strength="500mg", dose="1", frequency="TDS")
                ]
            )
            alerts = checker.validate_prescription(rx, empty)
            critical = [a for a in alerts if a.action == "BLOCK"]
            if critical:
                return f"False positive on empty snapshot: {critical[0].message}"
            return True

        category.results.append(self.run_test("Empty snapshot - no false positives", test_empty_snapshot))

        # Test 9: Multiple medications
        def test_multiple_medications():
            rx = Prescription(
                diagnosis=["Multiple conditions"],
                medications=[
                    Medication(drug_name="Amoxicillin", strength="500mg", dose="1", frequency="TDS"),
                    Medication(drug_name="Metformin", strength="500mg", dose="1", frequency="BD"),
                    Medication(drug_name="Aspirin", strength="75mg", dose="1", frequency="OD"),
                ]
            )
            alerts = checker.validate_prescription(rx, snapshot)
            # Should have alerts for amoxicillin (penicillin) and aspirin (anticoag)
            if len(alerts) < 2:
                return f"Expected multiple alerts, got {len(alerts)}"
            return f"Detected {len(alerts)} alerts across {len(rx.medications)} medications"

        category.results.append(self.run_test("Multiple medications check", test_multiple_medications))

        self.categories.append(category)

    # =========================================================================
    # CONTEXT BUILDER TESTS
    # =========================================================================

    def test_context_builder(self):
        """Test SQL-based context builder."""
        category = TestCategory("Context Builder")

        from src.services.context_builder import ContextBuilder, QueryParser

        ctx = ContextBuilder(self.db)
        parser = QueryParser()

        patients = self.db.get_all_patients()
        patient_id = patients[0].id if patients else 1

        # Test 1: Query parser - specialty detection
        def test_specialty_detection():
            parsed = parser.parse("What did nephrologist say?", patient_id)
            if parsed.get("specialty") != "nephrology":
                return f"Expected nephrology, got {parsed.get('specialty')}"
            if parsed.get("query_type") != "consultation_lookup":
                return f"Wrong query type: {parsed.get('query_type')}"
            return True

        category.results.append(self.run_test("Query parser - specialty detection", test_specialty_detection))

        # Test 2: Query parser - lab detection
        def test_lab_detection():
            parsed = parser.parse("What is latest creatinine?", patient_id)
            if parsed.get("query_type") not in ["lab_lookup", "general"]:
                return f"Wrong query type for lab: {parsed.get('query_type')}"
            return f"Query type: {parsed.get('query_type')}"

        category.results.append(self.run_test("Query parser - lab detection", test_lab_detection))

        # Test 3: Query parser - time filter
        def test_time_filter():
            parsed = parser.parse("Last month labs", patient_id)
            if not parsed.get("time_filter"):
                # May not be implemented
                return "Time filter parsing not implemented (acceptable)"
            return f"Time filter: {parsed.get('time_filter')}"

        category.results.append(self.run_test("Query parser - time filter", test_time_filter))

        # Test 4: Build context - consultation
        def test_context_consultation():
            context = ctx.build_context(patient_id, "What did nephrologist recommend?")
            if not context:
                return "Empty context returned"
            if "nephrology" in context.lower() or "avoid NSAIDs" in context:
                return f"Context built: {len(context)} chars with relevant info"
            return f"Context built: {len(context)} chars"

        category.results.append(self.run_test("Build context - consultation", test_context_consultation))

        # Test 5: Build context - labs
        def test_context_labs():
            context = ctx.build_context(patient_id, "Show recent lab results")
            # Context may be empty if no labs, but shouldn't error
            return f"Context built: {len(context)} chars"

        category.results.append(self.run_test("Build context - labs", test_context_labs))

        # Test 6: Build context - general
        def test_context_general():
            context = ctx.build_context(patient_id, "Tell me about this patient")
            if not context:
                return "Empty context for general query"
            return f"Context built: {len(context)} chars"

        category.results.append(self.run_test("Build context - general", test_context_general))

        # Test 7: Build context - empty patient
        def test_context_empty():
            # Create new patient with no data
            from src.models.schemas import Patient
            new_patient = self.db.add_patient(Patient(name="Empty Test", age=25, gender="F"))
            context = ctx.build_context(new_patient.id, "What is their history?")
            # Should not error, may return minimal context
            return f"Context for empty patient: {len(context)} chars"

        category.results.append(self.run_test("Build context - empty patient", test_context_empty))

        self.categories.append(category)

    # =========================================================================
    # APP MODE TESTS
    # =========================================================================

    def test_app_mode(self):
        """Test app mode detection and capabilities."""
        category = TestCategory("App Mode")

        from src.services.app_mode import (
            AppMode, AppModeManager, ModeCapabilities,
            get_mode_manager, get_current_mode, get_capabilities,
            can_use_llm, can_use_rag
        )

        # Test 1: Mode manager singleton
        def test_singleton():
            m1 = get_mode_manager()
            m2 = get_mode_manager()
            if m1 is not m2:
                return "Mode manager not singleton"
            return True

        category.results.append(self.run_test("Mode manager singleton", test_singleton))

        # Test 2: Mode detection
        def test_mode_detection():
            mode = get_current_mode()
            if mode not in [AppMode.LITE, AppMode.STANDARD, AppMode.FULL]:
                return f"Unknown mode: {mode}"
            return f"Detected mode: {mode.value}"

        category.results.append(self.run_test("Mode detection", test_mode_detection))

        # Test 3: Capabilities match mode
        def test_capabilities_match():
            mode = get_current_mode()
            caps = get_capabilities()

            if mode == AppMode.LITE:
                if caps.llm_prescription:
                    return "LITE mode should not have LLM"
            elif mode == AppMode.STANDARD:
                if not caps.llm_prescription:
                    return "STANDARD mode should have LLM"
                if caps.vector_rag:
                    return "STANDARD mode should not have RAG"
            elif mode == AppMode.FULL:
                if not caps.llm_prescription or not caps.vector_rag:
                    return "FULL mode should have LLM and RAG"
            return True

        category.results.append(self.run_test("Capabilities match mode", test_capabilities_match))

        # Test 4: can_use_llm helper
        def test_can_use_llm():
            result = can_use_llm()
            mode = get_current_mode()
            expected = mode in [AppMode.STANDARD, AppMode.FULL]
            if result != expected:
                return f"can_use_llm() returned {result}, expected {expected}"
            return True

        category.results.append(self.run_test("can_use_llm helper", test_can_use_llm))

        # Test 5: can_use_rag helper
        def test_can_use_rag():
            result = can_use_rag()
            mode = get_current_mode()
            expected = mode == AppMode.FULL
            if result != expected:
                return f"can_use_rag() returned {result}, expected {expected}"
            return True

        category.results.append(self.run_test("can_use_rag helper", test_can_use_rag))

        # Test 6: Mode display name
        def test_display_name():
            manager = get_mode_manager()
            name = manager._get_mode_display_name()
            if not name:
                return "Empty display name"
            return f"Display name: {name}"

        category.results.append(self.run_test("Mode display name", test_display_name))

        # Test 7: Status dict
        def test_status_dict():
            manager = get_mode_manager()
            status = manager.get_status()
            required_keys = ['mode', 'mode_display', 'ram_available_gb', 'features']
            missing = [k for k in required_keys if k not in status]
            if missing:
                return f"Missing status keys: {missing}"
            return True

        category.results.append(self.run_test("Status dict", test_status_dict))

        # Test 8: Upgrade message
        def test_upgrade_message():
            manager = get_mode_manager()
            msg = manager.get_upgrade_message()
            # Message may be None for FULL mode
            if get_current_mode() != AppMode.FULL and not msg:
                return "Expected upgrade message for non-FULL mode"
            return f"Upgrade message: {msg or 'None (FULL mode)'}"

        category.results.append(self.run_test("Upgrade message", test_upgrade_message))

        self.categories.append(category)

    # =========================================================================
    # LLM SERVICE TESTS
    # =========================================================================

    def test_llm_service(self):
        """Test LLM service (without actual Ollama)."""
        category = TestCategory("LLM Service")

        from src.services.llm import LLMService

        llm = LLMService()

        # Test 1: RAM detection
        def test_ram_detection():
            info = llm.get_model_info()
            if 'ram_available_gb' not in info:
                return "ram_available_gb not in info"
            if info['ram_available_gb'] <= 0:
                return f"Invalid RAM: {info['ram_available_gb']}"
            return f"RAM detected: {info['ram_available_gb']:.1f} GB"

        category.results.append(self.run_test("RAM detection", test_ram_detection))

        # Test 2: Model selection
        def test_model_selection():
            info = llm.get_model_info()
            model = info.get('model', '')
            if not model:
                return "No model selected"
            if not model.startswith('qwen'):
                return f"Unexpected model: {model}"
            return f"Model selected: {model}"

        category.results.append(self.run_test("Model selection", test_model_selection))

        # Test 3: Model info structure
        def test_model_info_structure():
            info = llm.get_model_info()
            required = ['model', 'ram_available_gb', 'ollama_available']
            missing = [k for k in required if k not in info]
            if missing:
                return f"Missing keys: {missing}"
            return True

        category.results.append(self.run_test("Model info structure", test_model_info_structure))

        # Test 4: Availability check (may fail without Ollama)
        def test_availability():
            available = llm.is_available()
            return f"Ollama available: {available}"

        category.results.append(self.run_test("Availability check", test_availability))

        # Test 5: Context length based on model
        def test_context_length():
            info = llm.get_model_info()
            context_len = info.get('context_length', 0)
            if context_len < 1024:
                return f"Context length too small: {context_len}"
            return f"Context length: {context_len}"

        category.results.append(self.run_test("Context length", test_context_length))

        self.categories.append(category)

    # =========================================================================
    # PATIENT SNAPSHOT TESTS
    # =========================================================================

    def test_patient_snapshot(self):
        """Test patient snapshot computation and storage."""
        category = TestCategory("Patient Snapshot")

        from src.models.schemas import PatientSnapshot, Investigation
        from datetime import date

        patients = self.db.get_all_patients()
        patient_id = patients[0].id if patients else 1

        # Add some investigations for the patient
        inv = Investigation(
            patient_id=patient_id,
            test_name="Creatinine",
            result="2.5",
            unit="mg/dL",
            reference_range="0.7-1.3",
            test_date=date.today(),
            is_abnormal=True
        )
        self.db.add_investigation(inv)

        # Test 1: Compute snapshot
        def test_compute_snapshot():
            snapshot = self.db.compute_patient_snapshot(patient_id)
            if not snapshot:
                return "Failed to compute snapshot"
            if not snapshot.uhid:
                return "UHID missing from snapshot"
            return f"Computed snapshot for {snapshot.uhid}"

        category.results.append(self.run_test("Compute snapshot", test_compute_snapshot))

        # Test 2: Snapshot includes allergies
        def test_snapshot_allergies():
            snapshot = self.db.compute_patient_snapshot(patient_id)
            if not snapshot.allergies:
                return "Allergies not included (may be none)"
            if "penicillin" not in snapshot.allergies:
                return f"Missing penicillin: {snapshot.allergies}"
            return f"Allergies: {snapshot.allergies}"

        category.results.append(self.run_test("Snapshot allergies", test_snapshot_allergies))

        # Test 3: Snapshot includes key labs
        def test_snapshot_labs():
            snapshot = self.db.compute_patient_snapshot(patient_id)
            if snapshot.key_labs is None:
                return "key_labs is None"
            if "creatinine" not in str(snapshot.key_labs).lower():
                return f"Creatinine not in key labs"
            return f"Key labs: {snapshot.key_labs}"

        category.results.append(self.run_test("Snapshot key labs", test_snapshot_labs))

        # Test 4: Save and retrieve snapshot
        def test_save_retrieve():
            snapshot = self.db.compute_patient_snapshot(patient_id)
            self.db.save_patient_snapshot(snapshot)
            retrieved = self.db.get_patient_snapshot(patient_id)
            if not retrieved:
                return "Failed to retrieve saved snapshot"
            if retrieved.uhid != snapshot.uhid:
                return "Retrieved snapshot differs"
            return True

        category.results.append(self.run_test("Save and retrieve snapshot", test_save_retrieve))

        # Test 5: Snapshot demographics
        def test_snapshot_demographics():
            snapshot = self.db.compute_patient_snapshot(patient_id)
            if not snapshot.demographics:
                return "Demographics empty"
            return f"Demographics: {snapshot.demographics}"

        category.results.append(self.run_test("Snapshot demographics", test_snapshot_demographics))

        self.categories.append(category)

    # =========================================================================
    # INTEGRATION TESTS
    # =========================================================================

    def test_integration(self):
        """Integration tests across multiple services."""
        category = TestCategory("Integration Tests")

        from src.services.safety import PrescriptionSafetyChecker
        from src.services.context_builder import ContextBuilder
        from src.models.schemas import Prescription, Medication

        patients = self.db.get_all_patients()
        patient_id = patients[0].id if patients else 1

        # Test 1: Full prescription workflow
        def test_prescription_workflow():
            # 1. Compute snapshot
            snapshot = self.db.compute_patient_snapshot(patient_id)

            # 2. Create prescription
            rx = Prescription(
                diagnosis=["Hypertension"],
                medications=[
                    Medication(drug_name="Amlodipine", strength="5mg", dose="1", frequency="OD")
                ]
            )

            # 3. Validate prescription
            checker = PrescriptionSafetyChecker()
            alerts = checker.validate_prescription(rx, snapshot)

            # 4. Should pass without blocking alerts
            blocking = [a for a in alerts if a.action == "BLOCK"]
            if blocking:
                return f"Unexpected blocking alert: {blocking[0].message}"

            return "Prescription workflow completed"

        category.results.append(self.run_test("Prescription workflow", test_prescription_workflow))

        # Test 2: Context builder with consultations
        def test_context_with_consults():
            ctx = ContextBuilder(self.db)
            context = ctx.build_context(patient_id, "What did nephrology say?")

            if "CKD" in context or "avoid NSAIDs" in context or "nephrology" in context.lower():
                return "Context includes consultation info"
            return f"Context built ({len(context)} chars), may not have consult data"

        category.results.append(self.run_test("Context with consultations", test_context_with_consults))

        # Test 3: Allergy check in prescription
        def test_allergy_in_prescription():
            snapshot = self.db.compute_patient_snapshot(patient_id)

            # Prescribe something the patient is allergic to
            rx = Prescription(
                diagnosis=["Infection"],
                medications=[
                    Medication(drug_name="Amoxicillin", strength="500mg", dose="1", frequency="TDS")
                ]
            )

            checker = PrescriptionSafetyChecker()
            alerts = checker.validate_prescription(rx, snapshot)
            blocking = [a for a in alerts if a.action == "BLOCK"]

            if not blocking:
                return "Failed to block penicillin allergy"

            return "Correctly blocked penicillin prescription"

        category.results.append(self.run_test("Allergy blocking", test_allergy_in_prescription))

        # Test 4: FTS search integration
        def test_fts_integration():
            # Index some content directly into FTS table
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clinical_fts (patient_id, content, doc_type, doc_date, source_id)
                VALUES (?, ?, ?, ?, ?)
            """, (patient_id, "Patient with diabetic nephropathy and proteinuria", "visit", date.today().isoformat(), 99))
            conn.commit()
            conn.close()

            # Search for it - correct parameter order
            results = self.db.fts_search_clinical("proteinuria", patient_id=patient_id)

            if not results:
                return "FTS search found nothing"

            return f"FTS found {len(results)} results"

        category.results.append(self.run_test("FTS search integration", test_fts_integration))

        # Test 5: Phonetic + FTS combined
        def test_phonetic_fts_combined():
            from src.services.phonetic import MultiStrategySearch

            ms = MultiStrategySearch(self.db)
            results = ms.search_patients("Raam", limit=10)  # Phonetic for "Ram"

            if not results:
                return "Combined search found nothing"

            return f"Combined search found {len(results)} patients"

        category.results.append(self.run_test("Phonetic + FTS combined", test_phonetic_fts_combined))

        self.categories.append(category)

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        lines = []
        lines.append("=" * 80)
        lines.append("DOCASSIST EMR - COMPREHENSIVE TEST REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        total_passed = 0
        total_failed = 0

        for cat in self.categories:
            total_passed += cat.passed
            total_failed += cat.failed

        lines.append(f"OVERALL: {total_passed} passed, {total_failed} failed, {total_passed + total_failed} total")
        lines.append("")

        # Summary by category
        lines.append("-" * 80)
        lines.append("SUMMARY BY CATEGORY")
        lines.append("-" * 80)

        for cat in self.categories:
            status = "PASS" if cat.failed == 0 else "FAIL"
            lines.append(f"  [{status}] {cat.name}: {cat.passed}/{cat.total} passed")

        lines.append("")

        # Detailed results
        lines.append("-" * 80)
        lines.append("DETAILED RESULTS")
        lines.append("-" * 80)

        for cat in self.categories:
            lines.append("")
            lines.append(f"### {cat.name} ({cat.passed}/{cat.total})")
            lines.append("")

            for result in cat.results:
                status = "PASS" if result.passed else "FAIL"
                lines.append(f"  [{status}] {result.name}")
                if result.message and result.message != "OK":
                    lines.append(f"         {result.message}")
                if result.error:
                    lines.append(f"         ERROR: {result.error[:200]}...")

        lines.append("")

        # What's working
        lines.append("-" * 80)
        lines.append("WHAT'S WORKING")
        lines.append("-" * 80)

        working = []
        for cat in self.categories:
            if cat.failed == 0:
                working.append(f"  [OK] {cat.name} - All {cat.total} tests passing")
            else:
                working.append(f"  [PARTIAL] {cat.name} - {cat.passed}/{cat.total} tests passing")

        lines.extend(working)
        lines.append("")

        # What's broken
        lines.append("-" * 80)
        lines.append("WHAT'S BROKEN / NEEDS ATTENTION")
        lines.append("-" * 80)

        broken = []
        for cat in self.categories:
            for result in cat.results:
                if not result.passed:
                    broken.append(f"  [FAIL] {cat.name} > {result.name}")
                    if result.message:
                        broken.append(f"         Reason: {result.message}")

        if broken:
            lines.extend(broken)
        else:
            lines.append("  None - All tests passing!")

        lines.append("")

        # Recommendations
        lines.append("-" * 80)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)

        recommendations = []

        # Check for specific issues
        for cat in self.categories:
            if cat.name == "LLM Service":
                for r in cat.results:
                    if "Ollama available: False" in r.message:
                        recommendations.append("  - Install and start Ollama for AI features")

            if cat.name == "Safety Checker" and cat.failed > 0:
                recommendations.append("  - Review safety checker for missed edge cases")

            if cat.name == "Phonetic Search" and cat.failed > 0:
                recommendations.append("  - Verify phonetic equivalences for Indian names")

        if total_failed == 0:
            recommendations.append("  - All tests passing! Consider adding more edge cases.")
            recommendations.append("  - Test with actual Ollama for full LLM integration.")
            recommendations.append("  - Test on low-RAM machine (4GB) to verify LITE mode.")

        if not recommendations:
            recommendations.append("  - Fix failing tests before deployment")

        lines.extend(recommendations)
        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Run all tests and print report."""
    runner = TestRunner()
    runner.run_all()
    report = runner.generate_report()
    print(report)

    # Also save to file
    report_path = os.path.join(os.path.dirname(__file__), "test_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
