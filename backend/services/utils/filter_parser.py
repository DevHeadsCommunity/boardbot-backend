from enum import Enum
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from weaviate.classes.query import Filter
import re


class ValueTypes(Enum):
    MEMORY = "memory"
    STORAGE = "storage"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    PROCESSOR_CORES = "processor_cores"
    POWER = "power"


class FeatureValues:
    # Memory and Storage sizes (in GB)
    MEMORY_STORAGE_VALUES = {
        0.1,
        0.2,
        0.5,
        1,
        1.0,
        2,
        2.0,
        4,
        4.0,
        8,
        8.0,
        16,
        16.0,
        32,
        32.0,
        64,
        64.0,
        128,
        128.0,
        256,
        256.0,
        320,
        320.0,
        512,
        512.0,
        1024,
        1024.0,
    }

    # Voltage values (in V)
    VOLTAGE_VALUES = {
        1,
        1.0,
        2,
        2.0,
        3,
        3.0,
        4,
        4.0,
        5,
        5.0,
        7,
        7.0,
        8,
        8.0,
        9,
        9.0,
        12,
        12.0,
        19,
        19.0,
        24,
        24.0,
        30,
        30.0,
        36,
        36.0,
        48,
        48.0,
    }

    # Temperature values (in °C)
    TEMPERATURE_VALUES = {
        -40,
        -40.0,
        -30,
        -30.0,
        -25,
        -25.0,
        -20,
        -20.0,
        -10,
        -10.0,
        0,
        0.0,
        5,
        5.0,
        35,
        35.0,
        40,
        40.0,
        45,
        45.0,
        50,
        50.0,
        55,
        55.0,
        60,
        60.0,
        65,
        65.0,
        70,
        70.0,
        75,
        75.0,
        80,
        80.0,
        85,
        85.0,
        90,
        90.0,
        95,
        95.0,
        100,
        100.0,
        105,
        105.0,
        125,
        125.0,
    }

    # Processor core counts
    PROCESSOR_CORES = {
        1,
        1.0,
        2,
        2.0,
        3,
        3.0,
        4,
        4.0,
        5,
        5.0,
        6,
        6.0,
        8,
        8.0,
        9,
        9.0,
        10,
        10.0,
        12,
        12.0,
        14,
        14.0,
        16,
        16.0,
        20,
        20.0,
        24,
        24.0,
        32,
        32.0,
        64,
        64.0,
        80,
        80.0,
        128,
        128.0,
    }

    # TDP power values (in W)
    POWER_VALUES = {
        1,
        1.0,
        2,
        2.0,
        5,
        5.0,
        6,
        6.0,
        7,
        7.0,
        8,
        8.0,
        9,
        9.0,
        10,
        10.0,
        12,
        12.0,
        13,
        13.0,
        15,
        15.0,
        17,
        17.0,
        19,
        19.0,
        25,
        25.0,
        28,
        28.0,
        31,
        31.0,
        35,
        35.0,
        45,
        45.0,
        65,
        65.0,
        70,
        70.0,
        77,
        77.0,
        80,
        80.0,
        95,
        95.0,
        100,
        100.0,
        105,
        105.0,
        125,
        125.0,
        160,
        160.0,
        205,
        205.0,
    }

    # Feature type mapping
    FEATURE_TYPE_MAP = {
        "memory": ValueTypes.MEMORY,
        "onboard_storage": ValueTypes.STORAGE,
        "input_voltage": ValueTypes.VOLTAGE,
        "operating_temperature_max": ValueTypes.TEMPERATURE,
        "operating_temperature_min": ValueTypes.TEMPERATURE,
        "processor_core_count": ValueTypes.PROCESSOR_CORES,
        "processor_tdp": ValueTypes.POWER,
    }

    @classmethod
    def _get_nearest_valid_values(cls, value: float, valid_set: Set[float], operator: str) -> List[float]:
        """Get nearest valid values based on operator."""
        if operator == ">=":
            return sorted([v for v in valid_set if v >= value])
        else:  # "<="
            return sorted([v for v in valid_set if v <= value])

    @classmethod
    def _format_numeric_values(cls, values: List[float]) -> List[str]:
        """Format numeric values to include both integer and float representations when applicable."""
        result = []
        for v in values:
            v_float = float(v)
            if v_float.is_integer():
                result.extend([f"{int(v_float)}", f"{v_float:.1f}"])
            else:
                result.append(f"{v_float}")
        return result

    @classmethod
    def get_valid_values(cls, feature_name: str, value: str) -> List[str]:
        """Get valid values for a given feature based on its type."""
        feature_type = cls.FEATURE_TYPE_MAP.get(feature_name)
        if not feature_type:
            return [value]

        operator = value[:2]  # '>=' or '<='
        try:
            num_value = float(value[2:])
        except ValueError:
            return [value]

        # Map feature types to their corresponding value sets
        value_set_map = {
            ValueTypes.MEMORY: cls.MEMORY_STORAGE_VALUES,
            ValueTypes.STORAGE: cls.MEMORY_STORAGE_VALUES,
            ValueTypes.VOLTAGE: cls.VOLTAGE_VALUES,
            ValueTypes.TEMPERATURE: cls.TEMPERATURE_VALUES,
            ValueTypes.PROCESSOR_CORES: cls.PROCESSOR_CORES,
            ValueTypes.POWER: cls.POWER_VALUES,
        }

        valid_set = value_set_map.get(feature_type)
        if valid_set is None:
            return [value]

        valid_values = cls._get_nearest_valid_values(num_value, valid_set, operator)
        return cls._format_numeric_values(valid_values)


