# BIS GQ Mapper (bis-gq-mapper)

A Python utility to automate the mapping of the Canadian regulatory return GM_GQ to the Bank for International Settlements (BIS) Locational Banking Statistics (LBS) Data Structure Definition (DSD).

## Purpose

This tool translates the granular data points from the quarterly GQ return into the aggregated format required for BIS LBS Residency (LBSR) and LBS Nationality (LBSN) reporting. It is designed to be maintainable by subject matter experts with minimal code changes.

## Key Features

- **Automated Mapping**: Converts GQ return data to BIS LBS DSD format using configurable rules
- **Dual Report Types**: Supports both LBSR (residency-based) and LBSN (nationality-based) reporting
- **Configuration-Driven**: Mapping rules and GQ structure definitions are externalized in YAML files
- **Validation**: Built-in validation of mapping rules and data integrity
- **Extensible**: Easy to update for new GQ codes or mapping requirements
- **Robust**: Handles missing data gracefully and provides detailed error reporting

## Project Structure

```
bis-gq-mapper/
├── data/
│   ├── input/              # Input GQ files (Excel/CSV)
│   └── output/             # Generated output reports
├── knowledge_base/
│   ├── gq_structure.yaml   # GQ return structure definition
│   └── lbs_mapping_rules.yaml  # Mapping formulas and rules
├── src/
│   ├── __init__.py
│   ├── models.py           # Data models (GQDataItem, DSDDataPoint)
│   ├── parsers.py          # GQ file parsers
│   └── engine.py           # Core mapping engine
├── tests/
│   ├── test_models.py
│   ├── test_parsers.py
│   └── test_engine.py
├── main.py                 # Command-line interface
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd IBSDSD2CA-Mapping
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python main.py --help
   ```

## Usage

The mapping process is run from the command line using `main.py`.

### LBS Residency (LBSR) Reporting

Generate a residency-based report:

```bash
python main.py \
    --gq-file data/input/GM_GQ_2022.xlsx \
    --report-type lbsr \
    --output data/output/lbsr_mapped_report.csv
```

### LBS Nationality (LBSN) Reporting

LBSN reporting requires the main GQ file to be pre-filtered for a specific nationality group:

```bash
python main.py \
    --gq-file data/input/gq_filtered_for_US_banks.xlsx \
    --report-type lbsn \
    --output data/output/lbsn_US_mapped_report.csv
```

### Advanced Usage

**Verbose output for debugging:**
```bash
python main.py \
    --gq-file data/input/GM_GQ_2022.xlsx \
    --report-type lbsr \
    --output data/output/lbsr_report.csv \
    --verbose
```

**Validate mapping rules without generating output:**
```bash
python main.py \
    --gq-file data/input/GM_GQ_2022.xlsx \
    --report-type lbsr \
    --output /dev/null \
    --validate-only
```

**Use custom configuration files:**
```bash
python main.py \
    --gq-file data/input/GM_GQ_2022.xlsx \
    --report-type lbsr \
    --output data/output/lbsr_report.csv \
    --gq-structure custom/gq_structure.yaml \
    --mapping-rules custom/mapping_rules.yaml
```

## Configuration Files

### GQ Structure Definition (`knowledge_base/gq_structure.yaml`)

Defines the structure and meaning of GQ return codes. Example:

```yaml
gq_codes:
  - code: 6
    description: "Total claims (Immediate risk basis)"
    part: I
    category: Total
  - code: 17
    description: "Total Inter-office positions (Asset)"
    part: I
    category: Inter-office
```

### Mapping Rules (`knowledge_base/lbs_mapping_rules.yaml`)

Defines the formulas for converting GQ codes to DSD codes. Example:

```yaml
lbsr_mappings:
  - dsd_code: "CAF"
    description: "Claims, All Instruments, on Non-bank Fin. Inst."
    formula: "201+208+215+221+(17-517)+230"
  - dsd_code: "CGB"
    description: "Claims, Loans & Deposits, Banks (Total)"
    formula: "4+376"
```

## Adding New Mappings

To add new mapping rules or update existing ones:

1. **For new GQ codes**: Update `knowledge_base/gq_structure.yaml`
2. **For new mapping formulas**: Update `knowledge_base/lbs_mapping_rules.yaml`
3. **Test your changes**: Run validation with `--validate-only`

No code changes are required for most mapping updates!

## Testing

Run the test suite to ensure everything works correctly:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_engine.py
```

## Input File Format

### Supported File Types
- Excel files (`.xlsx`)
- CSV files (`.csv`)

### Expected Structure
The GQ input file should contain at minimum:
- A column with GQ codes (numeric)
- A column with corresponding values (numeric)

The parser will automatically detect columns containing "code" and "value"/"amount"/"balance" in their names, or use the first two columns as fallback.

## Output Format

Generated reports are CSV files with the following columns:
- `dsd_code`: The BIS DSD code
- `value`: The calculated value
- `description`: Human-readable description
- `formula`: The formula used for calculation

## Error Handling

The application handles various error conditions gracefully:

- **Missing GQ codes**: Default to 0 in calculations
- **Invalid formulas**: Clear error messages with formula details
- **File format issues**: Automatic detection and fallback handling
- **Configuration errors**: Validation with detailed error reporting

## Troubleshooting

### Common Issues

1. **"GQ file not found"**
   - Check the file path is correct
   - Ensure the file exists and is readable

2. **"Validation errors found"**
   - Review the error messages for missing GQ codes
   - Update GQ structure file or input data as needed

3. **"Unable to identify code and value columns"**
   - Check that your GQ file has appropriate column headers
   - Ensure the file contains numeric data

4. **"Error evaluating formula"**
   - Verify formula syntax in mapping rules
   - Check for invalid characters or malformed expressions

### Getting Help

1. Run with `--verbose` flag for detailed output
2. Use `--validate-only` to check configuration without processing
3. Check the test files for examples of expected data formats

## Architecture

### Design Principles

1. **Separation of Concerns**: Mapping logic is separate from execution code
2. **Configuration-Driven**: Business rules are externalized in YAML files
3. **Type Safety**: Strong typing with dataclasses and type hints
4. **Testability**: Comprehensive test suite with >90% coverage
5. **Maintainability**: Clear structure and documentation

### Core Components

- **Models** (`src/models.py`): Data structures for type safety
- **Parsers** (`src/parsers.py`): Input file processing and validation
- **Engine** (`src/engine.py`): Core mapping logic and formula evaluation
- **CLI** (`main.py`): Command-line interface and user interaction

### Security Features

- **Safe Formula Evaluation**: Sanitized expression evaluation prevents code injection
- **Input Validation**: Comprehensive validation of files and configuration
- **Error Boundaries**: Graceful handling of invalid data

## Contributing

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest`
4. Follow PEP 8 style guidelines

### Adding Features

1. Update the appropriate module in `src/`
2. Add corresponding tests in `tests/`
3. Update configuration files if needed
4. Update documentation

## License

[Add your license information here]

## Version History

- **v1.0.0**: Initial implementation with LBSR and LBSN support
  - Core mapping engine
  - Configuration-driven architecture
  - Comprehensive test suite
  - CLI interface

## Support

For questions or issues, please:
1. Check this README for troubleshooting tips
2. Review the test files for usage examples
3. [Add your support contact information]