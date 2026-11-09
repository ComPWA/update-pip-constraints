import os
import re
from pathlib import Path
from textwrap import dedent

import pytest

import update_pip_constraints
from update_pip_constraints import (
    _find_setup_file,  # pyright: ignore[reportPrivateUsage]
    _form_constraint_file_path,  # pyright: ignore[reportPrivateUsage]
    _get_python_version,  # pyright: ignore[reportPrivateUsage]
    _get_supported_python_versions,  # pyright: ignore[reportPrivateUsage]
    main,
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


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        pytest.param(
            {
                "pyproject.toml": """
                [project]
                name = "x"
                requires-python = ">=3.9"
                classifiers = [
                    "Programming Language :: Python :: 3",
                    "Programming Language :: Python :: 3.11",
                    "Programming Language :: Python :: 3.10",
                ]
                """
            },
            ["3.10", "3.11"],
            id="pyproject-classifiers",
        ),
        pytest.param(
            {"pyproject.toml": '[project]\nname = "x"\nrequires-python = ">=3.13"\n'},
            ["3.13", "3.14", "3.15"],
            id="pyproject-requires-python",
        ),
        pytest.param(
            {"setup.cfg": SETUP_CFG}, [f"3.{m}" for m in range(6, 16)], id="setup-cfg"
        ),
    ],
)
def test_get_supported_python_versions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    expected: list[str],
):
    monkeypatch.chdir(tmp_path)
    for name, content in files.items():
        (tmp_path / name).write_text(dedent(content))
    assert _get_supported_python_versions() == expected


def test_main_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nrequires-python = ">=3.14"\n'
    )
    calls: list[str] = []

    def fake_update(output_file: Path, python_version: str, _: list[str]) -> int:
        calls.append(f"{python_version}:{output_file}")
        return 0

    monkeypatch.setattr(update_pip_constraints, "update_constraints_file", fake_update)
    assert main(["--all"]) == 0
    assert calls == ["3.14:.constraints/py3.14.txt", "3.15:.constraints/py3.15.txt"]


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
