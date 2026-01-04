"""Security tests for encryption key handling and authentication flows.

These tests verify:
- Encryption keys are properly derived and never stored in plaintext
- Password handling follows security best practices
- Recovery keys provide secure fallback access
- Encrypted data cannot be accessed without proper credentials
"""

import pytest
import tempfile
import os
import re
from pathlib import Path

from src.services.crypto import (
    CryptoService, EncryptedData,
    SALT_SIZE, NONCE_SIZE, KEY_SIZE,
    is_crypto_available
)


class TestKeyDerivation:
    """Tests for secure key derivation."""

    @pytest.fixture
    def crypto(self):
        """Create crypto service."""
        return CryptoService()

    def test_salt_is_random(self, crypto):
        """Test that each encryption uses unique random salt."""
        salts = set()
        for _ in range(10):
            encrypted = crypto.encrypt(b"test data", "password")
            salts.add(encrypted.salt)

        # All salts should be unique
        assert len(salts) == 10

    def test_salt_correct_size(self, crypto):
        """Test salt is correct size for Argon2."""
        encrypted = crypto.encrypt(b"test data", "password")

        # PyNaCl Argon2 requires exactly 16 bytes
        assert len(encrypted.salt) == SALT_SIZE
        assert SALT_SIZE == 16

    def test_nonce_is_random(self, crypto):
        """Test that each encryption uses unique random nonce."""
        nonces = set()
        for _ in range(10):
            encrypted = crypto.encrypt(b"test data", "password")
            nonces.add(encrypted.nonce)

        # All nonces should be unique
        assert len(nonces) == 10

    def test_nonce_correct_size(self, crypto):
        """Test nonce is correct size for XSalsa20."""
        encrypted = crypto.encrypt(b"test data", "password")

        # XSalsa20 requires 24 bytes
        assert len(encrypted.nonce) == NONCE_SIZE
        assert NONCE_SIZE == 24

    def test_key_size_is_256_bits(self):
        """Test derived keys are 256 bits (32 bytes)."""
        assert KEY_SIZE == 32

    def test_same_password_different_salt_produces_different_ciphertext(self, crypto):
        """Test same password with different salt produces different ciphertext."""
        data = b"test data"
        password = "same_password"

        encrypted1 = crypto.encrypt(data, password)
        encrypted2 = crypto.encrypt(data, password)

        # Ciphertexts should be different due to different salt/nonce
        assert encrypted1.ciphertext != encrypted2.ciphertext

    def test_password_not_stored(self, crypto):
        """Test password is never stored in encrypted data."""
        password = "super_secret_password_12345"
        encrypted = crypto.encrypt(b"test data", password)

        # Serialize to check what's stored
        serialized = encrypted.to_bytes()

        # Password should not appear anywhere
        assert password.encode() not in serialized
        assert password.encode() not in encrypted.ciphertext
        assert password.encode() not in encrypted.salt
        assert password.encode() not in encrypted.nonce


