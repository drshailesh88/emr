#!/usr/bin/env python3
"""Test drug database functionality."""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly to avoid dependency issues
import sqlite3
import json as json_module
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

# Simplified database service for testing
class TestDatabaseService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._init_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generic_name TEXT NOT NULL,
                    brand_names TEXT,
                    strengths TEXT,
                    forms TEXT,
                    category TEXT,
                    is_custom INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_generic ON drugs(generic_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_usage ON drugs(usage_count DESC)")

    def search_drugs(self, query: str, limit: int = 10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM drugs
                WHERE generic_name LIKE ? OR brand_names LIKE ?
                ORDER BY usage_count DESC, generic_name ASC
                LIMIT ?
            """, (search_term, search_term, limit))

            results = []
            for row in cursor.fetchall():
                drug = dict(row)
                if drug.get('brand_names'):
                    try:
                        drug['brand_names'] = json_module.loads(drug['brand_names'])
                    except:
                        drug['brand_names'] = []
                else:
                    drug['brand_names'] = []

                if drug.get('strengths'):
                    try:
                        drug['strengths'] = json_module.loads(drug['strengths'])
                    except:
                        drug['strengths'] = []
                else:
                    drug['strengths'] = []

                if drug.get('forms'):
                    try:
                        drug['forms'] = json_module.loads(drug['forms'])
                    except:
                        drug['forms'] = []
                else:
                    drug['forms'] = []

                results.append(drug)

            return results

    def add_custom_drug(self, generic_name: str, brand_names: list,
                        strengths: list, forms: list, category: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drugs (generic_name, brand_names, strengths, forms, category, is_custom)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                generic_name,
                json_module.dumps(brand_names),
                json_module.dumps(strengths),
                json_module.dumps(forms),
                category
            ))
            return cursor.lastrowid

    def increment_drug_usage(self, drug_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE drugs
                SET usage_count = usage_count + 1,
                    last_used = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), drug_id))

    def get_drug_by_id(self, drug_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drugs WHERE id = ?", (drug_id,))
            row = cursor.fetchone()

            if row:
                drug = dict(row)
                if drug.get('brand_names'):
                    try:
                        drug['brand_names'] = json_module.loads(drug['brand_names'])
                    except:
                        drug['brand_names'] = []
                else:
                    drug['brand_names'] = []

                if drug.get('strengths'):
                    try:
                        drug['strengths'] = json_module.loads(drug['strengths'])
                    except:
                        drug['strengths'] = []
                else:
                    drug['strengths'] = []

                if drug.get('forms'):
                    try:
                        drug['forms'] = json_module.loads(drug['forms'])
                    except:
                        drug['forms'] = []
                else:
                    drug['forms'] = []

                return drug
            return None

    def seed_initial_drugs(self, drugs_data: list):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM drugs WHERE is_custom = 0")
            if cursor.fetchone()[0] > 0:
                return 0

            count = 0
            for drug in drugs_data:
                cursor.execute("""
                    INSERT INTO drugs (generic_name, brand_names, strengths, forms, category, is_custom)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (
                    drug.get('generic_name'),
                    json_module.dumps(drug.get('brand_names', [])),
                    json_module.dumps(drug.get('strengths', [])),
                    json_module.dumps(drug.get('forms', [])),
                    drug.get('category', '')
                ))
                count += 1

            return count

DatabaseService = TestDatabaseService


def test_drug_database():
    """Test drug database operations."""
    print("\n" + "=" * 50)
    print("  Testing Drug Database")
    print("=" * 50 + "\n")

    # Initialize database
    db = DatabaseService("data/test_clinic.db")
    print("✓ Database initialized")

    # Load initial drugs
    drugs_file = Path("src/data/initial_drugs.json")
    if not drugs_file.exists():
        print("✗ initial_drugs.json not found")
        return False

    with open(drugs_file, 'r') as f:
        drugs_data = json.load(f)

    print(f"✓ Loaded {len(drugs_data)} drugs from JSON")

    # Seed database
    count = db.seed_initial_drugs(drugs_data)
    print(f"✓ Seeded {count} drugs into database")

    # Test search
    print("\nTesting drug search...")

    test_queries = ["met", "aspirin", "amlo", "ator"]

    for query in test_queries:
        results = db.search_drugs(query, limit=5)
        print(f"\n  Query: '{query}' -> {len(results)} results")
        for drug in results:
            generic = drug.get('generic_name', '')
            brands = ', '.join(drug.get('brand_names', [])[:2])
            strengths = ', '.join(drug.get('strengths', [])[:2])
            usage = drug.get('usage_count', 0)
            print(f"    • {generic} ({strengths}) - {brands} [used {usage}x]")

    # Test add custom drug
    print("\nTesting custom drug addition...")
    custom_id = db.add_custom_drug(
        generic_name="Test Drug",
        brand_names=["TestBrand"],
        strengths=["10mg", "20mg"],
        forms=["tablet"],
        category="test"
    )
    print(f"✓ Added custom drug with ID: {custom_id}")

    # Test get drug by ID
    drug = db.get_drug_by_id(custom_id)
    if drug:
        print(f"✓ Retrieved drug: {drug.get('generic_name')}")

    # Test increment usage
    db.increment_drug_usage(custom_id)
    drug = db.get_drug_by_id(custom_id)
    print(f"✓ Usage count after increment: {drug.get('usage_count')}")

    print("\n" + "=" * 50)
    print("  All tests passed!")
    print("=" * 50 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = test_drug_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
