"""JSON backend: deterministic serialization of the Project IR."""

from __future__ import annotations

from markdownizer.backends.base import RenderOptions
from markdownizer.ir import ProjectIR
from markdownizer.optimizer.rank import rank_ir


class JSONBackend:
    """Render the full ProjectIR as ``project.json``.

    This backend serializes the complete IR regardless of ``RenderOptions``;
    it is a faithful machine-readable representation of the analysis,
    including deterministic per-symbol and per-file ranking scores.
    """

    name = "json"

    def render(self, ir: ProjectIR, options: RenderOptions) -> dict[str, str]:
        rank_ir(ir)
        return {"project.json": ir.to_json() + "\n"}
