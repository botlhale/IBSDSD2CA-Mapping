"""
Tests for BIS GQ Mapper engine module.
"""

import pytest
import yaml
import tempfile
from pathlib import Path

from src.engine import MappingEngine
from src.models import DSDDataPoint


@pytest.fixture
def sample_mapping_rules():
    """Sample mapping rules configuration."""
    return {
        'lbsr_mappings': [
            {
                'dsd_code': 'CAF',
                'description': 'Claims, All Instruments, on Non-bank Fin. Inst.',
                'formula': '201+208+215+221+(17-517)+230'
            },
            {
                'dsd_code': 'CGB',
                'description': 'Claims, Loans & Deposits, Banks (Total)',
                'formula': '4+376'
            }
        ],
        'lbsn_mappings': [
            {
                'dsd_code': 'CAA',
                'description': 'Claims, All Instruments, All Sectors',
                'formula': '6+17+(228+229+230)'
            }
        ]
    }


@pytest.fixture
def sample_gq_data():
    """Sample GQ data for testing."""
    return {
        4: 100.0,
        6: 1000.0,
        17: 50.0,
        201: 200.0,
        208: 150.0,
        215: 75.0,
        221: 300.0,
        228: 25.0,
        229: 35.0,
        230: 45.0,
        376: 250.0,
        517: 20.0
    }


