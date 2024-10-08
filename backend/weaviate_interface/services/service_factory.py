from typing import Dict, Type
from .base_service import BaseService
from .route_service import RouteService
from .product_service import ProductService
from .raw_product_data_service import RawProductDataService
from .product_data_chunk_service import ProductDataChunkService
from .product_search_result_service import ProductSearchResultService
from weaviate_interface.weaviate_client import WeaviateClient


class ServiceFactory:
    """
    Factory class for creating service instances.
    """

    _services: Dict[str, Type[BaseService]] = {
        "Route": RouteService,
        "Product": ProductService,
        "RawProductData": RawProductDataService,
        "ProductSearchResult": ProductSearchResultService,
        "ProductDataChunk": ProductDataChunkService,
    }

    @classmethod
    def register_service(cls, class_name: str, service_class: Type[BaseService]):
        """
        Registers a new service class.
        """
        cls._services[class_name] = service_class

    @classmethod
    def get_service(cls, class_name: str, client: WeaviateClient) -> BaseService:
        """
        Returns an instance of the appropriate service class for the given class name.
        """
        service_class = cls._services.get(class_name)
        if not service_class:
            raise ValueError(f"No service registered for class '{class_name}'")
        return service_class(client)
