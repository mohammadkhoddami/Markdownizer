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

### Budgeted context

Produce the best possible representation of a project within a token budget:

```bash
markdownizer context . --max-tokens 20000 --profile api
markdownizer context . --profile django --query "user model"
```

Writes `context.md`. Options: `--max-tokens` (default 20000), `--profile`
(`architecture` default, `api`, `debugging`, `refactor`, `django`,
`onboarding`), `--rank` (`pagerank` default, `fanout`, `simple`), and
`--query` (deterministic keyword prefilter).

### Statistics

```bash
markdownizer stats . --rank pagerank
markdownizer stats . --json
```

Shows project counts, a token estimate, and top-ranked files/symbols.
Ranking is deterministic: PageRank over the import graph with
framework-aware boosts (Django models, URL configs, management commands),
combined with public/documented factors per symbol.

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
from markdownizer import extract_project, build_project_ir, optimize_context

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

# Or generate a budgeted, ranked context artifact:
ctx = optimize_context(ir, max_tokens=20000, profile="api", query="auth")
print(ctx.estimated_tokens, ctx.included_symbols)
print(ctx.text)
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

---

# راهنمای فارسی — Markdownizer برای توسعه‌دهندگان ایرانی

## مارک‌داونایزر چیست؟

مارک‌داونایزر (Markdownizer) یک ابزار خط‌فرمان پایتونی و کاملاً رایگان و متن‌باز است که کدهای پروژه‌ی شما را تحلیل می‌کند و آن‌ها را به یک **نمای تمیز، ساختارمند و کم‌حجم** از پروژه تبدیل می‌کند؛ خروجی‌ای که هم برای انسان‌ها قابل خواندن است و هم برای مدل‌های هوش مصنوعی (مثل Claude، ChatGPT، Gemini و ابزارهایی مثل Cursor یا Claude Code) آماده‌ی استفاده است.

نکته‌ی کلیدی این است که مارک‌داونایزر **هیچ‌چیز جدیدی تولید نمی‌کند**. نه مستندسازی می‌نویسد، نه خلاصه‌سازی می‌کند و نه کدی را تغییر می‌دهد. فقط چیزهایی که از قبل در کد شما هست — داک‌استرینگ‌ها، کامنت‌ها، دکوریتورها و خود کد — را به‌صورت دقیق و بدون کم‌وکاست استخراج می‌کند و مرتب تحویل می‌دهد.

> **چرا این مهم است؟** وقتی پروژه‌ای را به یک مدل هوش مصنوعی می‌دهید، هر توکن (کلمه‌ی پردازش‌شده) هزینه دارد و هرچه ورودی شلوغ‌تر باشد، نتیجه ضعیف‌تر می‌شود. مارک‌داونایزر مثل یک «کامپایلر» عمل می‌کند: پروژه‌ی خام را می‌گیرد و بهترین نسخه‌ی ممکن را در محدوده‌ی بودجه‌ی توکنی که شما تعیین می‌کنید تحویل می‌دهد.

## نصب

فقط پایتون ۳.۹ یا بالاتر لازم دارید؛ بدون هیچ وابستگی اضافه:

```bash
pip install markdownizer
```

یا اگر ترجیح می‌دهید ایزوله نصب کنید:

```bash
pipx install markdownizer
```

برای بررسی نصب:

```bash
markdownizer --version
```

## استفاده‌ی سریع

ساده‌ترین حالت — اسکن پروژه و تولید یک فایل مارک‌داون برای هر پکیج:

```bash
markdownizer /path/to/project -o ./docs
```

بعد از اجرا، داخل پوشه‌ی `docs` برای هر پکیج یک فایل `.md` می‌بینید که شامل داک‌استرینگ‌ها، کامنت‌ها، دکوریتورها و سورس‌کد هر کلاس و تابع است.

### انتخاب فرمت خروجی

