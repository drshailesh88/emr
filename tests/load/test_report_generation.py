"""Report generation performance tests.

Tests report generation and data export operations under load.
"""

import pytest
import time
import json
from datetime import datetime, date, timedelta
from tests.load.benchmarks import BENCHMARKS, format_benchmark_result


class TestReportPerformance:
    """Test suite for report generation performance."""

    def test_daily_summary_calculation(self, large_db, timer):
        """Calculate daily summary should complete in <3s."""
        db = large_db
        benchmark = BENCHMARKS['daily_summary']

        target_date = date.today()

        with timer("Daily summary calculation") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Patients seen today
                cursor.execute("""
                    SELECT COUNT(DISTINCT patient_id)
                    FROM visits
                    WHERE visit_date = ?
                """, (target_date,))
                patients_seen = cursor.fetchone()[0]

                # Total visits today
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM visits
                    WHERE visit_date = ?
                """, (target_date,))
                total_visits = cursor.fetchone()[0]

                # Common diagnoses today
                cursor.execute("""
                    SELECT diagnosis, COUNT(*) as count
                    FROM visits
                    WHERE visit_date = ?
                    GROUP BY diagnosis
                    ORDER BY count DESC
                    LIMIT 10
                """, (target_date,))
                top_diagnoses = cursor.fetchall()

        summary = {
            'date': str(target_date),
            'patients_seen': patients_seen,
            'total_visits': total_visits,
            'top_diagnoses': [{'diagnosis': d[0], 'count': d[1]} for d in top_diagnoses]
        }

        print(f"  {t}")
        print(f"  Patients seen: {patients_seen}")
        print(f"  Total visits: {total_visits}")
        print(f"\n{format_benchmark_result('daily_summary', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Daily summary too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_monthly_analytics(self, large_db, timer):
        """Generate monthly analytics should complete in <15s."""
        db = large_db
        benchmark = BENCHMARKS['monthly_analytics']

        # Calculate for last month
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        with timer("Monthly analytics") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Total patients
                cursor.execute("""
                    SELECT COUNT(DISTINCT patient_id)
                    FROM visits
                    WHERE visit_date BETWEEN ? AND ?
                """, (start_date, end_date))
                total_patients = cursor.fetchone()[0]

                # Total visits
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM visits
                    WHERE visit_date BETWEEN ? AND ?
                """, (start_date, end_date))
                total_visits = cursor.fetchone()[0]

                # Age distribution
                cursor.execute("""
                    SELECT
                        CASE
                            WHEN p.age < 18 THEN 'Child'
                            WHEN p.age < 45 THEN 'Adult'
                            WHEN p.age < 65 THEN 'Middle Age'
                            ELSE 'Elderly'
                        END as age_group,
                        COUNT(DISTINCT p.id) as count
                    FROM patients p
                    JOIN visits v ON p.id = v.patient_id
                    WHERE v.visit_date BETWEEN ? AND ?
                    GROUP BY age_group
                """, (start_date, end_date))
                age_distribution = cursor.fetchall()

                # Gender distribution
                cursor.execute("""
                    SELECT p.gender, COUNT(DISTINCT p.id) as count
                    FROM patients p
                    JOIN visits v ON p.id = v.patient_id
                    WHERE v.visit_date BETWEEN ? AND ?
                    GROUP BY p.gender
                """, (start_date, end_date))
                gender_distribution = cursor.fetchall()

                # Top diagnoses
                cursor.execute("""
                    SELECT diagnosis, COUNT(*) as count
                    FROM visits
                    WHERE visit_date BETWEEN ? AND ?
                      AND diagnosis IS NOT NULL
                    GROUP BY diagnosis
                    ORDER BY count DESC
                    LIMIT 20
                """, (start_date, end_date))
                top_diagnoses = cursor.fetchall()

        analytics = {
            'period': f"{start_date} to {end_date}",
            'total_patients': total_patients,
            'total_visits': total_visits,
            'age_distribution': dict(age_distribution),
            'gender_distribution': dict(gender_distribution),
            'top_diagnoses': top_diagnoses[:10]
        }

        print(f"  {t}")
        print(f"  Patients: {total_patients}, Visits: {total_visits}")
        print(f"\n{format_benchmark_result('monthly_analytics', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Monthly analytics too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_audit_trail_export(self, large_db, timer):
        """Export audit trail for 1 year should complete in <30s.

        Note: This simulates audit trail by using visit timestamps.
        Full implementation would have dedicated audit table.
        """
        db = large_db
        benchmark = BENCHMARKS['audit_trail_export']

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        with timer("Audit trail export (1 year)") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Get all changes in the period
                cursor.execute("""
                    SELECT
                        'visit' as record_type,
                        v.id as record_id,
                        v.patient_id,
                        p.name as patient_name,
                        v.created_at,
                        'created' as action
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.id
                    WHERE v.created_at BETWEEN ? AND ?
                    ORDER BY v.created_at DESC
                """, (start_date, end_date))

                audit_records = cursor.fetchall()

        print(f"  {t} - Exported {len(audit_records)} audit records")
        print(f"\n{format_benchmark_result('audit_trail_export', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Audit trail export too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_pdf_prescription_generation(self, medium_db, timer):
        """Generate single PDF prescription should complete in <1s.

        Note: This tests the data preparation. Actual PDF generation
        would be tested separately.
        """
        db = medium_db
        benchmark = BENCHMARKS['pdf_prescription_generation']

        # Get a patient with visits
        patients = db.get_all_patients()
        patient = patients[0]
        visits = db.get_patient_visits(patient.id)

        assert len(visits) > 0, "Patient should have visits"
        visit = visits[0]

        with timer("PDF data preparation") as t:
            # Prepare all data needed for PDF
            prescription_data = {
                'patient': {
                    'name': patient.name,
                    'uhid': patient.uhid,
                    'age': patient.age,
                    'gender': patient.gender,
                    'phone': patient.phone
                },
                'visit': {
                    'date': visit.visit_date,
                    'complaint': visit.chief_complaint,
                    'diagnosis': visit.diagnosis
                },
                'prescription': {}
            }

            # Parse prescription JSON
            if visit.prescription_json:
                prescription_data['prescription'] = json.loads(visit.prescription_json)

        print(f"  {t}")
        print(f"\n{format_benchmark_result('pdf_prescription_generation', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"PDF preparation too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_bulk_pdf_generation(self, medium_db, timer):
        """Generate 100 PDF prescriptions should complete in <60s."""
        db = medium_db
        benchmark = BENCHMARKS['bulk_pdf_generation']

        # Get visits to generate PDFs for
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, p.name, p.uhid, p.age, p.gender, p.phone
                FROM visits v
                JOIN patients p ON v.patient_id = p.id
                LIMIT 100
            """)
            visit_records = cursor.fetchall()

        with timer("Bulk PDF preparation (100)") as t:
            pdf_data_list = []

            for record in visit_records:
                # Prepare data for each PDF
                data = {
                    'patient': {
                        'name': record['name'],
                        'uhid': record['uhid'],
                        'age': record['age'],
                        'gender': record['gender'],
                        'phone': record['phone']
                    },
                    'visit': {
                        'date': record['visit_date'],
                        'complaint': record['chief_complaint'],
                        'diagnosis': record['diagnosis']
                    }
                }

                if record['prescription_json']:
                    data['prescription'] = json.loads(record['prescription_json'])

                pdf_data_list.append(data)

        print(f"  {t} - Prepared {len(pdf_data_list)} PDFs")
        print(f"\n{format_benchmark_result('bulk_pdf_generation', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Bulk PDF preparation too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_patient_history_report(self, heavy_patient_db, timer):
        """Generate complete patient history report."""
        db = heavy_patient_db

        # Get a patient with heavy history
        patients = db.get_all_patients()
        patient = patients[0]

        with timer("Patient history report") as t:
            # Get all patient data
            visits = db.get_patient_visits(patient.id)
            investigations = db.get_patient_investigations(patient.id)
            procedures = db.get_patient_procedures(patient.id)

            # Compile report
            report = {
                'patient': {
                    'name': patient.name,
                    'uhid': patient.uhid,
                    'age': patient.age,
                    'gender': patient.gender
                },
                'summary': {
                    'total_visits': len(visits),
                    'total_investigations': len(investigations),
                    'total_procedures': len(procedures),
                    'first_visit': visits[-1].visit_date if visits else None,
                    'last_visit': visits[0].visit_date if visits else None
                },
                'visits': visits,
                'investigations': investigations,
                'procedures': procedures
            }

        print(f"  {t}")
        print(f"  Visits: {len(visits)}, Investigations: {len(investigations)}, Procedures: {len(procedures)}")

        # Should complete in reasonable time even for heavy patient
        assert t.elapsed_ms <= 2000, \
            f"Patient history report too slow: {t.elapsed_ms:.2f}ms > 2000ms"

    def test_diagnosis_frequency_report(self, large_db, timer):
        """Generate diagnosis frequency report."""
        db = large_db

        with timer("Diagnosis frequency report") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        diagnosis,
                        COUNT(*) as frequency,
                        COUNT(DISTINCT patient_id) as unique_patients,
                        MIN(visit_date) as first_seen,
                        MAX(visit_date) as last_seen
                    FROM visits
                    WHERE diagnosis IS NOT NULL
                    GROUP BY diagnosis
                    ORDER BY frequency DESC
                    LIMIT 50
                """)
                results = cursor.fetchall()

        print(f"  {t} - Generated report for {len(results)} diagnoses")

        assert t.elapsed_ms <= 1000, \
            f"Diagnosis report too slow: {t.elapsed_ms:.2f}ms > 1000ms"

    def test_revenue_report(self, medium_db, timer):
        """Generate revenue report (simulated)."""
        db = medium_db

        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        with timer("Revenue report") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Count visits by type
                cursor.execute("""
                    SELECT
                        DATE(visit_date) as visit_day,
                        COUNT(*) as visit_count
                    FROM visits
                    WHERE visit_date BETWEEN ? AND ?
                    GROUP BY visit_day
                    ORDER BY visit_day
                """, (start_date, end_date))
                daily_visits = cursor.fetchall()

                # Simulate revenue calculation (₹500 per visit)
                total_revenue = sum(count * 500 for _, count in daily_visits)

        print(f"  {t}")
        print(f"  Total revenue (simulated): ₹{total_revenue:,}")

        assert t.elapsed_ms <= 1000, \
            f"Revenue report too slow: {t.elapsed_ms:.2f}ms > 1000ms"

    def test_patient_growth_report(self, large_db, timer):
        """Generate patient growth over time report."""
        db = large_db

        with timer("Patient growth report") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Patients registered by month
                cursor.execute("""
                    SELECT
                        strftime('%Y-%m', created_at) as month,
                        COUNT(*) as new_patients
                    FROM patients
                    GROUP BY month
                    ORDER BY month
                """)
                monthly_growth = cursor.fetchall()

                # Calculate cumulative
                cumulative = 0
                growth_data = []
                for month, count in monthly_growth:
                    cumulative += count
                    growth_data.append({
                        'month': month,
                        'new_patients': count,
                        'total_patients': cumulative
                    })

        print(f"  {t} - Generated growth data for {len(growth_data)} months")

        assert t.elapsed_ms <= 500, \
            f"Growth report too slow: {t.elapsed_ms:.2f}ms > 500ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
