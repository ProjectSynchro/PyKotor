from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.node import Node

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class PReturn(Node):
    """Base class for return nodes in the NCS decompiler parse tree."""

    def __init__(self):
        super().__init__()

    def clone(self) -> Node:
        raise NotImplementedError("PReturn.clone() should be implemented by subclasses")

    def apply(self, sw):
        if hasattr(sw, 'case_p_return'):
            sw.case_p_return(self)
        else:
            super().apply(sw)
