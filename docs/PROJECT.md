# Markdownizer — Project Documentation

**Version:** 0.4.5 · **IR version:** 1 · **License:** MIT · **Python:** 3.9+ · **Runtime dependencies:** none

---

## 1. What Markdownizer Is

Markdownizer is a **deterministic Codebase-to-Context Compiler** for Python
projects. It scans a project, builds a structured intermediate representation
(the Project IR), and produces clean, token-efficient context artifacts that
AI coding agents — OpenCode, Claude Code, Cursor, Cline, Gemini CLI, or any
LLM — can consume directly.

The defining principle:

> **AI is the consumer, never the engine.**

Markdownizer does not call models, does not need API keys, and never
generates, rewrites, summarizes, or improves documentation. It only extracts
what already exists in the source code — docstrings, comments, decorators,
and source — and structures it deterministically.

```
Project → Scan → Parse (AST + tokenize) → Classify → Project IR
        → Rank → Budget → Backends (Markdown / JSON / Compact) → AI agent
```

---

## 2. The Problem It Solves

Raw repositories are noisy, unstructured, over-budget, and mis-ordered for
LLM consumption:

- **Noise:** lockfiles, `__pycache__`, vendored code, generated files, and
  undocumented internals dominate token counts. 70–90 % of a naive repo dump
  is filler.
- **Size:** ~50k LOC of Python is roughly 400–500k tokens — beyond the
  *effective* window of most frontier models (typically 50–70 % of the
  advertised context).
- **Lost in the middle:** model recall drops sharply in the middle of long
  contexts; where content is placed matters.
- **Cost:** agent loops resend context every turn, so wasted tokens multiply
  across every turn of every session.

Markdownizer attacks the problem at the source: **which** tokens, not how
cheap they are. It removes what can be safely removed, preserves semantics
(public API, type signatures, docstrings, relationships), ranks what matters,
and fits the result inside a user-chosen token budget.

---

## 3. Core Guarantees

| Guarantee | Meaning |
| --- | --- |
| **Deterministic** | The same repository content always produces the same hash and the same output. |
| **No hallucination** | Verbatim extraction only; nothing is invented or inferred beyond static facts. |
| **No code modification** | Read-only against the input repository. |
| **Local-first** | The repository never leaves the machine; fully offline. |
| **AI-independent** | No API keys, no mandatory embeddings, no LLM calls. |
| **Zero runtime dependencies** | Standard library only; `tiktoken` is optional. |
| **Reproducible** | Same commit → same `ir.json` hash → same artifacts, cacheable. |
| **Explainable** | Every inclusion/exclusion decision follows from deterministic rules. |

---

## 4. How It Works

### 4.1 Pipeline

```
┌───────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ scanner.py    │ → │ parser.py    │ → │ classifier.py│ → │ ir.py        │
│ file discovery│   │ ast+tokenize │   │ framework    │   │ Project IR   │
└───────────────┘   └──────────────┘   │ taxonomy     │   │ + hash       │
                                       └──────────────┘   └──────┬───────┘
                                                                 │
                     ┌───────────────────────────────────────────┤
                     ▼                                           ▼
        ┌──────────────────────┐                  ┌──────────────────────┐
        │ optimizer/           │                  │ backends/            │
        │ rank.py  PageRank    │                  │ markdown.py  {pkg}.md│
        │ slice.py budgets     │                  │ json.py      ir.json │
        │ profiles.py presets  │                  │ compact.py   context │
        └──────────────────────┘                  └──────────────────────┘
```

1. **Scanner** (`scanner.py`) — walks the project with `rglob`, skipping
   ignored directories (`.git`, `venv`, `__pycache__`, `build`, `dist`,
   `node_modules`, …), hidden files, and user-provided `--exclude` globs.
   Yields `.py` files in sorted order for determinism.

2. **Parser** (`parser.py`) — for every file, `ast.parse` + `tokenize`:
   - module, class, function, async function, and method objects
   - verbatim docstrings (`clean=False` — formatting preserved)
   - preceding and inline comments, attributed to the right object
   - decorators verbatim (including call args)
   - parameters and return type annotations (`ast.unparse`)
   - full source segments
   - `SyntaxError` and non-UTF-8 files are tolerated — one bad file never
     aborts a project (UTF-8/BOM first, latin-1 fallback).

