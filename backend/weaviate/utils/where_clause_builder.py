import json
from typing import Any, Dict


class ClauseBuilder:
    def build(self) -> str:
        raise NotImplementedError


class WhereClauseBuilder(ClauseBuilder):
    def __init__(self, where_filter: Dict[str, Any]):
        self.where_filter = where_filter

    def build(self) -> str:
        if not self.where_filter:
            return ""
        clauses = [self._handle_condition(key, value) for key, value in self.where_filter.items()]
        return f"where: {{ {' '.join(clauses)} }}"

    def _handle_condition(self, key: str, value: Any) -> str:
        if key == "path":
            return self._format_path_condition(value)
        elif key in ["operator", "valueString", "valueInt", "valueFloat", "valueBoolean"]:
            return self._format_direct_condition(key, value)
        elif isinstance(value, tuple):
            return self._format_tuple_condition(key, value)
        elif isinstance(value, dict):
            return self._format_dict_condition(key, value)
        elif isinstance(value, str):  # Add this condition
            return f'path: ["{key}"], operator: Equal, valueString: "{value}"'
        else:
            raise ValueError(f"Unsupported where filter format for key '{key}': {value}")

    def _format_direct_condition(self, key: str, value: Any) -> str:
        if key == "operator":
            return f"{key}: {value}"  # Enum values should not be enclosed in quotes
        elif isinstance(value, str):
            return f'{key}: "{value}"'  # String values should be enclosed in quotes
        return f"{key}: {value}"

    def _format_path_condition(self, value: list) -> str:
        # Updated to handle nested paths
        if all(isinstance(item, str) for item in value):
            path_str = ", ".join([f'"{item}"' for item in value])
            return f"path: [{path_str}]"
        elif all(isinstance(item, list) for item in value):
            # Handling nested paths
            nested_path_clauses = []
            for path in value:
                nested_path_str = ", ".join([f'"{item}"' for item in path])
                nested_path_clauses.append(f"[{nested_path_str}]")
            return "path: " + " ".join(nested_path_clauses)
        else:
            raise ValueError("Invalid path format. Path should be a list of strings or a list of list of strings.")

    def _format_tuple_condition(self, key: str, value: tuple) -> str:
        operator, val = value
        if operator not in ["Equal", "NotEqual", "GreaterThan", "LessThan"]:
            raise ValueError(f"Unsupported operator in tuple: {operator}")
        return f'path: ["{key}"], operator: {operator}, valueString: "{val}"'

    def _format_dict_condition(self, key: str, value: dict) -> str:
        valid_keys = {"path", "operator", "valueString", "valueInt", "valueFloat", "valueBoolean"}
        if not valid_keys.issuperset(value.keys()):
            raise ValueError(f"Unsupported keys in dict condition: {value.keys()}")

        parts = [self._format_dict_part(sub_key, sub_val) for sub_key, sub_val in value.items()]
        return f"{key}: {{ {' '.join(parts)} }}"

    def _format_dict_part(self, key: str, value: Any) -> str:
        if key == "operator":
            return f"operator: {value}"
        elif key in ["valueString", "valueInt", "valueFloat", "valueBoolean"]:
            return f"{key}: {json.dumps(value)}"
        else:
            raise ValueError(f"Unsupported key in dict part: {key}")


class OffsetClauseBuilder(ClauseBuilder):
    def __init__(self, offset: int):
        self.offset = offset

    def build(self) -> str:
        return f"offset: {self.offset}" if self.offset is not None else ""
