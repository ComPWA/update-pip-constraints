# Update pip constraint files

[![Spelling checked](https://img.shields.io/badge/cspell-checked-brightgreen.svg)](https://github.com/streetsidesoftware/cspell/tree/main/packages/cspell)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Type-checked with mypy](https://mypy-lang.org/static/mypy_badge.svg)](https://mypy.readthedocs.io)
[![BSD 3-Clause license](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ComPWA/update-pip-constraints/main.svg)](https://results.pre-commit.ci/latest/github/ComPWA/update-pip-constraints/main)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This Python package is a wrapper around [`uv pip compile`](https://docs.astral.sh/uv/pip/compile). It helps updating a collection of [PyPI constraints files](https://pip.pypa.io/en/stable/user_guide/#constraints-files) for your repository. One constraint file is created for each Python version that your package supports (see [here](https://github.com/jazzband/pip-tools#cross-environment-usage-of-requirementsinrequirementstxt-and-pip-compile) why this is important). The package can be configured with `pyproject.toml`, `setup.cfg`, or `setup.py`, and constraints can be generated for any Python version that uv can resolve for, including Python 3.6. The file structure is as follows:

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

### Python package

Run the command with [`uvx`](https://docs.astral.sh/uv/guides/tools) from the root of your repository:

```shell
uvx --from git+https://github.com/ComPWA/update-pip-constraints@main update-pip-constraints --python-version 3.12
```

This creates or updates the constraint file `.constraints/py3.12.txt`. Without `--python-version`, the constraint file is created for the Python version that runs the command.

### GitHub Action

Here are two examples of how to use `update-pip-constraints` as a
[GitHub Action](https://github.com/features/actions):

<details>
<summary>
Update constraints files during a PR by pushing if there are dependency changes
</summary>

```yaml
name: Requirements (PR)

on:
  pull_request:
    branches: [main]

jobs:
  pip-constraints:
    name: Update pip constraints files
    runs-on: ubuntu-22.04
    strategy:
      fail-fast: false
      matrix:
        python-version:
          - "3.7"
          - "3.8"
          - "3.9"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check if there are dependency changes
        run: git diff origin/main --exit-code -- .constraints setup.cfg
        continue-on-error: true
      - name: Update pip constraints files
        if: success()
        uses: ComPWA/update-pip-constraints@main
        with:
          python-version: ${{ matrix.python-version }}

  push:
    name: Push changes
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-22.04
    needs:
      - pip-constraints
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.PAT }}
      - uses: actions/download-artifact@v2
      - run: rm -rf .constraints/
      - run: mv artifact .constraints
      - name: Commit and push changes
        run: |
          git remote set-url origin https://x-access-token:${{ secrets.PAT }}@github.com/${{ github.repository }}
          git config --global user.name "GitHub"
          git config --global user.email "noreply@github.com"
          git checkout -b ${GITHUB_HEAD_REF}
          if [[ $(git status -s) ]]; then
            git add -A
            git commit -m "ci: upgrade pinned requirements (automatic)"
            git config pull.rebase true
            git pull origin ${GITHUB_HEAD_REF}
            git push origin HEAD:${GITHUB_HEAD_REF}
          fi
```

</details>

<details>
<summary>
Create a PR with updated constraints files
</summary>

```yaml
name: Requirements (scheduled)

on:
  schedule:
    - cron: "0 2 * * 1"
  workflow_dispatch:

jobs:
  pip-constraints:
    name: Update pip constraint files
    runs-on: ubuntu-22.04
    strategy:
      fail-fast: false
      matrix:
        python-version:
          - "3.7"
          - "3.8"
          - "3.9"
    steps:
      - uses: actions/checkout@v4
      - uses: ComPWA/update-pip-constraints@v1
        with:
          python-version: ${{ matrix.python-version }}

  push:
    name: Create PR
    runs-on: ubuntu-22.04
    needs:
      - pip-constraints
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.PAT }}
      - uses: actions/download-artifact@v4
      - run: rm -rf .constraints/
      - run: mv artifact .constraints
      - uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "ci: update pip constraints files"
          committer: GitHub <noreply@github.com>
          author: GitHub <noreply@github.com>
          title: "ci: update pip constraints files"
          branch-suffix: timestamp
          delete-branch: true
          token: ${{ secrets.PAT }}
      - name: Print PR info
        run: |
          echo "Pull Request Number - ${{ steps.cpr.outputs.pull-request-number }}"
          echo "Pull Request URL - ${{ steps.cpr.outputs.pull-request-url }}"
```

</details>

Note that you will have to set a
[create a Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
(named `PAT` in the examples) in order to push the changes to the PR branch.
The automatic
[`GITHUB_TOKEN`](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
can be used as well, but that **will not start the workflows**.