@pytest.fixture
def temp_rules_file(sample_mapping_rules):
    """Create temporary rules file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = Path(tmpdir) / 'rules.yaml'
        with open(rules_file, 'w') as f:
            yaml.dump(sample_mapping_rules, f)
        yield str(rules_file)


class TestMappingEngine:
    """Test cases for MappingEngine class."""
    
    def test_init_valid_file(self, temp_rules_file):
        """Test engine initialization with valid rules file."""
        engine = MappingEngine(temp_rules_file)
        assert 'lbsr_mappings' in engine.rules
        assert 'lbsn_mappings' in engine.rules
        assert len(engine.rules['lbsr_mappings']) == 2
        assert len(engine.rules['lbsn_mappings']) == 1
    
    def test_init_missing_file(self):
        """Test engine initialization with missing rules file."""
        with pytest.raises(FileNotFoundError):
            MappingEngine('nonexistent.yaml')
    
    def test_evaluate_formula_simple(self, temp_rules_file, sample_gq_data):
        """Test simple formula evaluation."""
        engine = MappingEngine(temp_rules_file)
        
        # Test simple addition
        result = engine._evaluate_formula('4+376', sample_gq_data)
        assert result == 350.0  # 100 + 250
        
        # Test subtraction
        result = engine._evaluate_formula('17-517', sample_gq_data)
        assert result == 30.0  # 50 - 20
    
    def test_evaluate_formula_complex(self, temp_rules_file, sample_gq_data):
        """Test complex formula evaluation."""
        engine = MappingEngine(temp_rules_file)
        
        # Test complex formula with parentheses
        result = engine._evaluate_formula('201+208+215+221+(17-517)+230', sample_gq_data)
        expected = 200 + 150 + 75 + 300 + (50 - 20) + 45
        assert result == expected
        
        # Test formula with multiple parentheses
        result = engine._evaluate_formula('6+17+(228+229+230)', sample_gq_data)
        expected = 1000 + 50 + (25 + 35 + 45)
        assert result == expected
    
    def test_evaluate_formula_missing_codes(self, temp_rules_file):
        """Test formula evaluation with missing GQ codes."""
        engine = MappingEngine(temp_rules_file)
        
        # Codes 999 and 888 don't exist, should default to 0
        result = engine._evaluate_formula('999+888+4', {4: 100.0})
        assert result == 100.0
    
    def test_evaluate_formula_invalid(self, temp_rules_file, sample_gq_data):
        """Test invalid formula evaluation."""
        engine = MappingEngine(temp_rules_file)
        
        # Test invalid characters
        with pytest.raises(ValueError):
            engine._evaluate_formula('4+376; import os', sample_gq_data)
        
        # Test truly malformed expression
        with pytest.raises(ValueError):
            engine._evaluate_formula('4+', sample_gq_data)
    
    def test_generate_lbsr_report(self, temp_rules_file, sample_gq_data):
        """Test LBSR report generation."""
        engine = MappingEngine(temp_rules_file)
        mapped_data = engine.generate_report(sample_gq_data, 'lbsr')
        
        assert len(mapped_data) == 2
        assert all(isinstance(item, DSDDataPoint) for item in mapped_data)
        
        # Check specific mappings
        caf_item = next(item for item in mapped_data if item.code == 'CAF')
        assert caf_item.description == 'Claims, All Instruments, on Non-bank Fin. Inst.'
        expected_caf = 200 + 150 + 75 + 300 + (50 - 20) + 45  # 800
        assert caf_item.value == expected_caf
        
        cgb_item = next(item for item in mapped_data if item.code == 'CGB')
        assert cgb_item.value == 350.0  # 100 + 250
    
    def test_generate_lbsn_report(self, temp_rules_file, sample_gq_data):
        """Test LBSN report generation."""
        engine = MappingEngine(temp_rules_file)
        mapped_data = engine.generate_report(sample_gq_data, 'lbsn')
        
        assert len(mapped_data) == 1
        
        caa_item = mapped_data[0]
        assert caa_item.code == 'CAA'
        expected_caa = 1000 + 50 + (25 + 35 + 45)  # 1155
        assert caa_item.value == expected_caa
    
    def test_generate_report_invalid_type(self, temp_rules_file, sample_gq_data):
        """Test report generation with invalid report type."""
        engine = MappingEngine(temp_rules_file)
        
        with pytest.raises(ValueError, match="Invalid report type"):
            engine.generate_report(sample_gq_data, 'invalid')
    
    def test_validate_rules_valid(self, temp_rules_file):
        """Test rule validation with valid codes."""
        engine = MappingEngine(temp_rules_file)
        
        # All codes used in formulas exist
        available_codes = [4, 6, 17, 201, 208, 215, 221, 228, 229, 230, 376, 517]
        errors = engine.validate_rules(available_codes)
        
        assert len(errors) == 0
    
    def test_validate_rules_missing_codes(self, temp_rules_file):
        """Test rule validation with missing codes."""
        engine = MappingEngine(temp_rules_file)
        
        # Only provide subset of required codes
        available_codes = [4, 6, 17, 376]
        errors = engine.validate_rules(available_codes)
        
        assert len(errors) > 0
        assert any('CAF' in error for error in errors)  # CAF uses missing codes
    
    def test_generate_report_with_formula_errors(self, temp_rules_file):
        """Test report generation handling formula errors gracefully."""
        engine = MappingEngine(temp_rules_file)
        
        # Provide incomplete data that might cause issues
        incomplete_data = {4: 100.0}  # Missing most codes
        
        # Should still work, missing codes default to 0
        mapped_data = engine.generate_report(incomplete_data, 'lbsr')
        assert len(mapped_data) == 2
        
        # CAF should be calculated with missing codes as 0
        caf_item = next(item for item in mapped_data if item.code == 'CAF')
        assert caf_item.value == 0.0  # All missing codes = 0
        
        # CGB should work
        cgb_item = next(item for item in mapped_data if item.code == 'CGB')
        assert cgb_item.value == 100.0  # 100 + 0 (376 missing)


class TestFormulaEvaluation:
    """Additional tests for formula evaluation edge cases."""
    
    def test_division_and_multiplication(self, temp_rules_file):
        """Test division and multiplication in formulas."""
        engine = MappingEngine(temp_rules_file)
        data = {10: 100.0, 5: 20.0, 2: 2.0}
        
        # Test division
        result = engine._evaluate_formula('10/5', data)
        assert result == 5.0
        
        # Test multiplication
        result = engine._evaluate_formula('5*2', data)
        assert result == 40.0
        
        # Test complex expression
        result = engine._evaluate_formula('(10+5)*2', data)
        assert result == 240.0  # (100+20)*2
    
    def test_decimal_handling(self, temp_rules_file):
        """Test handling of decimal values."""
        engine = MappingEngine(temp_rules_file)
        data = {1: 1.5, 2: 2.7}
        
        result = engine._evaluate_formula('1+2', data)
        assert result == 4.2
    
    def test_whitespace_handling(self, temp_rules_file):
        """Test formula with various whitespace."""
        engine = MappingEngine(temp_rules_file)
        data = {1: 10.0, 2: 20.0}
        
        # All these should give same result
        formulas = ['1+2', '1 + 2', ' 1  +  2 ', '1+  2']
        
        for formula in formulas:
            result = engine._evaluate_formula(formula, data)
            assert result == 30.0