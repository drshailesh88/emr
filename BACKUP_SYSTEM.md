# DocAssist EMR - Local Backup System

## Overview

DocAssist EMR now includes a **bulletproof local backup system** designed specifically for medical records where **data loss is unacceptable**. The system is simple, reliable, and works entirely offline without requiring encryption passwords or cloud services.

## Features

✅ **Simple & Fast** - No encryption complexity, just direct file copies
✅ **Automatic Safety Backups** - Creates safety backup before any restore
✅ **Cross-Platform** - Works on Windows, Mac, and Linux
✅ **Timestamped Backups** - Easy to identify when each backup was created
✅ **Automatic Cleanup** - Keeps only the N most recent backups (default: 5)
✅ **Progress Tracking** - Real-time feedback during backup/restore
✅ **Database Integrity Checks** - Detects corruption and offers to restore
✅ **Auto-Backup on Close** - Optional backup when closing the app

## What Gets Backed Up?

Each backup includes:
- **clinic.db** - Main SQLite database (patients, visits, prescriptions)
- **chroma/** - Vector embeddings for AI search (if exists)
- **prescriptions/** - Generated PDF prescriptions (if exists)
- **settings.json** - App settings and preferences
- **backup_manifest.json** - Metadata about the backup

## Backup Location

Default backup location: `~/DocAssist/backups/`

This can be changed from the backup dialog to any folder you prefer (e.g., external drive, network share).

## Backup Naming Convention

Backups are named with timestamps for easy identification:

```
backup_2026-01-05_14-30-00/
  ├── clinic.db
  ├── chroma/
  ├── prescriptions/
  ├── settings.json
  └── backup_manifest.json
```

Format: `backup_YYYY-MM-DD_HH-MM-SS/`

## User Interface

### 1. Backup Status Indicator (Header)

Located in the app header, shows:
- **Green** - Recent backup (< 24 hours)
- **Orange** - Warning, backup needed (> 24 hours)
- **Red** - No backup exists

Click the indicator to open the full backup dialog.

### 2. Backup Dialog

Access via clicking the backup status indicator or the Settings menu.

**Features:**
- **Create Backup Now** - Manually create a backup anytime
- **Backup List** - View all available backups with timestamps and sizes
- **Restore** - Restore from any backup (with confirmation)
- **Delete** - Remove old backups to free space
- **Change Location** - Set custom backup directory

### 3. Automatic Features

#### Auto-Backup on Close
When enabled (default: ON), creates a backup every time you close the app.

#### Database Integrity Check
On startup, the app checks if the database is corrupted. If corruption is detected and backups exist, you'll be offered to restore automatically.

## Usage Guide

### Creating a Manual Backup

1. Click the **backup status indicator** in the header (or Settings > Backup)
2. Click **"Create Backup Now"**
3. Wait for the progress bar to complete
4. Backup is now safely stored!

### Restoring from a Backup

⚠️ **IMPORTANT**: Restore creates a safety backup of your current data first!

1. Open the backup dialog
2. Find the backup you want to restore
3. Click the **Restore** icon (↻)
4. Confirm the restore operation
5. A safety backup is created automatically
6. Your data is restored
7. Restart the app to see the restored data

### Changing Backup Location

1. Open the backup dialog
2. Click **"Change Location"**
3. Select your preferred backup folder
4. All future backups will be saved there
5. Existing backups remain in the old location

### Deleting Old Backups

1. Open the backup dialog
2. Find the backup to delete
3. Click the **Delete** icon (🗑)
4. Confirm deletion

**Note**: The system automatically keeps only the 5 most recent backups. Older backups are deleted automatically unless you change this setting.

## Technical Details

### Backup Service (`SimpleBackupService`)

**Location**: `src/services/simple_backup.py`

**Key Methods**:
- `create_backup()` - Creates a new backup
- `restore_backup(path)` - Restores from a backup
- `list_backups()` - Lists all available backups
- `get_last_backup_time()` - Gets timestamp of last backup
- `cleanup_old_backups()` - Removes old backups

**Configuration**:
```python
SimpleBackupService(
    data_dir=Path("data"),                  # Where to backup from
    backup_dir=Path.home() / "DocAssist/backups/",  # Where to backup to
    max_backups=5                           # How many to keep
)
```

### Backup Status Indicator (`BackupStatusIndicator`)

**Location**: `src/ui/components/backup_status.py`

**Features**:
- Real-time status updates
- Color-coded warnings
- Click to open backup dialog
- Automatic status refresh

### Backup Dialog (`SimpleBackupDialog`)

**Location**: `src/ui/simple_backup_dialog.py`

**Features**:
- Clean, user-friendly interface
- Progress bars for operations
- Confirmation dialogs for destructive actions
- Responsive design

## Safety Features

### 1. Safety Backup Before Restore

Before any restore operation, the system automatically creates a backup of your current state in a `safety_backup_YYYY-MM-DD_HH-MM-SS/` folder. This ensures you can recover if something goes wrong.

### 2. SQLite Safe Backup

Uses SQLite's built-in `backup()` API which is safe to use while the database is active. No risk of corruption during backup.

### 3. Database Integrity Check

On startup, checks if the database is accessible. If corrupted, automatically offers to restore from the most recent backup.

### 4. Atomic Operations

All file operations use atomic moves/copies to prevent partial writes.

### 5. Error Handling

Comprehensive error handling with detailed logging. All errors are logged to help diagnose issues.

## Best Practices

### For Individual Doctors

1. **Enable auto-backup on close** (default: ON)
2. **Create manual backups before major changes** (e.g., bulk data entry)
3. **Copy backups to external drive weekly**
4. **Test restore occasionally** to ensure backups work

### For Clinics

1. **Set backup location to network share** for centralized storage
2. **Schedule regular backup copies** to external media
3. **Document backup procedures** for staff
4. **Test disaster recovery quarterly**

### For Advanced Users

1. **Script additional backups** using cron/Task Scheduler
2. **Sync backup folder to cloud** (Dropbox, Google Drive) for off-site storage
3. **Monitor backup folder size** to ensure sufficient disk space
4. **Archive old backups** to compressed storage

## Troubleshooting

### "No backup" warning even though I just backed up

- Click the backup status indicator to refresh
- Check if backup was actually created in the backup folder
- Restart the app

### Backup failed with "Permission denied"

- Check write permissions on backup folder
- Try changing backup location to a folder you own
- On Mac/Linux, check if the folder requires sudo access

### Restore failed

- Check the safety backup was created
- Verify the backup folder contains valid files
- Check disk space (restore needs 2x the backup size)
- Try restoring a different backup

### Database still corrupted after restore

1. Close the app completely
2. Manually copy `clinic.db` from backup folder to `data/clinic.db`
3. Restart the app
4. If still failing, contact support

## File Locations

### Default Locations

**Linux/Mac**:
- App data: `~/DocAssist/data/` or `./data/`
- Backups: `~/DocAssist/backups/`

**Windows**:
- App data: `%USERPROFILE%\DocAssist\data\` or `.\data\`
- Backups: `%USERPROFILE%\DocAssist\backups\`

### Changing Locations

Set environment variable before starting the app:

```bash
# Linux/Mac
export DOCASSIST_DATA_DIR="/path/to/data"
python main.py

# Windows
set DOCASSIST_DATA_DIR=C:\path\to\data
python main.py
```

## Future Enhancements

Planned features for future releases:

- 📅 **Scheduled automatic backups** (hourly/daily/weekly)
- ☁️ **Optional cloud sync** (Google Drive, Dropbox, S3)
- 🔒 **Encrypted backups** (optional, with password)
- 📧 **Email notifications** on backup success/failure
- 📊 **Backup statistics dashboard**
- 🔄 **Incremental backups** for faster operations
- 🌐 **Multi-device sync** via cloud

## Support

If you encounter any issues with the backup system:

1. Check the logs: `data/logs/app.log`
2. Review this documentation
3. Contact support with:
   - Error message
   - Backup location
   - Steps to reproduce
   - Log files

## License

This backup system is part of DocAssist EMR and follows the same license.

---

**Remember**: A backup is only useful if it's recent and you can restore from it. Test your backups regularly!
