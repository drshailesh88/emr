#!/usr/bin/env python3
"""Test script for simple backup service."""

import logging
from pathlib import Path
from src.services.simple_backup import SimpleBackupService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_simple_backup():
    """Test simple backup functionality."""
    logger.info("=== Testing Simple Backup Service ===")

    # Initialize service
    backup_service = SimpleBackupService()
    logger.info(f"Backup location: {backup_service.get_backup_location()}")

    # Get stats
    stats = backup_service.get_backup_stats()
    logger.info(f"Current stats: {stats}")

    # List existing backups
    backups = backup_service.list_backups()
    logger.info(f"Found {len(backups)} existing backups")

    for backup in backups:
        logger.info(f"  - {backup.folder_name}")
        logger.info(f"    Created: {backup.created_at}")
        logger.info(f"    Size: {backup.size_bytes / (1024*1024):.2f} MB")
        logger.info(f"    Patients: {backup.patient_count}, Visits: {backup.visit_count}")

    # Test creating a new backup
    logger.info("\n=== Creating new backup ===")

    def progress_callback(message, percent):
        logger.info(f"[{percent}%] {message}")

    backup_path = backup_service.create_backup(progress_callback=progress_callback)

    if backup_path:
        logger.info(f"\n✅ Backup created successfully: {backup_path}")

        # List backups again
        backups = backup_service.list_backups()
        logger.info(f"\nNow have {len(backups)} backups")

        # Get last backup time
        last_backup = backup_service.get_last_backup_time()
        logger.info(f"Last backup: {last_backup}")
    else:
        logger.error("\n❌ Backup failed!")

    # Test backup stats
    stats = backup_service.get_backup_stats()
    logger.info(f"\nFinal stats:")
    logger.info(f"  Total backups: {stats['total_backups']}")
    logger.info(f"  Total size: {stats['total_size_mb']:.2f} MB")
    logger.info(f"  Location: {stats['backup_location']}")

    logger.info("\n=== Test Complete ===")


if __name__ == "__main__":
    test_simple_backup()