class QueryBuilder:
    def __init__(self):
        # Cache for parsed values from attribute descriptions
        self._valid_values_cache: Dict[str, Dict[str, Set[Union[int, float]]]] = {}

    def build_weaviate_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        """
        Converts dictionary filters into Weaviate Filter objects with generalized handling.
        """
        if not filters:
            return None

        filter_conditions = []

        for key, value in filters.items():
            if isinstance(value, str):
                if value.startswith(">=") or value.startswith("<="):
                    # Extract unit if present
                    numeric_part, unit = self._split_value_and_unit(value[2:])
                    if numeric_part:
                        # Get possible numeric values based on field examples
                        numeric_values = self._create_numeric_values(key, f"{value[:2]}{numeric_part}")
                        if numeric_values:
                            # Add back the unit to each value if it exists
                            possible_values = [f"{v}{unit}" for v in numeric_values] if unit else numeric_values
                            filter_conditions.append(Filter.by_property(key).contains_any(possible_values))
                else:
                    # Handle string values
                    filter_conditions.append(Filter.by_property(key).contains_any([value.upper()]))
            elif isinstance(value, list):
                # For array fields
                upper_values = [v.upper() for v in value]
                filter_conditions.append(Filter.by_property(key).contains_any(upper_values))
            else:
                # For any other types of values
                filter_conditions.append(Filter.by_property(key).equal(str(value)))

        return Filter.all_of(filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]

    def _split_value_and_unit(self, value: str) -> Tuple[str, str]:
        """Split a value into its numeric part and unit."""
        # Match number (including decimals) followed by any non-numeric characters
        match = re.match(r"^([-+]?\d*\.?\d+)([A-Za-z°℃\s]*)?$", value.strip())
        if match:
            return match.group(1), (match.group(2) or "").strip()
        return value, ""

    def _get_valid_values(self, field: str) -> Dict[str, Set[Union[int, float]]]:
        """
        Extracts and categorizes valid numeric values from attribute descriptions.
        Returns a dict with 'singles' and 'ranges' for the field.
        """
        if field in self._valid_values_cache:
            return self._valid_values_cache[field]

        examples = self._get_example_values(field)
        result = {"singles": set(), "ranges": set()}

        for example in examples:
            numeric_part, _ = self._split_value_and_unit(example)

            # Handle range format (e.g., "1-4")
            if "-" in numeric_part:
                range_nums = self._extract_range_numbers(numeric_part)
                if range_nums:
                    # Add both ends of the range
                    for num in range_nums:
                        if isinstance(num, float) and num.is_integer():
                            result["ranges"].add(int(num))
                        else:
                            result["ranges"].add(num)
            else:
                # Handle single number
                single_num = self._extract_number(numeric_part)
                if single_num is not None:
                    if isinstance(single_num, float) and single_num.is_integer():
                        result["singles"].add(int(single_num))
                    else:
                        result["singles"].add(single_num)

        self._valid_values_cache[field] = result
        return result

    def _create_numeric_values(self, field: str, value: str) -> List[str]:
        """Creates list of possible numeric values based on comparison operator and field type."""
        return FeatureValues.get_valid_values(field, value)

    def _get_example_values(self, field: str) -> List[str]:
        """Extract example values from attribute descriptions."""
        from weaviate_interface.models.product import attribute_descriptions

        desc = attribute_descriptions.get(field, "")
        if not desc or "e.g.," not in desc:
            return []

        # Extract examples between parentheses
        match = re.search(r"\((.*?)\)", desc)
        if not match:
            return []

        # Split examples and clean them
        examples = [ex.strip() for ex in match.group(1).split(",")]
        return [ex for ex in examples if ex and not ex.startswith("e.g")]

    def _extract_number(self, text: str) -> Optional[Union[int, float]]:
        """Extract the first number from a text string."""
        match = re.search(r"([-+]?\d*\.?\d+)", text)
        if match:
            try:
                value = float(match.group(1))
                return int(value) if value.is_integer() else value
            except ValueError:
                return None
        return None

    def _extract_range_numbers(self, text: str) -> Optional[Tuple[Union[int, float], Union[int, float]]]:
        """Extract two numbers from a range format."""
        # First split by any non-numeric characters that might separate the range
        numeric_part, _ = self._split_value_and_unit(text)
        numbers = re.findall(r"([-+]?\d*\.?\d+)", numeric_part)
        if len(numbers) >= 2:
            try:
                values = []
                for num in numbers[:2]:
                    val = float(num)
                    values.append(int(val) if val.is_integer() else val)
                return tuple(values)  # type: ignore
            except ValueError:
                pass
        return None