class TestPasswordSecurity:
    """Tests for password handling security."""

    @pytest.fixture
    def crypto(self):
        """Create crypto service."""
        return CryptoService()

    def test_empty_password_behavior(self, crypto):
        """Test empty password behavior.

        Note: Current implementation allows empty passwords.
        This test documents the behavior - consider adding validation
        in production to require minimum password length.
        """
        # Currently empty password is allowed - documenting behavior
        encrypted = crypto.encrypt(b"test data", "")

        # Should still be able to decrypt with empty password
        decrypted = crypto.decrypt(encrypted, "")
        assert decrypted == b"test data"

        # Wrong password should still fail
        with pytest.raises(Exception):
            crypto.decrypt(encrypted, "wrong")

    def test_unicode_password_supported(self, crypto):
        """Test unicode passwords work correctly."""
        password = "पासवर्ड123🔐"  # Hindi + emoji
        data = b"test data"

        encrypted = crypto.encrypt(data, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == data

    def test_very_long_password_supported(self, crypto):
        """Test very long passwords work."""
        password = "a" * 1000
        data = b"test data"

        encrypted = crypto.encrypt(data, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == data

    def test_special_characters_in_password(self, crypto):
        """Test passwords with special characters."""
        password = "p@$$w0rd!@#$%^&*()_+-=[]{}|;':\",./<>?"
        data = b"test data"

        encrypted = crypto.encrypt(data, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == data

    def test_wrong_password_fails_authentication(self, crypto):
        """Test wrong password fails to decrypt."""
        encrypted = crypto.encrypt(b"test data", "correct_password")

        with pytest.raises(Exception):
            crypto.decrypt(encrypted, "wrong_password")

    def test_similar_password_fails(self, crypto):
        """Test similar but different password fails."""
        encrypted = crypto.encrypt(b"test data", "password123")

        # Try common mistakes
        wrong_passwords = [
            "Password123",  # Case difference
            "password1234",  # Extra char
            "password12",   # Missing char
            "password123 ", # Trailing space
            " password123", # Leading space
        ]

        for wrong in wrong_passwords:
            with pytest.raises(Exception):
                crypto.decrypt(encrypted, wrong)


class TestRecoveryKeySecurity:
    """Tests for recovery key security."""

    @pytest.fixture
    def crypto(self):
        """Create crypto service."""
        return CryptoService()

    def test_recovery_key_is_64_hex_chars(self, crypto):
        """Test recovery key is exactly 64 hex characters (256 bits)."""
        recovery_key = crypto.generate_recovery_key()

        # Remove formatting (dashes)
        clean_key = recovery_key.replace("-", "")

        assert len(clean_key) == 64
        assert all(c in "0123456789abcdef" for c in clean_key)

    def test_recovery_key_is_random(self, crypto):
        """Test each recovery key is unique."""
        keys = set()
        for _ in range(10):
            key = crypto.generate_recovery_key()
            keys.add(key)

        assert len(keys) == 10

    def test_recovery_key_format(self, crypto):
        """Test recovery key format.

        Current implementation returns raw hex without formatting.
        The recovery_key_to_bytes method handles stripping dashes
        if user adds them for readability.
        """
        recovery_key = crypto.generate_recovery_key()

        # Current format: 64 hex chars without dashes
        assert len(recovery_key) == 64
        assert all(c in "0123456789abcdef" for c in recovery_key)

        # User can add dashes for readability - the code handles it
        formatted_key = "-".join([recovery_key[i:i+8] for i in range(0, 64, 8)])
        key_bytes = crypto.recovery_key_to_bytes(formatted_key)
        assert len(key_bytes) == 32  # 256 bits

    def test_recovery_key_can_decrypt(self, crypto):
        """Test recovery key can decrypt data."""
        recovery_key = crypto.generate_recovery_key()
        data = b"sensitive patient data"

        encrypted = crypto.encrypt_with_recovery_key(data, recovery_key)
        decrypted = crypto.decrypt_with_recovery_key(encrypted, recovery_key)

        assert decrypted == data

    def test_wrong_recovery_key_fails(self, crypto):
        """Test wrong recovery key fails to decrypt."""
        recovery_key = crypto.generate_recovery_key()
        wrong_key = crypto.generate_recovery_key()

        encrypted = crypto.encrypt_with_recovery_key(b"data", recovery_key)

        with pytest.raises(Exception):
            crypto.decrypt_with_recovery_key(encrypted, wrong_key)


class TestEncryptedDataIntegrity:
    """Tests for encrypted data integrity and tamper detection."""

    @pytest.fixture
    def crypto(self):
        """Create crypto service."""
        return CryptoService()

    def test_tampered_ciphertext_detected(self, crypto):
        """Test tampering with ciphertext is detected."""
        encrypted = crypto.encrypt(b"test data", "password")

        # Tamper with ciphertext
        tampered_ciphertext = bytes([
            encrypted.ciphertext[0] ^ 0xFF
        ]) + encrypted.ciphertext[1:]

        tampered = EncryptedData(
            ciphertext=tampered_ciphertext,
            salt=encrypted.salt,
            nonce=encrypted.nonce
        )

        with pytest.raises(Exception):
            crypto.decrypt(tampered, "password")

    def test_tampered_salt_detected(self, crypto):
        """Test tampering with salt is detected."""
        encrypted = crypto.encrypt(b"test data", "password")

        # Tamper with salt (changes derived key)
        tampered_salt = bytes([
            encrypted.salt[0] ^ 0xFF
        ]) + encrypted.salt[1:]

        tampered = EncryptedData(
            ciphertext=encrypted.ciphertext,
            salt=tampered_salt,
            nonce=encrypted.nonce
        )

        with pytest.raises(Exception):
            crypto.decrypt(tampered, "password")

    def test_tampered_nonce_detected(self, crypto):
        """Test tampering with nonce is detected."""
        encrypted = crypto.encrypt(b"test data", "password")

        # Tamper with nonce
        tampered_nonce = bytes([
            encrypted.nonce[0] ^ 0xFF
        ]) + encrypted.nonce[1:]

        tampered = EncryptedData(
            ciphertext=encrypted.ciphertext,
            salt=encrypted.salt,
            nonce=tampered_nonce
        )

        with pytest.raises(Exception):
            crypto.decrypt(tampered, "password")

    def test_truncated_ciphertext_detected(self, crypto):
        """Test truncated ciphertext is detected."""
        encrypted = crypto.encrypt(b"test data" * 100, "password")

        truncated = EncryptedData(
            ciphertext=encrypted.ciphertext[:10],  # Truncate
            salt=encrypted.salt,
            nonce=encrypted.nonce
        )

        with pytest.raises(Exception):
            crypto.decrypt(truncated, "password")


class TestFileEncryptionSecurity:
    """Tests for file encryption security."""

    @pytest.fixture
    def crypto(self):
        """Create crypto service."""
        return CryptoService()

    def test_encrypted_file_not_readable(self, crypto):
        """Test encrypted file content is not readable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with recognizable content
            original = Path(tmpdir) / "original.txt"
            original.write_text("PATIENT NAME: John Smith\nDIAGNOSIS: Diabetes")

            encrypted = Path(tmpdir) / "encrypted.bin"

            crypto.encrypt_file(original, encrypted, "password")

            # Encrypted file should not contain plaintext
            encrypted_content = encrypted.read_bytes()
            assert b"PATIENT" not in encrypted_content
            assert b"John Smith" not in encrypted_content
            assert b"Diabetes" not in encrypted_content

    def test_encrypted_file_header_not_recognizable(self, crypto):
        """Test encrypted file has no recognizable file type header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a text file
            original = Path(tmpdir) / "original.txt"
            original.write_text("Hello World")

            encrypted = Path(tmpdir) / "encrypted.bin"
            crypto.encrypt_file(original, encrypted, "password")

            # Check it doesn't have common file headers
            content = encrypted.read_bytes()

            # Not a ZIP file
            assert not content.startswith(b"PK")
            # Not a text file with BOM
            assert not content.startswith(b"\xef\xbb\xbf")
            # Not JSON
            assert not content.startswith(b"{")
            assert not content.startswith(b"[")


class TestCryptoAvailability:
    """Tests for graceful handling when crypto is unavailable."""

    def test_crypto_availability_check(self):
        """Test crypto availability can be checked."""
        result = is_crypto_available()
        assert isinstance(result, bool)

    def test_crypto_available_in_test_environment(self):
        """Test crypto is available in our test environment."""
        # This should be True since we're testing crypto
        assert is_crypto_available() is True


class TestSecureMemoryHandling:
    """Tests for secure memory handling (best effort)."""

    @pytest.fixture
    def crypto(self):
        """Create crypto service."""
        return CryptoService()

    def test_decrypt_returns_bytes_not_string(self, crypto):
        """Test decryption returns bytes, not string (for secure handling)."""
        encrypted = crypto.encrypt(b"test data", "password")
        decrypted = crypto.decrypt(encrypted, "password")

        # Should be bytes for secure memory handling
        assert isinstance(decrypted, bytes)

    def test_multiple_decrypt_operations_independent(self, crypto):
        """Test multiple decrypt operations don't interfere."""
        data1 = b"data one"
        data2 = b"data two"

        enc1 = crypto.encrypt(data1, "pass1")
        enc2 = crypto.encrypt(data2, "pass2")

        dec1 = crypto.decrypt(enc1, "pass1")
        dec2 = crypto.decrypt(enc2, "pass2")

        assert dec1 == data1
        assert dec2 == data2
