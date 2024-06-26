from typing import Any, Dict, List
from .weaviate_client import WeaviateClient
from abc import ABC, abstractmethod


class WeaviateService(ABC):
    def __init__(self, weaviate_client: WeaviateClient):
        self.client = weaviate_client

    @property
    @abstractmethod
    def object_type(self) -> str:
        """
        Abstract property to be defined in subclasses, representing the object type
        this service will handle.
        """
        pass

    @property
    @abstractmethod
    def properties(self) -> List[str]:
        """
        Abstract property to be defined in subclasses, representing the properties
        of the object type this service will handle.
        """
        pass

    async def upsert(self, response_data: Dict[str, Any]) -> str:
        """
        Import or update an object in Weaviate, returning the object's UUID.
        """
        return await self.client.create_object(response_data, self.object_type)

    async def get(self, uuid: str) -> Dict[str, Any]:
        """
        Retrieve an object by UUID from Weaviate.
        """
        return await self.client.get_object(uuid, self.object_type)

    async def get_all(self) -> Dict[str, Any]:
        """
        Retrieve all objects of the service's object type from Weaviate.
        """
        return await self.client.query_objects(self.object_type, self.properties)

    async def update(self, uuid: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update an object in Weaviate.
        """
        return await self.client.update_object(uuid, updated_data, self.object_type)

    async def delete(self, uuid: str) -> bool:
        """
        Delete an object from Weaviate.
        """
        return await self.client.delete_object(uuid, self.object_type)
