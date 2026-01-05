"""Cloud Backup Setup Wizard - Step-by-step cloud backup configuration."""

import flet as ft
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import threading

from ...services.crypto import CryptoService, is_crypto_available
from ...services.settings import SettingsService


class CloudSetupWizard:
    """Step-by-step wizard for setting up cloud backup."""

    def __init__(
        self,
        page: ft.Page,
        settings_service: SettingsService,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """Initialize cloud setup wizard.

        Args:
            page: Flet page
            settings_service: Settings service instance
            on_complete: Callback when setup is complete (receives config dict)
        """
        self.page = page
        self.settings_service = settings_service
        self.on_complete = on_complete

        # Wizard state
        self.current_step = 0
        self.max_steps = 5
        self.config: Dict[str, Any] = {
            'provider': 'docassist',
            'encryption_method': 'password',
            'encryption_password': '',
            'encryption_key': '',
            'credentials': {},
        }

        # UI components
        self.dialog: Optional[ft.AlertDialog] = None
        self.step_content: Optional[ft.Container] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.back_button: Optional[ft.TextButton] = None
        self.next_button: Optional[ft.ElevatedButton] = None
        self.step_indicator: Optional[ft.Text] = None

        # Build and show wizard
        self._build_wizard()

    def _build_wizard(self):
        """Build the wizard dialog."""
        # Progress bar
        self.progress_bar = ft.ProgressBar(
            value=0,
            width=500,
            color=ft.Colors.BLUE_700,
        )

        # Step indicator
        self.step_indicator = ft.Text(
            "Step 1 of 5",
            size=12,
            color=ft.Colors.GREY_600,
        )

        # Step content container
        self.step_content = ft.Container(
            content=self._build_step_1(),
            width=500,
            height=300,
            padding=20,
        )

        # Navigation buttons
        self.back_button = ft.TextButton(
            "Back",
            on_click=self._on_back,
            visible=False,
        )

        self.next_button = ft.ElevatedButton(
            "Next",
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._on_next,
        )

        # Build dialog
        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CLOUD_UPLOAD, color=ft.Colors.BLUE_700),
                ft.Text("Cloud Backup Setup"),
            ], spacing=10),
            content=ft.Column([
                self.step_indicator,
                self.progress_bar,
                ft.Divider(),
                self.step_content,
            ], spacing=10, tight=True),
            actions=[
                self.back_button,
                ft.TextButton("Cancel", on_click=self._on_cancel),
                self.next_button,
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Show dialog
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _build_step_1(self) -> ft.Control:
        """Step 1: Choose provider."""
        return ft.Column([
            ft.Text("Choose Cloud Storage Provider", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Select where you want to store your encrypted backups.",
                size=12,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),

            ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(
                        value="docassist",
                        label="DocAssist Cloud (Recommended)",
                    ),
                    ft.Text(
                        "  • Managed service with automatic updates\n"
                        "  • Free tier: 1 GB storage\n"
                        "  • ₹199/mo for 10 GB (Essential tier)",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=5),

                    ft.Radio(
                        value="s3",
                        label="Amazon S3 / Backblaze B2 (BYOS)",
                    ),
                    ft.Text(
                        "  • Use your own S3-compatible storage\n"
                        "  • Pay only for storage you use\n"
                        "  • Requires AWS/B2 account",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=5),

                    ft.Radio(
                        value="gdrive",
                        label="Google Drive (BYOS)",
                    ),
                    ft.Text(
                        "  • Use your existing Google Drive\n"
                        "  • 15 GB free with Google account\n"
                        "  • Requires Google Cloud setup",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=5),

                    ft.Radio(
                        value="local",
                        label="Local Network Share",
                    ),
                    ft.Text(
                        "  • Store on local NAS or network drive\n"
                        "  • No cloud service required\n"
                        "  • Requires local network access",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=5),
                value=self.config['provider'],
                on_change=self._on_provider_change,
            ),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _build_step_2(self) -> ft.Control:
        """Step 2: Enter credentials."""
        provider = self.config['provider']

        if provider == 'docassist':
            return self._build_docassist_credentials()
        elif provider == 's3':
            return self._build_s3_credentials()
        elif provider == 'gdrive':
            return self._build_gdrive_credentials()
        elif provider == 'local':
            return self._build_local_credentials()

    def _build_docassist_credentials(self) -> ft.Control:
        """DocAssist Cloud credentials."""
        self.api_key_field = ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            hint_text="Enter your DocAssist API key",
            width=400,
            value=self.config['credentials'].get('api_key', ''),
        )

        return ft.Column([
            ft.Text("DocAssist Cloud Credentials", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Don't have an API key? Sign up at https://docassist.health",
                size=11,
                color=ft.Colors.BLUE_700,
            ),
            ft.Divider(),

            self.api_key_field,

            ft.Container(
                content=ft.Column([
                    ft.Text("Free Tier (1 GB):", weight=ft.FontWeight.W_500, size=12),
                    ft.Text(
                        "• 1 GB encrypted backup storage\n"
                        "• Sync across devices\n"
                        "• 30-day backup history",
                        size=11,
                    ),
                ], spacing=5),
                bgcolor=ft.Colors.BLUE_50,
                padding=15,
                border_radius=8,
            ),

            ft.TextButton(
                "View Pricing Plans",
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=lambda e: self.page.launch_url("https://docassist.health/pricing"),
            ),
        ], spacing=10)

    def _build_s3_credentials(self) -> ft.Control:
        """S3-compatible credentials."""
        creds = self.config['credentials']

        self.s3_bucket = ft.TextField(
            label="Bucket Name",
            hint_text="my-emr-backups",
            width=300,
            value=creds.get('bucket', ''),
        )
        self.s3_access_key = ft.TextField(
            label="Access Key ID",
            width=300,
            value=creds.get('access_key', ''),
        )
        self.s3_secret_key = ft.TextField(
            label="Secret Access Key",
            password=True,
            can_reveal_password=True,
            width=300,
            value=creds.get('secret_key', ''),
        )
        self.s3_endpoint = ft.TextField(
            label="Endpoint URL (optional)",
            hint_text="https://s3.us-west-001.backblazeb2.com",
            width=400,
            value=creds.get('endpoint_url', ''),
        )
        self.s3_region = ft.TextField(
            label="Region",
            hint_text="us-east-1",
            width=200,
            value=creds.get('region', 'us-east-1'),
        )

        return ft.Column([
            ft.Text("S3-Compatible Storage", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Works with: Amazon S3, Backblaze B2, MinIO, DigitalOcean Spaces",
                size=11,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),

            ft.Row([self.s3_bucket, self.s3_region], spacing=10),
            self.s3_access_key,
            self.s3_secret_key,
            self.s3_endpoint,

            ft.Container(
                content=ft.Text(
                    "Note: For Backblaze B2, use the 'S3 Compatible API' credentials, "
                    "not the native B2 credentials.",
                    size=11,
                    color=ft.Colors.ORANGE_700,
                ),
                bgcolor=ft.Colors.ORANGE_50,
                padding=10,
                border_radius=8,
            ),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _build_gdrive_credentials(self) -> ft.Control:
        """Google Drive credentials."""
        self.gdrive_client_id = ft.TextField(
            label="Client ID",
            width=400,
            value=self.config['credentials'].get('client_id', ''),
        )
        self.gdrive_client_secret = ft.TextField(
            label="Client Secret",
            password=True,
            can_reveal_password=True,
            width=400,
            value=self.config['credentials'].get('client_secret', ''),
        )

        return ft.Column([
            ft.Text("Google Drive Setup", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "You'll need to create a Google Cloud project and enable the Drive API.",
                size=11,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),

            self.gdrive_client_id,
            self.gdrive_client_secret,

            ft.Container(
                content=ft.Column([
                    ft.Text("Setup Instructions:", weight=ft.FontWeight.W_500, size=12),
                    ft.Text(
                        "1. Go to console.cloud.google.com\n"
                        "2. Create a new project\n"
                        "3. Enable Google Drive API\n"
                        "4. Create OAuth 2.0 credentials\n"
                        "5. Copy Client ID and Secret here",
                        size=11,
                    ),
                ], spacing=5),
                bgcolor=ft.Colors.BLUE_50,
                padding=15,
                border_radius=8,
            ),
        ], spacing=10)

    def _build_local_credentials(self) -> ft.Control:
        """Local network share."""
        self.local_path = ft.TextField(
            label="Network Path",
            hint_text="/mnt/backup or \\\\server\\share\\emr-backups",
            width=400,
            value=self.config['credentials'].get('path', ''),
        )

        return ft.Column([
            ft.Text("Local Network Share", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Store backups on a local NAS, network drive, or external disk.",
                size=11,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),

            self.local_path,

            ft.Container(
                content=ft.Column([
                    ft.Text("Requirements:", weight=ft.FontWeight.W_500, size=12),
                    ft.Text(
                        "• Network drive must be mounted and accessible\n"
                        "• Path must have write permissions\n"
                        "• Backups are still encrypted locally\n"
                        "• No internet connection required",
                        size=11,
                    ),
                ], spacing=5),
                bgcolor=ft.Colors.GREEN_50,
                padding=15,
                border_radius=8,
            ),
        ], spacing=10)

    def _build_step_3(self) -> ft.Control:
        """Step 3: Set encryption password."""
        self.encryption_method = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(
                    value="password",
                    label="Password-based encryption (Recommended)",
                ),
                ft.Radio(
                    value="key",
                    label="64-character recovery key (Advanced)",
                ),
            ], spacing=10),
            value=self.config['encryption_method'],
            on_change=self._on_encryption_method_change,
        )

        self.password_field = ft.TextField(
            label="Backup Password",
            password=True,
            can_reveal_password=True,
            hint_text="Choose a strong password (min 12 characters)",
            width=350,
            value=self.config['encryption_password'],
        )

        self.password_confirm_field = ft.TextField(
            label="Confirm Password",
            password=True,
            hint_text="Re-enter password",
            width=350,
        )

        self.recovery_key_display = ft.TextField(
            label="Recovery Key (write this down!)",
            value="",
            read_only=True,
            multiline=True,
            min_lines=2,
            max_lines=3,
            width=400,
            text_style=ft.TextStyle(font_family="monospace"),
            visible=False,
        )

        self.generate_key_button = ft.ElevatedButton(
            "Generate Recovery Key",
            icon=ft.Icons.KEY,
            on_click=self._on_generate_key,
            visible=False,
        )

        return ft.Column([
            ft.Text("Encryption Security", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCK, color=ft.Colors.GREEN_700, size=30),
                    ft.Text(
                        "Zero-Knowledge Encryption",
                        color=ft.Colors.GREEN_700,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Your data is encrypted BEFORE upload. We cannot see your data, "
                        "even if we wanted to. Without your password, data is unrecoverable.",
                        size=11,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                bgcolor=ft.Colors.GREEN_50,
                padding=15,
                border_radius=8,
            ),
            ft.Divider(),

            self.encryption_method,
            self.password_field,
            self.password_confirm_field,
            self.recovery_key_display,
            self.generate_key_button,

            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.RED_700, size=20),
                    ft.Text(
                        "CRITICAL: If you lose your password, your data is PERMANENTLY LOST. "
                        "There is no password reset. We recommend writing down your password.",
                        size=11,
                        color=ft.Colors.RED_700,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                bgcolor=ft.Colors.RED_50,
                padding=15,
                border_radius=8,
            ),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _build_step_4(self) -> ft.Control:
        """Step 4: Test connection."""
        self.test_status = ft.Text(
            "Ready to test connection...",
            size=14,
            color=ft.Colors.GREY_700,
        )

        self.test_progress = ft.ProgressBar(
            visible=False,
            width=400,
        )

        self.test_results = ft.Column([], spacing=10)

        return ft.Column([
            ft.Text("Test Connection", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "We'll test your cloud storage configuration before proceeding.",
                size=12,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),

            self.test_status,
            self.test_progress,
            ft.Divider(),
            self.test_results,

            ft.ElevatedButton(
                "Run Connection Test",
                icon=ft.Icons.PLAY_ARROW,
                on_click=self._on_test_connection,
            ),
        ], spacing=10)

    def _build_step_5(self) -> ft.Control:
        """Step 5: Initial upload."""
        self.upload_status = ft.Text(
            "Click 'Upload' to create your first encrypted backup.",
            size=14,
            color=ft.Colors.GREY_700,
        )

        self.upload_progress = ft.ProgressBar(
            visible=False,
            width=400,
        )

        self.upload_progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False,
        )

        return ft.Column([
            ft.Text("Initial Backup Upload", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Create and upload your first encrypted backup to test the setup.",
                size=12,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),

            self.upload_status,
            self.upload_progress,
            self.upload_progress_text,

            ft.ElevatedButton(
                "Create & Upload Backup",
                icon=ft.Icons.CLOUD_UPLOAD,
                on_click=self._on_initial_upload,
            ),
        ], spacing=10)

    def _on_provider_change(self, e):
        """Handle provider selection change."""
        self.config['provider'] = e.control.value

    def _on_encryption_method_change(self, e):
        """Handle encryption method change."""
        method = e.control.value
        self.config['encryption_method'] = method

        # Show/hide appropriate fields
        is_password = (method == 'password')
        self.password_field.visible = is_password
        self.password_confirm_field.visible = is_password
        self.recovery_key_display.visible = not is_password
        self.generate_key_button.visible = not is_password

        self.page.update()

    def _on_generate_key(self, e):
        """Generate recovery key."""
        try:
            crypto = CryptoService()
            key = crypto.generate_recovery_key()
            formatted = crypto.format_recovery_key(key)
            self.recovery_key_display.value = formatted
            self.config['encryption_key'] = key
            self.page.update()
        except Exception as ex:
            self._show_snackbar(f"Error: {ex}", error=True)

    def _on_test_connection(self, e):
        """Test cloud connection."""
        self.test_progress.visible = True
        self.test_status.value = "Testing connection..."
        self.test_results.controls.clear()
        self.page.update()

        def do_test():
            try:
                # Get backend config
                provider = self.config['provider']
                backend_config = self._build_backend_config()

                # Test 1: Connection
                self._add_test_result("Testing connection...", pending=True)

                from ...services.sync import (
                    LocalStorageBackend, S3StorageBackend,
                    DocAssistCloudBackend, get_or_create_device_id
                )
                from ...services.backup import BackupService

                # Initialize backend
                if provider == 'docassist':
                    data_dir = Path(self.settings_service.data_dir)
                    device_id = get_or_create_device_id(data_dir)
                    backend = DocAssistCloudBackend(
                        api_key=backend_config['api_key'],
                        device_id=device_id
                    )
                    # Test API key
                    try:
                        info = backend.get_account_info()
                        if info:
                            self._add_test_result(
                                f"✓ Connected to DocAssist Cloud (Tier: {info.get('tier', 'Free')})",
                                success=True
                            )
                        else:
                            self._add_test_result("✗ Invalid API key", success=False)
                            return
                    except Exception as ex:
                        self._add_test_result(f"✗ Connection failed: {ex}", success=False)
                        return

                elif provider == 's3':
                    backend = S3StorageBackend(
                        bucket=backend_config['bucket'],
                        access_key=backend_config['access_key'],
                        secret_key=backend_config['secret_key'],
                        endpoint_url=backend_config.get('endpoint_url'),
                        region=backend_config.get('region', 'us-east-1')
                    )
                    # Test S3 access
                    try:
                        backend.list_files()
                        self._add_test_result("✓ Connected to S3 bucket", success=True)
                    except Exception as ex:
                        self._add_test_result(f"✗ S3 connection failed: {ex}", success=False)
                        return

                elif provider == 'local':
                    backend = LocalStorageBackend(Path(backend_config['path']))
                    # Test local path
                    try:
                        backend.list_files()
                        self._add_test_result("✓ Local path accessible", success=True)
                    except Exception as ex:
                        self._add_test_result(f"✗ Path not accessible: {ex}", success=False)
                        return

                # Test 2: Encryption
                self._add_test_result("Testing encryption...", pending=True)
                if not is_crypto_available():
                    self._add_test_result("✗ Crypto library not available", success=False)
                    return

                crypto = CryptoService()
                test_data = b"DocAssist EMR Test"
                password = self.config['encryption_password'] if self.config['encryption_method'] == 'password' else None

                if password:
                    encrypted = crypto.encrypt(test_data, password)
                    decrypted = crypto.decrypt(encrypted, password)
                    if decrypted == test_data:
                        self._add_test_result("✓ Encryption working", success=True)
                    else:
                        self._add_test_result("✗ Encryption test failed", success=False)
                        return
                else:
                    key = self.config.get('encryption_key')
                    if key:
                        encrypted = crypto.encrypt_with_recovery_key(test_data, key)
                        decrypted = crypto.decrypt_with_recovery_key(encrypted, key)
                        if decrypted == test_data:
                            self._add_test_result("✓ Encryption working", success=True)
                        else:
                            self._add_test_result("✗ Encryption test failed", success=False)
                            return
                    else:
                        self._add_test_result("✗ No encryption key", success=False)
                        return

                # All tests passed
                self.page.run_thread_safe(lambda: self._update_test_status("All tests passed! ✓", True))

            except Exception as ex:
                self.page.run_thread_safe(lambda: self._add_test_result(f"✗ Error: {ex}", success=False))
                self.page.run_thread_safe(lambda: self._update_test_status("Tests failed", False))

        threading.Thread(target=do_test, daemon=True).start()

    def _add_test_result(self, message: str, success: bool = False, pending: bool = False):
        """Add test result."""
        def update():
            icon = ft.Icons.CHECK_CIRCLE if success else (ft.Icons.PENDING if pending else ft.Icons.ERROR)
            color = ft.Colors.GREEN_700 if success else (ft.Colors.ORANGE_700 if pending else ft.Colors.RED_700)

            self.test_results.controls.append(
                ft.Row([
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(message, size=12, color=color),
                ], spacing=10)
            )
            self.page.update()

        if self.page:
            self.page.run_thread_safe(update)

    def _update_test_status(self, message: str, success: bool):
        """Update test status."""
        self.test_status.value = message
        self.test_status.color = ft.Colors.GREEN_700 if success else ft.Colors.RED_700
        self.test_progress.visible = False
        self.page.update()

    def _on_initial_upload(self, e):
        """Perform initial backup upload."""
        self.upload_progress.visible = True
        self.upload_progress_text.visible = True
        self.upload_status.value = "Creating backup..."
        self.page.update()

        def do_upload():
            try:
                from ...services.backup import BackupService

                def progress_cb(message, percent):
                    if self.page:
                        self.page.run_thread_safe(lambda: self._update_upload_progress(message, percent))

                # Create backup service
                backup_service = BackupService()

                # Get password
                password = self.config['encryption_password'] if self.config['encryption_method'] == 'password' else self.config.get('encryption_key')
                backend_config = self._build_backend_config()

                # Create and upload backup
                success = backup_service.sync_to_cloud(
                    password=password,
                    backend_config=backend_config,
                    progress_callback=progress_cb
                )

                if success:
                    self.page.run_thread_safe(lambda: self._update_upload_status("Upload complete! ✓", True))
                else:
                    self.page.run_thread_safe(lambda: self._update_upload_status("Upload failed", False))

            except Exception as ex:
                self.page.run_thread_safe(lambda: self._update_upload_status(f"Error: {ex}", False))

        threading.Thread(target=do_upload, daemon=True).start()

    def _update_upload_progress(self, message: str, percent: int):
        """Update upload progress."""
        self.upload_progress.value = percent / 100
        self.upload_progress_text.value = message
        self.page.update()

    def _update_upload_status(self, message: str, success: bool):
        """Update upload status."""
        self.upload_status.value = message
        self.upload_status.color = ft.Colors.GREEN_700 if success else ft.Colors.RED_700
        self.upload_progress.visible = False
        self.upload_progress_text.visible = False
        self.page.update()

    def _build_backend_config(self) -> Dict[str, Any]:
        """Build backend config from wizard state."""
        provider = self.config['provider']
        config = {'type': provider}

        if provider == 'docassist':
            config['api_key'] = self.api_key_field.value if hasattr(self, 'api_key_field') else self.config['credentials'].get('api_key', '')
        elif provider == 's3':
            config.update({
                'bucket': self.s3_bucket.value if hasattr(self, 's3_bucket') else self.config['credentials'].get('bucket', ''),
                'access_key': self.s3_access_key.value if hasattr(self, 's3_access_key') else self.config['credentials'].get('access_key', ''),
                'secret_key': self.s3_secret_key.value if hasattr(self, 's3_secret_key') else self.config['credentials'].get('secret_key', ''),
                'endpoint_url': self.s3_endpoint.value if hasattr(self, 's3_endpoint') else self.config['credentials'].get('endpoint_url'),
                'region': self.s3_region.value if hasattr(self, 's3_region') else self.config['credentials'].get('region', 'us-east-1'),
            })
        elif provider == 'local':
            config['path'] = self.local_path.value if hasattr(self, 'local_path') else self.config['credentials'].get('path', '')

        return config

    def _on_next(self, e):
        """Handle next button."""
        # Validate current step
        if not self._validate_step():
            return

        # Save current step data
        self._save_step_data()

        # Move to next step
        if self.current_step < self.max_steps - 1:
            self.current_step += 1
            self._update_step()
        else:
            # Finish wizard
            self._finish_wizard()

    def _on_back(self, e):
        """Handle back button."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step()

    def _validate_step(self) -> bool:
        """Validate current step."""
        if self.current_step == 0:
            # Provider selected
            return True
        elif self.current_step == 1:
            # Credentials
            provider = self.config['provider']
            if provider == 'docassist':
                if not hasattr(self, 'api_key_field') or not self.api_key_field.value:
                    self._show_snackbar("Please enter your API key", error=True)
                    return False
            elif provider == 's3':
                if not all([self.s3_bucket.value, self.s3_access_key.value, self.s3_secret_key.value]):
                    self._show_snackbar("Please fill in all S3 fields", error=True)
                    return False
            elif provider == 'local':
                if not self.local_path.value:
                    self._show_snackbar("Please enter the network path", error=True)
                    return False
            return True
        elif self.current_step == 2:
            # Encryption
            method = self.config['encryption_method']
            if method == 'password':
                password = self.password_field.value
                confirm = self.password_confirm_field.value
                if not password:
                    self._show_snackbar("Please enter a password", error=True)
                    return False
                if len(password) < 12:
                    self._show_snackbar("Password must be at least 12 characters", error=True)
                    return False
                if password != confirm:
                    self._show_snackbar("Passwords don't match", error=True)
                    return False
            else:
                if not self.config.get('encryption_key'):
                    self._show_snackbar("Please generate a recovery key", error=True)
                    return False
            return True
        elif self.current_step == 3:
            # Test connection (optional, but recommended)
            return True
        elif self.current_step == 4:
            # Upload (optional)
            return True
        return True

    def _save_step_data(self):
        """Save data from current step."""
        if self.current_step == 1:
            # Save credentials
            provider = self.config['provider']
            if provider == 'docassist':
                self.config['credentials']['api_key'] = self.api_key_field.value
            elif provider == 's3':
                self.config['credentials'].update({
                    'bucket': self.s3_bucket.value,
                    'access_key': self.s3_access_key.value,
                    'secret_key': self.s3_secret_key.value,
                    'endpoint_url': self.s3_endpoint.value or None,
                    'region': self.s3_region.value,
                })
            elif provider == 'gdrive':
                self.config['credentials'].update({
                    'client_id': self.gdrive_client_id.value,
                    'client_secret': self.gdrive_client_secret.value,
                })
            elif provider == 'local':
                self.config['credentials']['path'] = self.local_path.value
        elif self.current_step == 2:
            # Save encryption settings
            if self.config['encryption_method'] == 'password':
                self.config['encryption_password'] = self.password_field.value

    def _update_step(self):
        """Update wizard to show current step."""
        # Update progress
        progress = (self.current_step + 1) / self.max_steps
        self.progress_bar.value = progress
        self.step_indicator.value = f"Step {self.current_step + 1} of {self.max_steps}"

        # Update content
        if self.current_step == 0:
            self.step_content.content = self._build_step_1()
        elif self.current_step == 1:
            self.step_content.content = self._build_step_2()
        elif self.current_step == 2:
            self.step_content.content = self._build_step_3()
        elif self.current_step == 3:
            self.step_content.content = self._build_step_4()
        elif self.current_step == 4:
            self.step_content.content = self._build_step_5()

        # Update buttons
        self.back_button.visible = (self.current_step > 0)
        if self.current_step == self.max_steps - 1:
            self.next_button.text = "Finish"
            self.next_button.icon = ft.Icons.CHECK
        else:
            self.next_button.text = "Next"
            self.next_button.icon = ft.Icons.ARROW_FORWARD

        self.page.update()

    def _finish_wizard(self):
        """Finish wizard and save settings."""
        # Save cloud settings
        backup_settings = self.settings_service.get_backup_settings()
        backup_settings.cloud_backend_type = self.config['provider']

        # Build backend config
        backend_config = self._build_backend_config()
        backup_settings.cloud_config = backend_config

        # Save
        self.settings_service.update_backup_settings(backup_settings)

        # Close wizard
        self.dialog.open = False
        self.page.update()

        # Show success message
        self._show_snackbar("Cloud backup configured successfully!")

        # Call completion callback
        if self.on_complete:
            final_config = {
                'provider': self.config['provider'],
                'backend_config': backend_config,
                'encryption_method': self.config['encryption_method'],
                'encryption_password': self.config.get('encryption_password'),
                'encryption_key': self.config.get('encryption_key'),
            }
            self.on_complete(final_config)

    def _on_cancel(self, e):
        """Handle cancel button."""
        self.dialog.open = False
        self.page.update()

    def _show_snackbar(self, message: str, error: bool = False):
        """Show snackbar message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        )
        self.page.snack_bar.open = True
        self.page.update()


def show_cloud_setup_wizard(
    page: ft.Page,
    settings_service: SettingsService,
    on_complete: Optional[Callable[[Dict[str, Any]], None]] = None
):
    """Show cloud setup wizard.

    Args:
        page: Flet page
        settings_service: Settings service instance
        on_complete: Callback when setup is complete
    """
    CloudSetupWizard(page, settings_service, on_complete)
