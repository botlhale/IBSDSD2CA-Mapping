#!/usr/bin/env python3
"""
BIS GQ Mapper - Command Line Interface

From National Granularity to Global Standards

A configurable, testable, and auditable Python command-line utility that converts 
Canadian regulatory return GM_GQ data to Bank for International Settlements (BIS) 
Locational Banking Statistics (LBS) Data Structure Definition (DSD) format.

Automates historically manual, error-prone mapping with validation, extensibility, 
and safe formula evaluation to reduce operational risk and accelerate reporting cycles.
"""

import argparse
import sys
import csv
from pathlib import Path
from typing import List

from src.parsers import GQParser
from src.engine import MappingEngine
from src.models import DSDDataPoint


def save_to_csv(data: List[DSDDataPoint], output_path: str) -> None:
    """Save mapped data to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['dsd_code', 'value', 'description', 'formula']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in data:
            writer.writerow({
                'dsd_code': item.code,
                'value': item.value,
                'description': item.description,
                'formula': item.formula
            })


def validate_inputs(args) -> None:
    """Validate command line arguments."""
    if not Path(args.gq_file).exists():
        raise FileNotFoundError(f"GQ file not found: {args.gq_file}")
    
    if args.report_type not in ['lbsr', 'lbsn']:
        raise ValueError(f"Invalid report type: {args.report_type}. Must be 'lbsr' or 'lbsn'")
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="BIS GQ Mapper - From National Granularity to Global Standards. A configurable, testable, and auditable bridge converting Canadian GM_GQ regulatory data to BIS LBS DSD format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate LBSR report
  python main.py --gq-file data/input/GM_GQ_2022.xlsx --report-type lbsr --output data/output/lbsr_report.csv
  
  # Generate LBSN report
  python main.py --gq-file data/input/gq_filtered_US.xlsx --report-type lbsn --output data/output/lbsn_report.csv
        """
    )
    
    parser.add_argument(
        '--gq-file',
        required=True,
        help='Path to the Canadian GM_GQ regulatory return file (Excel or CSV format)'
    )
    
    parser.add_argument(
        '--report-type',
        required=True,
        choices=['lbsr', 'lbsn'],
        help='BIS LBS report type: lbsr (residency-based) or lbsn (nationality-based)'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Output path for the BIS LBS DSD compliant CSV report'
    )
    
    parser.add_argument(
        '--gq-structure',
        default='knowledge_base/gq_structure.yaml',
        help='Path to GQ structure definition file (default: knowledge_base/gq_structure.yaml)'
    )
    
    parser.add_argument(
        '--mapping-rules',
        default='knowledge_base/lbs_mapping_rules.yaml',
        help='Path to mapping rules file (default: knowledge_base/lbs_mapping_rules.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate mapping rules and data integrity without generating output (regulatory compliance check)'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate inputs
        validate_inputs(args)
        
        if args.verbose:
            print(f"Initializing BIS GQ Mapper...")
            print(f"GQ File: {args.gq_file}")
            print(f"Report Type: {args.report_type}")
            print(f"Output: {args.output}")
        
        # Initialize components
        parser_obj = GQParser(args.gq_file, args.gq_structure)
        engine = MappingEngine(args.mapping_rules)
        
        if args.verbose:
            print("Parsing GQ data...")
        
        # Parse GQ data
        gq_data = parser_obj.parse()
        
        if args.verbose:
            print(f"Parsed {len(gq_data)} GQ data points")
        
        # Validate mapping rules if requested
        if args.validate_only:
            errors = engine.validate_rules(list(gq_data.keys()))
            if errors:
                print("Validation errors found:")
                for error in errors:
                    print(f"  - {error}")
                return 1
            else:
                print("All mapping rules validated successfully!")
                return 0
        
        # Validate rules first
        errors = engine.validate_rules(list(gq_data.keys()))
        if errors:
            print("Warning: Validation errors found in mapping rules:")
            for error in errors:
                print(f"  - {error}")
            print("Proceeding with available data...")
        
        if args.verbose:
            print(f"Generating {args.report_type.upper()} report...")
        
        # Generate mapped report
        mapped_data = engine.generate_report(gq_data, args.report_type)
        
        if args.verbose:
            print(f"Generated {len(mapped_data)} mapped data points")
        
        # Save to CSV
        save_to_csv(mapped_data, args.output)
        
        print(f"Successfully generated {args.report_type.upper()} report: {args.output}")
        
        if args.verbose:
            print("\nSummary:")
            total_value = sum(item.value for item in mapped_data)
            print(f"  Total mapped value: {total_value:,.2f}")
            print(f"  Number of DSD codes: {len(mapped_data)}")
            
            print("\nTop 5 values:")
            sorted_data = sorted(mapped_data, key=lambda x: abs(x.value), reverse=True)
            for item in sorted_data[:5]:
                print(f"  {item.code}: {item.value:,.2f} - {item.description}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())