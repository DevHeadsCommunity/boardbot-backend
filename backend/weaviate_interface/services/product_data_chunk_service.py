from typing import List, Dict, Any, Optional
from .base_service import BaseService
from weaviate.classes.query import Filter
from weaviate_interface.weaviate_client import WeaviateClient


class ProductDataChunkService(BaseService):
    def __init__(self, client: WeaviateClient):
        super().__init__(client, "ProductDataChunk")

    def get_properties(self) -> List[str]:
        return [
            "product_id",
            "chunk_text",
            "source_type",
            "source_id",
        ]

    async def create_chunks(self, chunks: List[str], product_id: str, source_type: str, source_id: str) -> List[str]:
        chunk_objects = [
            {
                "chunk_text": chunk,
                "product_id": product_id,
                "source_type": source_type,
                "source_id": source_id,
            }
            for chunk in chunks
        ]
        return await self.batch_create_objects(chunk_objects)

    async def get_by_product_id(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve ProductDataChunk objects by product ID.
        """
        filter = Filter.by_property("product_id").equal(product_id)
        return await self.client.get_objects(self.class_name, filters=filter)

    async def delete_by_product_id(self, product_id: str) -> None:
        """
        Delete all objects associated with a product ID.
        """
        collection = self.client.get_collection(self.class_name)
        await collection.data.delete_many(where=Filter.by_property("product_id").equal(product_id))

    async def semantic_search(
        self, query: str, product_id: str, limit: int = 5, source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform a semantic search on ProductDataChunk objects.
        """

        filters = [Filter.by_property("product_id").equal(product_id)]

        if source_type:
            filters.append(Filter.by_property("source_type").equal(source_type))

        combined_filter = Filter.all_of(filters) if len(filters) > 1 else filters[0]

        return await self.search(
            query_text=query,
            filters=combined_filter,
            limit=limit,
            return_properties=["chunk_text", "source_type"],
        )
