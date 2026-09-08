"""JSON backend: deterministic serialization of the Project IR."""

from __future__ import annotations

from markdownizer.backends.base import RenderOptions
from markdownizer.ir import ProjectIR


class JSONBackend:
    """Render the full ProjectIR as ``project.json``.

    This backend serializes the complete IR regardless of ``RenderOptions``;
    it is a faithful machine-readable representation of the analysis.
    """

    name = "json"

    def render(self, ir: ProjectIR, options: RenderOptions) -> dict[str, str]:
        return {"project.json": ir.to_json() + "\n"}
