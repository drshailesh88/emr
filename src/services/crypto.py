"""Cryptographic services for end-to-end encrypted backups.

Implements WhatsApp-style zero-knowledge encryption:
- Client-side encryption with NaCl SecretBox (XSalsa20-Poly1305)
- Key derivation from password using Argon2id
- All encryption happens locally - server never sees plaintext or keys

Security model:
- Password -> Argon2id KDF -> 256-bit encryption key
- Data is encrypted before leaving the device
- Cloud only stores encrypted blobs
- Without password, data is unrecoverable (zero-knowledge)
"""

import os
import base64
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

# Try to import PyNaCl (preferred) or fall back to cryptography
_nacl_available = False
_crypto_available = False

try:
    import nacl.secret
    import nacl.utils
    import nacl.pwhash
    from nacl.exceptions import CryptoError
    _nacl_available = True
except ImportError:
    pass

if not _nacl_available:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
        from cryptography.hazmat.backends import default_backend
        _crypto_available = True
    except ImportError:
        pass


# Constants
# PyNaCl's argon2id requires exactly 16 bytes for salt
SALT_SIZE = 16  # 128 bits (required by nacl.pwhash.argon2id)
NONCE_SIZE = 24  # For XSalsa20 (NaCl) or 12 for AES-GCM
KEY_SIZE = 32   # 256 bits
CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for large files

