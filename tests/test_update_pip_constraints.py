import re
from pathlib import Path

import pytest

from update_pip_constraints import (
    _form_constraint_file_path,
    _get_python_version,
    update_constraints_file,
)


def test_form_constraint_file_path():
    path = _form_constraint_file_path("3.8")
    assert str(path) == ".constraints/py3.8.txt"


def test_get_python_version():
    python_version = _get_python_version()
    assert re.match(r"^[23]\.[0-9]+$", python_version) is not None


@pytest.mark.slow()
def test_update_constraints_file():
    this_directory = Path(__file__).parent.absolute()
    output_file = this_directory / "constraints.txt"
    with pytest.raises(SystemExit) as error:
        update_constraints_file(output_file)
    assert error.type is SystemExit
    assert error.value.code == 0
    with open(output_file) as stream:
        content = stream.read()
    expected_packages = [
        "black",
        "flake8",
        "pip-tools",
        "pylint",
        "pytest",
        "tox",
    ]
    for package in expected_packages:
        assert f"\n{package}==" in content
