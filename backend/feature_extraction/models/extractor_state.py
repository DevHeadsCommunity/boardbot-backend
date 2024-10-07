import operator
from typing_extensions import Annotated
from typing import Optional, TypedDict, List, Dict, Any


def usage_data_reducer(a: Dict[str, List[Any]], b: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
    result = {}
    for key in set(a.keys()).union(b.keys()):
        list_a = a.get(key, [])
        list_b = b.get(key, [])
        result[key] = list_a + list_b
    return result


def list_appender(a: List[int], b: int) -> List[int]:
    return a + [b]


class UsageData(TypedDict):
    input_tokens: int
    output_tokens: int
    time_taken: float


class ExtractorState(TypedDict):
    error: Optional[str]
    raw_data: str
    product_id: str
    extracted_features: Dict[str, Any]
    missing_features: List[str]
    low_confidence_features: List[str]
    missing_feature_counts: Annotated[List[int], list_appender]
    low_confidence_feature_counts: Annotated[List[int], list_appender]
    missing_feature_attempts: int
    low_confidence_attempts: int
    exclude_domains: Annotated[List[str], operator.add]
    usage_data: Annotated[Dict[str, List[UsageData]], usage_data_reducer]