3. **Classifier** (`classifier.py`) — maps objects to framework-aware labels
   purely from static base-class and decorator names:
   `Django Model / Form / Admin / Middleware / Management Command`,
   `DRF Serializer / ViewSet / API View`, `Signal`, `Signal Handler`,
   `URL Configuration`, `Enum`, `Dataclass`, `Property`, `Function`,
   `Method`, `Module`, `Package`.

4. **Project IR** (`ir.py`) — the deterministic contract between analysis
   and output:
   - `Project → Package → Module → Symbol`, plus relationship edges
     (`imports`, `inherits`, `defines`)
   - `IR_VERSION = 1`, independent of the package version
   - a `blake2b` hash over canonical content — machine metadata (`root`,
     `python_version`, `git`) and derived ranks are excluded from the hash,
     so the same content always hashes the same anywhere

5. **Import graph** (`imports.py`) — static collection of module-level
   imports; relative imports resolved against the project's own modules;
   unresolved imports are conservatively marked `external` and never
   guessed.

6. **Ranking** (`optimizer/rank.py`) — deterministic importance:
   - `pagerank` (default): PageRank power iteration over the import graph
     (fixed iteration count, pure Python)
   - `fanout`: in-degree of each module
   - `simple`: uniform
   - framework-aware file boosts (Django Model, Management Command, URL
     config, entrypoints) × public/documented symbol factors

7. **Budget packing** (`optimizer/slice.py`) — builds a context artifact
   within a token budget: project index → per-symbol blocks (full source for
   the highest-ranked symbols, signature-only for the rest), with
   high-ranked symbols placed at the start and end (primacy/recency).
   Token counting uses `tiktoken` when installed, `chars / 3.3` otherwise.

8. **Backends** (`backends/`) — render the same IR without re-analysis:
   - `markdown`: one file per package (the historical output, unchanged)
   - `json`: full deterministic IR serialization (`project.json`)
   - `compact`: structure-oriented `context.compact.md` (signatures,
     inheritance, decorators, docstrings — no bodies)

### 4.2 Project IR schema (v1)

```
ProjectIR
├── name, root, ir_version, python_version, git (informational)
├── hash                    # blake2b over content_dict (stable across machines)
├── stats                   # package/module/symbol/function/class counts, lines
├── packages[]              # name, path, is_namespace, module_paths
├── modules[]               # path, dotted name, package, docstring,
│                           # source, line_count, content_hash, symbol_ids
├── symbols[]               # id, name, qualified_name, kind, file_path,
│                           # lineno, decorators, base_classes, parameters,
│                           # type_annotation, docstring, comments, source,
│                           # is_public, framework, rank
├── imports[]               # from_module → to_module | external
├── inherits[]              # symbol_id → base
├── defines[]               # module → symbol, class → method
└── file_ranks{}            # module path → normalized importance
```

---

## 5. CLI Reference

### 5.1 Legacy alias (0.2.x behavior, unchanged)

```bash
markdownizer <project> -o <out>
```

### 5.2 Build

```bash
markdownizer build <project> -o <out> --format {markdown,json,compact}
```

Writes one `{package}.md` per package (markdown), `project.json` (json), or
`context.compact.md` (compact). Flags: `--exclude`, `--no-source`,
`--no-comments`, `--only-documented`, `--root-name`, `-v/-q`.

### 5.3 Context

```bash
markdownizer context <project> -o <out> \
  --max-tokens 20000 --profile api --rank pagerank --query "user model"
```

Writes a budgeted, ranked `context.md`. Options: `--max-tokens` (default
20000, soft ±10 %), `--profile`, `--rank`, `--query` (deterministic keyword
prefilter), `--prefer-tiktoken`.

### 5.4 Stats

```bash
markdownizer stats <project> [--rank pagerank] [--json]
```

Prints project counts, token estimate, and top-ranked files/symbols.

### 5.5 Exit codes

`0` success · `1` runtime error · `2` invalid arguments/paths.

---

## 6. Python API

```python
from pathlib import Path
from markdownizer import (
    extract_project,  # write backend output for a project
    build_project_ir,  # build the ProjectIR (no output)
    optimize_context,  # budgeted, ranked context artifact
    IR_VERSION,  # current IR schema version (1)
    ProjectIR,  # IR type
    OptimizedContext,  # result type of optimize_context
)

written = extract_project(Path("."), Path("docs"), exclude=["tests/*"])
ir = build_project_ir(Path("."), exclude=["tests/*"])
print(ir.hash, ir.stats.symbol_count)

ctx = optimize_context(ir, max_tokens=20000, profile="api", query="auth")
print(ctx.estimated_tokens, ctx.included_symbols, ctx.text)
```

