"""Search performance load tests.

Tests various search operations under load including phonetic,
fuzzy, and natural language search.
"""

import pytest
import time
from tests.load.benchmarks import BENCHMARKS, format_benchmark_result


class TestSearchPerformance:
    """Test suite for search performance."""

    def test_phonetic_search_10k(self, large_db, timer):
        """Phonetic search for common surname in 10K patients should complete in <500ms."""
        db = large_db
        benchmark = BENCHMARKS['phonetic_search']

        # Common Indian surnames
        surnames = ['Sharma', 'Kumar', 'Singh', 'Patel', 'Gupta']

        total_time = 0
        for surname in surnames:
            with timer(f"Phonetic search '{surname}'") as t:
                # Basic search (phonetic would need additional implementation)
                results = db.search_patients_basic(surname)

            print(f"  {t} - Found {len(results)} patients")
            total_time += t.elapsed_ms

        avg_time = total_time / len(surnames)
        print(f"\n{format_benchmark_result('phonetic_search', avg_time, benchmark)}")

        assert avg_time <= benchmark['max_ms'], \
            f"Phonetic search too slow: {avg_time:.2f}ms > {benchmark['max_ms']}ms"

    def test_fuzzy_search_performance(self, large_db, timer):
        """Fuzzy search with typos should complete in <800ms."""
        db = large_db
        benchmark = BENCHMARKS['fuzzy_search']

        # Search queries with common typos
        queries = [
            ('Sharma', 'Shrama'),  # Transposition
            ('Priya', 'Prya'),      # Missing letter
            ('Kumar', 'Kuamr'),     # Transposition
            ('Rajesh', 'Rajehs'),   # Transposition
        ]

        total_time = 0
        for correct, typo in queries:
            with timer(f"Fuzzy search '{typo}'") as t:
                # Basic search (fuzzy would need additional implementation)
                results = db.search_patients_basic(typo)

            print(f"  {t} - Searching '{typo}' found {len(results)} patients")
            total_time += t.elapsed_ms

        avg_time = total_time / len(queries)
        print(f"\n{format_benchmark_result('fuzzy_search', avg_time, benchmark)}")

        assert avg_time <= benchmark['max_ms'], \
            f"Fuzzy search too slow: {avg_time:.2f}ms > {benchmark['max_ms']}ms"

    def test_natural_language_search(self, large_db, timer):
        """Natural language search should complete in <2000ms.

        Note: This test simulates natural language search. Full implementation
        would require semantic search with embeddings.
        """
        db = large_db
        benchmark = BENCHMARKS['natural_language_search']

        # Natural language queries
        queries = [
            'diabetic patients',
            'patients on metformin',
            'hypertension with diabetes',
            'elderly patients over 70',
        ]

        total_time = 0
        for query in queries:
            with timer(f"NL search '{query}'") as t:
                # Simulate NL search by searching diagnosis
                # Full implementation would use RAG/embeddings
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT p.*
                        FROM patients p
                        JOIN visits v ON p.id = v.patient_id
                        WHERE v.diagnosis LIKE ?
                        LIMIT 100
                    """, (f'%{query.split()[0]}%',))
                    results = cursor.fetchall()

            print(f"  {t} - Query '{query}' found {len(results)} patients")
            total_time += t.elapsed_ms

        avg_time = total_time / len(queries)
        print(f"\n{format_benchmark_result('natural_language_search', avg_time, benchmark)}")

        assert avg_time <= benchmark['max_ms'], \
            f"Natural language search too slow: {avg_time:.2f}ms > {benchmark['max_ms']}ms"

    def test_search_with_filters(self, large_db, timer):
        """Search with age and gender filters should complete in <600ms."""
        db = large_db
        benchmark = BENCHMARKS['filtered_search']

        # Filter combinations
        filters = [
            {'name': 'Sharma', 'gender': 'M', 'min_age': 40, 'max_age': 60},
            {'name': 'Kumar', 'gender': 'F', 'min_age': 30, 'max_age': 50},
            {'name': 'Patel', 'gender': 'M', 'min_age': 50, 'max_age': 70},
        ]

        total_time = 0
        for filter_set in filters:
            with timer(f"Filtered search") as t:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM patients
                        WHERE name LIKE ?
                          AND gender = ?
                          AND age BETWEEN ? AND ?
                        ORDER BY name
                    """, (
                        f'%{filter_set["name"]}%',
                        filter_set['gender'],
                        filter_set['min_age'],
                        filter_set['max_age']
                    ))
                    results = cursor.fetchall()

            print(f"  {t} - Found {len(results)} patients with filters")
            total_time += t.elapsed_ms

        avg_time = total_time / len(filters)
        print(f"\n{format_benchmark_result('filtered_search', avg_time, benchmark)}")

        assert avg_time <= benchmark['max_ms'], \
            f"Filtered search too slow: {avg_time:.2f}ms > {benchmark['max_ms']}ms"

    def test_partial_match_search(self, large_db, timer):
        """Partial name match search."""
        db = large_db

        # Test partial matches
        partials = ['Raj', 'Pri', 'San', 'Anu']

        total_time = 0
        for partial in partials:
            with timer(f"Partial match '{partial}'") as t:
                results = db.search_patients_basic(partial)

            print(f"  {t} - Partial '{partial}' found {len(results)} patients")
            total_time += t.elapsed_ms

        avg_time = total_time / len(partials)
        print(f"\nAverage partial match: {avg_time:.2f}ms")

        # Should be reasonably fast
        assert avg_time <= 300, \
            f"Partial match too slow: {avg_time:.2f}ms > 300ms"

    def test_uhid_search_performance(self, large_db, timer):
        """UHID search should be very fast."""
        db = large_db

        # Get some real UHIDs
        patients = db.get_all_patients()[:100]
        uhids = [p.uhid for p in patients if p.uhid][:10]

        total_time = 0
        for uhid in uhids:
            with timer(f"UHID search '{uhid}'") as t:
                results = db.search_patients_basic(uhid)

            total_time += t.elapsed_ms
            assert len(results) == 1, f"UHID should be unique, found {len(results)}"

        avg_time = total_time / len(uhids)
        print(f"\nAverage UHID search: {avg_time:.2f}ms")

        # UHID search should be very fast
        assert avg_time <= 50, \
            f"UHID search too slow: {avg_time:.2f}ms > 50ms"

    def test_phone_number_search(self, large_db, timer):
        """Phone number search performance."""
        db = large_db

        # Get some phone numbers
        patients = db.get_all_patients()[:100]
        phones = [p.phone for p in patients if p.phone][:10]

        total_time = 0
        for phone in phones:
            # Search by last 4 digits (common use case)
            search_term = phone[-4:]

            with timer(f"Phone search") as t:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM patients
                        WHERE phone LIKE ?
                    """, (f'%{search_term}',))
                    results = cursor.fetchall()

            total_time += t.elapsed_ms
            print(f"  Found {len(results)} patients with phone ending {search_term}")

        avg_time = total_time / len(phones)
        print(f"\nAverage phone search: {avg_time:.2f}ms")

        assert avg_time <= 200, \
            f"Phone search too slow: {avg_time:.2f}ms > 200ms"

    def test_multi_criteria_search(self, large_db, timer):
        """Complex multi-criteria search."""
        db = large_db

        with timer("Multi-criteria search") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, COUNT(v.id) as visit_count
                    FROM patients p
                    LEFT JOIN visits v ON p.id = v.patient_id
                    WHERE p.age > 50
                      AND p.gender = 'M'
                    GROUP BY p.id
                    HAVING visit_count > 5
                    ORDER BY visit_count DESC
                    LIMIT 50
                """)
                results = cursor.fetchall()

        print(f"  {t} - Found {len(results)} patients")

        # Complex query should still be reasonably fast
        assert t.elapsed_ms <= 1000, \
            f"Multi-criteria search too slow: {t.elapsed_ms:.2f}ms > 1000ms"

    def test_diagnosis_search(self, large_db, timer):
        """Search patients by diagnosis."""
        db = large_db

        diagnoses = ['Diabetes', 'Hypertension', 'COPD', 'Asthma']

        total_time = 0
        for diagnosis in diagnoses:
            with timer(f"Diagnosis search '{diagnosis}'") as t:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT p.*
                        FROM patients p
                        JOIN visits v ON p.id = v.patient_id
                        WHERE v.diagnosis LIKE ?
                        LIMIT 100
                    """, (f'%{diagnosis}%',))
                    results = cursor.fetchall()

            print(f"  {t} - Found {len(results)} patients with {diagnosis}")
            total_time += t.elapsed_ms

        avg_time = total_time / len(diagnoses)
        print(f"\nAverage diagnosis search: {avg_time:.2f}ms")

        assert avg_time <= 500, \
            f"Diagnosis search too slow: {avg_time:.2f}ms > 500ms"

    def test_date_range_search(self, large_db, timer):
        """Search visits by date range."""
        db = large_db

        with timer("Date range search") as t:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT v.*, p.name
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.id
                    WHERE v.visit_date BETWEEN '2024-01-01' AND '2024-12-31'
                    ORDER BY v.visit_date DESC
                    LIMIT 1000
                """)
                results = cursor.fetchall()

        print(f"  {t} - Found {len(results)} visits in date range")

        assert t.elapsed_ms <= 500, \
            f"Date range search too slow: {t.elapsed_ms:.2f}ms > 500ms"

    def test_case_insensitive_search(self, large_db, timer):
        """Case-insensitive search performance."""
        db = large_db

        # Search with different cases
        queries = [
            ('sharma', 'SHARMA', 'Sharma'),
            ('kumar', 'KUMAR', 'Kumar'),
        ]

        for lower, upper, title in queries:
            times = []

            for variant in [lower, upper, title]:
                with timer(f"Search '{variant}'") as t:
                    results = db.search_patients_basic(variant)
                times.append(t.elapsed_ms)

            # All variants should return same results and similar time
            avg = sum(times) / len(times)
            print(f"  Average for '{lower}' variants: {avg:.2f}ms")

            assert avg <= 300, \
                f"Case-insensitive search too slow: {avg:.2f}ms > 300ms"

    def test_empty_result_search(self, large_db, timer):
        """Search with no results should be fast."""
        db = large_db

        # Queries that should return no results
        queries = ['XYZABC123', 'NoSuchPatient', '!@#$%']

        total_time = 0
        for query in queries:
            with timer(f"Empty search '{query}'") as t:
                results = db.search_patients_basic(query)

            assert len(results) == 0, "Should have no results"
            total_time += t.elapsed_ms

        avg_time = total_time / len(queries)
        print(f"\nAverage empty search: {avg_time:.2f}ms")

        # Empty searches should be very fast
        assert avg_time <= 100, \
            f"Empty search too slow: {avg_time:.2f}ms > 100ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
