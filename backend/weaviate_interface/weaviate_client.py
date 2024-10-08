import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from weaviate import WeaviateAsyncClient
from weaviate.connect import ConnectionParams
from weaviate.classes.query import Filter, Move, QueryReference, Sort, MetadataQuery
from weaviate.classes.config import Configure, Property, ReferenceProperty
from weaviate.classes.init import AdditionalConfig, Timeout

logger = logging.getLogger(__name__)


class WeaviateClient:
    def __init__(self, url: str, api_key: str, use_grpc: bool = True):
        self.client = WeaviateAsyncClient(
            connection_params=ConnectionParams.from_params(
                http_host=url,
                http_port=8080,
                http_secure=False,
                grpc_host=url if use_grpc else None,
                grpc_port=50051 if use_grpc else None,
                grpc_secure=False,
            ),
            additional_headers={"X-OpenAI-Api-Key": api_key},
            additional_config=AdditionalConfig(
                timeout=Timeout(init=30, query=60, insert=120),  # Values in seconds
            ),
            skip_init_checks=False,
        )

    # section 1: connection and setup
    async def connect(self):
        try:
            await self.client.connect()
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}", exc_info=True)
            raise

    async def close(self):
        await self.client.close()

    async def is_ready(self) -> bool:
        try:
            return await self.client.is_ready()
        except Exception as e:
            logger.error(f"Error checking Weaviate readiness: {e}", exc_info=True)
            return False

    # section 2: collection management
    async def get_schema(self) -> Dict[str, Any]:
        try:
            return await self.client.collections.list_all()
        except Exception as e:
            logger.error(f"Error retrieving schema: {e}", exc_info=True)
            raise

    async def create_collection(
        self,
        name: str,
        properties: List[Property],
        vectorizer_config: Optional[Configure.Vectorizer] = None,
        generative_config: Optional[Configure.Generative] = None,
        description: Optional[str] = None,
        references: Optional[List[ReferenceProperty]] = None,
    ) -> None:
        try:
            collection = self.client.collections.create(
                name=name,
                properties=properties,
                vectorizer_config=vectorizer_config,
                generative_config=generative_config,
                description=description,
                references=references,
            )
            await collection
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}", exc_info=True)
            raise

    def get_collection(self, name: str):
        try:
            return self.client.collections.get(name)
        except Exception as e:
            logger.error(f"Error retrieving collection {name}: {e}", exc_info=True)
            raise

    async def delete_collection(self, name: str) -> None:
        try:
            await self.client.collections.delete(name)
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}", exc_info=True)
            raise

    async def delete_all_collections(self) -> None:
        try:
            collections = await self.client.collections.list_all()
            for collection_name in collections:
                await self.client.collections.delete(collection_name)
        except Exception as e:
            logger.error(f"Error deleting all collections: {e}", exc_info=True)
            raise

    # section 3: single object operations
    async def insert_object(
        self, collection_name: str, data: Dict[str, Any], unique_properties: Optional[List[str]] = None
    ) -> str:
        try:
            collection = self.get_collection(collection_name)

            if unique_properties:
                filters = Filter.all_of(
                    *[Filter.by_property(prop).equal(data.get(prop)) for prop in unique_properties if prop in data]
                )
                existing_objects = await self.get_objects(collection_name, filters=filters, limit=1)
                if existing_objects:
                    logger.warn(
                        f"Object with properties {unique_properties} already exists in collection {collection_name}."
                    )
                    return existing_objects[0]["id"]

            result = await collection.data.insert(data)
            logger.info(f"Object inserted with UUID: {result}")
            return result
        except Exception as e:
            logger.error(f"Error inserting object into collection {collection_name}: {e}", exc_info=True)
            raise

    async def get_object(
        self,
        collection_name: str,
        uuid: str,
        include_vector: bool = False,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            collection = self.get_collection(collection_name)
            result = await collection.query.fetch_object_by_id(
                uuid,
                include_vector=include_vector,
                return_properties=return_properties,
                return_references=return_references,
            )
            if result:
                properties = result.properties
                # Extract the 'id' from 'uuid' and include it in properties
                if hasattr(result, "uuid"):
                    properties["id"] = str(result.uuid)
                else:
                    logger.warning(f"Object missing 'uuid' field: {result}")
                return properties
            return None
        except Exception as e:
            logger.error(f"Error retrieving object {uuid} from collection {collection_name}: {e}", exc_info=True)
            return None

    async def update_object(self, collection_name: str, uuid: str, data: Dict[str, Any]) -> None:
        try:
            collection = self.get_collection(collection_name)
            await collection.data.update(uuid, data)
        except Exception as e:
            logger.error(f"Error updating object {uuid} in collection {collection_name}: {e}", exc_info=True)
            raise

    async def delete_object(self, collection_name: str, uuid: str) -> None:
        try:
            collection = self.get_collection(collection_name)
            await collection.data.delete_by_id(uuid)
        except Exception as e:
            logger.error(f"Error deleting object {uuid} from collection {collection_name}: {e}", exc_info=True)
            raise

    # section 4: batch operations

    async def get_objects(
        self,
        collection_name: str,
        filters: Optional[Filter] = None,
        limit: int = 20,
        offset: int = 0,
        sort: Optional[Sort] = None,
        return_properties: Optional[List[str]] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        try:
            collection = self.get_collection(collection_name)
            results = await collection.query.fetch_objects(
                filters=filters,
                limit=limit,
                offset=offset,
                sort=sort,
                return_properties=return_properties,
                include_vector=include_vector,
            )
            objects = []
            for obj in results.objects:
                logger.info(f"\n\nObject: {obj}\n\n")
                properties = obj.properties
                logger.info(f"Properties: {properties}")
                # Extract the 'id' from 'uuid' and include it in properties
                if hasattr(obj, "uuid"):
                    properties["id"] = str(obj.uuid)
                else:
                    logger.warning(f"Product missing 'uuid' field: {obj}")
                objects.append(properties)
            return objects
        except Exception as e:
            logger.error(f"Error retrieving objects from collection {collection_name}: {e}", exc_info=True)
            return []

    # This function is not working because of bug in weaviate python client
    # async def batch_insert_objects(self, collection_name: str, objects: List[Dict[str, Any]]) -> List[str]:
    #     try:
    #         collection = self.get_collection(collection_name)
    #         uuids = []

    #         logger.info(f"Inserting {len(objects)} objects into collection {collection_name}")

    #         async with collection.batch.dynamic() as batch:
    #             for obj in objects:
    #                 result = await batch.add_object(properties=obj)
    #                 uuids.append(result["id"])

    #         logger.info(f"Batch insert completed. {len(uuids)} objects inserted.")
    #         return uuids
    #     except Exception as e:
    #         logger.error(f"Error batch inserting objects into collection {collection_name}: {e}", exc_info=True)
    #         raise

    async def batch_insert_objects(
        self,
        collection_name: str,
        objects: List[Dict[str, Any]],
        unique_properties: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> List[str]:
        try:
            uuids = []
            logger.info(f"Inserting {len(objects)} objects into collection {collection_name}")

            for i in range(0, len(objects), batch_size):
                batch = objects[i : i + batch_size]
                results = await asyncio.gather(
                    *[self.insert_object(collection_name, obj, unique_properties) for obj in batch]
                )
                uuids.extend(results)

            logger.info(f"Batch insert completed. {len(uuids)} objects inserted.")
            return uuids
        except Exception as e:
            logger.error(f"Error batch inserting objects into collection {collection_name}: {e}", exc_info=True)
            raise

    async def batch_delete_objects(
        self, collection_name: str, uuids: List[str], dry_run: bool = False, verbose: bool = False
    ) -> Dict[str, Any]:
        try:
            collection = self.get_collection(collection_name)
            result = await collection.data.delete_many(
                where=Filter.by_id().contains_any(uuids), dry_run=dry_run, verbose=verbose
            )
            logger.info(f"Batch delete result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error batch deleting objects from collection {collection_name}: {e}", exc_info=True)
            raise

    async def delete_objects_by_filter(
        self, collection_name: str, filters: Filter, dry_run: bool = False, verbose: bool = False
    ) -> Dict[str, Any]:
        try:
            collection = self.get_collection(collection_name)
            result = await collection.data.delete_many(where=filters, dry_run=dry_run, verbose=verbose)
            logger.info(f"Delete by filter result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error deleting objects by filter from collection {collection_name}: {e}", exc_info=True)
            raise

    async def aggregate(
        self,
        collection_name: str,
        group_by: Optional[List[str]] = None,
        properties: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            collection = self.get_collection(collection_name)
            query = collection.aggregate

            if group_by:
                query = query.group_by(group_by)
            if properties:
                for prop in properties:
                    query = query.with_fields(prop)

            results = await query.over_all(total_count=True)
            logger.info(f"Aggregation results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error performing aggregation in collection {collection_name}: {e}", exc_info=True)
            return {}

    # section 5: search operations

    async def search(
        self,
        collection_name: str,
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
            collection = self.get_collection(collection_name)
            move_to_obj = Move(**move_to) if move_to else None
            move_away_obj = Move(**move_away) if move_away else None

            results = await collection.query.near_text(
                query=query_text,
                limit=limit,
                filters=filters,
                move_to=move_to_obj,
                move_away=move_away_obj,
                return_properties=return_properties,
                return_references=return_references,
                include_vector=include_vector,
                return_metadata=MetadataQuery(distance=True, certainty=True),
            )
            return [
                {
                    **obj.properties,
                    "distance": obj.metadata.distance,
                    "certainty": obj.metadata.certainty,
                }
                for obj in results.objects
            ]
        except Exception as e:
            logger.error(f"Error performing search in collection {collection_name}: {e}", exc_info=True)
            return []

    async def hybrid_search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 5,
        alpha: float = 0.5,
        filters: Optional[Filter] = None,
        return_properties: Optional[List[str]] = None,
        return_references: Optional[QueryReference] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        try:
            collection = self.get_collection(collection_name)
            results = await collection.query.hybrid(
                query=query_text,
                alpha=alpha,
                limit=limit,
                filters=filters,
                return_properties=return_properties,
                return_references=return_references,
                include_vector=include_vector,
                return_metadata=MetadataQuery(distance=True, certainty=True),
            )
            return [
                {
                    **obj.properties,
                    "distance": obj.metadata.distance,
                    "certainty": obj.metadata.certainty,
                }
                for obj in results.objects
            ]
        except Exception as e:
            logger.error(f"Error performing hybrid search in collection {collection_name}: {e}", exc_info=True)
            return []

    async def keyword_search(
        self,
        collection_name: str,
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
            collection = self.get_collection(collection_name)
            response = await collection.query.bm25(
                query=query_text,
                query_properties=properties_to_search_on,
                filters=filters,
                return_metadata=MetadataQuery(score=True),
                limit=limit,
                offset=offset,
                auto_limit=auto_limit,
                include_vector=include_vector,
                return_properties=return_properties,
                return_references=return_references,
            )
            return [obj.properties for obj in response.objects]
        except Exception as e:
            logger.error(f"Error performing keyword search: {e}", exc_info=True)
            return []

    async def vector_search(
        self,
        collection_name: str,
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
            collection = self.get_collection(collection_name)
            if isinstance(query, str):
                response = await collection.query.near_text(
                    query=query,
                    filters=filters,
                    move_to=move_to,
                    move_away=move_away,
                    distance=distance,
                    limit=limit,
                    offset=offset,
                    auto_limit=auto_limit,
                    include_vector=include_vector,
                    return_metadata=MetadataQuery(distance=True),
                    return_properties=return_properties,
                    return_references=return_references,
                )
            else:
                response = await collection.query.near_vector(
                    near_vector=query,
                    filters=filters,
                    distance=distance,
                    limit=limit,
                    offset=offset,
                    auto_limit=auto_limit,
                    include_vector=include_vector,
                    return_metadata=MetadataQuery(distance=True),
                    return_properties=return_properties,
                    return_references=return_references,
                )
            return [obj.properties for obj in response.objects]
        except Exception as e:
            logger.error(f"Error performing vector search: {e}", exc_info=True)
            return []
