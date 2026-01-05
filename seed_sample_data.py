#!/usr/bin/env python3
"""Script to seed DocAssist EMR with sample patient data."""

import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.database import DatabaseService
from src.utils.sample_data import seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for seeding script."""
    logger.info("DocAssist EMR Sample Data Seeder")
    logger.info("=" * 50)

    # Initialize database service
    db_service = DatabaseService()

    # Seed the database
    counts = seed_database(db_service)

    if counts:
        logger.info("\n" + "=" * 50)
        logger.info("Sample data seeded successfully!")
        logger.info("=" * 50)
        logger.info(f"Created {counts['patients']} patients with:")
        logger.info(f"  - {counts['visits']} visits")
        logger.info(f"  - {counts['investigations']} investigations")
        logger.info(f"  - {counts['procedures']} procedures")
        logger.info("\nYou can now launch the EMR app to see the sample data.")
    else:
        logger.info("Database already contains data. No seeding performed.")
        logger.info("To reseed, delete data/clinic.db and run this script again.")


if __name__ == "__main__":
    main()
