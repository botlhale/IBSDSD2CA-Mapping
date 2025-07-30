"""
Parsers for BIS GQ Mapper.

This module contains parsers for reading and structuring input data from
GQ returns and configuration files.
"""

import pandas as pd
import yaml
from typing import Dict, List, Optional
from pathlib import Path

from .models import GQDataItem


class GQParser:
    """Parser for GQ Excel files with structure validation."""
    
    def __init__(self, gq_filepath: str, structure_filepath: str):
        """
        Initialize the GQ parser.
        
        Args:
            gq_filepath: Path to the GQ Excel file
            structure_filepath: Path to the GQ structure YAML file
        """
        self.gq_filepath = Path(gq_filepath)
        self.structure_filepath = Path(structure_filepath)
        
        # Validate file existence
        if not self.gq_filepath.exists():
            raise FileNotFoundError(f"GQ file not found: {gq_filepath}")
        if not self.structure_filepath.exists():
            raise FileNotFoundError(f"Structure file not found: {structure_filepath}")
            
        # Load structure configuration
        with open(self.structure_filepath, 'r') as f:
            self.structure = yaml.safe_load(f)
        
        # Create lookup for GQ codes
        self.gq_code_lookup = {
            item['code']: item for item in self.structure.get('gq_codes', [])
        }
    
    def parse(self) -> Dict[int, float]:
        """
        Parse the GQ Excel file and extract numeric codes with their values.
        
        Returns:
            Dictionary mapping GQ codes to their values
        """
        try:
            # Read the Excel file - handle different possible formats
            if self.gq_filepath.suffix.lower() == '.xlsx':
                df = pd.read_excel(self.gq_filepath)
            elif self.gq_filepath.suffix.lower() == '.csv':
                df = pd.read_csv(self.gq_filepath)
            else:
                raise ValueError(f"Unsupported file format: {self.gq_filepath.suffix}")
            
            gq_data = {}
            
            # Look for code and value columns - try common patterns
            code_columns = [col for col in df.columns if 'code' in col.lower()]
            value_columns = [col for col in df.columns if any(term in col.lower() 
                           for term in ['value', 'amount', 'balance', 'total'])]
            
            if not code_columns or not value_columns:
                # Fallback: assume first two columns are code and value
                if len(df.columns) >= 2:
                    code_col = df.columns[0]
                    value_col = df.columns[1]
                else:
                    raise ValueError("Unable to identify code and value columns")
            else:
                code_col = code_columns[0]
                value_col = value_columns[0]
            
            # Extract data, handling potential data quality issues
            for _, row in df.iterrows():
                try:
                    code = int(row[code_col])
                    value = float(row[value_col]) if pd.notna(row[value_col]) else 0.0
                    
                    # Only include codes that are in our structure definition
                    if code in self.gq_code_lookup:
                        gq_data[code] = value
                        
                except (ValueError, TypeError):
                    # Skip rows with invalid data
                    continue
            
            return gq_data
            
        except Exception as e:
            raise ValueError(f"Error parsing GQ file {self.gq_filepath}: {str(e)}")
    
    def get_gq_items(self) -> List[GQDataItem]:
        """
        Parse and return structured GQ data items with metadata.
        
        Returns:
            List of GQDataItem objects with full metadata
        """
        gq_data = self.parse()
        items = []
        
        for code, value in gq_data.items():
            if code in self.gq_code_lookup:
                structure_info = self.gq_code_lookup[code]
                item = GQDataItem(
                    code=code,
                    value=value,
                    description=structure_info.get('description', ''),
                    part=structure_info.get('part'),
                    category=structure_info.get('category'),
                    counterparty=structure_info.get('counterparty')
                )
                items.append(item)
        
        return items