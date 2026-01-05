"""
Test Watcher for DocAssist EMR

Watches for file changes and runs relevant tests automatically.
"""

import time
import subprocess
from pathlib import Path
from typing import List, Set
import sys


class TestWatcher:
    """Watch for file changes and run relevant tests"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.watch_dirs = [
            self.project_root / 'src',
            self.project_root / 'tests',
        ]
        self.last_modified = {}
        self.debounce_seconds = 1

    def get_test_files_for_change(self, changed_file: Path) -> List[str]:
        """Determine which tests to run based on changed file"""
        rel_path = str(changed_file.relative_to(self.project_root))

        # Direct test mapping
        test_mapping = {
            'src/services/database.py': ['tests/unit/test_database.py'],
            'src/services/llm.py': ['tests/unit/test_llm.py'],
            'src/services/rag.py': ['tests/unit/test_rag.py'],
            'src/services/pdf.py': ['tests/unit/test_pdf.py'],
            'src/models/schemas.py': ['tests/models/test_schemas.py', 'tests/unit/test_schemas.py'],
        }

        # Check for direct mapping
        if rel_path in test_mapping:
            return test_mapping[rel_path]

        # Pattern-based mapping
        if 'src/services/drugs/' in rel_path:
            return ['tests/test_drug_safety.py']

        if 'src/services/diagnosis/' in rel_path:
            return ['tests/test_diagnosis_engine.py']

        if 'src/services/clinical/' in rel_path:
            return ['tests/test_clinical_*.py']

        if 'src/ui/' in rel_path:
            return ['tests/smoke/']

        # If a test file changed, run that test
        if rel_path.startswith('tests/'):
            return [rel_path]

        # Default: run all unit tests
        return ['tests/unit/']

    def get_changed_files(self) -> Set[Path]:
        """Get files that have changed since last check"""
        changed = set()

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue

            for py_file in watch_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue

                mtime = py_file.stat().st_mtime

                if py_file not in self.last_modified:
                    self.last_modified[py_file] = mtime
                elif mtime > self.last_modified[py_file]:
                    changed.add(py_file)
                    self.last_modified[py_file] = mtime

        return changed

    def run_tests(self, test_paths: List[str]):
        """Run tests for given paths"""
        # Remove duplicates
        test_paths = list(set(test_paths))

        print("\n" + "="*70)
        print(f"Running tests: {', '.join(test_paths)}")
        print("="*70 + "\n")

        # Build pytest command
        cmd = ['pytest'] + test_paths + ['-v', '--tb=short', '--maxfail=3']

        # Run tests
        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode == 0:
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Some tests failed")

        return result.returncode

    def run(self):
        """Run the watcher"""
        print("DocAssist EMR Test Watcher")
        print("="*70)
        print("Watching for changes in:")
        for watch_dir in self.watch_dirs:
            print(f"  - {watch_dir}")
        print("\nPress Ctrl+C to stop")
        print("="*70)

        # Initial scan
        self.get_changed_files()

        try:
            while True:
                time.sleep(self.debounce_seconds)

                changed_files = self.get_changed_files()

                if changed_files:
                    # Collect all tests to run
                    tests_to_run = []
                    for changed_file in changed_files:
                        rel_path = changed_file.relative_to(self.project_root)
                        print(f"\n→ Detected change: {rel_path}")

                        test_files = self.get_test_files_for_change(changed_file)
                        tests_to_run.extend(test_files)

                    # Run tests
                    if tests_to_run:
                        self.run_tests(tests_to_run)

        except KeyboardInterrupt:
            print("\n\nStopping test watcher...")


def main():
    """Main entry point"""
    watcher = TestWatcher()
    watcher.run()


if __name__ == '__main__':
    main()
