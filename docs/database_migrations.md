# Database Migration System

## Overview

The database migration system in `/home/user/emr/src/services/database.py` provides version-controlled schema evolution for the SQLite database.

## Current Schema Version

**Version 1**: Initial schema with patients, visits, investigations, and procedures tables.

## How It Works

1. **Schema Version Tracking**: The `schema_versions` table stores each applied migration with a timestamp.

2. **Automatic Migration**: When `DatabaseService` is initialized:
   - Creates `schema_versions` table if it doesn't exist
   - Checks current schema version
   - Applies any pending migrations in sequence
   - Updates version after each successful migration

3. **Migration Safety**: Migrations run only once. Subsequent initializations skip already-applied migrations.

## Adding a New Migration

To add a new migration (e.g., adding an email column to patients table):

### Step 1: Increment SCHEMA_VERSION

```python
class DatabaseService:
    # Current schema version
    SCHEMA_VERSION = 2  # Increment from 1 to 2
```

### Step 2: Create Migration Function

```python
def _migration_v2(self):
    """Add email column to patients table."""
    logger.info("Running migration v2: Add email to patients")
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE patients ADD COLUMN email TEXT")
```

### Step 3: Register Migration

```python
@property
def _migrations(self):
    """Map of version numbers to migration functions."""
    return {
        1: self._migration_v1,
        2: self._migration_v2,  # Add new migration
    }
```

### Step 4: Test

The migration will run automatically on next initialization. Always test:
- Fresh database (no prior migrations)
- Existing database (with earlier versions)
- Multiple consecutive migrations

## Example Migration: Add Email Field

```python
# In database.py

SCHEMA_VERSION = 2

def _migration_v2(self):
    """Add email field to patients - v2."""
    logger.info("Adding email column to patients table (v2)")
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE patients ADD COLUMN email TEXT")
        # Create index if needed
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email)")

@property
def _migrations(self):
    return {
        1: self._migration_v1,
        2: self._migration_v2,
    }
```

## Migration Best Practices

1. **Never Modify Existing Migrations**: Once deployed, migrations should never be changed.
2. **Always Increment Version**: Each schema change requires a new version number.
3. **Test Thoroughly**: Test migrations on:
   - Empty databases
   - Databases with existing data
   - Multiple version jumps (e.g., v1 → v3)
4. **Use Transactions**: Migrations run within the connection context manager, which provides automatic rollback on errors.
5. **Log Everything**: Use `logger.info()` to track migration progress.
6. **Keep Migrations Small**: Each migration should represent a single logical change.

## Current Migrations

### Migration v1 (Initial Schema)
- Creates `patients` table
- Creates `visits` table
- Creates `investigations` table
- Creates `procedures` table
- Creates indexes on patient_id foreign keys and patient name

### Migration v2 (Placeholder)
- Sample placeholder for future use
- Currently does nothing
- Uncomment in `_migrations` dict when ready to apply

## Checking Schema Version

```python
from src.services.database import DatabaseService

db = DatabaseService()
version = db._get_schema_version()
print(f"Current schema version: {version}")
```

## Troubleshooting

### Migration Failed Mid-Way
- Check logs for error details
- The `schema_versions` table shows which migrations succeeded
- Failed migrations will be retried on next initialization

### Database Locked
- Ensure no other processes are accessing the database
- Close all connections before running migrations

### Testing Migrations
- Use temporary databases for testing
- See `/home/user/emr/tests/services/test_database.py::TestDatabaseMigrations` for examples
