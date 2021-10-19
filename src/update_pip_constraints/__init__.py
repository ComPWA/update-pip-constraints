"""Pin all package requirements to a constraint file with ``pip-tools``.

See `Constraints Files
<https://pip.pypa.io/en/stable/user_guide/#constraints-files>_ and `pip-tools
<https://github.com/jazzband/pip-tools>`_.
"""

import sys
from pathlib import Path

from piptools.scripts import compile  # type: ignore[import]


def main() -> None:
    python_version = _get_python_version()
    output_file = _form_constraint_file_path(python_version)
    if update_constraints_file(output_file):
        raise RuntimeError("There were issues running pip-compile")


def _get_python_version() -> str:
    version = sys.version_info
    return f"{version.major}.{version.minor}"


def _form_constraint_file_path(python_version: str) -> Path:
    constraints_dir = Path(".constraints")
    return constraints_dir / f"py{python_version}.txt"


def update_constraints_file(output_file: Path) -> int:
    output_file.parent.mkdir(exist_ok=True)
    command_arguments = [
        "setup.py",
        "--extra dev",
        "--no-annotate",
        "--upgrade",
        "--strip-extras",
        f"-o {output_file}",
    ]
    command_line = " ".join(command_arguments)
    # pylint: disable=no-value-for-parameter
    return compile.cli(command_line.split(" "))


if "__main__" in __name__:
    main()
