"""Backend abstraction: deterministic rendering of a ProjectIR into output files."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Union

from markdownizer.ir import ProjectIR

SourceMode = Union[bool, Literal["signature"]]


@dataclass
class RenderOptions:
    """Options controlling how a backend renders an IR.

    ``include_source`` may be ``True`` (full source), ``False`` (no source),
    or ``"signature"`` (declaration line only).
    """

    root_name: str = "_root"
    include_source: SourceMode = True
    include_comments: bool = True
    include_undocumented: bool = True


class Backend(Protocol):
    """A backend renders a ProjectIR into ``{filename: content}`` pairs.

    Implementations must be deterministic: the same IR always produces the
    same output.
    """

    name: str

    def render(self, ir: ProjectIR, options: RenderOptions) -> dict[str, str]: ...
