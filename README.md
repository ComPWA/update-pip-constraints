# Python Container Action Template

[![BSD 3-Clause license](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Spelling checked](https://img.shields.io/badge/cspell-checked-brightgreen.svg)](https://github.com/streetsidesoftware/cspell/tree/master/packages/cspell)
[![GitPod](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/ComPWA/update-pip-constraints)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ComPWA/update-pip-constraints/main.svg)](https://results.pre-commit.ci/latest/github/ComPWA/update-pip-constraints/main)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![code style: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort)

This Python package is a wrapper around
[`pip-tools`](https://github.com/jazzband/pip-tools). It helps updating a
collection of
[PyPI constraints files](https://pip.pypa.io/en/stable/user_guide/#constraints-files)
for your repository. One constraint file is created for each Python version
that your package supports (see
[here](https://github.com/jazzband/pip-tools#cross-environment-usage-of-requirementsinrequirementstxt-and-pip-compile)
why this is important). The file structure is as follows:

```text
.constraints/
├── py3.6.txt
├── py3.7.txt
└── ...
```

Constraint files allow you to pin your package requirements as follows:

```shell
python3 -m pip install -c .constraints/py3.7.txt -e .[dev]
```

This is just an example where you install your package in
[editable mode](https://packaging.python.org/guides/distributing-packages-using-setuptools/#working-in-development-mode)
(`-e` flag) on Python 3.7, where we also installed
[optional dependencies](https://setuptools.pypa.io/en/latest/userguide/dependency_management.html#optional-dependencies)
defined under an `extras_require` section called `[dev]`.

## Why ship your repository with constraint files?

- Constraint files
  [reduce the resolution time](https://pip.pypa.io/en/latest/topics/dependency-resolution/#use-constraint-files-or-lockfiles)
  of the PyPI dependency resolver.
- Constraint files make the developer environment reproducible _for each
  commit_ and _for each supported version of Python_.
- Constraint files provide a way out of
  [dependency hell](https://en.wikipedia.org/wiki/Dependency_hell).

## Usage

This Package can be installed with [`pip`](https://pypi.org/project/pip) from
GitHub:

```shell
python3 -m pip install git+https://github.com/ComPWA/update-pip-constraints@main
```

Now, if you run the command:

```shell
update-pip-constraints
```

an updated constraint file will be created for your version of Python under
`.constraints/py3.x.txt`.
