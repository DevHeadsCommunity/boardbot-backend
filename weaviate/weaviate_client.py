from weaviate.utils.graphql_query_builder import GraphQLQueryBuilder
from weaviate.utils.where_clause_builder import WhereClauseBuilder
from .http_client import HttpHandler
from typing import Any, Dict, List, Optional


SCHEMA_ENDPOINT = "/v1/schema"
GRAPHQL_ENDPOINT = "/v1/graphql"
OBJECTS_ENDPOINT = "/v1/objects"
BATCH_OBJECTS_ENDPOINT = "/v1/batch/objects"


class ClauseBuilder:
    def build(self) -> str:
        raise NotImplementedError


class LimitClauseBuilder(ClauseBuilder):
    def __init__(self, limit: int):
        self.limit = limit

    def build(self) -> str:
        return f"limit: {self.limit}" if self.limit is not None else ""


class NearTextClauseBuilder(ClauseBuilder):
    def __init__(self, near_text: Dict[str, Any]):
        self.near_text = near_text

    def build(self) -> str:
        if not self.near_text:
            return ""
        concepts_str = ", ".join([f'"{concept}"' for concept in self.near_text.get("concepts", [])])
        return f"nearText: {{ concepts: [{concepts_str}] }}"


class ReferenceWhereClauseBuilder(ClauseBuilder):
    def __init__(self, reference_path: List[str], operator: str, value: str):
        self.reference_path = reference_path
        self.operator = operator
        self.value = value

    def build(self) -> str:
        reference_path_str = ", ".join([f'"{path}"' for path in self.reference_path])
        return f'where: {{ path: [{reference_path_str}], operator: {self.operator}, valueText: "{self.value}" }}'


class WeaviateClient:
    def __init__(self, http_handler: HttpHandler) -> None:
        self.http_handler = http_handler

    async def get_schema(self) -> Dict[str, Any]:
        return await self.http_handler.get_json_response("GET", SCHEMA_ENDPOINT)

    async def create_class(self, class_info: Dict[str, Any]) -> None:
        await self.http_handler.get_json_response("POST", SCHEMA_ENDPOINT, class_info)

    async def delete_class(self, class_name: str) -> None:
        endpoint = f"{SCHEMA_ENDPOINT}/{class_name}"
        await self.http_handler.get_json_response("DELETE", endpoint)

    async def create_object(self, data: Dict[str, Any], class_name: str) -> str:
        payload = {"class": class_name, "properties": data}
        response = await self.http_handler.get_json_response("POST", OBJECTS_ENDPOINT, payload)
        return response.get("id")

    async def batch_create_objects(self, objects: List[Dict[str, Any]], class_name: str) -> bool:
        transformed_objects = [{"class": class_name, "properties": obj} for obj in objects]
        batch_data = {"objects": transformed_objects}
        response = await self.http_handler.get_json_response("POST", BATCH_OBJECTS_ENDPOINT, batch_data)
        return response[0].get("result", {}).get("status") == "SUCCESS"

    async def get_object(self, uuid: str, class_name: str) -> Dict[str, Any]:
        endpoint = f"{OBJECTS_ENDPOINT}/{class_name}/{uuid}"
        return await self.http_handler.get_json_response("GET", endpoint)

    async def update_object(self, uuid: str, data: Dict[str, Any], class_name: str) -> bool:
        endpoint = f"{OBJECTS_ENDPOINT}/{class_name}/{uuid}"
        await self.http_handler.get_json_response("PATCH", endpoint, data)
        return True

    async def delete_object(self, uuid: str, class_name: str) -> bool:
        endpoint = f"{OBJECTS_ENDPOINT}/{class_name}/{uuid}"
        await self.http_handler.get_json_response("DELETE", endpoint)
        return True

    async def run_query(self, graphql_query: str) -> Dict[str, Any]:
        return await self.http_handler.get_json_response("POST", GRAPHQL_ENDPOINT, {"query": graphql_query})

    async def count_class_entries(self, class_name: str) -> int:
        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Aggregate").set_class_name(class_name).set_properties(["meta { count }"])

        graphql_query = query_builder.build()
        response = await self.run_query(graphql_query)
        return response.get("data", {}).get("Aggregate", {}).get(class_name, [{}])[0].get("meta", {}).get("count", 0)

    async def query_objects(
        self,
        class_name: str,
        properties: List[str],
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Ensure that properties are not empty
        if not properties:
            raise ValueError("Properties list cannot be empty")

        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Get").set_class_name(class_name).set_properties(properties)

        if where_filter:
            query_builder.add_clause(WhereClauseBuilder(where_filter))

        graphql_query = query_builder.build()
        return await self.http_handler.get_json_response("POST", GRAPHQL_ENDPOINT, {"query": graphql_query})

    async def query_objects_with_reference(
        self,
        class_name: str,
        properties: List[str],
        reference_path: List[str],
        operator: str,
        value: str,
    ):
        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Get").set_class_name(class_name).set_properties(properties)
        query_builder.add_clause(ReferenceWhereClauseBuilder(reference_path, operator, value))

        graphql_query = query_builder.build()
        return await self.http_handler.get_json_response("POST", GRAPHQL_ENDPOINT, {"query": graphql_query})

    async def query_near_text(
        self,
        class_name: str,
        properties: List[str],
        near_text: Dict[str, Any],
        limit: Optional[int] = None,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not isinstance(near_text, dict):
            raise ValueError("near_text must be a dictionary")

        query_builder = GraphQLQueryBuilder()
        query_builder.set_operation("Get").set_class_name(class_name).set_properties(properties)

        if where_filter:
            query_builder.add_clause(WhereClauseBuilder(where_filter))
        if near_text:
            query_builder.add_clause(NearTextClauseBuilder(near_text))
        if limit is not None:
            query_builder.add_clause(LimitClauseBuilder(limit))

        graphql_query = query_builder.build()
        # print(f"===> Generated GraphQL Query: {graphql_query}")  # Print the generated query
        return await self.run_query(graphql_query)

    async def search(
        self,
        class_name: str,
        query: str,
        properties: List[str],
        limit: int,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        near_text = {"concepts": [query]}
        response = await self.query_near_text(class_name, properties, near_text, limit, where_filter)
        return response.get("data", {}).get("Get", {}).get(class_name, [])
