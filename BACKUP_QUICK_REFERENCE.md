# Backup System Quick Reference

## For Users

### Automatic Backups
Your data is automatically backed up:
- **On startup** (if last backup was > 1 hour ago)
- **Every 4 hours** while the app is running
- **On shutdown** when you close the app

You don't need to do anything - it just works!

### Manual Backup
Create a backup anytime:
1. Click the **Settings** button (gear icon)
2. Go to the **Backups** tab
3. Click **Backup Now**

Or use keyboard shortcut: **Ctrl+B**

### Viewing Backups
1. Open **Settings** → **Backups** tab
2. See list of all backups with:
   - Date and time created
   - Number of patients
   - File size

### Restoring a Backup
1. Open **Settings** → **Backups** tab
2. Find the backup you want to restore
3. Click the **Restore** button
4. Confirm the restore operation
5. **Restart the application** to use restored data

⚠️ **Warning**: Restoring will replace all current data. A backup of your current data is created before restore as a safety measure.

### Configuring Backups
1. Open **Settings** → **Preferences** tab
2. Adjust:
   - **Backup Frequency**: How often auto-backups happen (in hours)
   - **Backup Retention**: How many backups to keep

### Where Are Backups Stored?
- Location: `data/backups/`
- Format: Timestamped ZIP files
- Example: `backup_2026-01-02_10-30-00.zip`

### Backup Contents
Each backup includes:
- ✅ All patient records (SQLite database)
- ✅ All vector embeddings for search (ChromaDB)
- ✅ Metadata (patient count, creation time)

## For Developers

### BackupService API

```python
from src.services.backup import BackupService

# Initialize
backup = BackupService(
    data_dir=Path("data"),
    backup_dir=Path("data/backups"),
    max_backups=10
)

# Create backup
backup_path = backup.create_backup()

# List backups
backups = backup.list_backups()
for b in backups:
    print(f"{b['filename']}: {b['patient_count']} patients")

# Restore backup
success = backup.restore_backup(backup_path)

# Get last backup time
last_time = backup.get_last_backup_time()

# Auto-backup with cleanup
backup.auto_backup()  # Creates backup + cleanup old ones
```

### Integration Points

```python
# In app __init__
self.backup = BackupService()
self.last_backup_time = None
self.backup_interval_hours = 4

# On startup
def _startup_backup(self):
    threading.Thread(target=lambda: self.backup.auto_backup(), daemon=True).start()

# On shutdown
def _on_app_close(self, e):
    self.backup.auto_backup()

# Periodic timer
def _start_backup_timer(self):
    # Runs backup every self.backup_interval_hours
```

### Backup File Structure

```
backup_2026-01-02_10-30-00.zip
├── clinic.db                    # Full SQLite database
├── chroma/                      # ChromaDB vector store
│   ├── chroma.sqlite3
│   └── [other chroma files]
└── backup_manifest.json         # Metadata
    {
      "created_at": "2026-01-02T10:30:00",
      "version": "1.0",
      "patient_count": 150,
      "visit_count": 1200,
      "app_version": "0.1.0"
    }
```

### Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `create_backup()` | Create new backup | `Path` or `None` |
| `restore_backup(path)` | Restore from backup | `bool` |
| `list_backups()` | Get all backups | `list[dict]` |
| `cleanup_old_backups()` | Delete old backups | `None` |
| `get_last_backup_time()` | Last backup timestamp | `datetime` or `None` |
| `auto_backup()` | Backup + cleanup | `bool` |

### SQLite Backup API Usage

```python
def _backup_sqlite(self, source_db: Path, dest_db: Path):
    source_conn = sqlite3.connect(source_db)
    dest_conn = sqlite3.connect(dest_db)
    try:
        source_conn.backup(dest_conn)  # Atomic, safe copy
    finally:
        source_conn.close()
        dest_conn.close()
```

This is **safe to use while the database is active** - no need to stop the app!

### Threading Pattern

```python
def _manual_backup(self):
    def do_backup():
        if self.backup.auto_backup():
            self.last_backup_time = datetime.now()
            self.page.run_thread_safe(
                lambda: self._update_status("Backup completed")
            )

    threading.Thread(target=do_backup, daemon=True).start()
```

Always use background threads to avoid blocking the UI.

## Troubleshooting

### Backup Not Created
- Check console output for error messages
- Ensure `data/` directory exists and is writable
- Verify sufficient disk space

### Restore Fails
- Check if backup file exists and is valid ZIP
- Ensure app has write permissions to `data/` directory
- Try extracting the ZIP manually to verify integrity

### Old Backups Not Deleted
- Check `max_backups` setting
- Manually run `backup.cleanup_old_backups()`

### Status Bar Shows "Backup: none"
- This is normal on first run
- Create a manual backup to initialize

## Best Practices

### For Users
1. ✅ Keep backup frequency at 4 hours or less
2. ✅ Maintain at least 10 backups for recovery options
3. ✅ Periodically export backups to external drive/USB
4. ✅ Test restore occasionally to verify backups work

### For Developers
1. ✅ Always use `auto_backup()` which includes cleanup
2. ✅ Run backups in background threads
3. ✅ Use `page.run_thread_safe()` for UI updates
4. ✅ Handle backup failures gracefully
5. ✅ Log backup operations for debugging

## FAQ

**Q: How long does a backup take?**
A: Typically < 5 seconds for a practice with 1000 patients. Runs in background.

**Q: How much disk space do backups use?**
A: ~1-2 MB per 100 patients (with ZIP compression). 10 backups ≈ 10-20 MB.

**Q: Can I backup to external drive?**
A: Yes, copy files from `data/backups/` to external drive. Future feature will automate this.

**Q: What if backup fails?**
A: App continues working normally. Check console logs. Try manual backup.

**Q: Do I need to stop seeing patients to restore?**
A: Yes, close the app, restore, then restart.

**Q: Can I delete old backups manually?**
A: Yes, just delete ZIP files from `data/backups/`. The app manages retention automatically.

---
*Quick Reference for DocAssist EMR Backup System*
