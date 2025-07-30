"""
Tests for BIS GQ Mapper models module.
"""

import pytest
from src.models import GQDataItem, DSDDataPoint


class TestGQDataItem:
    """Test cases for GQDataItem dataclass."""
    
    def test_basic_creation(self):
        """Test basic GQDataItem creation."""
        item = GQDataItem(
            code=6,
            value=1000.0,
            description="Total claims"
        )
        
        assert item.code == 6
        assert item.value == 1000.0
        assert item.description == "Total claims"
        assert item.part is None
        assert item.category is None
        assert item.counterparty is None
    
    def test_full_creation(self):
        """Test GQDataItem creation with all fields."""
        item = GQDataItem(
            code=221,
            value=500.0,
            description="Loans to Non-banks",
            part="I",
            category="Loans",
            counterparty="F"
        )
        
        assert item.code == 221
        assert item.value == 500.0
        assert item.description == "Loans to Non-banks"
        assert item.part == "I"
        assert item.category == "Loans"
        assert item.counterparty == "F"
    
    def test_equality(self):
        """Test GQDataItem equality comparison."""
        item1 = GQDataItem(code=6, value=1000.0, description="Total claims")
        item2 = GQDataItem(code=6, value=1000.0, description="Total claims")
        item3 = GQDataItem(code=17, value=1000.0, description="Total claims")
        
        assert item1 == item2
        assert item1 != item3


class TestDSDDataPoint:
    """Test cases for DSDDataPoint dataclass."""
    
    def test_basic_creation(self):
        """Test basic DSDDataPoint creation."""
        point = DSDDataPoint(
            code="CAF",
            value=1500.0,
            description="Claims, All Instruments, on Non-bank Fin. Inst."
        )
        
        assert point.code == "CAF"
        assert point.value == 1500.0
        assert point.description == "Claims, All Instruments, on Non-bank Fin. Inst."
        assert point.formula is None
    
    def test_full_creation(self):
        """Test DSDDataPoint creation with formula."""
        point = DSDDataPoint(
            code="CGB",
            value=350.0,
            description="Claims, Loans & Deposits, Banks (Total)",
            formula="4+376"
        )
        
        assert point.code == "CGB"
        assert point.value == 350.0
        assert point.description == "Claims, Loans & Deposits, Banks (Total)"
        assert point.formula == "4+376"
    
    def test_equality(self):
        """Test DSDDataPoint equality comparison."""
        point1 = DSDDataPoint(code="CAF", value=1000.0, description="Test")
        point2 = DSDDataPoint(code="CAF", value=1000.0, description="Test")
        point3 = DSDDataPoint(code="CGB", value=1000.0, description="Test")
        
        assert point1 == point2
        assert point1 != point3