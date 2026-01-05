# Cloud Backup UI Integration Guide

This guide shows how to integrate the cloud backup UI components into DocAssist EMR.

## Components Overview

### 1. CloudSetupWizard
Step-by-step wizard for configuring cloud backup.

**Features:**
- Provider selection (DocAssist Cloud, S3, Google Drive, Local)
- Credential entry
- Encryption setup (password or recovery key)
- Connection testing
- Initial backup upload

### 2. CloudStatusPanel
Displays current cloud sync status.

**Features:**
- Last sync time
- Storage usage (for DocAssist Cloud)
- Quick sync button
- Visual status indicators

### 3. EncryptionKeyDialog
Manages encryption keys and passwords.

**Features:**
- Generate recovery key
- Display key with copy/print options
- Security warnings
- "I have saved it" confirmation

### 4. RestoreFromCloudDialog
Lists and restores cloud backups.

**Features:**
- List all cloud backups
- Show backup metadata (date, size)
- Password/recovery key input
- Progress tracking
- Conflict warnings

### 5. SyncConflictDialog
Resolves conflicts between local and cloud data.

**Features:**
- Side-by-side comparison
- Recommended action
- Options: Use Local, Use Cloud, Keep Both

### 6. CloudBackupManager
Service that orchestrates cloud operations.

**Features:**
- Background sync scheduling
- Conflict detection and resolution
- Multiple provider support
- Secure password management
- Connection testing

## Integration Example

```python
from pathlib import Path
import flet as ft

from src.services.backup import BackupService
from src.services.settings import SettingsService
from src.services.cloud_backup_manager import CloudBackupManager
from src.ui.backup_dialog import show_backup_dialog
from src.ui.cloud.cloud_setup_wizard import show_cloud_setup_wizard
from src.ui.cloud.cloud_status_panel import CloudStatusPanel

def main(page: ft.Page):
    # Initialize services
    data_dir = Path("data")
    backup_service = BackupService(data_dir=data_dir)
    settings_service = SettingsService(data_dir=data_dir)

    # Initialize cloud backup manager
    cloud_backup_manager = CloudBackupManager(
        backup_service=backup_service,
        settings_service=settings_service,
        data_dir=data_dir,
    )

    # Set up conflict handler
    def handle_conflict(local_info, cloud_info):
        """Handle sync conflicts - return 'local', 'cloud', or 'both'"""
        from src.ui.cloud.sync_conflict_dialog import show_sync_conflict_dialog

        resolution = None

        def on_resolve(res):
            nonlocal resolution
            resolution = res

        show_sync_conflict_dialog(page, local_info, cloud_info, on_resolve)

        # Wait for user decision (simplified - use proper async in production)
        return resolution or "skip"

    cloud_backup_manager.on_conflict = handle_conflict

    # Start background sync (every 4 hours)
    cloud_backup_manager.start_background_sync(interval_hours=4.0)

    # Add cloud status panel to UI
    status_panel = CloudStatusPanel(
        settings_service=settings_service,
        cloud_backup_manager=cloud_backup_manager,
        on_sync_click=lambda: cloud_backup_manager.sync_now(),
        on_settings_click=lambda: show_cloud_setup_wizard(
            page,
            settings_service,
            on_complete=lambda cfg: print(f"Cloud configured: {cfg}")
        ),
    )

    # Add to page layout
    page.add(
        ft.Container(
            content=status_panel,
            padding=20,
        )
    )

    # Button to open full backup dialog
    def open_backup_dialog(e):
        show_backup_dialog(
            page=page,
            backup_service=backup_service,
            settings_service=settings_service,
            cloud_backup_manager=cloud_backup_manager,
        )

    page.add(
        ft.ElevatedButton(
            "Backup & Cloud Settings",
            icon=ft.Icons.CLOUD_UPLOAD,
            on_click=open_backup_dialog,
        )
    )

    # Start auto-refresh of status panel
    status_panel.start_auto_refresh(interval_seconds=30)

ft.app(target=main)
```

## Usage Scenarios

### First-Time Setup

When a user opens the app for the first time:

```python
# Check if cloud is configured
if not cloud_backup_manager.is_configured():
    # Show setup wizard
    show_cloud_setup_wizard(
        page,
        settings_service,
        on_complete=lambda config: start_initial_sync(config)
    )
```

### Manual Sync

User clicks "Sync Now" button:

```python
def on_sync_click():
    # Prompt for password if not saved
    password = prompt_password()  # Your password dialog

    # Sync in background
    success = cloud_backup_manager.sync_now(password=password)

    if success:
        show_snackbar("Sync complete!")
    else:
        status = cloud_backup_manager.get_sync_status()
        show_snackbar(f"Sync failed: {status['last_error']}", error=True)
```

### Restore from Cloud

User wants to restore from a cloud backup:

```python
def on_restore_click():
    show_restore_from_cloud(
        page=page,
        backup_service=backup_service,
        settings_service=settings_service,
        on_restore_complete=lambda: restart_app()
    )
```

### Show Recovery Key

User needs to see or generate their recovery key:

```python
from src.ui.cloud.encryption_key_dialog import show_encryption_key_dialog

def on_show_key():
    show_encryption_key_dialog(
        page=page,
        key_type="recovery",  # or "password"
        on_save=lambda key_type, key_value: save_key(key_type, key_value)
    )
```

## Security Best Practices

