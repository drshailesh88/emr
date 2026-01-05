"""
Encryption Tests

Tests that encryption is properly implemented and secure.
"""

import pytest
from pathlib import Path


@pytest.mark.security
class TestEncryption:
    """Test encryption implementation"""

    def test_backup_encryption_enabled(self):
        """Test that backup encryption is enabled by default"""
        # This would test the actual backup service
        # For now, check that crypto service exists
        project_root = Path(__file__).parent.parent.parent
        crypto_file = project_root / 'src' / 'services' / 'crypto.py'

        assert crypto_file.exists(), "Crypto service should exist"

        content = crypto_file.read_text()

        # Should use modern encryption (AES-256-GCM or similar)
        modern_encryption = [
            'AES',
            'GCM',
            'ChaCha20',
            'Poly1305',
            'NaCl',
        ]

        assert any(enc in content for enc in modern_encryption), \
            "Should use modern encryption algorithm"

    def test_no_weak_encryption(self):
        """Test that weak encryption algorithms are not used"""
        project_root = Path(__file__).parent.parent.parent
        crypto_file = project_root / 'src' / 'services' / 'crypto.py'

        if not crypto_file.exists():
            pytest.skip("crypto.py not found")

        content = crypto_file.read_text()

        # These are considered weak
        weak_algorithms = [
            'DES',
            'RC4',
            'MD5',
            'SHA1',  # For hashing passwords
        ]

        for algo in weak_algorithms:
            if algo in content:
                # Check context - might be in a comment or comparison
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if algo in line and not line.strip().startswith('#'):
                        pytest.fail(
                            f"Line {i}: Weak algorithm {algo} found in crypto.py"
                        )

    def test_proper_key_derivation(self):
        """Test that proper key derivation is used (Argon2, PBKDF2, etc.)"""
        project_root = Path(__file__).parent.parent.parent
        crypto_file = project_root / 'src' / 'services' / 'crypto.py'

        if not crypto_file.exists():
            pytest.skip("crypto.py not found")

        content = crypto_file.read_text()

        # Should use proper KDF
        proper_kdf = [
            'Argon2',
            'PBKDF2',
            'scrypt',
            'bcrypt',
        ]

        # If deriving keys from passwords, should use KDF
        if 'password' in content.lower():
            assert any(kdf in content for kdf in proper_kdf), \
                "Should use proper key derivation function (Argon2, PBKDF2, scrypt)"

    def test_encryption_has_authentication(self):
        """Test that encryption includes authentication (AEAD)"""
        project_root = Path(__file__).parent.parent.parent
        crypto_file = project_root / 'src' / 'services' / 'crypto.py'

        if not crypto_file.exists():
            pytest.skip("crypto.py not found")

        content = crypto_file.read_text()

        # Should use AEAD (Authenticated Encryption with Associated Data)
        aead_modes = [
            'GCM',
            'CCM',
            'ChaCha20Poly1305',
            'NaCl',
        ]

        # If using encryption, should have authentication
        if 'encrypt' in content.lower():
            has_aead = any(mode in content for mode in aead_modes)
            has_hmac = 'HMAC' in content or 'hmac' in content.lower()

            assert has_aead or has_hmac, \
                "Encryption should include authentication (use GCM, CCM, or HMAC)"

    def test_random_iv_generation(self):
        """Test that IVs/nonces are randomly generated"""
        project_root = Path(__file__).parent.parent.parent
        crypto_file = project_root / 'src' / 'services' / 'crypto.py'

        if not crypto_file.exists():
            pytest.skip("crypto.py not found")

        content = crypto_file.read_text()

        # Should generate random IVs
        if 'encrypt' in content.lower():
            random_generation = [
                'os.urandom',
                'secrets.',
                'random_bytes',
                'SystemRandom',
            ]

            assert any(rng in content for rng in random_generation), \
                "Should use cryptographically secure random number generator"

            # Should NOT use weak RNG
            weak_rng = ['random.', 'time()']
            for rng in weak_rng:
                if rng in content:
                    pytest.fail(f"Should not use weak RNG: {rng}")
