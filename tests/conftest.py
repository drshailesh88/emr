"""Pytest configuration and fixtures for DocAssist tests.

This module configures imports to allow testing of individual services
without loading heavy dependencies (chromadb, sentence-transformers, etc.)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock heavy dependencies before they're imported
# This allows testing backup/crypto/sync without chromadb, sentence-transformers, etc.
MOCK_MODULES = [
    'chromadb',
    'chromadb.config',
    'chromadb.api',
    'sentence_transformers',
    'flet',
    'fpdf',
    'fpdf2',
]

for mod_name in MOCK_MODULES:
    if mod_name not in sys.modules:
        mock = MagicMock()
        # Make FPDF class available
        if mod_name == 'fpdf':
            mock.FPDF = MagicMock()
        sys.modules[mod_name] = mock
