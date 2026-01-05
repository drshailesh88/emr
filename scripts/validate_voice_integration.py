"""Validation script for voice integration - checks code structure without dependencies."""

import ast
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_file(file_path: Path) -> dict:
    """Validate a Python file can be parsed."""
    try:
        with open(file_path) as f:
            code = f.read()

        # Try to parse the AST
        ast.parse(code)

        # Count classes and functions
        tree = ast.parse(code)
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        return {
            "valid": True,
            "classes": classes,
            "functions": functions,
            "lines": len(code.splitlines()),
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
        }


def main():
    """Validate all voice integration files."""

    files_to_check = [
        "src/services/voice/whisper_manager.py",
        "src/services/voice/audio_processor.py",
        "src/ui/components/voice_status_indicator.py",
        "src/ui/components/voice_input_button_enhanced.py",
        "tests/test_voice_integration.py",
        "examples/voice_integration_example.py",
    ]

    print("=" * 70)
    print("Voice Integration Validation")
    print("=" * 70)
    print()

    all_valid = True

    for file_path in files_to_check:
        full_path = Path(file_path)

        if not full_path.exists():
            print(f"❌ {file_path}: FILE NOT FOUND")
            all_valid = False
            continue

        result = validate_file(full_path)

        if result["valid"]:
            print(f"✅ {file_path}")
            print(f"   Classes: {len(result['classes'])}")
            print(f"   Functions: {len(result['functions'])}")
            print(f"   Lines: {result['lines']}")
        else:
            print(f"❌ {file_path}: {result['error']}")
            all_valid = False

        print()

    print("=" * 70)
    if all_valid:
        print("✅ All voice integration files are valid!")
    else:
        print("❌ Some files have issues")
    print("=" * 70)

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
