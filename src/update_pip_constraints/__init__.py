"""Pin all package requirements to a constraint file with ``uv pip compile``.

See `Constraints Files <https://pip.pypa.io/en/stable/user_guide/#constraints-files>`_
and `uv pip compile <https://docs.astral.sh/uv/pip/compile>`_.
"""

from __future__ import annotations

import re
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.specifiers import SpecifierSet

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(description="Update pip constraints file")
    versions = parser.add_mutually_exclusive_group()
    versions.add_argument(
        "-p",
        "--python-version",
        default=_get_python_version(),
        help="Python version to use. E.g. 3.9, 3.10, 3.11, etc.",
        type=str,
    )
    versions.add_argument(
        "--all",
        action="store_true",
        help="Update the constraint files for all Python versions that the package supports.",
    )
    args = parser.parse_args(argv)
    python_versions = (
        _get_supported_python_versions() if args.all else [args.python_version]
    )
    exit_code = 0
    for python_version in python_versions:
        output_file = _form_constraint_file_path(python_version)
        exit_code |= update_constraints_file(
            output_file, python_version, ["setuptools"]
        )
    return exit_code


def _get_python_version() -> str:
    v = sys.version_info
    return f"{v.major}.{v.minor}"


def _get_supported_python_versions() -> list[str]:
    """Determine the supported Python versions from the package metadata.

    The versions are taken from the ``Programming Language :: Python :: 3.X``
    classifiers or, if there are none, from the minimal Python version.
    """
    classifiers, requires_python = _get_python_metadata()
    prefix = "Programming Language :: Python :: "
    versions = [
        c[len(prefix) :]
        for c in classifiers
        if re.fullmatch(rf"{re.escape(prefix)}3\.\d+", c)
    ]
    if not versions and requires_python:
        specifier = SpecifierSet(requires_python)
        versions = [f"3.{minor}" for minor in range(6, 16) if f"3.{minor}" in specifier]
    if not versions:
        msg = "Could not determine the supported Python versions from the package metadata"
        raise ValueError(msg)
    return sorted(set(versions), key=lambda v: int(v.split(".")[1]))


def _get_python_metadata() -> tuple[list[str], str]:
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        with pyproject.open("rb") as f:
            project = tomllib.load(f).get("project")
        if project is not None:
            return project.get("classifiers", []), project.get("requires-python", "")
    if Path("setup.cfg").exists():
        cfg = ConfigParser()
        cfg.read("setup.cfg")
        classifiers = cfg.get("metadata", "classifiers", fallback="").split("\n")
        requires_python = cfg.get("options", "python_requires", fallback="")
        return [c.strip() for c in classifiers if c.strip()], requires_python.strip()
    return [], ""


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
