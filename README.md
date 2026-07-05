# Markdownizer

Extract existing documentation from Python projects into Markdown.

Markdownizer **never** generates, rewrites, summarizes, or improves documentation.
It only extracts what is already present in your source code: docstrings,
comments, decorators, and source.

## Installation

```bash
pip install -e .
```

## Usage

```bash
markdownizer /path/to/project -o ./docs
```

This recursively scans the project, parses every Python file with the AST, and
writes one Markdown file per package into `./docs`.

### What is extracted

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