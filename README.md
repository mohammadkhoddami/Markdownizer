# Markdownizer

Extract existing documentation from Python projects into Markdown.

![CI](https://github.com/mohammadkhoddami/Markdownizer/actions/workflows/ci.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/markdownizer)](https://pypi.org/project/markdownizer/)
![Python](https://img.shields.io/pypi/pyversions/markdownizer)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Markdownizer **never** generates, rewrites, summarizes, or improves documentation.
It only extracts what is already present in your source code: docstrings,
comments, decorators, and source.

## Installation

```bash
pip install markdownizer
```

Or with [pipx](https://pipx.pypa.io/) for an isolated CLI:

```bash
pipx install markdownizer
```

Requires Python 3.9+. No runtime dependencies.

## Usage

### CLI

```bash
markdownizer /path/to/project -o ./docs
```

This recursively scans the project, parses every Python file with the AST, and
writes one Markdown file per package into `./docs`.

Common options:

```bash
markdownizer . -o ./docs \
  --exclude "tests/*" --exclude "migrations" \
  --only-documented --no-source
```

| Option | Description |
| --- | --- |
| `-o, --output DIR` | Output directory (default: `./docs`) |
| `--root-name NAME` | Filename for files at the project root (default: `_root`) |
| `--exclude GLOB` | Skip matching paths; may be repeated |
| `--no-source` | Omit the `## Source Code` section |
| `--no-comments` | Omit the `## Comments` section |
| `--only-documented` | Only include objects with a docstring |
| `-v, --verbose` | Increase logging verbosity |
| `-q, --quiet` | Suppress non-error output |
| `--version` | Show the version |

Run `markdownizer --help` for the full list.

### Python API

```python
from pathlib import Path
from markdownizer import extract_project

written = extract_project(
    Path("."),
    Path("docs"),
    exclude=["tests/*"],
    include_source=False,
)
print(written)  # list of written Markdown files
```

## What is extracted

For every documented object (modules, packages, classes, dataclasses, enums,
functions, async functions, methods, properties, Django models, Django forms,
Django admin classes, DRF serializers, DRF viewsets, signals, middleware,
management commands, URL configuration, and any other object with a docstring):

- The docstring, verbatim
- Comments that belong to the object (preceding and inline)
- Decorators
- The complete source code

## Output format

Each generated Markdown file groups all modules inside a single package and
uses specialized headers such as:

```
# Django Model: User
# DRF Serializer: UserSerializer
# DRF ViewSet: UserViewSet
# Enum: Status
# Dataclass: Point
# Async Function: fetch_data
```

Every section preserves the original formatting of the source documentation.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, checks, and release steps.
Changes are recorded in [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).