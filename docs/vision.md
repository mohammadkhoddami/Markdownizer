# Executive Summary

Markdownizer 0.2.1 is a deterministic, static, zero-runtime-dependency Python extractor: scanner (rglob+fnmatch) → parser (ast+tokenize → DocObject) → classifier (Django/DRF taxonomy) → renderer (Markdown) → extractor (group by directory → one md per package) → cli (argparse) + Python API. 495 executable statements, 101 tests + 1 skip at 91% line / branch, mypy --strict clean on 3.12, ruff clean, CI matrix 3.9-3.13 + OIDC release, py.typed, Alpha on PyPI.

**Thesis to test:** Project → Markdownizer → clean structured token-efficient AI-ready context → any LLM/agent. Consumer is AI, engine is deterministic.

**Verdict:** Thesis is right, but only if narrowed. Token-price collapse (GPT-4 $30/$60 → Luna $0.20/$1.20, caching 90% off) killed generic "save tokens" pitch. Effective window (1M advertised → 200-300k usable) + lost-in-middle (-20pp) + 10-turn loop 3K×30 = $18/mo/dev on Sonnet vs $0.90 on mini means the real problem is which tokens, not how cheap. Markdownizer's existing ast+tokenize frontend, Django-aware headers, and include_source/comments/undocumented toggles are the exact primitive for structural compression (signatures > bodies, docstrings > noise), which literature shows beats token-pruning (+21.4% at ¼ tokens with LongLLMLingua vs +30-50 point grounding drop with LLMLingua pruning). Generic packers (Repomix 28k★, Gitingest 15k★, Aider map 1k) already own dump everything; vector RAG (Sourcegraph $16k/yr, Cursor $20/mo) owns hosted scale. No incumbent owns local, deterministic, Python/Django-aware, comment-preserving, hash-stable ir.json + Markdown + MCP at $0.

**Recommendation:** Do not become another docs generator. Do not become a hosted RAG/LLM wrapper. Become a **Codebase-to-Context Compiler**: local, offline, zero-LLM core that emits a versioned Project IR (Project→Package→Module→Symbol + imports/inherits/defines edges) and multiple backends (markdown default, compact signatures-only, json typed inventory, xml, mcp resources). Python-first, Django moat deepened; ship incrementally 0.3.x IR+backends → 0.4.x budget/rank → 0.5.x MCP/query → 0.6.x intelligence → 1.0.0 freeze. One maintainer, 10-15h/week, 12-month plan. Name stays Markdownizer (brand expanded, not renamed).

# Current Markdownizer Assessment

## 1. What is already good

* **Static safety:** parser.py:276 ast.parse + tokenize.generate_tokens:70 never imports target; survives SyntaxError:287 fallback, TokenError:74 fallback, DJANGO_SETTINGS_MODULE side-effects where sphinx/pdoc/mkdocstrings break.
* **Verbatim triad:** ast.get_docstring(clean=False):155 + _decorator_source:46 verbatim + _collect_comments:66 + _preceding_comment_block:87/_inline_comments:104 owned-vs-module split via owned_linenos:304-342. No other packer preserves preceding # TODO above @receiver.
* **Django/DRF taxonomy:** classifier.py:55-131 7 sets + _decorator_base:59 → 13 headers (Model/Form/Admin/Serializer/ViewSet/APIView/Enum/Dataclass/Middleware/Management Command/Signal/Handler/URL Configuration). test_classifier.py:27 100% coverage; fixes dataclass(frozen=True)/receiver(...) in 0.2.0.
* **Zero deps, typed, deterministic:** pyproject.toml:30 dependencies=[], py.typed, mypy strict, sorted(rglob:61) + sorted (file,lineno) + as_posix:149 → snapshot-stable for RAG cache. 91% coverage (ci.yml:30 gate 85), ruff E,F,I,B,UP,SIM clean.
* **Single-sourced version, trusted publish:** [tool.setuptools.dynamic] attr=markdownizer.**version**:55, release.yml OIDC, CHANGELOG.md Keep-a-Changelog.

## 2. What is technically unique

No competitor combines all four: static ast+tokenize dual (not regex), zero import + zero deps, comment/decorator/source verbatim, Django/DRF-aware Markdown sections. pdoc is HTML+import, Sphinx is reST+conf.py, mkdocstrings+griffe is MkDocs-locked, Repomix/Gitingest/code2prompt are generic flat dumps, Aider map is lossy ranked signatures without docstrings, Sourcegraph/Cursor are cloud embeddings $16k/$20mo. Repomix compress via Tree-sitter even drops comments.

## 3. What should be preserved

* never generates/rewrites (CONTRIBUTING.md:42, README.md:10). Verbatim + no hallucination is moat vs LLMLingua-style pruning.
* Zero-runtime-dependency contract (fails only for optional tiktoken/tree-sitter extras behind markers).
* Deterministic sorted scan + stable Markdown headings (RAG-chunkable).
* extract_project() signature as alias forever.

## 4. What should be redesigned later

