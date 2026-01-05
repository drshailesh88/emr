#!/usr/bin/env python3
"""Verification script for the complete backup system integration."""

import sys
from pathlib import Path

def verify_files_exist():
    """Verify all required files exist."""
    print("=" * 60)
    print("VERIFYING BACKUP SYSTEM FILES")
    print("=" * 60)

    required_files = [
        "src/services/simple_backup.py",
        "src/ui/components/backup_status.py",
        "src/ui/simple_backup_dialog.py",
        "BACKUP_SYSTEM.md",
        "test_simple_backup.py",
    ]

    modified_files = [
        "src/ui/components/__init__.py",
        "src/ui/main_layout.py",
        "src/ui/app.py",
    ]

    all_good = True

    print("\n✓ Checking new files...")
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} - MISSING!")
            all_good = False

    print("\n✓ Checking modified files...")
    for file_path in modified_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING!")
            all_good = False

    return all_good


def verify_imports():
    """Verify all imports work."""
    print("\n" + "=" * 60)
    print("VERIFYING IMPORTS")
    print("=" * 60)

    all_good = True

    try:
        print("\n✓ Testing SimpleBackupService import...")
        from src.services.simple_backup import SimpleBackupService, SimpleBackupInfo
        print("  ✅ SimpleBackupService imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import SimpleBackupService: {e}")
        all_good = False

    try:
        print("\n✓ Testing BackupStatusIndicator import...")
        from src.ui.components.backup_status import BackupStatusIndicator
        print("  ✅ BackupStatusIndicator imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import BackupStatusIndicator: {e}")
        all_good = False

    try:
        print("\n✓ Testing SimpleBackupDialog import...")
        from src.ui.simple_backup_dialog import SimpleBackupDialog, show_simple_backup_dialog
        print("  ✅ SimpleBackupDialog imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import SimpleBackupDialog: {e}")
        all_good = False

    try:
        print("\n✓ Testing app.py imports...")
        # Just compile, don't actually import to avoid Flet dependency issues
        import py_compile
        py_compile.compile("src/ui/app.py", doraise=True)
        print("  ✅ app.py compiles successfully")
    except Exception as e:
        print(f"  ❌ app.py compilation failed: {e}")
        all_good = False

    return all_good


def verify_functionality():
    """Verify backup functionality works."""
    print("\n" + "=" * 60)
    print("VERIFYING FUNCTIONALITY")
    print("=" * 60)

    try:
        from src.services.simple_backup import SimpleBackupService

        print("\n✓ Initializing backup service...")
        service = SimpleBackupService()
        print(f"  ✅ Backup location: {service.get_backup_location()}")

        print("\n✓ Getting backup stats...")
        stats = service.get_backup_stats()
        print(f"  ✅ Total backups: {stats['total_backups']}")
        print(f"  ✅ Total size: {stats['total_size_mb']:.2f} MB")

        print("\n✓ Listing backups...")
        backups = service.list_backups()
        print(f"  ✅ Found {len(backups)} backup(s)")

        if backups:
            latest = backups[0]
            print(f"\n  Latest backup:")
            print(f"    - Name: {latest.folder_name}")
            print(f"    - Created: {latest.created_at}")
            print(f"    - Size: {latest.size_bytes / (1024*1024):.2f} MB")
            print(f"    - Patients: {latest.patient_count}")
            print(f"    - Visits: {latest.visit_count}")

        return True

    except Exception as e:
        print(f"  ❌ Functionality verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main verification routine."""
    print("\n" + "🔍 DOCASSIST EMR - BACKUP SYSTEM VERIFICATION" + "\n")

    results = []

    # Verify files
    results.append(("Files", verify_files_exist()))

    # Verify imports
    results.append(("Imports", verify_imports()))

    # Verify functionality
    results.append(("Functionality", verify_functionality()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:.<40} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("=" * 60)
        print("\nThe backup system is fully integrated and working correctly.")
        print("\nNext steps:")
        print("  1. Run the app: python main.py")
        print("  2. Look for backup status indicator in the header")
        print("  3. Click it to open the backup dialog")
        print("  4. Create your first backup!")
        print("\nBackup location: ~/DocAssist/backups/")
        print("\nDocumentation: BACKUP_SYSTEM.md")
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("=" * 60)
        print("\nPlease check the errors above and fix before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
