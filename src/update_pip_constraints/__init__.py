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

import shutil
import os
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import List, Optional, Sequence
from argparse import ArgumentParser
import toml


def main(argv: Optional[Sequence[str]] = None) -> int:
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
    excludes: List[str] = []
    if shutil.which("uv") is None or not __uses_pyproject():
        excludes = [
            "pip",
            "setuptools",
            *_get_main_packages(),
        ]
        exit_code = update_constraints_file_py36(output_file, excludes)
    else:
        excludes = ["setuptools"]
        exit_code = update_constraints_file(output_file, python_version, excludes)
    if exit_code != 0:
        msg = "There were issues running pip-compile"
        raise RuntimeError(msg)
    return exit_code


def _get_python_version() -> str:
    v = sys.version_info
    return f"{v.major}.{v.minor}"


def _get_main_packages() -> List[str]:
    where = __get_package_directory()
    packages = find_packages(where)
    package_name = __get_package_name()
    if package_name is not None:
        packages.insert(0, package_name)
    packages = [p.replace("_", "-") for p in packages]
    packages = [p for p in packages if "." not in p]
    return sorted(set(packages))


def __get_package_name() -> Optional[str]:
    if os.path.exists("setup.cfg"):
        cfg = ConfigParser()
        cfg.read("setup.cfg")
        if cfg.has_option("metadata", "name"):
            return cfg.get("metadata", "name").strip().strip("=")
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml") as f:
            pyproject = toml.load(f)  #  type: ignore[arg-type]
        return pyproject.get("project", {}).get("name", None)
    return None


def __get_package_directory() -> str:
    if os.path.exists("setup.cfg"):
        cfg = ConfigParser()
        cfg.read("setup.cfg")
        if cfg.has_option("options", "package_dir"):
            return cfg.get("options", "package_dir").strip().strip("=")
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml") as f:
            pyproject = toml.load(f)  #  type: ignore[arg-type]
        setuptools_config = pyproject.get("tool", {}).get("setuptools", {})
        package_dir = setuptools_config.get("package-dir", {})
        where = package_dir.get("")
        if where is not None:
            return where
    return "."


def __uses_pyproject() -> bool:
    with open("pyproject.toml") as f:
        pyproject = toml.load(f)  #  type: ignore[arg-type]
    return pyproject.get("project", {}).get("name", None) is not None


def _form_constraint_file_path(python_version: str) -> Path:
    constraints_dir = Path(".constraints")
    return constraints_dir / f"py{python_version}.txt"


def update_constraints_file(
    output_file: Path, python_version: str, unsafe_packages: List[str]
) -> int:
    import subprocess  # noqa: PLC0415, S404

    if not __uses_pyproject():
        msg = "Package has to be configured with pyproject.toml"
        raise ValueError(msg)
    output_file.parent.mkdir(exist_ok=True)
    command_arguments = [
        "uv",
        "pip",
        "compile",
        "pyproject.toml",
        "-o",
        str(output_file),
        "--all-extras",
        "--no-annotate",
        f"--python-version={python_version}",
        "--upgrade",
    ]
    for package in unsafe_packages:
        command_arguments.append("--no-emit-package")
        command_arguments.append(package)
    return subprocess.check_call(command_arguments)  # noqa: S603


def update_constraints_file_py36(output_file: Path, unsafe_packages: List[str]) -> int:
    from piptools.scripts import compile  # type: ignore[import]  # noqa: PLC0415

    if sys.version_info < (3, 8):
        from importlib_metadata import version  # noqa: PLC0415
    else:
        from importlib.metadata import version  # noqa: PLC0415

    print("Resolving dependencies with pip-tools...")  # noqa: T201
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
    for package in unsafe_packages:
        command_arguments.append("--unsafe-package")
        command_arguments.append(package)
    return compile.cli(command_arguments)  # type: ignore[misc]


if __name__ == "__main__":
    raise SystemExit(main())
