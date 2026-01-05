"""
Import Validator

Validates that all Python modules can be imported without errors.
"""

import sys
import importlib
from pathlib import Path
from typing import Tuple, List


class ImportValidator:
    """Validate all imports work"""

    name = "Import Validator"

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.errors = []

    def validate(self) -> Tuple[bool, str]:
        """Validate all imports"""
        sys.path.insert(0, str(self.project_root))

        # Find all Python files
        python_files = self._find_python_files()

        # Try importing each module
        failed_imports = []
        for py_file in python_files:
            module_name = self._get_module_name(py_file)
            if module_name:
                try:
                    importlib.import_module(module_name)
                except Exception as e:
                    failed_imports.append(f"{module_name}: {str(e)}")

        if failed_imports:
            message = f"Failed to import {len(failed_imports)} module(s):\n"
            message += "\n".join(f"  - {err}" for err in failed_imports[:5])
            if len(failed_imports) > 5:
                message += f"\n  ... and {len(failed_imports) - 5} more"
            return False, message

        return True, f"All {len(python_files)} modules imported successfully"

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in src/"""
        src_dir = self.project_root / 'src'
        if not src_dir.exists():
            return []

        python_files = []
        for py_file in src_dir.rglob('*.py'):
            # Skip __pycache__
            if '__pycache__' in str(py_file):
                continue
            python_files.append(py_file)

        return python_files

    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            # Convert path to module name: src/services/database.py -> src.services.database
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            return '.'.join(module_parts)
        except ValueError:
            return None