* DocObject monkey-patch _children:211 → proper children: list[DocObject] field.
* Flat renderer.py:17-98 sections.append templating → Backend interface; fence escape for  ```  inside docstrings.
* Directory-grouping (extractor.py:15 _package_key parent dir) → package-aware (**init**.py presence).
* Single-verb cli.py:16 flat argparse → subcommands (scan/build/context/inspect/stats).

## 5. What naturally supports the compiler vision

* Current split already mirrors compiler: scanner (lex), parser (frontend), classifier (semantic), renderer (backend), extractor (driver). parser→DocObject is proto-IR; classifier is analysis; renderer is backend; extractor is linker. Refactor is 4-file move, not rewrite.
* include_source/comments/undocumented toggles are compiler flags.
* scanner --exclude + IGNORED_DIR_NAMES are noise filters — optimizer precursor.

## 6. Technical debt

Shallow traversal (one class depth, no AnnAssign/a=b=Signal() alias, no **all** filtering), unused all_comment_linenos:88, comment window anchor-len_blank gap, source duplication (class + methods both emit bodies), rglob no prune / no .gitignore, Middleware suffix heuristic, **main**.py 0% coverage, vision.md 0-byte untracked (prior 27 kB draft lost).

## 7. Missing capabilities (for context compiler)

Dependency graph, symbol ranking/PageRank, token budgeting (--max-tokens), signature-only mode, incremental mtime/hash cache, query-aware --query, ir.json serializable IR, multi-backend (json/xml/mcp), stats/diff/inspect, framework expansion (FastAPI/Pydantic/SQLAlchemy), **all**/private filtering.

# Product Definition

## Positioning is strong — with a naming caveat

* "Codebase-to-Context Compiler" is strong: explains in → out, deterministic, local, budget-aware, and "compiler" signals IR + optimization passes + backends to developers.
* "Compiler" metaphor: good for Pythonista/architects (they know IR → backends, passes, budget). Risk: non-compiler devs hear "complex." Mitigate with subtitle: Markdownizer — deterministic Codebase-to-Context Compiler (scan → understand → optimize → emit).
* "Context Compiler" vs "Codebase-to-Context": Codebase-to-Context is clearer for landing page/SEO (repomix is "pack repo for AI"); Context Compiler is shorter for CLI (markdownizer build). Use both: title Codebase-to-Context Compiler, binary stays markdownizer.
* "AI-ready context" as value prop: strong if concretized (see §AI-Ready, §Guarantees). Vague alone. Concretize: "public API 100% retained, signal-to-noise 3-5×, same commit → same hash, no API keys."
* Is Markdown correct output? Yes as default, no as identity. Markdown is best human+LLM first artifact (paste into ChatGPT/Claude/Cursor, commit to docs/, chunk for RAG). But compact JSON (typed inventory) for agents, xml for Claude, mcp for live inspect(trace) are higher-signal per token. Keep Markdown default; expand name meaning rather than rename package.
* Does Markdownizer become limiting? Only if marketed literally. markdownizer build --format json is oxymoronic at first glance. Mitigate: README subtitle "Markdown by default, multi-backend by design — Markdown is one compiler target"; package name stays (SEO, PyPI markdownizer downloads, pipx install muscle memory cost of rename dwarfs benefit). Options B/D: keep brand, expand meaning. No rename unless >10k stars and host demands.

## Working definition (recommended)

Markdownizer is a deterministic, local, zero-LLM Codebase-to-Context Compiler: it scans a completed or partially completed Python project, builds a stable Project IR (packages→modules→symbols + imports/inherits/defines edges + Django/DRF labels), ranks and budgets context deterministically, and emits AI-ready artifacts (Markdown by default; compact, JSON, XML, MCP on demand) that any LLM/agent consumes — the repository never leaves the machine and the same commit always yields the same context.

# Core User Problem

**Who:** Python/Django developer handing a project to an AI — inherited/open-source repo for refactoring, partially completed feature branch, migration (Django 3→5), or onboarding another dev. Has own Claude Code / OpenCode / Cursor / Cline / Gemini CLI / ChatGPT subscription; does not want another LLM bill, another vector DB, or to paste 50k LOC → 500k tokens raw.

**Problem:** Raw repo is noisy + unstructured + over budget + lossy in the middle. Noise (node_modules/**pycache**/.venv/migrations fixtures, generic packers dump 500k); no structure (grep returns 69 files 1.4M naive); effective window is ½-¼ advertised (RULER: 1M → 200-300k, TokenMix Sonnet 200k→150k); middle recall 75%→55% (Liu et al); 20-turn loop 30×3K = 90K/day before codebase. More context often degrades (+1.5% at 50 vs 20 docs). Current agents cope via weak maps (Aider 1k) or brute search (Cursor hybrid loses call-graph, OpenCode has no map). User pastes cat . | llm and gets hallucinations.

**Markdownizer solution:** markdownizer build . --max-tokens 20k --profile architecture → ir.json + context.md (ranked signatures + docstrings + decorators, dependency-ordered, edge-placed). Signal-to-noise 3-5×, public API 100%, 2.8k vs 61k disciplined vs 1.4M naive (Emre Cavunt graph), ~1k vs 10k explorer (Codebase-Memory), commit-stable for RAG cache.

**Importance:** Even at $0.20/M, 1.2M×20 turns = $4.80 vs $0.24 plus 75%→55% accuracy cliff. With caching, volatile RAG suffix still costs; with 1M windows, length-alone hurts 13.9-85% within window (EMNLP 2025) even at perfect retrieval at beginning with masked distractors. Structured less-but-better text is durability, not price.

# Codebase-to-Context Vision

Pipeline (deterministic, no LLM):

```text
Project (snapshot dir)
 ↓
Markdownizer
 ├─ Analyze: rglob + fnmatch + .gitignore + ast + tokenize → Project IR (versioned, hashable)
 ├─ Understand: imports graph, inheritance, framework (Django model→fields, DRF serializer/viewset, FastAPI route, Pydantic BaseModel), entrypoints (manage.py/urls/settings), test→code map
 ├─ Remove noise: IGNORED + generated (`DO NOT EDIT`) + lockfiles + dupe content
 ├─ Preserve semantics: public API, type signatures, docstrings, important comments, decorators, relationships
 ├─ Structure: Package→Module→Symbol hierarchy, dependency-compressed, edge-placed (high-rank at primacy/recency)
 ├─ Optimize: rank (PageRank on import graph) + budget packer (layered emit: stats→signatures→source→comments) + query slice (FTS5)
 ↓
AI-ready context (Markdown default; compact/JSON/XML/MCP)
 ↓
User pipes to chosen AI (Claude Code `cat context.md | claude -p`, OpenCode `mcp`, Cursor `@docs`, ChatGPT paste)
```

**Example:**

```text
50k LOC Python (500k tokens raw)
 ↓ markdownizer build . --profile architecture --max-tokens 20k
 → ir.json  (typed, hashable, cached, <200kB)
 → context.md  (20k tokens: package index 5% + public signatures 15% + ranked source 60% + comments 20%, edge-placed)
 → stats.json  (raw 500k → output 20k : ratio 25:1, public API 100%, 42 packages, 128 symbols, build 0.8s)
 ↓ Claude Sonnet 200k effective window (70% = 140k)
 AI sees 20k well-placed vs 500k shuffled → +21% accuracy at ¼ tokens (LongLLMLingua) + no middle loss
