# copyright<sup>2</sup>

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/phyrwork/copyright2/ci.yaml)

copyright<sup>2</sup> (copyright-right) is a text file copyright notice lint and update
tool to help keep the years listed in your copyright notices up to date with when they
were modified.

## Features

- Supports any text file.
- Configurable to match your specific copyright notice format.
- Configurable to include/exclude specific files/directories.
- Check mode which shows changes missing from files.
- Fix mode which updates files with missing changes.
- Intelligently simplifies copyright year expressions e.g. `2009,2010,2011,2013` to
  `2009-11,3`.
- Git path mode for using Git to identify which files to check in CI.
- Configurable to quickly add current year to modified files when using Git path mode.

## Getting Started

### Prerequisites

- Python 3.10 or later

### Installation

Install using your favourite package manager e.g.

```bash
pip install copyright2
```

```bash
poetry install copyright2
```

or, if using as an application only, install in isolation e.g.

```bash
pipx install copyright2
````

```bash
uv tool install copyright2
```

### Usage

#### Configuration

Create a `.copyrightrc.yaml` at the top level of your project and describe your copyright
notice and specify some files to manage using regular expressions.

By default, no files or directories are included and no changes are made to included
files.

```yaml
# .copyrightrc.yaml
root: yes
copyright: "Copyright \(c\) {ts}"
include_dirs:
  - .*  # All directories.
include_files:
  - README.md$
simplify: yes  # Simplify copyright year expression.
```
   
Options specified in `.copyrightrc.yaml` of subdirectories take precedence for that
directory.

```yaml
# src/.copyrightrc.yaml
include_files:
  - .*\.py$  # All .py files in this directory and below.
```

```yaml
# src/ext/.copyrightrc.yaml
include_files:
  - .*\.(c|h)$  # Only .c, .h files in this directory and below.
```

#### Run (development)

Check files that will be managed by `copyright`

```bash
examples/readme$ copyright list
README.md
src/readme.py
src/ext/readme.h
src/ext/readme.c
4
```

then scan for changes that need to be made to any copyright notices

```bash
examples/readme$ copyright check
README.md: notice not found
src/ext/readme.h: 2: simplified timestamp expression
2
```

and fix them

```bash
examples/readme$ copyright fix
README.md: notice not found
fixing src/readme.py... ok
fixing src/ext/readme.h... ok
2

examples/readme$ git diff
diff --git a/examples/readme/src/readme.py b/examples/readme/src/readme.py
index 65785b6..cb2603b 100644
--- a/examples/readme/src/readme.py
+++ b/examples/readme/src/readme.py
@@ -1 +1 @@
-"""Copyright (c) 2023,2024,2025."""
+"""Copyright (c) 2023-5."""
```

#### Run (CI)

The `check` command will only return `0` if no required changes are detected.

To restrict the check to only files which have changed between the previous and current
commit

```bash
examples/readme$ copyright list --find-path git HEAD~1
src/readme.py
1
```

To ensure that the current year has been added to files which have changed between the
previous and current commit, add the `--add-now` flag

```bash
examples/readme$ copyright check --find-path git HEAD~1 --add-now
src/readme.py: 1: added year 2024 to timestamp
1
```
