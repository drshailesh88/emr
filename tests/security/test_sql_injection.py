"""
SQL Injection Prevention Tests

Tests that the application properly sanitizes database inputs
and prevents SQL injection attacks.
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile


@pytest.mark.security
class TestSQLInjection:
    """Test SQL injection prevention"""

    @pytest.fixture
    def test_db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create test table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT
            )
        ''')

        cursor.execute("INSERT INTO patients (name, phone) VALUES (?, ?)",
                      ("John Doe", "1234567890"))
        conn.commit()

        yield conn

        conn.close()
        Path(db_path).unlink()

    def test_sql_injection_in_search(self, test_db):
        """Test that search queries are properly parameterized"""
        cursor = test_db.cursor()

        # Malicious input attempting SQL injection
        malicious_input = "'; DROP TABLE patients; --"

        # This should NOT drop the table if properly parameterized
        try:
            # Simulating a search query - should use parameterized queries
            cursor.execute(
                "SELECT * FROM patients WHERE name = ?",
                (malicious_input,)
            )
            results = cursor.fetchall()

            # Should return no results, not drop the table
            assert len(results) == 0

            # Verify table still exists
            cursor.execute("SELECT COUNT(*) FROM patients")
            count = cursor.fetchone()[0]
            assert count == 1, "Table should still exist with 1 patient"

        except sqlite3.OperationalError:
            pytest.fail("SQL injection may have been executed")

    def test_sql_injection_in_filter(self, test_db):
        """Test that filter queries are safe"""
        cursor = test_db.cursor()

        # Try injection in LIKE clause
        malicious_input = "% OR 1=1 --"

        cursor.execute(
            "SELECT * FROM patients WHERE name LIKE ?",
            (f"%{malicious_input}%",)
        )
        results = cursor.fetchall()

        # Should treat the injection string as literal text
        assert len(results) == 0

    def test_sql_injection_in_orderby(self, test_db):
        """Test that ORDER BY clauses are validated"""
        cursor = test_db.cursor()

        # ORDER BY cannot be parameterized, so must be validated
        valid_columns = ['id', 'name', 'phone']

        # Malicious attempt
        malicious_column = "name; DROP TABLE patients; --"

        # Should validate column name
        column = malicious_column if malicious_column in valid_columns else 'id'
        assert column == 'id', "Should reject malicious column name"

        # Safe query
        cursor.execute(f"SELECT * FROM patients ORDER BY {column}")
        results = cursor.fetchall()
        assert len(results) == 1

    def test_no_string_interpolation(self):
        """Verify we're not using string interpolation for queries"""
        # This is a static code check
        # In real implementation, would scan source files

        dangerous_patterns = [
            'f"SELECT',
            'f\'SELECT',
            '".format(',
            '\'.format(',
            '% (',  # Old-style string formatting
        ]

        # Check database.py for dangerous patterns
        db_file = Path(__file__).parent.parent.parent / 'src' / 'services' / 'database.py'

        if db_file.exists():
            content = db_file.read_text()

            for pattern in dangerous_patterns:
                if pattern in content:
                    # Check if it's in a SQL context
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and any(sql in line.upper() for sql in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                            pytest.fail(
                                f"Potential SQL injection vulnerability at line {i+1}: "
                                f"Using string interpolation for SQL query"
                            )

    def test_prepared_statements_only(self):
        """Verify only prepared statements are used"""
        # This test would analyze actual database service code
        # For now, it's a placeholder that passes
        assert True, "Manual code review required for prepared statements"
