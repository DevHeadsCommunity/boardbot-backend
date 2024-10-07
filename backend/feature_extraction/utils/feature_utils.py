import logging
from typing import Dict, List, Any


logger = logging.getLogger(__name__)


def get_missing_features(extracted_features: Dict[str, Any]) -> List[str]:
    """
    Identify missing features in the extracted_features dictionary.
    A feature is considered missing if its confidence is 0 or its value is 'Not available'.
    """
    missing = []

    def recurse(features, path=""):
        for key, value in features.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                if "confidence" in value and "value" in value:
                    if value["confidence"] == 0 or (
                        isinstance(value["value"], str) and value["value"].lower() == "not available"
                    ):
                        missing.append(current_path)
                else:
                    recurse(value, current_path)

    recurse(extracted_features)
    return missing


def get_low_confidence_features(features: Dict[str, Any], confidence_threshold: float) -> List[str]:
    """
    Identify low-confidence features in the feature dictionary.
    """
    low_confidence = []

    def recurse(features, path=""):
        for key, value in features.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                if "confidence" in value and 0 < value["confidence"] < confidence_threshold:
                    low_confidence.append(current_path)
                else:
                    recurse(value, current_path)

    recurse(features)
    return low_confidence


def filter_features_by_confidence(features: Dict[str, Any], confidence_threshold: float) -> Dict[str, Any]:
    """
    Filter features based on confidence threshold.
    """
    filtered_features = {}

    def recurse(features, filtered):
        for key, value in features.items():
            if isinstance(value, dict):
                if "value" in value and "confidence" in value:
                    if value["confidence"] >= confidence_threshold:
                        filtered[key] = value["value"]
                    else:
                        filtered[key] = "Not Available"
                else:
                    filtered[key] = {}
                    recurse(value, filtered[key])
            else:
                filtered[key] = value

    recurse(features, filtered_features)
    return filtered_features


def build_missing_features_structure(
    missing_features_list: List[str],
) -> Dict[str, Any]:
    """
    Build a nested dictionary structure of missing features based on the list of missing feature paths.
    """
    logger.info(f"\n\nBuilding missing features structure for: {missing_features_list}\n\n")
    missing_features_structure = {}

    for feature_path in missing_features_list:
        keys = feature_path.split(".")
        current_level = missing_features_structure

        for key in keys[:-1]:
            if key not in current_level:
                current_level[key] = {}
            current_level = current_level[key]

        last_key = keys[-1]
        current_level[last_key] = {"value": "Not available", "confidence": 0}

    logger.info(f"\n\nMissing features structure: {missing_features_structure}\n\n")
    return missing_features_structure