```

**Why no AI needed:** Every step above is ast/tokenize/graph/FTS5/tiktoken. See §Why No AI.

**Why No AI Is Required:** Every step above is ast/tokenize/graph/FTS5/tiktoken. See §Why No AI.

# Why No AI Is Required

Core can achieve analysis→rank→optimize→context with:

* ast + tokenize (already 100% local, parser.py:1-364 proves)
* fnmatch + Path + .gitignore via pathspec (deterministic noise filter)
* imports graph (ast.Import/ImportFrom → resolved Path via **init**.py probe) + PageRank (pure Python power iteration, no networkx) → Aider proves 1k map works, codebase-index proves FTS5+graph 70% Recall@3 vs 40% rg, 13× fewer answer tokens
* FTS5 SQLite prefilter for query("fix auth") (no embeddings) + optional all-MiniLM rerank as markdownizer[ai] extra, off by default
* Deterministic ranking: file_importance = PageRank, symbol = file_score × is_public(1.5/0.7) × has_docstring(1.3/0.8) — no LLM
* Budget packer: layered emit loop + tiktoken cl100k_base or chars/3.3 fallback (already measured 9.1 tok/line via loctok)
* Framework detection: bare-name sets (classifier.py pattern extends to FastAPI APIRouter/Pydantic BaseModel)

## Strategic benefits

1. **Privacy:** repo never leaves machine; air-gapped banking/health Django viable vs Cursor cloud embeddings / Sourcegraph $16k/yr single-tenant.
2. **Cost:** $0 vs $0.20-5/M + cache-write 1.25×; compressor overhead +18% only in narrow window (Kummer) → deterministic 0ms is cheaper than GPT2-small perplexity pass.
3. **Reproducibility:** same commit blake2b → same ir.json hash → RAG cache hit (Cursor simhash reuse), auditable git diff of context.
4. **Offline/OSS:** pipx install markdownizer works on locked CI, no OPENAI_API_KEY, no vector DB (ChromaDB vs SQLite FTS5), contributors can mypy+pytest without billing.
5. **Trust:** never generates (CONTRIBUTING.md:42) — no hallucinated User.email field; LongLLMLingua token pruning creates ungrammatical gibberish that hurts code reasoning (Passage Counting <20%→4.5%), extractive keep whole chunks wins (Jha 10× minimal degradation).

**Optional AI (off by default, markdownizer[ai] extra, local all-MiniLM):** semantic query rerank, architecture explain sentence, nothing in core.

# Product Directions

## A — Advanced deterministic Python docs extractor

**Vision:** best static sans import docs for Python.
**User:** Django team hating Sphinx conf.py.
**Value:** less config, Django headers nobody else has.
**Market:** Sphinx 7,986★ + pdoc 2,514★ + mkdocstrings 2k★ 15-18y incumbents, free.
**Difficulty:** low (add FastAPI/SQLAlchemy/Celery sets, TOC anchors, include_private/**all**).
**Differentiation:** 3/10 — verbatim decorators/comments only edge.
**Defensibility:** commodity.
**OSS:** meh.
**Monetization:** none.
**Risk:** invisible vs pdoc zero-conf + HTML beauty.
**Verdict:** Not standalone.

## B — Token-efficient AI context generator

**Vision:** Repository → remove noise → compress structure → budget.
**User:** >50k LOC Django monorepo on Claude/Cursor.
**Value:** 22× (61k→2.8k) Emre, 5.5× (188k→33k) TokenMix via caching.
**Market:** subset >30k LOC needs it; median 14k LOC (168k tokens) fits.
**Difficulty:** medium (PageRank, dedupe).
**Differentiation:** 7/10 via docs-as-context wedge.
**Defensibility:** weak if generic.
**OSS:** token story sells.
**Monetization:** managed mcp only.
**Risk:** price collapse (Luna $0.20), caching beats compression for static prefix.
**Verdict:** Valuable layer, not product.

## C — Deterministic Codebase-to-Context Compiler

**Vision:** compiler: Input → Scanner → Parser → IR → Analysis → Optimizer → Backends.
**User:** any Python/Django + any agent.
**Value:** one tool, many outputs, deterministic same commit → same hash, Markdown+compact+json+xml+mcp.
**Market:** 7/10 — broadens beyond docs to all agents.
**Difficulty:** medium (IR + graph + packer), no LLM.
**Differentiation:** 8/10 — only deterministic Python/Django compiler.
**Defensibility:** 7/10 — IR schema + Django taxonomy moat.
**OSS:** 8/10 — IR is own category.
**Monetization:** 6/10 paid backends.
**Risk:** import resolution for namespace packages/DJANGO_SETTINGS_MODULE.
**Verdict:** Core identity.

## D — AI agent context provider

**Vision:** Repo → Markdownizer Context Engine → OpenCode/Claude/Cursor/Cline/Gemini.
**User:** agent users hitting no-map / stale-index / privacy.
**Value:** OpenCode has no map (#2108), Claude no indexer (33k vs 188k 5.5× gap), Cursor misses call-graph, Context7 61k★ only upstream docs.
**Market:** every agent user.
**Difficulty:** MCP stdio 15-20h thin.
**Differentiation:** 8/10 — single structured read vs 30× read_file (6.4× Holysheep).
**Defensibility:** 6/10 vendors could absorb.
**OSS:** 9/10 — MCP is hot (33k servers).
**Monetization:** managed mcp.
**Risk:** platform churn.
**Verdict:** Best go-to-market for C.

## E — Repository intelligence engine

**Vision:** symbol graph + dependency + API discovery + entrypoint + test→code map + ownership.
**User:** enterprise 10k-repo estates, 500k LOC monoliths.
**Value:** impact("change User.email → 14 services").
**Difficulty:** high (Python metaclass ModelBase).
**Differentiation:** 9/10 Python static gap (TS has tree-sitter).
**Defensibility:** 8/10.
**OSS:** cool but heavy.
**Monetization:** enterprise.
**Risk:** needs hosted + multi-repo to monetize, 1 maintainer cannot.
**Verdict:** Moat to grow into, not start with.

## F — CLI developer tool

**Verbs:** scan/inspect/context/optimize/diff/stats/explain/export/mcp.
**Value:** DX, not strategy.
**Market:** 5/10.
**Difficulty:** low.
**Differentiation:** 4/10.
**Required polish for any direction; not identity.**

## G — Library + CLI + MCP ecosystem

**Layers:** library (keep) + CLI (keep) + MCP (add, 20h) + GH Action (add, 5h) + IDE via MCP (not extension) + hosted (defer).
**Market:** 7 via Action.
**Difficulty:** hosting is trap.
**Keep library+CLI+MCP+Action, defer hosted/IDE.**

**Strongest combination:** C as architecture, D as GTM, E as moat, F as DX.

**Tagline:** "The only deterministic Python context compiler safe for Django that any agent can read."

# Strategic Comparison

| Dimension 1-10                                | A Docs | B Optimizer |
| --------------------------------------------- | -----: | ----------: |
| User pain                                     |      4 |           7 |
| Market size                                   |      5 |           6 |
| Feasibility (1 maintainer)                    |      8 |           7 |
| Differentiation                               |      3 |           7 |
| Defensibility                                 |      2 |           5 |
| OSS attractiveness                            |      5 |           7 |
| AI relevance                                  |      2 |           9 |
| Token saving (real 5-22× vs generic 20× hype) |      1 |           8 |
| Developer adoption                            |      6 |           6 |
| Integration                                   |      4 |           6 |
| Monetization                                  |      2 |           5 |
| Overall                                       |    3.9 |         6.8 |

**Strongest long-term:** E
**Short-term:** D
**Commercial:** C/D
**Technical:** C
**OSS:** D
**Easiest:** F→A
**AI-aligned:** D
**Best combined:** C/D/E/F.

# Competitive Landscape

No star/pricing claims without source: all stars/pricing from 2026-02–08 GitHub/PyPI/official pages as cited in research.

## Python docs

* **Sphinx autodoc** 7,986★ BSD-2 4.3M dl/w — gold manual, needs import+conf.py+toctree, HTML/PDF, intersphinx. Fails on Django side-effects, heavy for SaaS product docs.
* **pdoc** 2,514★ MIT-0 (pdoc3 frozen 1,182★ AGPL-3 infection) — pdoc ./pkg -o html zero-conf, live-reload, but HTML-only + dynamic import.
* **pydoctor** 223★ MIT — static for Twisted/zope.interface, dated HTML, no Markdown.
* **mkdocstrings+griffe** 2,084+676★ ISC — ::: id injection in MkDocs Material, griffe static-or-runtime, needs mkdocs.yml, non-zero griffe chain.

**Redundancy:** if team ships themed HTML site, Sphinx wins.
**Win:** no import, verbatim, Django headers, single Markdown, zero deps, <1s — pre-processor that can feed them.

## AI packers (highest redundancy risk)

* **Repomix** 28,071★ MIT 254k npm/mo — npx repomix → single XML/MD/JSON, .gitignore, Secretlint, Tree-sitter compress ~70%, repomix.com, MCP, GH Action. Flat 50-500k tokens, stale snapshot, no Django.
* **Gitingest** 15,337★ MIT — hub→ingest URL hack, gitingest.com PAT, pip install gitingest lib. Same flat dump.
* **code2prompt** 7,619★ MIT Rust — Handlebars templates, git diff smart, code2prompt-rs bindings, MCP. Needs Cargo, flat.
* **files-to-prompt** 2,777★ Apache-2 (Simon Willison) — files-to-prompt path/ --cxml, minimal cat, stale 0.6 Feb 2025.

**Redundancy:** if Markdownizer is generic dump everything it loses to Repomix mindshare.
**Differentiation:** AST-aware Python packer (app>models.py#class X(Model) with fields/comments), zero Node (Python stdlib), token-aware headers for sub-select.

## Repo-map / structural

* **Aider --map** 47,300★ Apache-2 6.8M installs — Tree-sitter 40+ langs → PageRank → ~1k ranked map (--map-tokens, 8,192 fallback), 15B tokens/week, deterministic, inspectable. Lossy (no docstrings), tied to Aider.
* **Universal Ctags** 7,273★ GPL-2, **Tree-sitter** 26,766★ MIT — libraries, not tools.

**Complement:** Markdownizer as faithful full-content second layer to Aider's lossy map; Stacklit 250-token Go validates compact idea.

## RAG / hosted

* **Sourcegraph Cody** — since 2025-07-23 enterprise-only from $16k/yr (~$59/u), no indie trial. Batch Changes.
* **Cursor** — fork VS Code, hybrid semantic+lexical Bloom+Merkle, file-as-context -46.9%, Hobby $0 / Pro $20 / Pro+ $60 / Ultra $200 / Teams $40/u, >1M paid, cloud embeddings privacy/opaque.
* **Continue** 35,661★ Apache-2 — acquired by Cursor note, Teams $10/dev, now IDE plugin uncertainty.
* **Context7** 61,343★ MIT @$10/seat — version-specific upstream library docs (not your code), 30+ MCP clients.

**Win:** $0 vs $16k/yr, local git-commit context, air-gapped, no vector drift.

## MCP servers

* **Filesystem MIT** — read/write/list/search, no ranking/parsing.
* **codebase-memory-mcp** 40,932★ MIT C/Go static binary, ms avg / 3min Linux 75K files/28M LOC, ~120x (412k→3.4k), 12 tools Cypher, watcher.
* **Desktop Commander** 5,700★ MIT — terminal +Python/Node/R in-mem, Excel/PDF, blacklist risk.

**Gap:** No MCP emits Django-aware Markdown. Markdownizer-mcp (get_django_overview/list_apps/get_model_markdown) is 1 call vs 10 greps — fastest wedge.

See research for full star/pricing tables and vs Markdownizer battle cards (pdoc/Sphinx: never import; Repomix: extract signal not noise; Filesystem: eliminate 30 calls; Sourcegraph: no $1k min).

# Token Efficiency Analysis

## Does reduction = performance?

No — which tokens + where.

### Measured compatibilities

* **Repo size:** 10K LOC → 80-100k (7-10 tok/line, loctok 9.1), 50K → 400-500k, 100K → 800k-1M; GitTaskBench 54 tasks mean 52.6k LOC → 449k; repo-tokens >70% window red.
* **Cost:** 2023 median 100 → 2026 median 12 (-88%, BenchLM.ai); 1.2M @ $3/M Sonnet = $3.60, @ $0.30 Flash = $0.36, @ $0.20 Luna = $0.24; 20 turns×1.2M = $72 vs $7.20; but Batch -50%, Anthropic cache hit 0.10× = 90%, OpenAI 0.50×, Google 0.25×, DeepSeek V4-Flash $0.0028 cache-hit 1,785× cheaper than Opus.
* **Effective:** claimed → effective LWM-1M→<4K, GPT-4 128K→64K, Mixtral 32K→44.5% at 128K (RULER, only 4/17 pass 32K); NoLiMa lexical-overlap leak → GPT-4o 8K effective when >85% own baseline; Spheron Google/xAI double >200K, Anthropic 1M no surcharge.
* **Lost-in-middle:** Liu 1,051 cites U-shaped 75%→55%→72%, Grep + 50 docs +1.5% vs 20; LONGPIBENCH Findings ACL 2025 commercial still -20-30% relative spacing; EMNLP 2025 Length Alone Hurts 13.9-85% drop even perfect retrieval at beginning with masked blanks ≥7.9% at 30K, HumanEval 50% masked, recite-before +4%.
* **Optimizations:** Selective Context stale 423★ query-unaware; LLMLingua 20× at -1.5pp GSM8K but unreadable, rate-miss; LongLLMLingua +21.4% at ¼ question-aware+reorder; LLMLingua-2 3-6× faster (BERT distill); CPC 10.93× sentence-level; Aider 12× 12K→1k, binary search 15%; CTloc 5.85% MAPE; Kummer 30K queries 5 models 100-50K prompt 1.5-5×: up to 18% E2E speedup ONLY >5K prompt 4× A100, vLLM = 0, >1.3× only non-optimized, 75% memory → consumer GPU +0.3s.
* **Hierarchy:** (Berkeley Jha 2407.08892, 30K runs): extractive reranker (keep whole chunks, drop docs) > token pruning > abstractive summarization. All drop HotpotQA -30, QuAC -50, GSM8K compressed ICL worse than none. Rate-distortion optimal variable-rate far above existing; LLMLingua-2 Dynamic only beats optimal agnostic.
* **Dreaming.press killer pattern:** Cache stable prefix (90% Anthropic) + compress volatile suffix (fresh RAG) with question-aware gentle ratio on sentence-level, preserve grammar.

## Verdict for Markdownizer (nuanced)

Real as enabling layer, not standalone compression product. Brute force got 15× cheaper; median 14k LOC=168k fits; 78% production traffic <16k. Only >30k LOC / >10 turn loops / 70% window + middle-sensitivity needs it. For those, deterministic FTS5+graph 70% Recall@3 vs 40% rg, 13× fewer tokens + edge-placement is demonstrably 10-22× and more accurate (removes noise, puts signal at primacy/recency). For small services, ROI is repo-tokens + .claudeignore + caching + model cascade 4.4×.

If Markdownizer builds it, build hybrid: FTS5 + tree-sitter/ast graph + token-budgeted evidence packets, cache static 90%, compress volatile gently LongLLMLingua-2/CPC, budget to effective not advertised (50-70% rule), monitor Recall@K + task success, not tokens ×.

# AI-Ready Context Definition

Not marketing — testable.

## Structural understanding (exposed in IR ir_version)

* Project {name, root, git {commit, branch, dirty}, python_version, ir_version, hash} → Package {name, path, is_namespace} → Module {path, docstring, is_package, mtime, line_count} → Symbol {name, qualified_name, kind, lineno, decorators, base_classes, type_annotation, docstring, preceding_comments, inline_comments, source, is_public, is_async, is_method}.
* Symbol.kind ∈ {class,function,method,property,enum,dataclass,signal,urlconf} expanded to classifier labels (Django Model etc.).
* Relationships: imports (Module→Module, resolved vs external, alias), inherits (Class→Class, rightmost + MRO hint), defines (Module→Symbol, Class→Method), framework (Model→fields via ast, Serializer→fields, ViewSet→queryset, URL→view), entrypoints (manage.py, wsgi, urls, settings).

## Semantic preservation (must retain, deterministic)

* Public API (**all** if present else not name.startswith("_")), full type signatures (ast.unparse(annotation)), docstrings clean=False, decorators verbatim, inheritance chain, import aliases, config settings.INSTALLED_APPS / urls.py.
* Property: public API ⊆ output (invariant test).

## Noise elimination (safe vs dangerous)

* **Safe always:** IGNORED + .git/**pycache**/.venv/node_modules/site-packages/.eggs/build/dist, *.pyc, *.egg-info, htmlcov, .coverage, .idea/.vscode (add to scanner). Detected generated (DO NOT EDIT, // Code generated, **generated**) and vendored (vendor/).
* **Safe with flag:** migrations (profile != debugging), fixtures/*.json, *.lock, **pycache** tests (profile api drops tests/).
* **Dangerous to drop silently:** comments on undocumented public symbols (refactor profile keeps), type stubs *.pyi, **init**.py package docstrings, decorators with side effects (@receiver).

**Decision log per file:** FileInventory {path, reason: ignored|excluded|generated|kept}.

## Context optimization

* **rank:** PageRank on import graph + framework boosts (Model +2, urls/settings +2, management +3).
* **slice:** layered budget packer (--max-tokens 20k) 0: index 5% → 1: public signatures 15% → 2: ranked source → 3: comments + edge-place (high-rank at start/end).
* **query:** FTS5 over (name, qualified_name, docstring, file_path) + 1-hop graph expansion. No mandatory embeddings; markdownizer[ai] local all-MiniLM optional rerank.
* **Metrics ( §Success Metrics).**

# Compiler Architecture

```text
Input Layer         Path + git commit/branch/dirty + .gitignore + --exclude + CLI profile
  ↓
