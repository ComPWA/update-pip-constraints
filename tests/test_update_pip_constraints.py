import os
import re
from pathlib import Path

import pytest

from update_pip_constraints import (
    _find_setup_file,  # pyright: ignore[reportPrivateUsage]
    _form_constraint_file_path,  # pyright: ignore[reportPrivateUsage]
    _get_python_version,  # pyright: ignore[reportPrivateUsage]
    update_constraints_file,
)

SETUP_CFG = """\
[metadata]
name = my-package

[options]
python_requires = >=3.6
install_requires =
    attrs

[options.extras_require]
test =
    pytest
"""


def test_form_constraint_file_path():
    path = _form_constraint_file_path("3.8")
    assert str(path) == ".constraints/py3.8.txt"


def test_get_python_version():
    python_version = _get_python_version()
    assert re.match(r"^[23]\.[0-9]+$", python_version) is not None


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        ({"pyproject.toml": '[project]\nname = "x"\n'}, "pyproject.toml"),
        ({"pyproject.toml": "[tool.ruff]\n", "setup.cfg": ""}, "setup.cfg"),
        ({"setup.py": ""}, "setup.py"),
    ],
)
def test_find_setup_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    expected: str,
):
    monkeypatch.chdir(tmp_path)
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    assert _find_setup_file() == Path(expected)


def test_find_setup_file_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        _find_setup_file()


@pytest.mark.slow
def test_update_constraints_file_setup_cfg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    if "CI" in os.environ:
        pytest.skip()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "setup.cfg").write_text(SETUP_CFG)
    (tmp_path / "setup.py").write_text("from setuptools import setup\n\nsetup()\n")
    output_file = tmp_path / ".constraints" / "py3.6.txt"
    exit_code = update_constraints_file(output_file, "3.6", ["setuptools"])
    assert exit_code == 0
    content = output_file.read_text()
    assert "\nattrs==22.2.0\n" in content
    assert re.search(r"\npytest==7\.0\.\d+\n", content) is not None
