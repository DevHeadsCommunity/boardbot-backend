from typing import List, Dict, Any, Optional
from .base_service import BaseService
from weaviate_interface.weaviate_client import WeaviateClient
from weaviate.classes.query import Filter


class RawProductDataService(BaseService):
    def __init__(self, client: WeaviateClient):
        super().__init__(client, "RawProductData")

    def get_properties(self) -> List[str]:
        print("🧭 FUNCTION NAME: get_properties, FILE_NAME: backend/weaviate_interface/service/raw_product_data_service.py")
        return [
            "product_id",
            "raw_data",
        ]

    async def get_by_product_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        print("🧭 FUNCTION NAME: get_by_product_id, FILE_NAME: backend/weaviate_interface/service/raw_product_data_service.py")
        """
        Retrieve a RawProductData object by product ID.
        """
        filter = Filter.by_property("product_id").equal(product_id)
        results = await self.client.get_objects(
            self.class_name,
            filters=filter,
            limit=1,
        )
        return results[0] if results else None

    async def delete_by_product_id(self, product_id: str) -> None:
        print("🧭 FUNCTION NAME: delete_by_product_id, FILE_NAME: backend/weaviate_interface/service/raw_product_data_service.py")
        """
        Delete all objects associated with a product ID.
        """
        collection = self.client.get_collection(self.class_name)
        await collection.data.delete_many(where=Filter.by_property("product_id").equal(product_id))
