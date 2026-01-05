"""EMR Services - Core business logic and data access."""

# Database
from .database import DatabaseService

# LLM (optional - requires Ollama)
try:
    from .llm import LLMService
except ImportError:
    LLMService = None

# RAG (Vector-based - optional, for 8GB+ systems, requires chromadb)
try:
    from .rag import RAGService
except ImportError:
    RAGService = None

# PDF Generation (optional - requires fpdf2)
try:
    from .pdf import PDFService
except ImportError:
    PDFService = None

# Export Service
try:
    from .export import ExportService
except ImportError:
    ExportService = None

# Phonetic Search (for Indian names)
from .phonetic import IndianPhoneticSearch, MultiStrategySearch, get_phonetic_code

# Safety Framework
from .safety import (
    PrescriptionSafetyChecker,
    CriticalInfoBanner,
    DRUG_DATABASE,
    ALLERGY_CROSS_REACTIVITY,
)

# SQL-based Context Builder (alternative to vector RAG)
from .context_builder import ContextBuilder, QueryParser

# App Mode Detection
from .app_mode import (
    AppMode,
    AppModeManager,
    ModeCapabilities,
    get_mode_manager,
    get_current_mode,
    get_capabilities,
    can_use_llm,
    can_use_rag,
)

# Backup and Cloud Sync - deferred imports to avoid crypto crashes
BackupService = None
BackupInfo = None
CryptoService = None
EncryptedData = None
DecryptionError = None
is_crypto_available = None
SyncService = None
SyncStatus = None
SyncProgress = None
StorageBackend = None
LocalStorageBackend = None
S3StorageBackend = None
DocAssistCloudBackend = None
get_or_create_device_id = None
SettingsService = None
BackupSettings = None
DoctorSettings = None
AppSettings = None
BackupScheduler = None

def _load_backup_services():
    """Load backup services lazily to avoid crypto crashes at import time."""
    global BackupService, BackupInfo, CryptoService, EncryptedData, DecryptionError
    global is_crypto_available, SyncService, SyncStatus, SyncProgress
    global StorageBackend, LocalStorageBackend, S3StorageBackend, DocAssistCloudBackend
    global get_or_create_device_id, SettingsService, BackupSettings, DoctorSettings
    global AppSettings, BackupScheduler

    try:
        from .backup import BackupService as _BackupService, BackupInfo as _BackupInfo
        from .crypto import CryptoService as _CryptoService, EncryptedData as _EncryptedData
        from .crypto import DecryptionError as _DecryptionError, is_crypto_available as _is_crypto_available
        from .sync import (
            SyncService as _SyncService, SyncStatus as _SyncStatus, SyncProgress as _SyncProgress,
            StorageBackend as _StorageBackend, LocalStorageBackend as _LocalStorageBackend,
            S3StorageBackend as _S3StorageBackend, DocAssistCloudBackend as _DocAssistCloudBackend,
            get_or_create_device_id as _get_or_create_device_id
        )
        from .settings import SettingsService as _SettingsService, BackupSettings as _BackupSettings
        from .settings import DoctorSettings as _DoctorSettings, AppSettings as _AppSettings
        from .scheduler import BackupScheduler as _BackupScheduler

        BackupService = _BackupService
        BackupInfo = _BackupInfo
        CryptoService = _CryptoService
        EncryptedData = _EncryptedData
        DecryptionError = _DecryptionError
        is_crypto_available = _is_crypto_available
        SyncService = _SyncService
        SyncStatus = _SyncStatus
        SyncProgress = _SyncProgress
        StorageBackend = _StorageBackend
        LocalStorageBackend = _LocalStorageBackend
        S3StorageBackend = _S3StorageBackend
        DocAssistCloudBackend = _DocAssistCloudBackend
        get_or_create_device_id = _get_or_create_device_id
        SettingsService = _SettingsService
        BackupSettings = _BackupSettings
        DoctorSettings = _DoctorSettings
        AppSettings = _AppSettings
        BackupScheduler = _BackupScheduler
        return True
    except Exception:
        return False

# Note: Call _load_backup_services() manually when backup features are needed
# This avoids crashes from broken crypto libraries at import time

__all__ = [
    # Database
    "DatabaseService",
    # LLM
    "LLMService",
    # RAG
    "RAGService",
    # PDF
    "PDFService",
    # Export
    "ExportService",
    # Phonetic
    "IndianPhoneticSearch",
    "MultiStrategySearch",
    "get_phonetic_code",
    # Safety
    "PrescriptionSafetyChecker",
    "CriticalInfoBanner",
    "DRUG_DATABASE",
    "ALLERGY_CROSS_REACTIVITY",
    # Context Builder
    "ContextBuilder",
    "QueryParser",
    # App Mode
    "AppMode",
    "AppModeManager",
    "ModeCapabilities",
    "get_mode_manager",
    "get_current_mode",
    "get_capabilities",
    "can_use_llm",
    "can_use_rag",
    # Backup
    "BackupService",
    "BackupInfo",
    "CryptoService",
    "EncryptedData",
    "DecryptionError",
    "is_crypto_available",
    "SyncService",
    "SyncStatus",
    "SyncProgress",
    "StorageBackend",
    "LocalStorageBackend",
    "S3StorageBackend",
    "DocAssistCloudBackend",
    "get_or_create_device_id",
    "SettingsService",
    "BackupSettings",
    "DoctorSettings",
    "AppSettings",
    "BackupScheduler",
]