# Argon2 parameters (tuned for security vs. usability)
# These should take ~0.5-1 second on modern hardware
ARGON2_OPS_LIMIT = 3  # Number of passes
ARGON2_MEM_LIMIT = 67108864  # 64 MB memory


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata."""
    ciphertext: bytes
    salt: bytes
    nonce: bytes
    version: int = 1

    def to_bytes(self) -> bytes:
        """Serialize to bytes for storage."""
        # Format: version (1) + salt (16) + nonce (24) + ciphertext
        return (
            self.version.to_bytes(1, 'big') +
            self.salt +
            self.nonce +
            self.ciphertext
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'EncryptedData':
        """Deserialize from bytes."""
        if len(data) < 1 + SALT_SIZE + NONCE_SIZE:
            raise ValueError("Invalid encrypted data: too short")

        version = data[0]
        salt = data[1:1 + SALT_SIZE]
        nonce = data[1 + SALT_SIZE:1 + SALT_SIZE + NONCE_SIZE]
        ciphertext = data[1 + SALT_SIZE + NONCE_SIZE:]

        return cls(
            ciphertext=ciphertext,
            salt=salt,
            nonce=nonce,
            version=version
        )

    def to_base64(self) -> str:
        """Encode as base64 string."""
        return base64.b64encode(self.to_bytes()).decode('utf-8')

    @classmethod
    def from_base64(cls, data: str) -> 'EncryptedData':
        """Decode from base64 string."""
        return cls.from_bytes(base64.b64decode(data))


class CryptoService:
    """Zero-knowledge encryption service for backup data.

    Usage:
        crypto = CryptoService()

        # Encrypt with password
        encrypted = crypto.encrypt(plaintext_bytes, "user_password")

        # Decrypt with same password
        decrypted = crypto.decrypt(encrypted, "user_password")

        # Generate recovery key (64-digit hex)
        recovery_key = crypto.generate_recovery_key()

        # Encrypt with recovery key instead of password
        encrypted = crypto.encrypt_with_key(plaintext_bytes, recovery_key)
    """

    def __init__(self):
        """Initialize crypto service."""
        if not _nacl_available and not _crypto_available:
            raise ImportError(
                "No cryptography library available. "
                "Install PyNaCl: pip install pynacl"
            )

        self.use_nacl = _nacl_available

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using Argon2id.

        Args:
            password: User's password
            salt: Random salt (must be stored with ciphertext)

        Returns:
            32-byte encryption key
        """
        if self.use_nacl:
            return nacl.pwhash.argon2id.kdf(
                KEY_SIZE,
                password.encode('utf-8'),
                salt,
                opslimit=ARGON2_OPS_LIMIT,
                memlimit=ARGON2_MEM_LIMIT
            )
        else:
            # Fall back to scrypt if Argon2 not available
            kdf = Scrypt(
                salt=salt,
                length=KEY_SIZE,
                n=2**14,  # CPU/memory cost
                r=8,      # Block size
                p=1,      # Parallelism
                backend=default_backend()
            )
            return kdf.derive(password.encode('utf-8'))

    def generate_salt(self) -> bytes:
        """Generate cryptographically secure random salt."""
        return secrets.token_bytes(SALT_SIZE)

    def generate_nonce(self) -> bytes:
        """Generate cryptographically secure random nonce."""
        if self.use_nacl:
            return nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        else:
            return secrets.token_bytes(12)  # AES-GCM nonce

    def generate_recovery_key(self) -> str:
        """Generate a 64-character hex recovery key.

        This can be used instead of a password. User should write it down
        and store in a safe place.

        Returns:
            64-character hex string (256 bits of entropy)
        """
        return secrets.token_hex(32)

    def recovery_key_to_bytes(self, recovery_key: str) -> bytes:
        """Convert recovery key string to bytes."""
        # Remove any spaces/dashes for user convenience
        clean_key = recovery_key.replace(' ', '').replace('-', '')
        if len(clean_key) != 64:
            raise ValueError("Recovery key must be 64 hex characters")
        return bytes.fromhex(clean_key)

    def format_recovery_key(self, recovery_key: str) -> str:
        """Format recovery key for display (groups of 4)."""
        clean = recovery_key.replace(' ', '').replace('-', '')
        return ' '.join(clean[i:i+4] for i in range(0, len(clean), 4))

    def encrypt(self, plaintext: bytes, password: str) -> EncryptedData:
        """Encrypt data with password.

        Args:
            plaintext: Data to encrypt
            password: User's password

        Returns:
            EncryptedData container with ciphertext and metadata
        """
        salt = self.generate_salt()
        key = self.derive_key(password, salt)
        return self._encrypt_with_key_bytes(plaintext, key, salt)

    def encrypt_with_recovery_key(self, plaintext: bytes, recovery_key: str) -> EncryptedData:
        """Encrypt data with recovery key (no password).

        Args:
            plaintext: Data to encrypt
            recovery_key: 64-character hex recovery key

        Returns:
            EncryptedData container
        """
        key = self.recovery_key_to_bytes(recovery_key)
        salt = self.generate_salt()  # Still need salt for format consistency
        return self._encrypt_with_key_bytes(plaintext, key, salt)

    def _encrypt_with_key_bytes(self, plaintext: bytes, key: bytes, salt: bytes) -> EncryptedData:
        """Internal encryption with raw key bytes."""
        if self.use_nacl:
            box = nacl.secret.SecretBox(key)
            nonce = self.generate_nonce()
            # NaCl prepends nonce to ciphertext, but we handle it explicitly
            ciphertext = box.encrypt(plaintext, nonce).ciphertext
        else:
            aesgcm = AESGCM(key)
            nonce = self.generate_nonce()
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return EncryptedData(
            ciphertext=ciphertext,
            salt=salt,
            nonce=nonce,
            version=1
        )

    def decrypt(self, encrypted: EncryptedData, password: str) -> bytes:
        """Decrypt data with password.

        Args:
            encrypted: EncryptedData container
            password: User's password

        Returns:
            Decrypted plaintext bytes

        Raises:
            CryptoError: If decryption fails (wrong password)
        """
        key = self.derive_key(password, encrypted.salt)
        return self._decrypt_with_key_bytes(encrypted, key)

    def decrypt_with_recovery_key(self, encrypted: EncryptedData, recovery_key: str) -> bytes:
        """Decrypt data with recovery key.

        Args:
            encrypted: EncryptedData container
            recovery_key: 64-character hex recovery key

        Returns:
            Decrypted plaintext bytes
        """
        key = self.recovery_key_to_bytes(recovery_key)
        return self._decrypt_with_key_bytes(encrypted, key)

    def _decrypt_with_key_bytes(self, encrypted: EncryptedData, key: bytes) -> bytes:
        """Internal decryption with raw key bytes."""
        if self.use_nacl:
            box = nacl.secret.SecretBox(key)
            try:
                return box.decrypt(encrypted.ciphertext, encrypted.nonce)
            except nacl.exceptions.CryptoError as e:
                raise DecryptionError("Decryption failed - wrong password?") from e
        else:
            aesgcm = AESGCM(key)
            try:
                return aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, None)
            except Exception as e:
                raise DecryptionError("Decryption failed - wrong password?") from e

    def encrypt_file(self, input_path: Path, output_path: Path, password: str) -> bool:
        """Encrypt a file to another file.

        Args:
            input_path: Path to plaintext file
            output_path: Path to write encrypted file
            password: Encryption password

        Returns:
            True if successful
        """
        try:
            with open(input_path, 'rb') as f:
                plaintext = f.read()

            encrypted = self.encrypt(plaintext, password)

            with open(output_path, 'wb') as f:
                f.write(encrypted.to_bytes())

            return True
        except Exception as e:
            print(f"Encryption failed: {e}")
            return False

    def decrypt_file(self, input_path: Path, output_path: Path, password: str) -> bool:
        """Decrypt a file to another file.

        Args:
            input_path: Path to encrypted file
            output_path: Path to write decrypted file
            password: Decryption password

        Returns:
            True if successful
        """
        try:
            with open(input_path, 'rb') as f:
                data = f.read()

            encrypted = EncryptedData.from_bytes(data)
            plaintext = self.decrypt(encrypted, password)

            with open(output_path, 'wb') as f:
                f.write(plaintext)

            return True
        except Exception as e:
            print(f"Decryption failed: {e}")
            return False

    def compute_checksum(self, data: bytes) -> str:
        """Compute SHA-256 checksum for integrity verification.

        Args:
            data: Data to checksum

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(data).hexdigest()

    def verify_checksum(self, data: bytes, expected_checksum: str) -> bool:
        """Verify data integrity against checksum.

        Args:
            data: Data to verify
            expected_checksum: Expected SHA-256 hex string

        Returns:
            True if checksum matches
        """
        return self.compute_checksum(data) == expected_checksum


class DecryptionError(Exception):
    """Raised when decryption fails (wrong password or corrupted data)."""
    pass


def is_crypto_available() -> bool:
    """Check if cryptography libraries are available."""
    return _nacl_available or _crypto_available


def get_crypto_backend() -> str:
    """Get name of the active crypto backend."""
    if _nacl_available:
        return "PyNaCl (libsodium)"
    elif _crypto_available:
        return "cryptography"
    else:
        return "none"
