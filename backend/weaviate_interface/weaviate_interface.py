from weaviate_interface.schema import SCHEMA
from weaviate_interface.services.base_service import BaseService
from weaviate_interface.schema_manager import SchemaManager
from weaviate_interface.weaviate_client import WeaviateClient
from weaviate_interface.services.service_factory import ServiceFactory


class WeaviateInterface:
    """
    Provides a unified interface to interact with Weaviate services.
    """

    def __init__(self, url: str, openai_key: str):
        self.client = WeaviateClient(url, openai_key)
        self.schema = SchemaManager(self.client, SCHEMA)
        self.product_service = self.get_service("Product")
        self.route_service = self.get_service("Route")
        self.raw_product_data_service = self.get_service("RawProductData")
        self.product_data_chunk_service = self.get_service("ProductDataChunk")
        self.product_search_result_service = self.get_service("ProductSearchResult")

    def get_service(self, class_name: str) -> BaseService:
        """
        Returns the appropriate service for the given class name.
        """
        return ServiceFactory.get_service(class_name, self.client)
