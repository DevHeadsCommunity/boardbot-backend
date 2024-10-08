from typing import TypedDict, Optional


class ConfigSchema(TypedDict, total=False):
    model_name: Optional[str]
    max_missing_feature_attempts: Optional[int]
    max_low_confidence_attempts: Optional[int]
    confidence_threshold: Optional[float]
