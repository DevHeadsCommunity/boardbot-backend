import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from weaviate_old.utils.graphql_query_builder import GraphQLQueryBuilder
from weaviate_old.utils.where_clause_builder import OffsetClauseBuilder, WhereClauseBuilder
from .weaviate_client import LimitClauseBuilder, WeaviateClient
from .weaviate_service import WeaviateService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ProductService(WeaviateService):
    def __init__(self, weaviate_client: WeaviateClient):
        super().__init__(weaviate_client)

    @property
    def object_type(self) -> str:
        return "Product"

    @property
    def properties(self) -> List[str]:
        return [
            "_additional{id}",
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

    async def semantic_search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        try:
            query_obj = {
                "concepts": [query],
                "certainty": 0.7,
            }
            results = await self.client.search(
                self.object_type, query_obj, self.properties, limit, where_filter=filters
            )
            return [(self._process_result(result), score) for result, score in results]
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            raise

    async def keyword_search(
        self, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        try:
            results = await self.get_all(limit=limit, where_filter=filters)
            return [(self._process_result(result), 1.0) for result in results]
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            raise

    async def hybrid_search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        try:
            semantic_results = await self.semantic_search(query, limit, filters)
            keyword_results = await self.keyword_search(limit, filters)

            all_results = semantic_results + keyword_results
            unique_results = {}
            for result, score in all_results:
                if result["name"] not in unique_results or score > unique_results[result["name"]][1]:
                    unique_results[result["name"]] = (result, score)

            sorted_results = sorted(unique_results.values(), key=lambda x: x[1], reverse=True)
            return sorted_results[:limit]
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise

    async def upsert(self, response_data: Dict[str, Any]) -> str:
        return await self.client.create_object(response_data, self.object_type)

    async def batch_upsert(self, response_data: List[Dict[str, Any]]) -> bool:
        return await self.client.batch_create_objects(response_data, self.object_type)

    async def get(self, uuid: str) -> Dict[str, Any]:
        result = await self.client.get_object(uuid, self.object_type)
        return self._process_result(result)

    async def get_all(
        self, limit: int = 10, offset: int = 0, where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Get").set_class_name(self.object_type).set_properties(self.properties)
        query_builder.add_clauses(LimitClauseBuilder(limit))
        query_builder.add_clauses(OffsetClauseBuilder(offset))

        if where_filter:
            query_builder.add_clauses(WhereClauseBuilder(where_filter))

        graphql_query = query_builder.build()
        logger.info(f"Generated GraphQL query: {graphql_query}")

        response = await self.client.run_query(graphql_query)
        results = response.get("data", {}).get("Get", {}).get(self.object_type, [])
        return [self._process_result(result) for result in results]

    async def count(self, where_filter: Optional[Dict[str, Any]] = None) -> int:
        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Aggregate").set_class_name(self.object_type).set_properties(["meta { count }"])

        if where_filter:
            if isinstance(where_filter, str):
                where_filter = json.loads(where_filter)
            query_builder.add_clauses(WhereClauseBuilder(where_filter))

        graphql_query = query_builder.build()
        logger.info(f"Count GraphQL query: {graphql_query}")
        response = await self.client.run_query(graphql_query)
        return (
            response.get("data", {}).get("Aggregate", {}).get(self.object_type, [{}])[0].get("meta", {}).get("count", 0)
        )

    async def update(self, uuid: str, updated_data: Dict[str, Any]) -> bool:
        return await self.client.update_object(uuid, updated_data, self.object_type)

    async def delete(self, uuid: str) -> bool:
        return await self.client.delete_object(uuid, self.object_type)

    def _process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        processed = {key: result.get(key) for key in self.properties if key != "_additional{id}"}
        processed["id"] = result.get("_additional", {}).get("id")
        return processed
