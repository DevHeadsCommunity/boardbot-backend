from typing import List, Dict, Any
from .base_service import BaseService
from weaviate.classes.query import Filter
from weaviate_interface.weaviate_client import WeaviateClient


class ProductSearchResultService(BaseService):
    def __init__(self, client: WeaviateClient):
        super().__init__(client, "ProductSearchResult")

    def get_properties(self) -> List[str]:
        print("🧭 FUNCTION NAME: get_properties, FILE_NAME: backend/weaviate_interface/service/product_search_result_service.py")
        return [
            "product_id",
            "search_query",
            "search_result",
            "data_source",
        ]

    async def get_by_product_id(self, product_id: str) -> List[Dict[str, Any]]:
        print("🧭 FUNCTION NAME: get_by_product_id, FILE_NAME: backend/weaviate_interface/service/product_search_result_service.py")

        """
        Retrieve ProductSearchResult objects by product ID.
        """
        filter = Filter.by_property("product_id").equal(product_id)
        return await self.client.get_objects(self.class_name, filters=filter)

    async def delete_by_product_id(self, product_id: str) -> None:
        print("🧭 FUNCTION NAME: delete_by_product_id, FILE_NAME: backend/weaviate_interface/service/product_search_result_service.py")

        """
        Delete all ProductSearchResult objects associated with a product ID.
        """
        collection = self.client.get_collection(self.class_name)
        await collection.data.delete_many(where=Filter.by_property("product_id").equal(product_id))
