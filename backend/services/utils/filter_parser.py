from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from weaviate.classes.query import Filter


class FilterOperator(Enum):
    EQUAL = "eq"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN_EQUAL = "lte"
    RANGE = "range"
    IN_LIST = "in"


@dataclass
class FilterRule:
    attribute: str
    pattern: str
    unit: Optional[str] = None
    is_list: bool = False
    case_sensitive: bool = False

    def normalize_value(self, value: str) -> str:
        """Normalize value by removing unit and standardizing format"""
        if not value:
            return value
        if self.unit:
            value = value.replace(self.unit, "").strip()
        return value.upper() if not self.case_sensitive else value


class FilterNormalizer:
    def __init__(self):
        self.rules = {
            "memory": FilterRule(
                attribute="memory", pattern=r"(\d+(?:\.\d+)?)\s*GB(?:\s+(?:DDR\d|LPDDR\d))?", unit="GB", is_list=False
            ),
            "wireless": FilterRule(
                attribute="wireless",
                pattern=r"(WI-FI|BLUETOOTH|CELLULAR|GPS|ZIGBEE|LORA|NFC)",
                is_list=True,
                case_sensitive=False,
            ),
            "operating_temperature_min": FilterRule(
                attribute="operating_temperature_min", pattern=r"(-?\d+(?:\.\d+)?)", unit="°C"
            ),
            "operating_temperature_max": FilterRule(
                attribute="operating_temperature_max", pattern=r"(-?\d+(?:\.\d+)?)", unit="°C"
            ),
            "processor_tdp": FilterRule(attribute="processor_tdp", pattern=r"(\d+(?:\.\d+)?)", unit="W"),
        }

    def parse_value(self, value: str, rule: FilterRule) -> Union[str, List[str], Dict[str, Any]]:
        """Parse value based on filter rule and detect operators"""
        if not value:
            return value

        # Handle list-type attributes
        if rule.is_list:
            if isinstance(value, str):
                return [rule.normalize_value(value)]
            elif isinstance(value, list):
                return [rule.normalize_value(v) for v in value]

        # Handle operator detection
        normalized = rule.normalize_value(value)
        if isinstance(value, str):
            if value.startswith(">="):
                return {"$gte": rule.normalize_value(value[2:])}
            elif value.startswith("<="):
                return {"$lte": rule.normalize_value(value[2:])}
            elif "-" in value:
                min_val, max_val = value.split("-", 1)
                return {"$gte": rule.normalize_value(min_val), "$lte": rule.normalize_value(max_val)}

        return normalized

    def normalize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all filters based on defined rules"""
        if not filters:
            return {}

        normalized = {}
        for key, value in filters.items():
            if key not in self.rules:
                normalized[key] = value.upper() if isinstance(value, str) else value
                continue

            rule = self.rules[key]
            normalized[key] = self.parse_value(value, rule)

        return normalized


class QueryBuilder:
    def build_weaviate_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        """
        Converts dictionary filters into Weaviate Filter objects.

        Args:
            filters: Dictionary of filters with operators

        Returns:
            Weaviate Filter object or None if no filters
        """
        if not filters:
            return None

        filter_conditions = []

        for key, value in filters.items():
            if isinstance(value, dict):
                # Handle operators like $gte, $lte, etc.
                for op, val in value.items():
                    if op == "$gte":
                        filter_conditions.append(Filter.by_property(key).greater_than_equal(val))
                    elif op == "$lte":
                        filter_conditions.append(Filter.by_property(key).less_than_equal(val))
                    elif op == "$in":
                        if isinstance(val, list):
                            filter_conditions.append(Filter.by_property(key).contains_any(val))
            elif isinstance(value, list):
                # Handle list values (e.g., wireless capabilities)
                filter_conditions.append(Filter.by_property(key).contains_any(value))
            else:
                # Handle simple equality
                filter_conditions.append(Filter.by_property(key).equal(value))

        # Combine all conditions with AND
        return Filter.all_of(filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]
