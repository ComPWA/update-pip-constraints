"""Pin all package requirements to a constraint file with ``uv pip compile``.

See `Constraints Files <https://pip.pypa.io/en/stable/user_guide/#constraints-files>`_
and `uv pip compile <https://docs.astral.sh/uv/pip/compile>`_.
"""

from __future__ import annotations

import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(description="Update pip constraints file")
    parser.add_argument(
        "-p",
        "--python-version",
        default=_get_python_version(),
        help="Python version to use. E.g. 3.9, 3.10, 3.11, etc.",
        type=str,
    )
    args = parser.parse_args(argv)
    python_version = args.python_version
    output_file = _form_constraint_file_path(python_version)
    return update_constraints_file(output_file, python_version, ["setuptools"])


def _get_python_version() -> str:
    v = sys.version_info
    return f"{v.major}.{v.minor}"


def _form_constraint_file_path(python_version: str) -> Path:
    constraints_dir = Path(".constraints")
    return constraints_dir / f"py{python_version}.txt"


def _find_setup_file() -> Path:
    """Find the file that defines the package requirements.

    Packages configured with :file:`setup.cfg` or :file:`setup.py` are supported as
    well, so that constraints can still be generated for packages that support old
    Python versions.
    """
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        with pyproject.open("rb") as f:
            if "project" in tomllib.load(f):
                return pyproject
    for path in (Path("setup.cfg"), Path("setup.py")):
        if path.exists():
            return path
    msg = (
        "Could not find a pyproject.toml with a [project] table, setup.cfg, or setup.py"
    )
    raise FileNotFoundError(msg)


def update_constraints_file(
    output_file: Path, python_version: str, unsafe_packages: list[str]
) -> int:
    setup_file = _find_setup_file()
    output_file.parent.mkdir(exist_ok=True)
    command_arguments = [
        "uv",
        "pip",
        "compile",
        str(setup_file),
        "-o",
        str(output_file),
        "--all-extras",
        "--no-annotate",
        f"--python-version={python_version}",
        "--upgrade",
    ]
    for package in unsafe_packages:
        command_arguments.extend(("--no-emit-package", package))
    return subprocess.check_call(command_arguments)  # ruff: ignore[subprocess-without-shell-equals-true]


if __name__ == "__main__":
    raise SystemExit(main())
