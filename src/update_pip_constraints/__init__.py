"""Pin all package requirements to a constraint file with ``pip-tools``.

See `Constraints Files
<https://pip.pypa.io/en/stable/user_guide/#constraints-files>_ and `pip-tools
<https://github.com/jazzband/pip-tools>`_.
"""

# fmt: off
import warnings  # noqa: I001
warnings.filterwarnings("ignore", category=UserWarning)

from setuptools import find_packages  # noqa: I001  # import setuptools first!
# fmt: on

import os
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import List, Optional

import toml
from piptools.scripts import compile  # type: ignore[import]

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version


def main() -> None:
    python_version = _get_python_version()
    output_file = _form_constraint_file_path(python_version)
    unsafe_packages = None
    if not os.path.exists("setup.cfg"):
        unsafe_packages = _get_main_packages()
        unsafe_packages.insert(0, "setuptools")
        unsafe_packages.insert(0, "pip")
    if update_constraints_file(output_file, unsafe_packages):
        msg = "There were issues running pip-compile"
        raise RuntimeError(msg)


def _get_python_version() -> str:
    version = sys.version_info
    return f"{version.major}.{version.minor}"


def _get_main_packages() -> List[str]:
    where = __get_package_directory()
    packages = find_packages(where)
    packages = [p.replace("_", "-") for p in packages]
    return [p for p in packages if "." not in p]


def __get_package_directory() -> str:
    if os.path.exists("setup.cfg"):
        cfg = ConfigParser()
        cfg.read("setup.cfg")
        if cfg.has_option("options", "package_dir"):
            return cfg.get("options", "package_dir").strip().strip("=")
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "rb") as f:
            pyproject = toml.load(f)  #  type: ignore[arg-type]
        setuptools_config = pyproject.get("tool", {}).get("setuptools", {})
        package_dir = setuptools_config.get("package-dir", {})
        where = package_dir.get("")
        if where is not None:
            return where
    return "."


def _form_constraint_file_path(python_version: str) -> Path:
    constraints_dir = Path(".constraints")
    return constraints_dir / f"py{python_version}.txt"


def update_constraints_file(
    output_file: Path, unsafe_packages: Optional[List[str]] = None
) -> int:
    output_file.parent.mkdir(exist_ok=True)
    command_arguments = [
        "-o",
        output_file,
        "--extra",
        "dev",
        "--no-annotate",
        "--strip-extras",
        "--upgrade",
    ]
    major, minor, *_ = (int(i) for i in version("pip-tools").split("."))
    if (major, minor) >= (6, 8):
        command_arguments.append("--resolver=backtracking")
    if unsafe_packages is not None:
        for package in unsafe_packages:
            command_arguments.append("--unsafe-package")
            command_arguments.append(package)
    return compile.cli(command_arguments)  # type: ignore[misc]


if "__main__" in __name__:
    main()
