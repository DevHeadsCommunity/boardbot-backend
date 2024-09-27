from typing import Dict, Any, List

MAX_QUERY_LENGTH = 400


def construct_search_query(features: Dict[str, Any], target_features: List[str]) -> str:
    """
    Constructs a search query based on existing features and target features.
    """
    name = features.get("name", {}).get("value", "")
    manufacturer = features.get("manufacturer", {}).get("value", "")
    form_factor = features.get("form_factor", {}).get("value", "")

    base_query = f"{name} by {manufacturer}"
    if form_factor and form_factor.lower() != "not available":
        base_query += f", form factor {form_factor}"

    target_features_str = ", ".join([tf.replace(".", " ") for tf in target_features])
    query = f"{base_query}. Find product specs: {target_features_str}."

    if len(query) > MAX_QUERY_LENGTH:
        query = query[: MAX_QUERY_LENGTH - 3] + "..."

    return query.strip()
