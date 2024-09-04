import logging
from typing import Any, Dict, List, Optional, Tuple

from weaviate.utils.graphql_query_builder import GraphQLQueryBuilder
from weaviate.utils.where_clause_builder import OffsetClauseBuilder, WhereClauseBuilder
from .weaviate_client import LimitClauseBuilder, WeaviateClient
from .weaviate_service import WeaviateService


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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

    async def upsert(self, response_data: Dict[str, Any]) -> str:
        return await self.client.create_object(response_data, self.object_type)

    async def batch_upsert(self, response_data: List[Dict[str, Any]]) -> bool:
        return await self.client.batch_create_objects(response_data, self.object_type)

    async def get(self, uuid: str) -> Dict[str, Any]:
        return await self.client.get_object(uuid, self.object_type)

    # async def get_all(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    #     query = f"""
    #     {{
    #       Get {{
    #         {self.object_type}(limit: {limit}, offset: {offset}) {{
    #           {', '.join(self.properties)}
    #         }}
    #       }}
    #     }}
    #     """
    #     response = await self.client.run_query(query)
    #     return response.get("data", {}).get("Get", {}).get(self.object_type, [])

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
        response = await self.client.run_query(graphql_query)
        return response.get("data", {}).get("Get", {}).get(self.object_type, [])

    async def count(self, where_filter: Optional[Dict[str, Any]] = None) -> int:
        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Aggregate").set_class_name(self.object_type).set_properties(["meta { count }"])

        if where_filter:
            query_builder.add_clause(WhereClauseBuilder(where_filter))

        graphql_query = query_builder.build()
        response = await self.client.run_query(graphql_query)
        return (
            response.get("data", {}).get("Aggregate", {}).get(self.object_type, [{}])[0].get("meta", {}).get("count", 0)
        )

    async def update(self, uuid: str, updated_data: Dict[str, Any]) -> bool:
        return await self.client.update_object(uuid, updated_data, self.object_type)

    async def delete(self, uuid: str) -> bool:
        return await self.client.delete_object(uuid, self.object_type)

    async def search(
        self, query: str, fields: Optional[List[str]] = None, limit: int = 3
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not fields:
            fields = self.properties

        res_products = await self.client.search(self.object_type, query, fields, limit)
        # logger.info(f"Found {len(res_products)} products")
        # logger.info(f"Products: {res_products}")
        products = []
        for product, certainty in res_products:
            products.append(
                (
                    {
                        "id": product["_additional"]["id"],
                        "ids": product["ids"],
                        "name": product["name"],
                        "manufacturer": product["manufacturer"],
                        "form_factor": product["form_factor"],
                        "processor": product["processor"],
                        "core_count": product["core_count"],
                        "processor_tdp": product["processor_tdp"],
                        "memory": product["memory"],
                        "io": product["io"],
                        "operating_system": product["operating_system"],
                        "environmentals": product["environmentals"],
                        "certifications": product["certifications"],
                        "short_summary": product["short_summary"],
                        "full_summary": product["full_summary"],
                        "full_product_description": product["full_product_description"],
                    },
                    certainty,
                )
            )
        # logger.info(f"Products2: {products}")
        return products

    # async def count(self) -> int:
    #     query = f"""
    #     {{
    #       Aggregate {{
    #         {self.object_type} {{
    #           meta {{
    #             count
    #           }}
    #         }}
    #       }}
    #     }}
    #     """
    #     response = await self.client.run_query(query)
    #     return (
    #         response.get("data", {}).get("Aggregate", {}).get(self.object_type, [{}])[0].get("meta", {}).get("count", 0)
    #     )
