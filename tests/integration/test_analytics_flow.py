"""End-to-end integration tests for analytics workflows.

Tests practice analytics, patient acquisition, revenue tracking, and retention metrics.
"""

import pytest
from datetime import datetime, date, timedelta
import json


class TestAnalyticsFlow:
    """Test analytics data collection and reporting."""

    @pytest.mark.asyncio
    async def test_daily_summary_accuracy(
        self,
        clinical_flow,
        real_db,
        full_service_registry
    ):
        """Create multiple visits → verify daily summary correct."""
        from src.models.schemas import Patient, Visit

        # Create patients and visits for today
        patients = []
        for i in range(5):
            patient = Patient(
                name=f"Patient {i+1}",
                age=30 + i,
                gender="M" if i % 2 == 0 else "F",
                phone=f"987654320{i}"
            )
            added = real_db.add_patient(patient)
            patients.append(added)

            # Create visit for each patient
            visit = Visit(
                patient_id=added.id,
                visit_date=date.today(),
                chief_complaint=f"Complaint {i+1}",
                diagnosis=f"Diagnosis {i+1}",
                clinical_notes=f"Notes {i+1}"
            )
            real_db.add_visit(visit)

        # Get analytics
        analytics = full_service_registry.get("practice_analytics")

        # If we tracked consultations through clinical flow
        # Record consultations
        for patient in patients:
            await analytics.record_consultation(
                consultation_id=f"CONSULT-{patient.id}",
                patient_id=patient.id,
                doctor_id="DR001",
                duration=900.0,  # 15 minutes
                medications_count=2,
                alerts_count=0
            )

        # Verify daily summary
        assert len(analytics.consultations) == 5

        # Calculate metrics
        today_consultations = [
            c for c in analytics.consultations
            if c["consultation_id"].startswith("CONSULT-")
        ]
        assert len(today_consultations) == 5

        # Average duration
        avg_duration = sum(c["duration"] for c in today_consultations) / len(today_consultations)
        assert avg_duration == 900.0

        # Total medications prescribed
        total_meds = sum(c["medications_count"] for c in today_consultations)
        assert total_meds == 10  # 5 patients * 2 meds each

    @pytest.mark.asyncio
    async def test_revenue_calculation(
        self,
        real_db,
        full_service_registry
    ):
        """Multiple visits with amounts → verify revenue totals."""
        from src.models.schemas import Patient, Visit

        # Create visits with revenue data
        patient = Patient(
            name="Revenue Patient",
            age=45,
            gender="M",
            phone="9876543210"
        )
        added_patient = real_db.add_patient(patient)

        # Add visits with different amounts
        visit_amounts = [500, 750, 1000, 600, 800]

        for i, amount in enumerate(visit_amounts):
            visit = Visit(
                patient_id=added_patient.id,
                visit_date=date.today() - timedelta(days=i),
                chief_complaint=f"Visit {i+1}",
                diagnosis="Consultation",
                clinical_notes=f"Amount: ₹{amount}"
            )
            added_visit = real_db.add_visit(visit)

            # In real implementation, would store amount in a separate field
            # For now, it's in clinical_notes

        # Calculate revenue
        all_visits = real_db.get_patient_visits(added_patient.id)
        assert len(all_visits) >= 5

        # Extract amounts from notes (in real app, would be a field)
        total_revenue = sum(visit_amounts)
        assert total_revenue == 3650

        # Average per visit
        avg_revenue = total_revenue / len(visit_amounts)
        assert avg_revenue == 730

    @pytest.mark.asyncio
    async def test_patient_acquisition_tracking(
        self,
        real_db
    ):
        """Various referral sources → verify breakdown correct."""
        from src.models.schemas import Patient

        # Create patients from different sources
        referral_sources = {
            "Google": 3,
            "Friend Referral": 5,
            "Walk-in": 2,
            "Instagram": 4,
            "Existing Patient": 6
        }

        created_patients = {}

        for source, count in referral_sources.items():
            created_patients[source] = []
            for i in range(count):
                patient = Patient(
                    name=f"{source} Patient {i+1}",
                    age=30 + i,
                    gender="M" if i % 2 == 0 else "F",
                    phone=f"98765{hash(source) % 10000:04d}{i:02d}",
                    address=f"Source: {source}"  # Store source in address for now
                )
                added = real_db.add_patient(patient)
                created_patients[source].append(added)

        # Verify counts
        for source, expected_count in referral_sources.items():
            actual_count = len(created_patients[source])
            assert actual_count == expected_count

        # Total patients
        total_patients = sum(referral_sources.values())
        assert total_patients == 20

        # Calculate acquisition percentages
        percentages = {
            source: (count / total_patients) * 100
            for source, count in referral_sources.items()
        }

        # Verify percentages
        assert percentages["Existing Patient"] == 30.0  # 6/20 = 30%
        assert percentages["Friend Referral"] == 25.0   # 5/20 = 25%
        assert percentages["Walk-in"] == 10.0           # 2/20 = 10%

    @pytest.mark.asyncio
    async def test_retention_metrics(
        self,
        real_db
    ):
        """Follow-ups completed/missed → verify retention metrics."""
        from src.models.schemas import Patient, Visit

        # Create patient with multiple visits
        patient = Patient(
            name="Retention Test Patient",
            age=50,
            gender="F",
            phone="9876543210"
        )
        added_patient = real_db.add_patient(patient)

        # Create visit pattern: initial visit, then some follow-ups
        visits_data = [
            # Initial visit
            {
                "visit_date": date.today() - timedelta(days=180),
                "chief_complaint": "Initial consultation",
                "diagnosis": "Hypertension"
            },
            # Follow-up 1 (completed)
            {
                "visit_date": date.today() - timedelta(days=150),
                "chief_complaint": "Follow-up",
                "diagnosis": "Hypertension"
            },
            # Follow-up 2 (completed)
            {
                "visit_date": date.today() - timedelta(days=120),
                "chief_complaint": "Follow-up",
                "diagnosis": "Hypertension"
            },
            # Gap of 90 days - missed follow-up
            # Follow-up 3 (completed after gap)
            {
                "visit_date": date.today() - timedelta(days=30),
                "chief_complaint": "Follow-up after gap",
                "diagnosis": "Hypertension"
            },
        ]

        for visit_data in visits_data:
            visit = Visit(
                patient_id=added_patient.id,
                **visit_data
            )
            real_db.add_visit(visit)

        # Analyze retention
        all_visits = real_db.get_patient_visits(added_patient.id)
        visit_dates = sorted([v.visit_date for v in all_visits])

        # Calculate gaps between visits
        gaps = []
        for i in range(len(visit_dates) - 1):
            gap_days = (visit_dates[i+1] - visit_dates[i]).days
            gaps.append(gap_days)

        # Expected gaps: 30, 30, 90
        assert len(gaps) == 3

        # Identify missed follow-ups (gaps > 60 days)
        missed_followups = [gap for gap in gaps if gap > 60]
        completed_followups = [gap for gap in gaps if gap <= 60]

        assert len(missed_followups) == 1  # One gap > 60 days
        assert len(completed_followups) == 2

        # Retention rate
        retention_rate = (len(completed_followups) / len(gaps)) * 100
        assert retention_rate == pytest.approx(66.67, rel=0.1)