Repository Scanner  scanner.py (evolved) → FileInventory[] (path, mtime, size, hash, ignore reason)
  ↓                 rglob sorted, fnmatch, .gitignore via pathspec, os.scandir prune, hash=blake2b
Parser Frontend     parser.py → split frontends/python.py (ast+tokenize) , frontends/js.py (tree-sitter optional)
  ↓                 Raw IR: DocObjects + import nodes
Project IR Builder  ir.py  NEW  → Project IR v1 (JSON, hashable, versioned)
  ↓                 nodes: Package/Module/Symbol; edges: imports, inherits, defines, framework
Analysis Engine     analysis/ NEW
  ├─ framework.py   classifier.py generalized (Django/DRF/FastAPI/Pydantic/SQLAlchemy/Celery detectors)
  ├─ graph.py       import graph + PageRank (pure Python) + trace/bfs, cycle detect
  └─ metadata.py    entrypoints, test→code map (import + pytest --collect-only), config discovery, owners
  ↓
Context Optimizer   optimizer/ NEW
  ├─ rank.py        file/symbol importance
  ├─ slice.py       budget packer + edge placement + tiktoken/chars fallback
  └─ query.py       FTS5 SQLite prefilter + optional semantic rerank
  ↓
Output Backends     backends/ NEW  (renderer.py → backends/markdown.py)
  ├─ markdown.py    human+LLM (default, symbols-only variant `compact`)
  ├─ json.py        typed inventory (for RAG embedding, grep)
  ├─ xml.py         Claude-optimized (cxml)
  ├─ llms.py        llms.txt
  └─ mcp.py         resource/tool provider (stdio)
  ↓
