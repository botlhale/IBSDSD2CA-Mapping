"""
Tests for BIS GQ Mapper parsers module.
"""

import pytest
import pandas as pd
import yaml
import tempfile
import os
from pathlib import Path

from src.parsers import GQParser
from src.models import GQDataItem


@pytest.fixture
def sample_gq_structure():
    """Sample GQ structure configuration."""
    return {
        'gq_codes': [
            {'code': 6, 'description': 'Total claims', 'part': 'I', 'category': 'Total'},
            {'code': 17, 'description': 'Inter-office positions', 'part': 'I', 'category': 'Inter-office'},
            {'code': 221, 'description': 'Loans to Non-banks', 'part': 'I', 'category': 'Loans', 'counterparty': 'F'}
        ]
    }


@pytest.fixture
def sample_gq_data():
    """Sample GQ data as DataFrame."""
    return pd.DataFrame({
        'Code': [6, 17, 221, 999],  # 999 is not in structure
        'Value': [1000.0, 50.0, 200.0, 100.0]
    })


@pytest.fixture
def temp_files(sample_gq_structure, sample_gq_data):
    """Create temporary files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create structure file
        structure_file = Path(tmpdir) / 'structure.yaml'
        with open(structure_file, 'w') as f:
            yaml.dump(sample_gq_structure, f)
        
        # Create GQ Excel file
        gq_file = Path(tmpdir) / 'gq_data.xlsx'
        sample_gq_data.to_excel(gq_file, index=False)
        
        # Create CSV version too
        csv_file = Path(tmpdir) / 'gq_data.csv'
        sample_gq_data.to_csv(csv_file, index=False)
        
        yield {
            'structure': str(structure_file),
            'excel': str(gq_file),
            'csv': str(csv_file),
            'tmpdir': tmpdir
        }


class TestGQParser:
    """Test cases for GQParser class."""
    
    def test_init_valid_files(self, temp_files):
        """Test parser initialization with valid files."""
        parser = GQParser(temp_files['excel'], temp_files['structure'])
        assert parser.gq_filepath.exists()
        assert parser.structure_filepath.exists()
        assert len(parser.gq_code_lookup) == 3
        assert 6 in parser.gq_code_lookup
        assert 17 in parser.gq_code_lookup
        assert 221 in parser.gq_code_lookup
    
    def test_init_missing_gq_file(self, temp_files):
        """Test parser initialization with missing GQ file."""
        with pytest.raises(FileNotFoundError):
            GQParser('nonexistent.xlsx', temp_files['structure'])
    
    def test_init_missing_structure_file(self, temp_files):
        """Test parser initialization with missing structure file."""
        with pytest.raises(FileNotFoundError):
            GQParser(temp_files['excel'], 'nonexistent.yaml')
    
    def test_parse_excel_file(self, temp_files):
        """Test parsing Excel file."""
        parser = GQParser(temp_files['excel'], temp_files['structure'])
        gq_data = parser.parse()
        
        # Should only include codes that are in structure
        assert len(gq_data) == 3
        assert gq_data[6] == 1000.0
        assert gq_data[17] == 50.0
        assert gq_data[221] == 200.0
        assert 999 not in gq_data  # Not in structure, should be excluded
    
    def test_parse_csv_file(self, temp_files):
        """Test parsing CSV file."""
        parser = GQParser(temp_files['csv'], temp_files['structure'])
        gq_data = parser.parse()
        
        assert len(gq_data) == 3
        assert gq_data[6] == 1000.0
        assert gq_data[17] == 50.0
        assert gq_data[221] == 200.0
    
    def test_get_gq_items(self, temp_files):
        """Test getting structured GQ items."""
        parser = GQParser(temp_files['excel'], temp_files['structure'])
        items = parser.get_gq_items()
        
        assert len(items) == 3
        assert all(isinstance(item, GQDataItem) for item in items)
        
        # Check specific item
        item_6 = next(item for item in items if item.code == 6)
        assert item_6.value == 1000.0
        assert item_6.description == 'Total claims'
        assert item_6.part == 'I'
        assert item_6.category == 'Total'
        
        # Check item with counterparty
        item_221 = next(item for item in items if item.code == 221)
        assert item_221.counterparty == 'F'
    
    def test_parse_unsupported_format(self, temp_files):
        """Test parsing unsupported file format."""
        # Create a file with unsupported extension
        unsupported_file = Path(temp_files['tmpdir']) / 'data.txt'
        unsupported_file.write_text('some text')
        
        parser = GQParser(str(unsupported_file), temp_files['structure'])
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse()
    
    def test_parse_with_missing_columns(self, temp_files, sample_gq_structure):
        """Test parsing file with unclear column structure."""
        # Create DataFrame with non-standard column names
        df = pd.DataFrame({
            'A': [6, 17],
            'B': [1000.0, 50.0]
        })
        
        # Create temporary file
        unclear_file = Path(temp_files['tmpdir']) / 'unclear.xlsx'
        df.to_excel(unclear_file, index=False)
        
        parser = GQParser(str(unclear_file), temp_files['structure'])
        gq_data = parser.parse()
        
        # Should still work by assuming first two columns are code and value
        assert len(gq_data) == 2
        assert gq_data[6] == 1000.0
        assert gq_data[17] == 50.0