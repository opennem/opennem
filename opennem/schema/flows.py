"""
Structures for flow types
"""

from enum import Enum


class FlowType(Enum):
    imports = "imports"
    exports = "exports"