Cache & Incremental ir.json (hash) + mtime/content-hash → skip unchanged (90% win on 200-file repo)
```

* **Remains:** scanner ignore/exclude, parser DocObject core, classifier taxonomy tables, renderer Markdown formatting.
* **Extracted:** _package_key/label → ir, _matches_exclude → scanner, _decorator_base → framework.
* **Stable interfaces:** FileInventory, Project IR schema (ir_version:1), Backend.render(ir, opts)->str (semver). ir.json is artifact users git commit or .gitignore (choice).
* **Internal:** tokenize fallback, _children monkey-patch → Symbol.children.
* **Plugins:** entry_points: markdownizer.backends / markdownizer.frameworks.

# How much exists implicitly

~40% — scanner/parser/classifier/renderer/extractor is frontend/middleware/backend; need IR builder + graph + optimizer (~400 LOC) + backends split.

# Project IR Strategy

Should it exist? **Yes — foundation for 1.0.**

```text
Project {
  meta: { name, root, git: {commit, branch, dirty}, python_version, ir_version:1, hash: blake2b, built_at },
  packages: Package[]  // Package {name: "pkg", path: "pkg", is_namespace: bool, modules: Module[]}
  modules: Module[]    // Module {path: "pkg/models.py", docstring, is_package, mtime, line_count, hash}
  symbols: Symbol[]    // Symbol {id, name, qualified_name, kind, file, lineno, decorators, base_classes,
                       //         type_annotation, docstring, preceding_comments, inline_comments, source,
                       //         is_public, is_async, is_method, framework: "Django Model"|...}
  edges: {
    imports:  {from: Module, to: Module|external, alias, level}[],
    inherits: {from: Class Symbol, to: Class string}[],
    defines:  {from: Module|Class, to: Symbol}[],
    framework:{from: Symbol, to: {fields, url, serializer}}[]
  }
  entrypoints: {manage, wsgi, urls, settings}?
  stats: {files, symbols, tokens_est, packages}
}
```

* Deterministic (sorted, blake2b(sorted_file_hashes)), serializable (ir.json, 500k tokens → <200kB), versioned (ir_version), hashable (cache key), reusable (all backends read one ir.json).
* Evolves DocObject → Symbol (add type_annotation, is_public, framework, children field). Migration shim keeps DocObject alias 1.0.
* Stored as docs/.markdownizer/ir.json or stdout --emit-ir.
* Enables: diff (ir.json@HEAD~1 → ir.json@HEAD), inspect(symbol) (callers/callees via edges), incremental (mtime/hash skip), query (FTS5 over symbols).

# Output Formats

| Format                 | Human |                    LLM |                                     Tokens |
| ---------------------- | ----: | ---------------------: | -----------------------------------------: |
| Markdown               |   ★★★ |            ★★★ (paste) |                               ★★ (verbose) |
| Compact (symbols-only) |    ★★ |            ★★★ (Aider) | ★★★ 5× smaller (signatures+docstring only) |
| JSON (typed inventory) |    ★☆ |       ★★★ (agent JSON) |                                        ★★★ |
| XML (cxml)             |    ★☆ | ★★★ (Claude loves XML) |                                         ★★ |
| llms.txt               |    ★★ |                     ★★ |                                         ★★ |
| MCP resources          |     — |             ★★★ (live) |                            ★★★ (on demand) |
| Custom DSL             |    ★☆ |       ★☆ (LLM hostile) |                                        ★★★ |

* Keep Markdown-first as default human+LLM artifact (paste, git commit, RAG chunk, llms.txt source). But become compiler with Markdown as one backend — otherwise token-price, lost-in-middle, and agent diversity force bespoke formats anyway.
* compact is the token story: 50k LOC 500k → compact 100k (5×) without dropping public API.
* json is the machine story: jq '.symbols[] | select(.framework=="Django Model")' + text-embedding-3 chunking (already denoised → higher RAG).
* mcp is the interaction story: context(query,budget,profile) on demand vs static dump.

# CLI Strategy

Current (cli.py:16): single verb markdownizer <project> -o <out> flat flags (--exclude, --no-source, --only-documented, -v/-q, --version) — clean for 0.2.1 but not scalable to compiler.

## Smallest excellent CLI (additive, old form stays alias)

```bash
markdownizer [project] -o <out>                     # 0.2 compat alias → build
markdownizer scan  [project] [--json] --stats       # FileInventory, no parse (fast)
markdownizer build [project] -o <out> [--format md|compact|json|xml] [--emit-ir]
markdownizer context [project] [--query "fix auth"] [--max-tokens 20k] [--profile arch|api|debug|refactor|django|onboard] [--format md]  # budget+rank+query slice
markdownizer inspect <symbol> [--callers|--callees] # DocObject + edges
markdownizer stats [project] [--json]               # counts, tokens_est, coverage, top PageRank
markdownizer diff  [revA [revB]]                    # ir.json diff (changed symbols+dependents)
markdownizer export [project] --format json|xml     # alias to build --format
markdownizer mcp    [--root .]                      # stdio MCP server (3 tools, 2 resources)
```

* Additive: markdownizer . -o ./docs keeps working (main() dispatches to build if no subcommand).
* Subparsers via add_subparsers(dest="cmd", required=False); build_parser() splits to parsers["build"].
* Flags additive: --max-tokens, --profile, --query, --emit-ir, --check/--diff.
* Help stays markdownizer --help → verbs + markdownizer context --help per-verb.

# MCP Strategy

Model: User project ↓ Markdownizer → Project IR (ir.json) → MCP server (stdio) → AI agent

Should it exist? Yes — as optional, zero-LLM, local.

* **Tools (3):** context(query?, budget?, profile?, format?) → ranked string (FTS5+graph, budget-aware, edge-placed); inspect(symbol) → Symbol+callers/callees/defined-in; stats → {files, symbols, tokens_est, top PageRank}.
* **Resources (2):** resource://markdownizer/packages/{pkg} (Markdown slice), resource://markdownizer/ir.json (full IR JSON).
* Belongs in 0.5.x, not 0.x now — needs IR+query (0.3-0.4) first. Separate optional package markdownizer[mcp] (mcp SDK >=1.0 dep) vs core zero deps — install as pipx install markdownizer[mcp] or uvx markdownizer mcp. Single binary markdownizer mcp --root . works with claude mcp add, opencode.json, cursor mcp.json, cline_mcp_settings.json.
* Why not Filesystem MCP? read_file brute force (6.4× tokens Holysheep) vs one context("fix auth", budget=20k) call.

# Python-First Strategy

Smart — keep Python-first until 1.0.

* Python ast is stdlib, no tree-sitter wheels; Python metaclass/graph is under-served (TS has better tooling). Django/DRF vertical 13 headers is defensible wedge vs generic packers that treat class User(Model): as plain class. django-packages has no context category.
* Framework moat (prioritized):

| Framework              | Symbol to detect (ast pattern)                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------- |
| Django Model           | ClassDef(bases: rightmost∈{Model,AbstractUser,...}) already 100% tests + field = models.*Field(...) |
| DRF Serializer/ViewSet | ModelSerializer/Serializer, ModelViewSet/ViewSet already                                            |
| Django URLs            | urlpatterns = [...] already                                                                         |
| Django Admin           | ModelAdmin/TabularInline already                                                                    |
| Django Settings        | settings.py: INSTALLED_APPS/MIDDLEWARE via Assign                                                   |
| Celery tasks           | @shared_task/@app.task + _decorator_base                                                            |
| FastAPI                | APIRouter.get/post, Depends                                                                         |
| Pydantic               | BaseModel + Field(...)                                                                              |
| SQLAlchemy             | DeclarativeBase + Mapped[...]                                                                       |
| pytest                 | test_*.py + Test* + fixture                                                                         |

* Do not add multi-language before 1.0 (tree-sitter 371 langs vs stdlib). Optional markdownizer[js] after 1.0 if demand.

# Open-Source Strategy

Core stays MIT, local, deterministic, zero-LLM, zero runtime deps (CONTRIBUTING.md:44).

* **Free/open:** library + CLI + MCP server + GH Action + pre-commit + IR schema + backends/markdown+compact+json/xml + framework detectors. Publish mcp-registry entry, django-packages listing.
* **Plugins stay free:** entry_points: markdownizer.frameworks/backends.
* **Do NOT invent SaaS prematurely.** Token story is $0.20/M collapsing; hosted context API would compete with Cursor $20-200/mo and Sourcegraph $16k. Only justify monetization if 0.5.0 MCP shows >1k weekly invocations + enterprise asks for private-repo cache/SSO/hosted ir.json sync. Then: Open core + Hosted incremental cache + Team diff dashboard + Managed MCP (SOC2) — never paywall core.

# Core Product Guarantees

Official principles (add to README.md + CONTRIBUTING.md):

1. **Deterministic:** same repo state (commit blake2b) → same ir.json + same Markdown hash. Test: hash(ir.json@commit).
2. **No hallucination:** never invents fields/docstrings; only ast/tokenize verbatim. Test: output ⊂ repo (every emitted name/field exists in ast).
3. **No code modification:** read-only rglob + parse_file; never writes to project (only to -o).
4. **Local-first:** repo never leaves machine; offline; no telemetry by default (opt-in stats only).
5. **AI-independent:** no OPENAI_API_KEY, no all-MiniLM by default; markdownizer[ai] optional local rerank.
6. **Reproducible:** ir.json includes ir_version, hash, built_at; markdownizer diff explains drift.
7. **Explainable:** stats --explain shows include/exclude/generated reason per file; FileInventory.reason.

# Benchmark Strategy

Compare: Raw repo (cat) | naive concat | Repomix (default + compress) | Gitingest | Aider RepoMap (1k) | Markdownizer (full + compact) on same 5 real Python/Django repos: Django, Wagtail, Saleor (100k LOC), FastAPI, Self.

## Metrics (technical)

* tokens (tiktoken o200k + chars/3.3), files, symbols, public API retention (emitted public / total public), relevant-symbol Recall@3 (FTS5 top-3 vs rg), context coverage (symbols in budget / total), determinism (hash), latency (cold/cached), memory (graph vs ir.json size).
* **Do not claim 5×/20× without benchmark** — measure per profile (architecture vs api).

## Task success (product)

On GitTaskBench-style issues (fix auth, add field to User, trace signal``): agent (Claude Code + context artifact) vs agent alone → files edited correct / tests pass / turns. 1 maintainer can run 5×6 configs ×3 queries manually; automate in benchmark/ later.

## Product metrics

stars, PyPI dl/week, weekly context/mcp invocations (opt-in), GH Action adoption, ir.json cache hits.

# Conservative Roadmap

**Identity:** best docs extractor. Safest, smallest TAM.

* **0.2.x polish (4-6w):** --mode file, include_private + **all** respect, TOC anchors + mkdocs nav snippet, golden snapshots.
* **0.3.x frameworks (6w):** FastAPI/Pydantic/SQLAlchemy/Celery detectors + plugin hook.
* **0.4.x pipelines (4w):** GH Action uses: markdownizer/action@v1, pre-commit --check --diff.
* **0.5.x-1.0.0:** stabilize Markdown hash, 1.0 semver. No AI.

**Why not primary:** caps at docs, no AI tailwind, pdoc zero-conf already wins.

# Ambitious Roadmap

**Identity:** Codebase-to-Context Compiler. Recommended.

* **0.3.0 IR + Backend Split (6-8w):** Project IR v1 (ir.py, hash, versioned), backends/markdown.py (renderer refactor) + backends/json.py + backends/compact.py (signature mode), include_source="signature", ir.json artifact, import graph (Import/ImportFrom → Path).
* **0.4.0 Budget + Rank (6w):** layered packer + edge-place + tiktoken optional + profile presets, stats + context verbs.
* **0.5.0 MCP + Query (6w):** markdownizer mcp 3 tools/2 resources, FTS5 query+trace 1-hop, GH Action llms.txt, OpenCode/Claude/Cursor guides.
* **0.6.0 Intelligence + Incremental (8w):** framework detectors (FastAPI/Pydantic), entrypoints, test→code map, explain --architecture, mtime/hash cache (<200ms cached on 200 files).
* **1.0.0 (8-12w after):** freeze IR v1 + Backend + CLI verbs, DocObject→Symbol shim, mike docs site.

**Each minor useful standalone; kill if ir.json adoption <5% after 0.3 8w → fallback Conservative.**

# Moonshot Roadmap

**Identity:** repository intelligence / context infrastructure (hosted, multi-lang, team).

0.3-0.6 as Ambitious plus:

* **0.7.x multi-language:** JS/TS via tree-sitter (markdownizer[js]), Go/Rust later, language-agnostic IR.
* **0.8.x team/temporal:** CODEOWNERS ownership, git log churn/hotspot, diff HEAD~1 incremental, hosted sync.
* **0.9.x platform:** hosted private-repo cache, team API, VS Code extension, vector rerank, RBAC.
* **1.0→2.0 multi-repo:** impact("change User.email") → 14 services cross-repo graph.

**Why not now:** needs team/funding, competes with Sourcegraph $16k/Cursor.

# Recommended Roadmap

Ambitious with Conservative polish and Moonshot optionality.

Does not follow blind 0.2→0.3→… numbers — gates on maturity, not calendar.

| Version     | Goal          | User value                 | Features                                                                                              |
| ----------- | ------------- | -------------------------- | ----------------------------------------------------------------------------------------------------- |
| 0.2.2 patch | foundation    | trust                      | raise gate 85→90, Windows CI, dependabot, concurrency, fix **main** coverage, restore or rm vision.md |
| 0.3.0       | IR + backends | one artifact, many outputs | IR v1+hash, json+compact backends, signature mode, import graph                                       |
| 0.4.0       | budget + rank | fits window                | PageRank, layered packer, edge-place, tiktoken opt, profile                                           |
| 0.5.0       | MCP + query   | any agent                  | mcp stdio, FTS5 query/trace, GH Action                                                                |
| 0.6.0       | intelligence  | understand repo            | FastAPI/Pydantic, entrypoints, test→code, explain, cache                                              |
| 1.0.0       | freeze        | semver trust               | IR v1 stable, Backend stable, Symbol                                                                  |

**Advance to Moonshot only if 0.5.0 MCP >1k weekly + enterprise pull.**

# Version Strategy

* **0.2.x alpha patch (0.2.2 now).** 0.3-0.6 minor = feature, patch = fix (breaking allowed per 0.y.z but avoided via alias). IR ir_version:1 bump only on breaking IR change. 1.0.0 freezes IR+Backend+CLI; DocObject→Symbol shim with deprecation. Beyond 1.0 strict semver: new backends/frameworks = minor, IR break = major, hosted never breaks OSS.
* **0.3-0.6:** minor = feature, patch = fix (breaking allowed per 0.y.z but avoided via alias).
* **1.0.0:** freezes IR+Backend+CLI; DocObject→Symbol shim with deprecation.
* **Beyond 1.0:** strict semver; new backends/frameworks = minor, IR break = major; hosted never breaks OSS.

# What NOT To Build

* Mandatory LLM API — breaks local/privacy/offline, adds billing; keep markdownizer[ai] opt-in local all-MiniLM only.
* LLM summaries / doc generation — hallucinates, breaks verbatim; optional --ai-summary only post-1.0 behind --opt-in.
* Cloud service / SaaS / hosted vector DB / RAG platform — premature, competes with Cursor/Sourcegraph, kills zero-deps; defer until >5k★ + enterprise pull.
* Vector DB in core — FTS5 SQLite suffices; embeddings RAM/freshness/privacy liability.
* GUI / VS Code extension before MCP — MCP reaches all agents in 20h; extension is 10× distribution.
* Multi-language before 1.0 — tree-sitter wheels bloat, Python/Django moat lost.
* Custom DSL / new format — LLM-hostile, unparseable; use md/json/xml/mcp.
* Complex embeddings / automatic rewriting — IR is read-only; rewriting is agent job.
* Watch daemon in core — entr/watchexec + mcp covers; daemon scope creep.

# 12-Month Plan

**1 maintainer, 10-15h/week, Python-first, no paid AI.**

## Phase 0 — Foundation (W 1-2, 0.2.2)

Raise gate, Windows CI, dependabot, concurrency, **main** test, restore/rm vision.md.

**Deliverable:** 0.2.2 patch.

## Phase 1 — IR + Backends (W 3-10, 0.3.0)

Design IR schema + hash, spike import resolver on Django/Wagtail/Saleor, extract ir.py, split renderer→backends/markdown|json|compact, signature mode, ir.json + extract_project(emit_ir), IR golden tests.

**Success:** ir.json on 5 repos, compact 5× vs full.

## Phase 2 — Budget/Rank (W 11-16, 0.4.0)

PageRank (pure Python), layered packer + edge-place, tiktoken opt / chars/3.3 fallback, profile presets, context+stats verbs, determinism hash test, blog Docs-as-context with Saleor 500k→20k numbers.

**Validation:** public API 100%.

## Phase 3 — MCP/Query (W 17-22, 0.5.0)

mcp.py 3 tools/2 resources via mcp SDK, FTS5 query+trace 1-hop, query.py rerank optional, OpenCode integration (opencode.json example), Claude/Cursor guides, GH Action llms.txt, mcp inspector video.

**Success:** 1k mcp weekly.

## Phase 4 — Intelligence/Incremental (W 23-32, 0.6.0)

FastAPI/Pydantic detectors, entrypoints (manage/urls/settings), test→code map, explain --architecture deterministic, mtime/hash cache (<200ms on 200 files).

**Validation:** Saleor cold <1s.

## Phase 5 — 1.0.0 (W 33-36)

Freeze IR v1 + Backend + verbs, DocObject→Symbol shim, mike site, pip-audit, tag 1.0.0 OIDC.

Announce django-packages/r/Python/r/LLMDev/OpenCode Discord.

**Kill criteria:** 0.3.0 ir.json adoption <5% after 8w → pause graph, polish Markdown. 0.5.0 mcp <500 weekly → defer 0.6 intelligence, ship 1.0 on 0.4 base.

# Success Metrics

## Technical (per profile, measured on 5 repos)

* compression ratio = raw tokens / output tokens (raw via tiktoken, output per backend)
* public API retention = emitted public / total public (must 100% for compact)
* Recall@3 = top-3 FTS5+graph hits contain ground-truth file (70% vs 40% rg benchmark)
* determinism = hash(ir.json@commit) stable
* latency cold (<1s/200 files) / cached (<200ms), memory (ir.json <200kB/500k tok), branch coverage ≥90%

## Product

* GitHub stars (1k by 1.0)
* PyPI dl/week (500)
* weekly context/mcp invocations (1k)
* GH Action adoption (10 repos)
* ir.json cache hits

**Benchmark suite:** benchmark/ raw|repomix|Gitingest|Aider 1k|Markdownizer full|compact × tokens/files/symbols/coverage/Recall@3/latency, with GitTaskBench-style task success (files correct/tests pass/turns).

# Risks

## Technical

* **Import resolution** (namespace/DJANGO_SETTINGS_MODULE, alias, **/) → 70% graph → mark external.
* **Django ModelBase field metaclass** → griffe/django-stubs hint post-1.0.
* **PageRank repo-sensitive** (n8n grep wins) → expose --rank.
* **Token divergence** → soft limit +10%.
* **Cache invalidation** → blake2b+mtime.
* **MCP churn** → pin SDK.
* **Monorepo 10k files** → --jobs after 0.6.

## Product

* **Token price $0.20 kills generic pitch** → pitch accuracy+loop with Recall not tokens.
* **Repomix 28k★ mindshare** → Python/Django qualifier + zero Node.
* **Vendor absorb** → niche deterministic Django moat.
* **1 maintainer scope** → each minor standalone useful + kill criteria.
* **Principle tension (never generates)** → keep zero-LLM default.
* **Multi-language temptation** → PYTHON-FIRST until 1.0.

# Final Product Definition

### One sentence

Markdownizer is a deterministic, local, zero-LLM Codebase-to-Context Compiler that turns any completed Python project into a hash-stable, budget-aware context artifact any AI agent can read.

### One paragraph

Developers hand completed/partial/inherited Python/Django projects to Claude Code/OpenCode/Cursor/Cline/Gemini/ChatGPT by pasting raw repos and hit 1M→200k effective windows, 75%→55% middle recall, and 30× loop cost. Markdownizer solves it before the AI sees it: static ast+tokenize scan → Project IR (packages→modules→symbols + imports/inherits/defines + Django/DRF labels) → deterministic PageRank+FTS5 rank → layered, edge-placed, max-tokens-budgeted emit (Markdown default, compact/json/xml/mcp on demand). No API keys, no cloud, same commit → same hash for RAG cache.

### One example

```text
Raw:  50,000 lines Python (500k tokens) + fixtures + migrations + 69 files naive
 → $ markdownizer build . --profile architecture --max-tokens 20k --format markdown
