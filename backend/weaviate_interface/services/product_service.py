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
            "name",
            "ids",
            "manufacturer",
            "form_factor",
            "processor",
            "core_count",
            "processor_tdp",
            "memory",
            "io",
            "operating_system",
            "environmentals",
            "certifications",
            "short_summary",
            "full_summary",
            "full_product_description",
        ]