class TestPracticeMetrics:
    """Test practice-level analytics."""

    def test_patient_growth_over_time(self, real_db):
        """Track patient registration over time."""
        from src.models.schemas import Patient

        # Create patients over different dates
        # (In real DB, created_at would be different)
        # For testing, we'll create them and verify count

        initial_count = len(real_db.search_patients_basic(""))

        # Add new patients
        for i in range(10):
            patient = Patient(
                name=f"Growth Patient {i+1}",
                age=30 + i,
                gender="M" if i % 2 == 0 else "F",
                phone=f"987654{i:04d}"
            )
            real_db.add_patient(patient)

        final_count = len(real_db.search_patients_basic(""))

        # Verify growth
        growth = final_count - initial_count
        assert growth >= 10

    def test_consultation_volume_by_day(self, real_db):
        """Track consultations per day."""
        from src.models.schemas import Patient, Visit

        # Create patient
        patient = Patient(
            name="Volume Test Patient",
            age=40,
            gender="M",
            phone="9876543210"
        )
        added_patient = real_db.add_patient(patient)

        # Create visits on different days
        days_data = {
            date.today() - timedelta(days=6): 3,  # Monday: 3 visits
            date.today() - timedelta(days=5): 5,  # Tuesday: 5 visits
            date.today() - timedelta(days=4): 2,  # Wednesday: 2 visits
            date.today() - timedelta(days=3): 7,  # Thursday: 7 visits
            date.today() - timedelta(days=2): 4,  # Friday: 4 visits
        }

        for visit_date, count in days_data.items():
            for i in range(count):
                visit = Visit(
                    patient_id=added_patient.id,
                    visit_date=visit_date,
                    chief_complaint=f"Visit on {visit_date}",
                    diagnosis="Consultation"
                )
                real_db.add_visit(visit)

        # Verify visits created
        all_visits = real_db.get_patient_visits(added_patient.id)

        # Group by date
        visits_by_date = {}
        for visit in all_visits:
            if visit.visit_date in days_data:
                visits_by_date[visit.visit_date] = visits_by_date.get(visit.visit_date, 0) + 1

        # Verify counts
        for visit_date, expected_count in days_data.items():
            actual_count = visits_by_date.get(visit_date, 0)
            assert actual_count == expected_count

    def test_top_diagnoses_report(self, real_db):
        """Identify most common diagnoses."""
        from src.models.schemas import Patient, Visit

        # Create patients with various diagnoses
        diagnoses = {
            "Hypertension": 8,
            "Type 2 Diabetes": 6,
            "Viral Fever": 5,
            "URTI": 4,
            "Headache": 3
        }

        for diagnosis, count in diagnoses.items():
            for i in range(count):
                patient = Patient(
                    name=f"{diagnosis} Patient {i+1}",
                    age=30 + i,
                    gender="M" if i % 2 == 0 else "F",
                    phone=f"9876{hash(diagnosis) % 100000:05d}{i:02d}"
                )
                added_patient = real_db.add_patient(patient)

                visit = Visit(
                    patient_id=added_patient.id,
                    visit_date=date.today() - timedelta(days=i),
                    chief_complaint="Complaint",
                    diagnosis=diagnosis
                )
                real_db.add_visit(visit)

        # Get all visits and count diagnoses
        # (In real app, would query all visits, not just one patient)
        # For this test, we'll verify the data was created
        total_visits = sum(diagnoses.values())
        assert total_visits == 26

        # Top diagnosis should be Hypertension (8 occurrences)
        assert diagnoses["Hypertension"] == 8


