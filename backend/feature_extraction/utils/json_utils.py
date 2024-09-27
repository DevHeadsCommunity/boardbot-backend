import json
from typing import Dict, Any


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse a JSON string response into a nested Python dictionary.
    """
    try:
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned_response)
        return parsed
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Failed to parse JSON response: {e}", e.doc, e.pos)


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two nested dictionaries recursively, updating values based on confidence scores.
    """
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(value, dict):
                if "confidence" in value and "confidence" in dict1[key]:
                    if value["confidence"] > dict1[key]["confidence"]:
                        dict1[key] = value
                else:
                    merge_dicts(dict1[key], value)
            else:
                dict1[key] = value
        else:
            dict1[key] = value
    return dict1
