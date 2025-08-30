"""
Mapping engine for BIS GQ Mapper.

This module contains the core logic engine that applies mapping rules
to transform GQ data into DSD format.
"""

import yaml
import re
from typing import Dict, List
from pathlib import Path

from .models import DSDDataPoint


class MappingEngine:
    """Core logic engine for applying mapping rules."""

    def __init__(self, rules_filepath: str):
        """
        Initialize the mapping engine.

        Args:
            rules_filepath: Path to the mapping rules YAML file
        """
        self.rules_filepath = Path(rules_filepath)

        if not self.rules_filepath.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_filepath}")

        with open(self.rules_filepath, "r") as f:
            self.rules = yaml.safe_load(f)

    def _evaluate_formula(self, formula: str, gq_data: Dict[int, float]) -> float:
        """
        Safely evaluate a formula string using GQ data.

        This method parses formulas like "4+376" or "201+208+215+221+(17-517)+230"
        and evaluates them using the provided GQ data.

        Args:
            formula: Formula string to evaluate
            gq_data: Dictionary mapping GQ codes to values

        Returns:
            Computed value from the formula
        """
        try:
            # Remove whitespace
            formula = formula.replace(" ", "")

            # Find all numeric codes in the formula
            # This regex finds sequences of digits
            code_pattern = r"\b\d+\b"
            codes = re.findall(code_pattern, formula)

            # Replace each code with its value from gq_data
            # Use placeholder approach to avoid substring replacement conflicts
            evaluated_formula = formula

            # First pass: replace codes with unique placeholders
            placeholders = {}
            for i, code_str in enumerate(codes):
                placeholder = f"__PLACEHOLDER_{i}__"
                placeholders[placeholder] = gq_data.get(int(code_str), 0.0)
                pattern = r"\b" + re.escape(code_str) + r"\b"
                evaluated_formula = re.sub(pattern, placeholder, evaluated_formula)

            # Second pass: replace placeholders with actual values
            for placeholder, value in placeholders.items():
                evaluated_formula = evaluated_formula.replace(placeholder, str(value))

            # Now evaluate the mathematical expression
            # For safety, only allow basic arithmetic operations
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in evaluated_formula):
                raise ValueError(f"Formula contains invalid characters: {formula}")

            # Evaluate using eval() - this is safe since we've sanitized the input
            result = eval(evaluated_formula)
            return float(result)

        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {str(e)}")

    def generate_report(
        self, gq_data: Dict[int, float], report_type: str
    ) -> List[DSDDataPoint]:
        """
        Generate the final mapped report for either 'lbsr' or 'lbsn'.

        Args:
            gq_data: Dictionary mapping GQ codes to values
            report_type: Either 'lbsr' or 'lbsn'

        Returns:
            List of DSDDataPoint objects representing the mapped data
        """
        if report_type not in ["lbsr", "lbsn"]:
            raise ValueError(
                f"Invalid report type: {report_type}. Must be 'lbsr' or 'lbsn'"
            )

        mapped_data = []
        mapping_key = f"{report_type}_mappings"
        mapping_rules = self.rules.get(mapping_key, [])

        if not mapping_rules:
            raise ValueError(f"No mapping rules found for report type: {report_type}")

        for rule in mapping_rules:
            try:
                dsd_code = rule["dsd_code"]
                formula = rule["formula"]
                description = rule["description"]

                value = self._evaluate_formula(formula, gq_data)

                mapped_data.append(
                    DSDDataPoint(
                        code=dsd_code,
                        value=value,
                        description=description,
                        formula=formula,
                    )
                )

            except KeyError as e:
                raise ValueError(f"Missing required field in mapping rule: {e}")
            except Exception as e:
                raise ValueError(
                    f"Error processing rule for {rule.get('dsd_code', 'unknown')}: {str(e)}"
                )

        return mapped_data

    def validate_rules(self, gq_codes: List[int]) -> List[str]:
        """
        Validate that all GQ codes referenced in formulas exist in the data.

        Args:
            gq_codes: List of available GQ codes

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        gq_code_set = set(gq_codes)

        for report_type in ["lbsr", "lbsn"]:
            mapping_key = f"{report_type}_mappings"
            mapping_rules = self.rules.get(mapping_key, [])

            for rule in mapping_rules:
                formula = rule.get("formula", "")
                dsd_code = rule.get("dsd_code", "unknown")

                # Extract all numeric codes from the formula
                code_pattern = r"\b\d+\b"
                formula_codes = [
                    int(code) for code in re.findall(code_pattern, formula)
                ]

                # Check if all codes exist in the available GQ codes
                missing_codes = [
                    code for code in formula_codes if code not in gq_code_set
                ]

                if missing_codes:
                    errors.append(
                        f"Rule {dsd_code} ({report_type}): Missing GQ codes {missing_codes} in formula '{formula}'"
                    )

        return errors