### 1. Password Storage

**DO NOT** store encryption passwords in plaintext. Options:

```python
# Option A: Use system keyring (recommended)
import keyring

def save_password(password: str):
    keyring.set_password("docassist_emr", "backup_encryption", password)

def get_password() -> str:
    return keyring.get_password("docassist_emr", "backup_encryption")

# Option B: Prompt user each time (most secure)
def get_password() -> str:
    # Show password dialog
    return user_entered_password
```

### 2. Recovery Key Storage

Recovery keys should NEVER be stored digitally:

```python
# Show key once, force user to write it down
show_encryption_key_dialog(
    page=page,
    key_type="recovery",
    on_save=lambda kt, kv: None  # Don't save digitally
)
```

### 3. Zero-Knowledge Verification

Verify encryption before cloud upload:

```python
from src.services.crypto import CryptoService

crypto = CryptoService()

# Test encryption round-trip
test_data = b"test"
encrypted = crypto.encrypt(test_data, password)
decrypted = crypto.decrypt(encrypted, password)

assert decrypted == test_data, "Encryption test failed!"
```

## Error Handling

### Network Errors

```python
try:
    cloud_backup_manager.sync_now(password)
except ConnectionError as e:
    show_snackbar("No internet connection. Sync will retry later.", error=True)
except Exception as e:
    show_snackbar(f"Sync error: {e}", error=True)
```

### Quota Exceeded

```python
status = cloud_backup_manager.get_sync_status()

if status['storage_used'] >= status['storage_quota']:
    show_dialog(
        "Storage Quota Exceeded",
        "Please upgrade your plan or free up space.",
        actions=["Upgrade Plan", "Manage Backups"]
    )
```

### Invalid Credentials

```python
success, error = cloud_backup_manager.test_connection(backend_config)

if not success:
    if "401" in error or "Invalid API key" in error:
        show_snackbar("Invalid credentials. Please check your API key.", error=True)
        show_cloud_setup_wizard(page, settings_service)
```

## Advanced: Auto-Sync Scheduler

Configure automatic sync based on user preferences:

```python
# Enable auto-sync every 4 hours
settings_service.enable_cloud_sync(
    enabled=True,
    backend_type="docassist",
    config={"api_key": "your-api-key"}
)

# Start background sync
cloud_backup_manager.start_background_sync(interval_hours=4.0)

# Set callbacks
cloud_backup_manager.on_sync_start = lambda: update_ui("Syncing...")
cloud_backup_manager.on_sync_complete = lambda success, error: (
    update_ui("Synced!") if success else update_ui(f"Error: {error}")
)

# Stop on app close
def on_app_close():
    cloud_backup_manager.stop_background_sync()
```

## Testing

### Test Cloud Setup

```python
# Test DocAssist Cloud
backend_config = {
    'type': 'docassist',
    'api_key': 'test-api-key'
}

success, error = cloud_backup_manager.test_connection(backend_config)
print(f"Connection test: {'✓' if success else '✗'} {error or ''}")

# Test S3
backend_config = {
    'type': 's3',
    'bucket': 'my-bucket',
    'access_key': 'ACCESS_KEY',
    'secret_key': 'SECRET_KEY',
    'region': 'us-east-1'
}

success, error = cloud_backup_manager.test_connection(backend_config)
print(f"S3 test: {'✓' if success else '✗'} {error or ''}")
```

### Test Encryption

```python
from src.services.crypto import CryptoService, is_crypto_available

if not is_crypto_available():
    print("❌ Crypto library not available - install pynacl")
    exit(1)

crypto = CryptoService()

# Test password encryption
password = "test-password-123"
data = b"Sensitive patient data"

encrypted = crypto.encrypt(data, password)
decrypted = crypto.decrypt(encrypted, password)

assert decrypted == data, "Encryption failed!"
print("✓ Password encryption working")

# Test recovery key encryption
key = crypto.generate_recovery_key()
encrypted = crypto.encrypt_with_recovery_key(data, key)
decrypted = crypto.decrypt_with_recovery_key(encrypted, key)

assert decrypted == data, "Recovery key encryption failed!"
print(f"✓ Recovery key working: {crypto.format_recovery_key(key)}")
```

## Troubleshooting

### Issue: Cloud sync fails silently

**Solution:** Check sync status:

```python
status = cloud_backup_manager.get_sync_status()
print(f"Syncing: {status['syncing']}")
print(f"Last sync: {status['last_sync_time']}")
print(f"Last error: {status['last_error']}")
```

### Issue: "Wrong password" error on restore

**Possible causes:**
1. User entered wrong password
2. Backup corrupted during upload
3. Different encryption key used

**Solution:**
- Verify password is correct
- Try recovery key if available
- Check backup integrity with checksum

### Issue: High memory usage during sync

**Solution:** Implement chunked upload:

```python
# Already implemented in sync service
# Files are uploaded in 1MB chunks
# See CHUNK_SIZE in crypto.py
```

## Next Steps

1. **Implement secure password storage** using system keyring
2. **Add sync progress notifications** to status bar
3. **Create cloud backup health dashboard** showing:
   - Last 10 sync attempts
   - Success/failure rate
   - Storage trends
   - Backup size over time
4. **Implement differential backups** to reduce sync time
5. **Add support for scheduled backups** (e.g., daily at 2 AM)
6. **Create mobile app integration** for cross-device sync
