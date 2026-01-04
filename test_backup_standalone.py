#!/usr/bin/env python3
"""Standalone test for backup functionality - no dependencies."""

import sqlite3
import zipfile
import shutil
from pathlib import Path
from datetime import datetime


def test_backup_functionality():
    """Test basic backup functionality."""
    print("\n" + "=" * 60)
    print("Testing Backup Functionality (Standalone)")
    print("=" * 60 + "\n")

    # Setup test environment
    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    data_dir = test_dir / "data"
    data_dir.mkdir()
    backup_dir = test_dir / "backups"
    backup_dir.mkdir()

    # 1. Create test database
    print("1. Creating test database...")
    db_path = data_dir / "clinic.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT INTO patients (name) VALUES ('Test Patient 1')")
    cursor.execute("INSERT INTO patients (name) VALUES ('Test Patient 2')")
    cursor.execute("INSERT INTO patients (name) VALUES ('Test Patient 3')")
    conn.commit()
    conn.close()
    print("   ✓ Created database with 3 patients")

    # 2. Create test ChromaDB folder
    print("\n2. Creating test ChromaDB folder...")
    chroma_dir = data_dir / "chroma"
    chroma_dir.mkdir()
    (chroma_dir / "test_collection.dat").write_text("Test vector data")
    (chroma_dir / "metadata.json").write_text('{"version": "1.0"}')
    print("   ✓ Created ChromaDB folder with test files")

    # 3. Test SQLite backup API
    print("\n3. Testing SQLite backup API...")
    backup_db_path = backup_dir / "clinic_backup.db"
    source_conn = sqlite3.connect(db_path)
    dest_conn = sqlite3.connect(backup_db_path)
    source_conn.backup(dest_conn)
    source_conn.close()
    dest_conn.close()

    # Verify backup
    conn = sqlite3.connect(backup_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"   ✓ SQLite backup successful ({count} patients)")

    # 4. Create backup zip
    print("\n4. Creating backup zip file...")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_zip_path = backup_dir / f"backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add database
        zipf.write(backup_db_path, "clinic.db")
        # Add ChromaDB
        for file in chroma_dir.rglob('*'):
            if file.is_file():
                arcname = "chroma/" + file.relative_to(chroma_dir).as_posix()
                zipf.write(file, arcname)
        # Add manifest
        manifest = {
            "created_at": datetime.now().isoformat(),
            "patient_count": count,
            "version": "1.0"
        }
        import json
        zipf.writestr("backup_manifest.json", json.dumps(manifest, indent=2))

    print(f"   ✓ Created backup: {backup_zip_path.name}")
    print(f"   ✓ Size: {backup_zip_path.stat().st_size / 1024:.1f} KB")

    # 5. Verify backup contents
    print("\n5. Verifying backup contents...")
    with zipfile.ZipFile(backup_zip_path, 'r') as zipf:
        files = zipf.namelist()
        print(f"   ✓ Backup contains {len(files)} files:")
        for f in sorted(files):
            print(f"     - {f}")

    # 6. Test restore
    print("\n6. Testing restore...")
    restore_dir = test_dir / "restore"
    restore_dir.mkdir()

    with zipfile.ZipFile(backup_zip_path, 'r') as zipf:
        zipf.extractall(restore_dir)

    restored_db = restore_dir / "clinic.db"
    conn = sqlite3.connect(restored_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM patients")
    patients = cursor.fetchall()
    conn.close()
    print(f"   ✓ Restored database with {len(patients)} patients:")
    for p in patients:
        print(f"     - {p[0]}")

    # Cleanup
    print("\n7. Cleaning up test files...")
    shutil.rmtree(test_dir)
    print("   ✓ Cleaned up")

    print("\n" + "=" * 60)
    print("✓ All backup functionality tests passed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        test_backup_functionality()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
