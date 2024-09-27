import pytest
import json
from feature_extraction.utils.json_utils import parse_json_response, merge_dicts


def test_parse_json_response():
    # Test case 1: Valid JSON
    valid_json = '{"name": "John", "age": 30}'
    result = parse_json_response(valid_json)
    assert result == {"name": "John", "age": 30}

    # Test case 2: JSON with code block markers
    json_with_markers = '```json\n{"name": "Jane", "age": 25}\n```'
    result = parse_json_response(json_with_markers)
    assert result == {"name": "Jane", "age": 25}

    # Test case 3: Invalid JSON
    with pytest.raises(json.JSONDecodeError):
        parse_json_response('{"name": "Invalid,}')


def test_merge_dicts():
    # Test case 1: Merge two simple dictionaries
    dict1 = {"a": 1, "b": 2}
    dict2 = {"b": 3, "c": 4}
    result = merge_dicts(dict1, dict2)
    assert result == {"a": 1, "b": 3, "c": 4}

    # Test case 2: Merge nested dictionaries with confidence scores
    dict1 = {"person": {"name": {"value": "John", "confidence": 0.8}, "age": {"value": 30, "confidence": 0.9}}}
    dict2 = {
        "person": {
            "name": {"value": "Johnny", "confidence": 0.9},
            "occupation": {"value": "Engineer", "confidence": 0.7},
        }
    }
    result = merge_dicts(dict1, dict2)
    assert result == {
        "person": {
            "name": {"value": "Johnny", "confidence": 0.9},
            "age": {"value": 30, "confidence": 0.9},
            "occupation": {"value": "Engineer", "confidence": 0.7},
        }
    }

    # Test case 3: Merge dictionaries with non-dict values
    dict1 = {"a": 1, "b": {"x": 10, "y": 20}}
    dict2 = {"b": {"y": 30, "z": 40}, "c": 3}
    result = merge_dicts(dict1, dict2)
    assert result == {"a": 1, "b": {"x": 10, "y": 30, "z": 40}, "c": 3}
