"""
Data models for BIS GQ Mapper.

This module defines the core data structures used throughout the application
for representing GQ data items and DSD data points.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GQDataItem:
    """Represents a single data item from the GQ return."""
    code: int
    value: float
    description: str
    part: Optional[str] = None
    category: Optional[str] = None
    counterparty: Optional[str] = None


@dataclass
class DSDDataPoint:
    """Represents a mapped data point in the DSD format."""
    code: str
    value: float
    description: str
    formula: Optional[str] = None