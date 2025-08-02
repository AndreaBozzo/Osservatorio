#!/usr/bin/env python3
"""
Day 6: Import Standardization Script

Standardizes import patterns across the codebase according to PEP 8:
1. Standard library imports
2. Related third-party imports
3. Local application/library imports

Each group separated by blank lines and sorted alphabetically.
"""
from pathlib import Path
from typing import List, Tuple

from utils import ScriptContext, print_error, print_info, print_step, print_success


class ImportStandardizer:
    """Standardizes Python import statements according to PEP 8."""

    def __init__(self):
        self.standard_library_modules = {
            # Core built-in modules
            "abc",
            "argparse",
            "ast",
            "asyncio",
            "atexit",
            "base64",
            "bisect",
            "builtins",
            "calendar",
            "collections",
            "concurrent",
            "configparser",
            "contextlib",
            "copy",
            "csv",
            "datetime",
            "decimal",
            "enum",
            "functools",
            "gc",
            "glob",
            "hashlib",
            "heapq",
            "html",
            "http",
            "importlib",
            "io",
            "itertools",
            "json",
            "logging",
            "math",
            "multiprocessing",
            "os",
            "pathlib",
            "pickle",
            "re",
            "shutil",
            "socket",
            "sqlite3",
            "ssl",
            "string",
            "subprocess",
            "sys",
            "tempfile",
            "threading",
            "time",
            "traceback",
            "typing",
            "unittest",
            "urllib",
            "uuid",
            "warnings",
            "weakref",
            "xml",
            "zipfile",
            "zlib",
        }

        self.third_party_modules = {
            # Common third-party packages
            "aiofiles",
            "aiohttp",
            "alembic",
            "click",
            "duckdb",
            "fastapi",
            "httpx",
            "jinja2",
            "msal",
            "numpy",
            "pandas",
            "pydantic",
            "pytest",
            "redis",
            "requests",
            "sqlalchemy",
            "starlette",
            "uvicorn",
            "dotenv",
        }

    def classify_import(self, import_name: str, is_relative: bool = False) -> str:
        """Classify import as standard library, third-party, or local."""
        if is_relative:
            return "local"

        # Get the top-level module name
        top_level = import_name.split(".")[0]

        if top_level in self.standard_library_modules:
            return "standard"
        elif top_level in self.third_party_modules:
            return "third_party"
        elif top_level in ("src", "tests", "scripts"):
            return "local"
        else:
            # If unknown, assume third-party (safer than local)
            return "third_party"

    def parse_imports(
        self, content: str
    ) -> Tuple[List[str], List[str], List[str], str]:
        """Parse imports from file content."""
        lines = content.split("\n")

        # Find import section (after docstring, before first non-import)
        import_start = 0
        import_end = len(lines)

        # Skip docstring
        in_docstring = False
        docstring_quotes = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle docstrings
            if not in_docstring and stripped.startswith(('"""', "'''")):
                in_docstring = True
                docstring_quotes = stripped[:3]
                if stripped.count(docstring_quotes) >= 2:
                    in_docstring = False
                    import_start = i + 1
                continue
            elif in_docstring and docstring_quotes and docstring_quotes in stripped:
                in_docstring = False
                import_start = i + 1
                continue
            elif in_docstring:
                continue

            # Skip empty lines and comments at the start
            if not stripped or stripped.startswith("#"):
                if import_start == i:
                    import_start += 1
                continue

            # If we hit non-import code, stop
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                import_end = i
                break

        # Extract import lines
        import_lines = lines[import_start:import_end]
        before_imports = "\n".join(lines[:import_start])
        after_imports = "\n".join(lines[import_end:])

        # Parse imports
        standard_imports = []
        third_party_imports = []
        local_imports = []

        current_import = ""

        for line in import_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Handle multi-line imports
            if current_import:
                current_import += " " + stripped
                if not stripped.endswith(("\\", ",")):
                    self._classify_and_add_import(
                        current_import,
                        standard_imports,
                        third_party_imports,
                        local_imports,
                    )
                    current_import = ""
            else:
                if stripped.endswith(("\\", ",")) and "(" not in stripped:
                    current_import = stripped
                else:
                    self._classify_and_add_import(
                        stripped, standard_imports, third_party_imports, local_imports
                    )

        return (
            standard_imports,
            third_party_imports,
            local_imports,
            before_imports + after_imports,
        )

    def _classify_and_add_import(
        self, import_line: str, standard: List, third_party: List, local: List
    ):
        """Classify and add import to appropriate list."""
        import_line = import_line.strip()

        if import_line.startswith("from ."):
            # Relative import
            local.append(import_line)
        elif import_line.startswith("from "):
            # from X import Y
            module_name = import_line.split()[1]
            category = self.classify_import(module_name, module_name.startswith("."))
        elif import_line.startswith("import "):
            # import X
            module_name = import_line.split()[1].split(",")[0]
            category = self.classify_import(module_name)
        else:
            category = "third_party"  # Default

        if category == "standard":
            standard.append(import_line)
        elif category == "third_party":
            third_party.append(import_line)
        else:
            local.append(import_line)

    def format_imports(
        self, standard: List[str], third_party: List[str], local: List[str]
    ) -> str:
        """Format imports according to PEP 8."""
        result = []

        if standard:
            result.extend(sorted(standard))
            result.append("")

        if third_party:
            result.extend(sorted(third_party))
            result.append("")

        if local:
            result.extend(sorted(local))
            result.append("")

        # Remove trailing empty line
        while result and result[-1] == "":
            result.pop()

        return "\n".join(result)

    def standardize_file(self, file_path: Path) -> bool:
        """Standardize imports in a single file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            standard, third_party, local, rest = self.parse_imports(content)
            formatted_imports = self.format_imports(standard, third_party, local)

            # Reconstruct file
            lines = content.split("\n")

            # Find where imports start and end
            import_start = 0
            import_end = len(lines)

            # Skip docstring and initial comments
            in_docstring = False
            docstring_quotes = None

            for i, line in enumerate(lines):
                stripped = line.strip()

                if not in_docstring and stripped.startswith(('"""', "'''")):
                    in_docstring = True
                    docstring_quotes = stripped[:3]
                    if stripped.count(docstring_quotes) >= 2:
                        in_docstring = False
                        import_start = i + 1
                    continue
                elif in_docstring and docstring_quotes and docstring_quotes in stripped:
                    in_docstring = False
                    import_start = i + 1
                    continue
                elif in_docstring:
                    continue

                if not stripped or stripped.startswith("#"):
                    if import_start == i:
                        import_start += 1
                    continue

                if not (stripped.startswith("import ") or stripped.startswith("from ")):
                    import_end = i
                    break

            # Reconstruct file
            before = "\n".join(lines[:import_start])
            after = "\n".join(lines[import_end:])

            new_content = before
            if formatted_imports:
                if before and not before.endswith("\n"):
                    new_content += "\n"
                new_content += formatted_imports
                if after and not formatted_imports.endswith("\n"):
                    new_content += "\n"
            new_content += after

            # Only write if changed
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True

            return False

        except Exception as e:
            print_error(f"Error processing {file_path}", str(e))
            return False


def main():
    """Main function to standardize imports across the codebase."""
    with ScriptContext(
        "import_standardizer", "Import Standardization", "PEP 8 import ordering"
    ):
        standardizer = ImportStandardizer()

        # Directories to process
        directories = [
            Path("src"),
            Path("tests"),
            Path("scripts"),
        ]

        total_files = 0
        modified_files = 0

        for directory in directories:
            if not directory.exists():
                print_error(f"Directory not found: {directory}")
                continue

            print_step(total_files + 1, f"Processing {directory}")

            for py_file in directory.rglob("*.py"):
                total_files += 1

                if standardizer.standardize_file(py_file):
                    modified_files += 1
                    print_info(f"Standardized: {py_file}")

        print_success(
            f"Import standardization completed",
            f"Modified {modified_files} out of {total_files} files",
        )


if __name__ == "__main__":
    main()
