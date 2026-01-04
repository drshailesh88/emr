"""Tests for the crypto service."""

import pytest
import tempfile
from pathlib import Path

# Skip if crypto not available
try:
    from src.services.crypto import (
        CryptoService, EncryptedData, DecryptionError,
        is_crypto_available, get_crypto_backend
    )
    CRYPTO_AVAILABLE = is_crypto_available()
except ImportError:
    CRYPTO_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not CRYPTO_AVAILABLE,
    reason="Cryptography libraries not available"
)


class TestCryptoService:
    """Tests for CryptoService."""

    @pytest.fixture
    def crypto(self):
        """Create a CryptoService instance."""
        return CryptoService()

    def test_encrypt_decrypt_roundtrip(self, crypto):
        """Test basic encryption and decryption."""
        plaintext = b"Hello, DocAssist! Patient data here."
        password = "secure_password_123"

        encrypted = crypto.encrypt(plaintext, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == plaintext

    def test_encrypt_produces_different_output(self, crypto):
        """Each encryption should produce different output (random nonce)."""
        plaintext = b"Same data"
        password = "password"

        encrypted1 = crypto.encrypt(plaintext, password)
        encrypted2 = crypto.encrypt(plaintext, password)

        # Ciphertexts should differ due to random nonce
        assert encrypted1.ciphertext != encrypted2.ciphertext
        assert encrypted1.nonce != encrypted2.nonce

    def test_wrong_password_fails(self, crypto):
        """Decryption with wrong password should fail."""
        plaintext = b"Secret data"
        encrypted = crypto.encrypt(plaintext, "correct_password")

        with pytest.raises(DecryptionError):
            crypto.decrypt(encrypted, "wrong_password")

    def test_recovery_key_generation(self, crypto):
        """Test recovery key generation."""
        key = crypto.generate_recovery_key()

        # Should be 64 hex characters (256 bits)
        assert len(key) == 64
        assert all(c in '0123456789abcdef' for c in key)

    def test_recovery_key_encryption(self, crypto):
        """Test encryption with recovery key."""
        plaintext = b"Data encrypted with recovery key"
        recovery_key = crypto.generate_recovery_key()

        encrypted = crypto.encrypt_with_recovery_key(plaintext, recovery_key)
        decrypted = crypto.decrypt_with_recovery_key(encrypted, recovery_key)

        assert decrypted == plaintext

    def test_recovery_key_formatting(self, crypto):
        """Test recovery key formatting for display."""
        key = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab5678cdef9012"
        formatted = crypto.format_recovery_key(key)

        # Should be grouped in 4s with spaces
        assert " " in formatted
        assert formatted.replace(" ", "") == key

    def test_encrypted_data_serialization(self, crypto):
        """Test EncryptedData serialization/deserialization."""
        plaintext = b"Test data"
        encrypted = crypto.encrypt(plaintext, "password")

        # Serialize to bytes
        data_bytes = encrypted.to_bytes()
        restored = EncryptedData.from_bytes(data_bytes)

        assert restored.ciphertext == encrypted.ciphertext
        assert restored.salt == encrypted.salt
        assert restored.nonce == encrypted.nonce
        assert restored.version == encrypted.version

        # Should still decrypt correctly
        decrypted = crypto.decrypt(restored, "password")
        assert decrypted == plaintext

    def test_encrypted_data_base64(self, crypto):
        """Test EncryptedData base64 encoding."""
        plaintext = b"Test data"
        encrypted = crypto.encrypt(plaintext, "password")

        # Encode to base64
        b64_string = encrypted.to_base64()
        assert isinstance(b64_string, str)

        # Decode and verify
        restored = EncryptedData.from_base64(b64_string)
        decrypted = crypto.decrypt(restored, "password")
        assert decrypted == plaintext

    def test_file_encryption(self, crypto):
        """Test file encryption and decryption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test file
            input_path = tmpdir / "test.txt"
            input_path.write_bytes(b"Secret file contents!")

            encrypted_path = tmpdir / "test.encrypted"
            decrypted_path = tmpdir / "test.decrypted.txt"

            password = "file_password"

            # Encrypt
            assert crypto.encrypt_file(input_path, encrypted_path, password)
            assert encrypted_path.exists()

            # Encrypted file should be different
            assert encrypted_path.read_bytes() != input_path.read_bytes()

            # Decrypt
            assert crypto.decrypt_file(encrypted_path, decrypted_path, password)
            assert decrypted_path.exists()

            # Content should match
            assert decrypted_path.read_bytes() == input_path.read_bytes()

    def test_checksum(self, crypto):
        """Test checksum computation and verification."""
        data = b"Data to checksum"

        checksum = crypto.compute_checksum(data)
        assert len(checksum) == 64  # SHA-256 hex

        # Verify
        assert crypto.verify_checksum(data, checksum)
        assert not crypto.verify_checksum(b"Different data", checksum)

    def test_large_data(self, crypto):
        """Test encryption of larger data."""
        # 1 MB of data
        plaintext = b"x" * (1024 * 1024)
        password = "password"

        encrypted = crypto.encrypt(plaintext, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == plaintext

    def test_unicode_password(self, crypto):
        """Test encryption with unicode password."""
        plaintext = b"Data"
        password = "पासवर्ड123"  # Hindi + numbers

        encrypted = crypto.encrypt(plaintext, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == plaintext

    def test_empty_data(self, crypto):
        """Test encryption of empty data."""
        plaintext = b""
        password = "password"

        encrypted = crypto.encrypt(plaintext, password)
        decrypted = crypto.decrypt(encrypted, password)

        assert decrypted == plaintext


class TestCryptoAvailability:
    """Tests for crypto availability checks."""

    def test_is_crypto_available(self):
        """Test crypto availability check."""
        assert is_crypto_available() == CRYPTO_AVAILABLE

    def test_get_crypto_backend(self):
        """Test getting crypto backend name."""
        backend = get_crypto_backend()
        assert backend in ["PyNaCl (libsodium)", "cryptography", "none"]
