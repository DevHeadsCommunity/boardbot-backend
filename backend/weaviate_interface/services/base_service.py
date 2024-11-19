import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from weaviate.classes.query import Filter, Move, QueryReference, Sort
from weaviate_interface.weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class BaseService(ABC):
    def __init__(self, client: WeaviateClient, class_name: str):
        self.client = client
        self.class_name = class_name

    async def create(self, data: Dict[str, Any], unique_properties: Optional[List[str]] = None) -> str:
        try:
            return await self.client.insert_object(self.class_name, data, unique_properties)
        except Exception as e:
            logger.error(f"Error creating object in {self.class_name}: {e}")
            raise

    async def get(
        self,
        uuid: str,
        include_vector: bool = False,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            if return_properties is None:
                return_properties = self.get_properties()
            result = await self.client.get_object(
                self.class_name, uuid, include_vector, return_properties, return_references
            )
            return result
        except Exception as e:
            logger.error(f"Error retrieving object {uuid} from {self.class_name}: {e}")
            return None

    async def get_all(
        self,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Filter] = None,
        sort: Optional[Sort] = None,
        return_properties: Optional[List[str]] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        try:
            if return_properties is None:
                return_properties = self.get_properties()
            return await self.client.get_objects(
                self.class_name, filters, limit, offset, sort, return_properties, include_vector
            )
        except Exception as e:
            logger.error(f"Error retrieving all objects from {self.class_name}: {e}")
            return []

    async def update(self, uuid: str, data: Dict[str, Any]) -> None:
        try:
            await self.client.update_object(self.class_name, uuid, data)
        except Exception as e:
            logger.error(f"Error updating object {uuid} in {self.class_name}: {e}")
            raise

    async def delete(self, uuid: str) -> None:
        try:
            await self.client.delete_object(self.class_name, uuid)
        except Exception as e:
            logger.error(f"Error deleting object {uuid} from {self.class_name}: {e}")
            raise

    async def get_sorted(
        self,
        limit: int = 5,
        filters: Optional[Filter] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        return_properties: Optional[List[str]] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get objects with sorting capabilities

        Args:
            sort_order: Either "asc" or "desc" (will be converted to boolean ascending parameter)
        """
        try:
            if return_properties is None:
                return_properties = self.get_properties()

            sort = None
            if sort_by:
                # Convert sort_order string to boolean ascending parameter
                ascending = sort_order.lower() == "asc"
                sort = Sort.by_property(sort_by, ascending=ascending)

            results = await self.client.get_objects(
                self.class_name,
                filters=filters,
                limit=limit,
                sort=sort,
                return_properties=return_properties,
                include_vector=include_vector,
            )

            return results
        except Exception as e:
            logger.error(f"Error retrieving sorted objects from {self.class_name}: {e}")
            return []

    async def search(
        self,
        query_text: str,
        limit: int = 5,
        filters: Optional[Filter] = None,
        move_to: Optional[Dict[str, Any]] = None,
        move_away: Optional[Dict[str, Any]] = None,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        try:
            return await self.client.search(
                self.class_name,
                query_text,
                limit,
                filters,
                move_to,
                move_away,
                return_properties,
                return_references,
                include_vector,
            )
        except Exception as e:
            logger.error(f"Error searching in {self.class_name}: {e}")
            return []

    async def hybrid_search(
        self,
        query_text: str,
        limit: int = 5,
        alpha: float = 0.5,
        filters: Optional[Filter] = None,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        try:
            return await self.client.hybrid_search(
                self.class_name, query_text, limit, alpha, filters, return_properties, return_references, include_vector
            )
        except Exception as e:
            logger.error(f"Error performing hybrid search in {self.class_name}: {e}")
            return []

    async def count(self) -> int:
        try:
            result = await self.client.aggregate(self.class_name)
            logger.info(f"Count result: {result}")
            return result.total_count
        except Exception as e:
            logger.error(f"Error counting objects in {self.class_name}: {e}")
            return 0

    async def batch_create_objects(
        self, objects: List[Dict[str, Any]], unique_properties: Optional[List[str]] = None, batch_size: int = 100
    ) -> List[str]:
        try:
            return await self.client.batch_insert_objects(self.class_name, objects, unique_properties, batch_size)
        except Exception as e:
            logger.error(f"Error batch creating objects in {self.class_name}: {e}")
            raise

    async def batch_delete_objects(
        self, uuids: List[str], dry_run: bool = False, verbose: bool = False
    ) -> Dict[str, Any]:
        try:
            return await self.client.batch_delete_objects(self.class_name, uuids, dry_run, verbose)
        except Exception as e:
            logger.error(f"Error batch deleting objects from {self.class_name}: {e}")
            raise

    async def delete_objects_by_filter(
        self, filters: Filter, dry_run: bool = False, verbose: bool = False
    ) -> Dict[str, Any]:
        try:
            return await self.client.delete_objects_by_filter(self.class_name, filters, dry_run, verbose)
        except Exception as e:
            logger.error(f"Error deleting objects by filter from {self.class_name}: {e}")
            raise

    async def aggregate(
        self, group_by: Optional[List[str]] = None, properties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            return await self.client.aggregate(self.class_name, group_by, properties)
        except Exception as e:
            logger.error(f"Error performing aggregation in {self.class_name}: {e}")
            return {}

    async def keyword_search(
        self,
        query_text: str,
        properties_to_search_on: Optional[List[str]] = None,
        filters: Optional[Filter] = None,
        include_vector: bool = False,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
        limit: int = 20,
        offset: int = 0,
        auto_limit: int = 3,
    ) -> List[Dict[str, Any]]:
        try:
            return await self.client.keyword_search(
                self.class_name,
                query_text,
                properties_to_search_on,
                filters,
                include_vector,
                return_properties,
                return_references,
                limit,
                offset,
                auto_limit,
            )
        except Exception as e:
            logger.error(f"Error performing keyword search in {self.class_name}: {e}")
            return []

    async def vector_search(
        self,
        query: Union[str, List[float]],
        filters: Optional[Filter] = None,
        move_to: Optional[Move] = None,
        move_away: Optional[Move] = None,
        distance: Optional[float] = None,
        include_vector: bool = True,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
        limit: int = 20,
        offset: int = 0,
        auto_limit: int = 3,
    ) -> List[Dict[str, Any]]:
        try:
            return await self.client.vector_search(
                self.class_name,
                query,
                filters,
                move_to,
                move_away,
                distance,
                include_vector,
                return_properties,
                return_references,
                limit,
                offset,
                auto_limit,
            )
        except Exception as e:
            logger.error(f"Error performing vector search in {self.class_name}: {e}")
            return []

    @abstractmethod
    def get_properties(self) -> List[str]:
        pass