```bash
# مارک‌داون (پیش‌فرض) — مناسب انسان و هوش مصنوعی
markdownizer build . -o ./docs --format markdown

# JSON — نمای کامل و ماشینی پروژه (مناسب ابزارها و سیستم‌ها)
markdownizer build . -o ./docs --format json

# فشرده — ساختار، امضاها و داک‌استرینگ‌ها بدون بدنه‌ی کد
markdownizer build . -o ./docs --format compact
```

### تولید کانتکست با بودجه‌ی توکنی

اگر می‌خواهید دقیقاً مشخص کنید چند توکن صرف شود:

```bash
markdownizer context . --max-tokens 20000 --profile api
```

این دستور فایل `context.md` می‌سازد؛ بهترین نمای پروژه در محدوده‌ی ۲۰ هزار توکن. برای پروژه‌های جنگویی:

```bash
markdownizer context . --profile django --query "user model"
```

پروفایل‌های آماده: `architecture` (پیش‌فرض)، `api`، `debugging`، `refactor`، `django` و `onboarding`.

### آمار پروژه

```bash
markdownizer stats .
markdownizer stats . --json
```

تعداد فایل‌ها، سمبل‌ها، پکیج‌ها و مهم‌ترین فایل‌های پروژه را بر اساس گراف ایمپورت‌ها (PageRank) نشان می‌دهد.

### نمونه‌ی کامل

```bash
# ۱. نصب
pip install markdownizer

# ۲. ساخت کانتکست فشرده برای هوش مصنوعی
markdownizer context . --max-tokens 20000 --profile architecture -o ./docs

# ۳. استفاده از خروجی — مثلاً ارسال به Claude Code
cat docs/context.md | claude -p "توضیح بده معماری این پروژه چطور است"
```

## نکته‌های کاربردی

- اگر پوشه‌ی پروژه‌ی شما `build`، `context` یا `stats` نام دارد، حتماً با `./` صدا بزنید: `markdownizer ./build`.
- برای رد کردن پوشه‌هایی مثل تست‌ها یا مایگریشن‌ها: `--exclude "tests/*" --exclude "migrations"`
- خروجی کاملاً قطعی است: با همان کد، همیشه همان خروجی تولید می‌شود؛ یعنی می‌توانید فایل‌های تولیدشده را داخل گیت ذخیره کنید و از تغییرات ناخواسته باخبر شوید.
- مارک‌داونایزر کد شما را اجرا نمی‌کند و به اینترنت وصل نمی‌شود؛ کاملاً امن و آفلاین است.

## استفاده در کد پایتون

```python
from pathlib import Path
from markdownizer import build_project_ir, optimize_context

ir = build_project_ir(Path("."))
print(ir.hash)                # هش قطعی پروژه
print(ir.stats.symbol_count)  # تعداد سمبل‌ها

ctx = optimize_context(ir, max_tokens=20000, profile="api")
print(ctx.text)
```

## محدودیت‌ها

- در حال حاضر فقط پروژه‌های پایتون پشتیبانی می‌شوند (پشتیبانی از زبان‌های دیگر در برنامه‌ی آینده است).
- گراف ایمپورت فقط ایمپورت‌های سطح ماژول را می‌بیند؛ ایمپورت‌های داخل توابع عمداً در نظر گرفته نمی‌شوند.
- اگر پرسش‌وجو (جست‌وجوی کلمه‌ای) نیاز دارید، فعلاً یک فیلتر ساده و قطعی است؛ جست‌وجوی معنایی در نسخه‌های بعدی اضافه می‌شود.

## مستندات بیشتر

- مستندات کامل فنی پروژه: [docs/PROJECT.md](docs/PROJECT.md)
- تاریخچه‌ی تغییرات: [CHANGELOG.md](CHANGELOG.md)
- راهنمای مشارکت: [CONTRIBUTING.md](CONTRIBUTING.md)

---

*این راهنما برای توسعه‌دهندگان فارسی‌زبان نوشته شده است. اگر سؤال یا پیشنهادی دارید، از طریق [GitHub Issues](https://github.com/mohammadkhoddami/Markdownizer/issues) در میان بگذارید.*