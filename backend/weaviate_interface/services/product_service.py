from typing import List
from weaviate_interface.services.base_service import BaseService
from weaviate_interface.weaviate_client import WeaviateClient


class ProductService(BaseService):
    """
    Service for interacting with Product objects in Weaviate.
    """

    def __init__(self, client: WeaviateClient):
        super().__init__(client, "Product")

    def get_properties(self) -> List[str]:
        return [
            "_additional{id}",
            "product_id",
            "name",
            "manufacturer",
            "form_factor",
            "evaluation_or_commercialization",
            "processor_architecture",
            "processor_core_count",
            "processor_manufacturer",
            "processor_tdp",
            "memory",
            "onboard_storage",
            "input_voltage",
            "io_count",
            "wireless",
            "operating_system_bsp",
            "operating_temperature_max",
            "operating_temperature_min",
            "certifications",
            "price",
            "stock_availability",
            "lead_time",
            "short_summary",
            "full_summary",
            "full_product_description",
            "target_applications",
            "duplicate_ids",
        ]