---

## 7. Context Profiles

| Profile | Source | Comments | Undocumented | Purpose |
| --- | --- | --- | --- | --- |
| `architecture` (default) | signature | yes | no | structural overview |
| `api` | signature | no | no, public only | public API surface |
| `debugging` | full (top-ranked) | yes | yes | bug investigation |
| `refactor` | signature | yes | yes | rename/move planning |
| `django` | signature | yes | yes | Django/DRF teams |
| `onboarding` | none | yes | no | docstrings only |

---

## 8. Output Formats

| Format | Artifact | Content | Use case |
| --- | --- | --- | --- |
| `markdown` | `{package}.md` per package | full sections, verbatim | human + LLM paste |
| `json` | `project.json` | complete IR (incl. ranks) | tooling, diffing, RAG embedding |
| `compact` | `context.compact.md` | structure only | token-efficient overview |
| `context` command | `context.md` | budgeted, ranked | direct agent context |

All outputs are deterministic: same content → same bytes.

---

## 9. Determinism & Hashing

- Collections are sorted before serialization (files, symbols, edges).
- The hash is `blake2b` over a canonical JSON rendering of content only.
- Excluded from the hash: `name`, `root`, `python_version`, `git` metadata,
  and ranking data — so the hash describes *repository content*, not where
  the checkout lives.
- `project.json` is stable for the same content on the same platform; rank
  values are deterministic per platform (documented IEEE-754 caveat).

---

## 10. Compatibility

- **API:** `extract_project()` keeps its original signature; new parameters
  are additive with defaults preserving prior behavior.
- **CLI:** the legacy invocation remains a working alias.
- **Markdown output:** byte-identical to 0.2.x for the same inputs.
- **Versioning:** SemVer. IR schema frozen per `ir_version`; schema changes
  require a version bump of the IR, not just the package.

---

## 11. Quality

- **Tests:** 220 + 1 skip; coverage gate 85 % (actual ≈ 94 %).
- **Typing:** `mypy --strict` clean; `py.typed` shipped.
- **Lint:** `ruff` (E, F, I, B, UP, SIM) + format checks in CI.
- **CI:** matrix Python 3.9–3.13 (test, lint, type, coverage, build, twine).
- **Release:** tag push → OIDC trusted publishing to PyPI.

---

## 12. Version History

| Version | Highlights |
| --- | --- |
| 0.1.0 | initial scanner/parser/classifier/renderer/CLI |
| 0.2.0 | exclude globs, rendering toggles, logging, typing, tests, CI |
| 0.2.1 | Python 3.9/3.10 packaging fix |
| 0.3.0 | Project IR + backends (markdown/json/compact) + signature mode + import graph |
| 0.3.1 | mypy narrowing fix |
| 0.4.0 | ranking (pagerank/fanout/simple), token budgets, profiles, `context`/`stats` CLI |
| 0.4.1 | context packing fixes (single emission, accurate metrics, budget validation) |
| 0.4.2 | encoding robustness; module-level-only import graph |
| 0.4.3 | Persian (فارسی) user guide in README |
| 0.4.4 | ruff-format Markdown code blocks |
| 0.4.5 | repositioned as Codebase-to-Context Compiler (summary, README, keywords) |

---

## 13. Roadmap

**Planned (not yet implemented):**

- **0.5.0 — MCP + Query:** `markdownizer mcp` stdio server
  (`context`/`inspect`/`stats` tools), SQLite FTS5 query prefilter with
  1-hop import tracing, agent integration guides (OpenCode, Claude Code,
  Cursor, Cline), GitHub Action producing `llms.txt` + docs artifacts.
- **0.6.0 — Intelligence:** FastAPI/Pydantic/SQLAlchemy/Celery detectors,
  entrypoint detection, test→code mapping, deterministic `explain`, and
  incremental caching (<200 ms cached builds).
- **1.0.0 — Stability freeze:** IR v1 schema, Backend interface, and CLI
  verbs frozen under SemVer; `DocObject → Symbol` migration shim; docs site.

**Explicitly out of scope:** LLM summarization in core, hosted RAG/vector
databases, custom DSLs, multi-language support before 1.0.

---

## 14. Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format .
mypy markdownizer tests
pytest -q
```

See `CONTRIBUTING.md` and `CHANGELOG.md` for workflow and history.
The strategic direction and product research live in `docs/vision.md`.