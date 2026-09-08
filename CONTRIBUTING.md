# Contributing

Thanks for considering a contribution to Markdownizer!

## Development setup

Requires Python 3.9+.

```bash
git clone https://github.com/mohammadkhoddami/Markdownizer.git
cd Markdownizer
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

Run all checks before submitting a pull request:

```bash
ruff check .
ruff format .
mypy markdownizer tests
pytest -q
```

The CI pipeline runs the same checks on Python 3.9-3.13 and fails under 85%
coverage.

## Releasing

1. Update `CHANGELOG.md` and bump `__version__` in `markdownizer/__init__.py`.
2. Merge to `main`.
3. Tag the release: `git tag v0.2.0 && git push origin v0.2.0`.
4. The `Release` workflow publishes to PyPI using trusted publishing
   (requires a PyPI project with OpenID Connect configured).

## Design principles

- Markdownizer **extracts** documentation; it never generates or rewrites it.
  Features that summarize or modify content are out of scope.
- Zero runtime dependencies is a feature. New runtime imports need a strong
  justification.
- The public API is `markdownizer.extract_project`, `markdownizer.build_project_ir`,
  and the `markdownizer` CLI. Keep additions backward compatible.
- The internal pipeline is `scan → parse → classify → Project IR → backend → write`.
  Output backends (Markdown, JSON, compact) consume the same deterministic IR.