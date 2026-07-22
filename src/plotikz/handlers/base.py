"""Base abstract class for trace handlers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Set, Optional


class TraceHandler(ABC):
    """Base class for Plotly trace conversion handlers."""

    def __init__(self):
        self.packages: Set[str] = set()
        self.libraries: Set[str] = set()

    @abstractmethod
    def can_handle(self, trace_type: str) -> bool:
        """Check if this handler supports trace_type."""
        pass

    @abstractmethod
    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process trace and return trace metadata dictionary."""
        pass
