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

This recursively scans the project, parses every Python file with the AST,
builds a deterministic Project IR, and writes one Markdown file per package
into `./docs`.

The compiler-style form is equivalent and supports format selection:

```bash
markdownizer build /path/to/project -o ./docs --format markdown
markdownizer build /path/to/project -o ./docs --format json
markdownizer build /path/to/project -o ./docs --format compact
```

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
| `--format FMT` | Output backend: `markdown`, `json`, or `compact` |
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
from markdownizer import extract_project, build_project_ir

written = extract_project(
    Path("."),
    Path("docs"),
    exclude=["tests/*"],
    include_source=False,
)
print(written)  # list of written output files

# Or build the Project IR directly:
ir = build_project_ir(Path("."), exclude=["tests/*"])
print(ir.ir_version, ir.hash, ir.stats.symbol_count)
```

### Output formats

The pipeline builds a deterministic **Project IR** (packages → modules →
symbols, plus import/inherit/define edges) and renders it through a backend:

| Format | Command | Output |
| --- | --- | --- |
| `markdown` (default) | `markdownizer build . -o ./docs` | One `.md` file per package |
| `json` | `markdownizer build . -o ./docs --format json` | `project.json` — full IR serialization |
| `compact` | `markdownizer build . -o ./docs --format compact` | `context.compact.md` — signatures, docstrings, inheritance, decorators (no bodies) |

The legacy invocation `markdownizer <project> -o <out>` is kept as a
compatibility alias for `markdownizer build <project> --format markdown`.

### Signature mode

Instead of full source or no source, `extract_project()` accepts
`include_source="signature"` to emit only declaration lines:

```python
extract_project(Path("."), Path("docs"), include_source="signature")
```

Functions render as `def foo(x: int = 1) -> str:`, async functions as
`async def ...`, classes as `class User(models.Model):` (with base classes),
and methods with their parameters. Modules render without source. The
boolean modes (`True`/`False`) are unchanged.

### Project IR

`build_project_ir(project_root, exclude=None)` returns a `ProjectIR` with:

- `ir_version` — schema version (currently `1`), independent of the package version
- `packages`, `modules`, `symbols` — the project hierarchy
- `imports`, `inherits`, `defines` — relationship edges
- `stats` — file/module/symbol counts
- `hash` — deterministic `blake2b` of the canonical IR content

The hash and JSON serialization are deterministic: the same repository
content always produces the same hash and the same `project.json`, making
the output suitable for version control and caching. Machine-specific
metadata (`root`, `python_version`, `git`) is excluded from the hash.

Import resolution is conservative and fully static: project code is never
imported or executed. Imports that cannot be resolved to a project module
are marked `external`.

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