IR:   ir.json  {packages 12, modules 64, symbols 312, hash blake2b, 0.8s}
Out:  context.md 20k (index 1k + public signatures 3k + ranked source 12k + comments 4k, edge-placed)
 → cat context.md | claude -p "explain auth"   # Sonnet 200k effective, 20k well-placed → no middle loss
Metrics: raw 500k → 20k (25:1), public API 100%, Recall@3 70% vs 40% rg, cold 0.8s cached 0.12s
```

### Taglines (5, pick 1)

1. **Your codebase, compiled for AI.** ← strongest
2. Deterministic context for any agent.
3. Markdown by default, multi-backend by design.
4. The only Django-aware context compiler that never invents.
5. Same commit → same context — local, free, explainable.

# Final Recommendation

1. **What:** deterministic Codebase-to-Context Compiler (Python-first, Django-moat, Markdown default, multi-backend, MCP-optional).
2. **Why:** effective window << advertised + lost-in-middle + loop amplification make which tokens the durability problem even as price → $0; static structural compression beats pruning (+21.4% at ¼) and cache beats generic compression (90%). Markdownizer's ast+tokenize + zero import + Django taxonomy is the only local wedge vs Repomix generic dump / Cursor/Sourcegraph hosted.
3. **Who:** Django team >30k LOC or >10 turn loops handing a project to any agent; secondary 500k LOC enterprise needing air-gapped context.
4. **Core problem:** raw repo is noisy, unstructured, over-budget, and mis-ordered → agents lose middle and burn turns.
5. **Why important:** even perfect retrieval at beginning still degrades 7.9% at 30k masked (length alone hurts); 10k vs 1k explorer 10× at 9pp loss shows signal matters more than price.
6. **Why Markdownizer uniquely:** zero deps, static ast+tokenize, verbatim decorators/comments, Django/DRF 13 headers, sorted hash-stable Markdown, 91% strict-typed, already compiler-shaped — IR+backends is 4-file refactor, not rewrite.
7. **Why no AI internally:** privacy, $0, offline, reproducible, never generates trust, deterministic 10-22× already beats LLMLingua 50-point grounding drop and 18% speedup-only pruning; FTS5+graph beats embeddings 70% vs 40% without API.
8. **What next:** 0.3.0 Project IR v1 + backends/json+compact + import graph + ir.json. Everything composes on it.
9. **What NOT:** mandatory LLM, vector DB/RAG in core, cloud/SaaS, HTML/PDF site, JS/TS before 1.0, GUI, watch daemon, custom DSL, token-pruning default.
10. **What is 1.0:** frozen IR v1 schema + Backend interface + CLI verbs (scan/build/context/inspect/stats/diff/mcp) + Symbol + deterministic hash + public API 100% guarantee, semver thereafter, with migration shim preserving extract_project().

If built as above, Markdownizer becomes the pipx install that every Python/Django + AI team git commits once (ir.json + context.md) and every agent (OpenCode first) reads in one call instead of thirty — the cheapest, most defensible infrastructure for the AI coding era a single maintainer can ship.
