"""
Syntax Validator

Validates Python syntax in all source files.
"""

import ast
from pathlib import Path
from typing import Tuple, List


class SyntaxValidator:
    """Validate Python syntax"""

    name = "Syntax Validator"

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.errors = []

    def validate(self) -> Tuple[bool, str]:
        """Validate syntax of all Python files"""
        python_files = self._find_python_files()

        syntax_errors = []
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                ast.parse(code, filename=str(py_file))
            except SyntaxError as e:
                rel_path = py_file.relative_to(self.project_root)
                syntax_errors.append(f"{rel_path}:{e.lineno}: {e.msg}")
            except Exception as e:
                rel_path = py_file.relative_to(self.project_root)
                syntax_errors.append(f"{rel_path}: {str(e)}")

        if syntax_errors:
            message = f"Found {len(syntax_errors)} syntax error(s):\n"
            message += "\n".join(f"  - {err}" for err in syntax_errors[:5])
            if len(syntax_errors) > 5:
                message += f"\n  ... and {len(syntax_errors) - 5} more"
            return False, message

        return True, f"All {len(python_files)} files have valid syntax"

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in src/ and tests/"""
        python_files = []

        for directory in ['src', 'tests']:
            dir_path = self.project_root / directory
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    if '__pycache__' not in str(py_file):
                        python_files.append(py_file)

        return python_files
