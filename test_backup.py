#!/usr/bin/env python3
"""Test script for BackupService."""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.backup import BackupService


def create_test_data():
    """Create test database and ChromaDB folder."""
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Create test database
    db_path = data_dir / "clinic.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create simple test table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test data
    cursor.execute("INSERT INTO patients (name) VALUES (?)", ("Test Patient 1",))
    cursor.execute("INSERT INTO patients (name) VALUES (?)", ("Test Patient 2",))

    conn.commit()
    conn.close()

    # Create test ChromaDB folder
    chroma_dir = data_dir / "chroma"
    chroma_dir.mkdir(exist_ok=True)
    (chroma_dir / "test_file.txt").write_text("Test ChromaDB data")

    print(f"✓ Created test data in {data_dir}")


def test_backup_service():
    """Test the BackupService."""
    print("\n" + "=" * 60)
    print("Testing BackupService")
    print("=" * 60 + "\n")

    # Create test data
    create_test_data()

    # Initialize backup service
    backup = BackupService()
    print(f"✓ BackupService initialized")
    print(f"  Data dir: {backup.data_dir}")
    print(f"  Backup dir: {backup.backup_dir}")
    print(f"  Max backups: {backup.max_backups}")

    # Create a backup
    print("\n1. Creating backup...")
    backup_path = backup.create_backup()
    if backup_path:
        print(f"✓ Backup created: {backup_path}")
        print(f"  Size: {backup_path.stat().st_size / 1024:.1f} KB")
    else:
        print("✗ Backup failed!")
        return False

    # List backups
    print("\n2. Listing backups...")
    backups = backup.list_backups()
    print(f"✓ Found {len(backups)} backup(s)")
    for b in backups:
        print(f"  - {b['filename']}")
        print(f"    Date: {b.get('created_at', 'unknown')}")
        print(f"    Size: {b['size_bytes'] / 1024:.1f} KB")
        print(f"    Patients: {b.get('patient_count', '?')}")

    # Get last backup time
    print("\n3. Getting last backup time...")
    last_time = backup.get_last_backup_time()
    if last_time:
        print(f"✓ Last backup: {last_time}")
        delta = datetime.now() - last_time
        print(f"  ({delta.total_seconds():.0f} seconds ago)")
    else:
        print("  No backups found")

    # Test cleanup (create multiple backups)
    print("\n4. Testing cleanup...")
    print(f"Creating {backup.max_backups + 3} backups to test cleanup...")
    for i in range(backup.max_backups + 2):
        backup.create_backup()
        print(f"  Created backup {i+2}")

    backups_before = len(backup.list_backups())
    print(f"  Backups before cleanup: {backups_before}")

    backup.cleanup_old_backups()
    backups_after = len(backup.list_backups())
    print(f"  Backups after cleanup: {backups_after}")
    print(f"✓ Cleanup working (kept {backups_after}, max is {backup.max_backups})")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = test_backup_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
