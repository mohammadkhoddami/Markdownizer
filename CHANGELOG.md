# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-08-29

### Added

- **Project IR** (`markdownizer/ir.py`): a deterministic intermediate
  representation of a scanned project — `Project → Package → Module →
  Symbol` plus `imports`, `inherits`, and `defines` relationship edges.
  Versioned via `IR_VERSION = 1` (independent of the package version),
  serializable to JSON, and hashable: the same repository content always
  yields the same `blake2b` hash, regardless of where the checkout lives.
- **Backend architecture** (`markdownizer/backends/`): rendering is now
  split into pluggable backends consuming the same IR.
  - `markdown` (default): the historical one-Markdown-file-per-package
    output, unchanged.
  - `json`: deterministic `project.json` serialization of the full IR.
  - `compact`: structure-oriented `context.compact.md` with packages,
    modules, public symbols, signatures, inheritance, decorators, and
    docstrings — without full source bodies.
- **Signature mode**: `include_source="signature"` (Python API) renders the
  declaration line instead of the full body for functions, async functions,
  methods, and classes. The existing boolean modes are unchanged.
- **Import graph** (`markdownizer/imports.py`): first deterministic static
  import analysis. Resolves `import` / `from ... import` statements against
  project modules (including relative imports and aliases); unresolved
  imports are conservatively marked `external`, never guessed.
- **CLI `build` command**: `markdownizer build <project> -o <out>
  --format {markdown,json,compact}`. The legacy invocation
  `markdownizer <project> -o <out>` remains fully supported as an alias.
- `extract_project()` accepts a new `format` keyword argument and
  `build_project_ir()` is now part of the public API.
- Symbol metadata: `parameters`, `type_annotation`, `is_public`, and
  `framework` extracted during parsing/classification.

### Changed

- The internal pipeline is now `scan → parse → classify → build IR →
  backend → write`; `extract_project()` is a thin wrapper over it.
- CLI success message now reads `Wrote N file(s) to ...` (format-agnostic).
- `parse_file()` accepts an optional pre-read `source` argument to avoid
  double file reads.

### Fixed

- Relative imports with no module part (`from . import x`,
  `from .... import x`) are now recorded instead of being dropped.

## [0.2.1] - 2026-08-28

### Fixed

- Fixed Python 3.9/3.10 compatibility in packaging tests by using `tomli` as a fallback for `tomllib`.
- Added a conditional `tomli` development dependency for Python < 3.11.


## [0.2.0] - 2026-08-28

### Added

- `scan_python_files()` and CLI now accept `--exclude` glob patterns (repeatable)
  to skip paths such as `tests/*` or `migrations`.
- `extract_project()` accepts `include_source`, `include_comments`, and
  `include_undocumented` flags; exposed on the CLI as `--no-source`,
  `--no-comments`, and `--only-documented`.
- CLI `--version`, `-v/--verbose`, and `-q/--quiet` flags.
- Structured logging (`logging` module) with a scan/write summary.
- `markdownizer/py.typed` marker and strict `mypy` typing for the whole package.
- Full `pytest` test suite (100+ tests, ~91% coverage).
- CI pipeline (`.github/workflows/ci.yml`) testing Python 3.9-3.13, linting,
  formatting, typing, and package build; PyPI release workflow
  (`.github/workflows/release.yml`) using trusted publishing.
- `pyproject.toml` metadata: `project.urls`, `keywords`, expanded classifiers,
  `readme`/`license` tables, `[project.optional-dependencies].dev`,
  `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]`, `[tool.coverage]` sections.
- `CHANGELOG.md` and `CONTRIBUTING.md`.

### Fixed

- Classifier now recognizes decorators with call arguments, e.g.
  `@receiver(post_save, sender=User)` correctly classifies as `Signal Handler`
  and `@dataclass(frozen=True)` as `Dataclass`.
- Scanner now skips hidden files (e.g. `.hidden.py`) even at the project root.
- Packages containing multiple modules no longer concatenate all module sources
  into a single misleading `## Source Code` block; each module gets its own
  section.
- Duplicate `# Package: ...` heading removed from generated Markdown.
- `**File:**` paths in generated Markdown are now POSIX-style on all platforms.
- `python -m markdownizer` now propagates the process exit code.
- Fixed author name typo in `pyproject.toml` and `LICENSE`.

### Changed

- Version is single-sourced from `markdownizer.__version__` via
  `[tool.setuptools.dynamic]`.

## [0.1.0] - 2026-07-05

### Added

- Initial release.
- Recursive project scanning with AST + tokenize based extraction.
- Verbatim extraction of docstrings, comments, decorators, and source code.
- Framework-aware classification (Django models/forms/admins/middleware,
  DRF serializers/viewsets/views, enums, dataclasses, signals, URL configs).
- One Markdown file per package via the `markdownizer` CLI.