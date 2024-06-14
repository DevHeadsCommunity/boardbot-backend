from typing import Any, Dict, List
from .weaviate_client import WeaviateClient
from .weaviate_service import WeaviateService


class ProductService(WeaviateService):

    def __init__(
        self,
        weaviate_client: WeaviateClient,
    ):
        super().__init__(weaviate_client)

    @property
    def object_type(self) -> str:
        return "Product"

    @property
    def properties(self) -> List[str]:
        return ["name", "description", "price", "feature", "specification", "location", "summary"]

    async def upsert(self, response_data: Dict[str, Any]) -> str:
        return await self.client.create_object(response_data, self.object_type)

    async def batch_upsert(self, response_data: List[Dict[str, Any]]) -> bool:
        return await self.client.batch_create_objects(response_data, self.object_type)

    async def get(self, uuid: str) -> Dict[str, Any]:
        return await self.client.get_object(uuid, self.object_type)

    async def get_all(self) -> Dict[str, Any]:
        return await self.client.query_objects(self.object_type, self.properties)

    async def update(self, uuid: str, updated_data: Dict[str, Any]) -> bool:
        return await self.client.update_object(uuid, updated_data, self.object_type)

    async def delete(self, uuid: str) -> bool:
        return await self.client.delete_object(uuid, self.object_type)

    async def search(self, query: str, fields: List[str], limit: int = 3) -> List[Dict[str, Any]]:
        return await self.client.search(self.object_type, query, fields, limit)