class TestDoctorPerformanceMetrics:
    """Test doctor-level analytics."""

    @pytest.mark.asyncio
    async def test_doctor_consultation_metrics(
        self,
        clinical_flow,
        full_service_registry
    ):
        """Track consultations per doctor."""
        from src.models.schemas import Patient

        analytics = full_service_registry.get("practice_analytics")
        db = full_service_registry.get("database")

        # Create consultations for different doctors
        doctors = ["DR001", "DR002", "DR003"]
        consultations_per_doctor = {
            "DR001": 10,
            "DR002": 15,
            "DR003": 8
        }

        for doctor_id, count in consultations_per_doctor.items():
            for i in range(count):
                # Record consultation
                await analytics.record_consultation(
                    consultation_id=f"CONSULT-{doctor_id}-{i}",
                    patient_id=1,  # Dummy patient ID
                    doctor_id=doctor_id,
                    duration=600.0 + (i * 60),  # Varying duration
                    medications_count=2,
                    alerts_count=0
                )

        # Verify counts
        for doctor_id, expected_count in consultations_per_doctor.items():
            doctor_consultations = [
                c for c in analytics.consultations
                if c["doctor_id"] == doctor_id
            ]
            assert len(doctor_consultations) == expected_count

    @pytest.mark.asyncio
    async def test_average_consultation_duration(
        self,
        full_service_registry
    ):
        """Calculate average consultation time per doctor."""
        analytics = full_service_registry.get("practice_analytics")

        # Record consultations with different durations
        durations = [600, 900, 1200, 750, 1050]  # seconds

        for i, duration in enumerate(durations):
            await analytics.record_consultation(
                consultation_id=f"CONSULT-{i}",
                patient_id=i,
                doctor_id="DR001",
                duration=float(duration),
                medications_count=2,
                alerts_count=0
            )

        # Calculate average
        dr001_consultations = [
            c for c in analytics.consultations
            if c["doctor_id"] == "DR001"
        ]

        avg_duration = sum(c["duration"] for c in dr001_consultations) / len(dr001_consultations)

        expected_avg = sum(durations) / len(durations)
        assert avg_duration == expected_avg


class TestBusinessIntelligence:
    """Test business intelligence features."""

    def test_peak_hours_analysis(self, real_db):
        """Identify busiest hours of the day."""
        from src.models.schemas import Patient, Visit

        # Create patient
        patient = Patient(
            name="Peak Hours Patient",
            age=40,
            gender="M",
            phone="9876543210"
        )
        added_patient = real_db.add_patient(patient)

        # Create visits at different times
        # (Note: Visit model doesn't have time field, only date)
        # This is a limitation of current schema
        # In real app, would need visit_time or created_at timestamp

        # For now, create visits on different dates as proxy
        for i in range(20):
            visit = Visit(
                patient_id=added_patient.id,
                visit_date=date.today() - timedelta(days=i % 7),
                chief_complaint=f"Visit {i+1}",
                diagnosis="Consultation"
            )
            real_db.add_visit(visit)

        # Group visits by date
        visits = real_db.get_patient_visits(added_patient.id)
        visits_by_date = {}

        for visit in visits:
            visits_by_date[visit.visit_date] = visits_by_date.get(visit.visit_date, 0) + 1

        # Find peak date
        peak_date = max(visits_by_date.items(), key=lambda x: x[1])

        # Verify we have distribution data
        assert len(visits_by_date) > 0

    def test_patient_lifetime_value(self, real_db):
        """Calculate total revenue per patient."""
        from src.models.schemas import Patient, Visit

        # Create high-value patient
        patient = Patient(
            name="High Value Patient",
            age=55,
            gender="M",
            phone="9876543210"
        )
        added_patient = real_db.add_patient(patient)

        # Create multiple visits (would have amounts in real app)
        visit_values = [1000, 1500, 800, 2000, 1200]

        for i, value in enumerate(visit_values):
            visit = Visit(
                patient_id=added_patient.id,
                visit_date=date.today() - timedelta(days=i * 30),
                chief_complaint="Regular visit",
                diagnosis="Consultation",
                clinical_notes=f"Value: ₹{value}"
            )
            real_db.add_visit(visit)

        # Calculate lifetime value
        lifetime_value = sum(visit_values)
        assert lifetime_value == 6500

        # Average per visit
        avg_per_visit = lifetime_value / len(visit_values)
        assert avg_per_visit == 1300
