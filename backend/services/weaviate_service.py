from dataclasses import dataclass
from enum import Enum
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, TypedDict, Union
from services.utils.enhanced_error_logger import create_error_logger
from services.utils.filter_parser import QueryBuilder
from weaviate_interface import WeaviateInterface, route_descriptions
from feature_extraction.product_data_preprocessor import ProductDataProcessor
from weaviate.classes.query import Filter
from weaviate.classes.config import Property, DataType

logger = logging.getLogger(__name__)
logger.error = create_error_logger(logger)

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortConfig:
    field: str
    order: SortOrder
    weight: float = 1.0  # For multi-sort scenarios


class SearchParams(TypedDict, total=False):
    query: Optional[str]
    filters: Optional[Dict[str, Any]]
    sort: Optional[Union[SortConfig, List[SortConfig]]]
    limit: int
    offset: int
    search_type: str


class WeaviateService:

    def __init__(self, openai_key: str, weaviate_url: str, product_data_preprocessor: ProductDataProcessor):
        self.connected = False
        self.wi = WeaviateInterface(weaviate_url, openai_key)
        self.data_processor = product_data_preprocessor
        self.query_builder = QueryBuilder()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_connection()

    async def connect(self):
        if not self.connected:
            await self.wi.client.connect()
            self.connected = True
            logger.debug("Weaviate client connected.")

    async def close_connection(self):
        if self.connected:
            await self.wi.client.close()
            self.connected = False
            logger.debug("Weaviate client disconnected.")

    async def initialize_weaviate(self, reset: bool = False) -> None:
        logger.info("Initializing Weaviate...")
        try:
            if not self.connected:
                await self.connect()

            # if not (await self.wi.schema.is_valid()) or reset:
            #     await self.wi.schema.reset_schema()
            #     # Optionally load initial data
            #     await self._load_product_data()
            #     await self._load_semantic_routes()

            is_valid = await self.wi.schema.is_valid()
            info = await self.wi.schema.info()
            logger.info(f"Weaviate schema is valid: {is_valid}")
            logger.info(f"Weaviate schema info: {info}")
        except Exception as e:
            logger.error(f"Error initializing Weaviate: {e}", exc_info=True)
            raise

    async def _load_product_data(self):
        try:
            processed_data = self.data_processor.load_and_preprocess_data("data/cleaned_data.csv")

            for i in range(0, len(processed_data), 20):
                batch = processed_data[i : i + 20]

                # Debug: Print out the first item in each batch
                if batch:
                    logger.debug(f"First item in batch after preprocessing: {json.dumps(batch[0], indent=2)}")

                try:
                    await self.wi.product_service.batch_create_objects(batch)
                    logger.info(f"Inserted batch {i // 20 + 1} of {len(processed_data) // 20 + 1}")
                except Exception as e:
                    logger.error(f"Error inserting products at index {i}: {e}", exc_info=True)
                    continue

        except Exception as e:
            logger.error(f"Error loading initial data: {e}", exc_info=True)
            raise

    async def _load_semantic_routes(self):
        try:
            routes = await self.wi.route_service.get_all()
            if not routes:
                await self.wi.route_service.create(route_descriptions)
        except Exception as e:
            logger.error(f"Error loading semantic routes: {e}", exc_info=True)
            raise

    async def search_routes(self, query: str) -> List[Tuple[str, float]]:
        try:
            routes = await self.wi.route_service.search(query_text=query, return_properties=["route"], limit=1)
            return [(route["route"], route["certainty"]) for route in routes]
        except Exception as e:
            logger.error(f"Error searching routes: {e}", exc_info=True)
            raise

    async def get_all_products(self) -> List[Dict[str, Any]]:
        try:
            return await self.wi.product_service.get_all()
        except Exception as e:
            logger.error(f"Error getting all products: {e}", exc_info=True)
            raise

    async def get_product(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.wi.product_service.get(id)
        except Exception as e:
            logger.error(f"Error getting product {id}: {e}", exc_info=True)
            return None

    async def add_product(self, product_data: Dict[str, Any]) -> str:
        try:
            return await self.wi.product_service.create(product_data)
        except Exception as e:
            logger.error(f"Error adding product: {e}", exc_info=True)
            raise

    async def update_product(self, id: str, product_data: Dict[str, Any]) -> None:
        try:
            # Remove 'id' from product_data if it exists
            product_data_copy = product_data.copy()
            product_data_copy.pop("id", None)

            await self.wi.product_service.update(id, product_data_copy)
        except Exception as e:
            logger.error(f"Error updating product {id}: {e}", exc_info=True)
            raise

    async def delete_product(self, id: str) -> None:
        try:
            await self.wi.product_service.delete(id)
        except Exception as e:
            logger.error(f"Error deleting product {id}: {e}", exc_info=True)
            raise

    async def get_products(
        self, limit: int = 10, offset: int = 0, filter_dict: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            weaviate_filter = None
            if filter_dict:
                filter_conditions = []
                for key, value in filter_dict.items():
                    filter_conditions.append(Filter.by_property(key).equal(value))
                weaviate_filter = (
                    Filter.all_of(filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]
                )

            products = await self.wi.product_service.get_all(limit=limit, offset=offset, filters=weaviate_filter)
            total_count = await self.wi.product_service.count()
            return products, total_count
        except Exception as e:
            logger.error(f"Error getting products: {e}", exc_info=True)
            raise

    async def store_raw_data(self, product_id: str, raw_data: str) -> str:
        try:
            # Store the raw data
            raw_data_id = await self.wi.raw_product_data_service.create(
                {"product_id": product_id, "raw_data": raw_data}
            )

            # Create and store chunks
            chunks = self.data_processor.create_chunks(raw_data)
            logger.info(f"Storing {len(chunks)} chunks for product {product_id}")
            await self.store_chunks(product_id, chunks, "raw_data", raw_data_id)

            return raw_data_id
        except Exception as e:
            logger.error(f"Error storing raw data for product {product_id}: {e}", exc_info=True)
            raise

    async def store_search_results(
        self, product_id: str, search_query: str, search_result: str, data_source: str
    ) -> str:
        try:
            # Store the search result
            search_result_id = await self.wi.product_search_result_service.create(
                {
                    "product_id": product_id,
                    "search_query": search_query,
                    "search_result": search_result,
                    "data_source": data_source,
                }
            )

            # Create and store chunks
            chunks = self.data_processor.create_chunks(search_result)
            await self.store_chunks(product_id, chunks, "search_result", search_result_id)

            return search_result_id
        except Exception as e:
            logger.error(f"Error storing search results for product {product_id}: {e}", exc_info=True)
            raise

    async def store_chunks(self, product_id: str, chunks: List[str], source_type: str, source_id: str) -> List[str]:
        try:
            return await self.wi.product_data_chunk_service.create_chunks(chunks, product_id, source_type, source_id)
        except Exception as e:
            logger.error(f"Error storing chunks for product {product_id}: {e}", exc_info=True)
            raise

    async def get_raw_product_data(self, product_id: str) -> Dict[str, Any]:
        try:
            return await self.wi.raw_product_data_service.get_by_product_id(product_id)
        except Exception as e:
            logger.error(f"Error getting raw product data for {product_id}: {e}", exc_info=True)
            raise

    async def get_search_results(self, product_id: str) -> List[Dict[str, Any]]:
        try:
            return await self.wi.product_search_result_service.get_by_product_id(product_id)
        except Exception as e:
            logger.error(f"Error getting search results for {product_id}: {e}", exc_info=True)
            raise

    async def get_relevant_chunks(
        self, product_id: str, query: str, limit: int = 5, source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            return await self.wi.product_data_chunk_service.semantic_search(
                query=query, product_id=product_id, limit=limit, source_type=source_type
            )
        except Exception as e:
            logger.error(f"Error getting relevant chunks for {product_id}: {e}", exc_info=True)
            raise

    async def delete_product_data(self, product_id: str) -> None:
        try:
            await self.wi.raw_product_data_service.delete_by_product_id(product_id)
            await self.wi.product_search_result_service.delete_by_product_id(product_id)
            await self.wi.product_data_chunk_service.delete_by_product_id(product_id)
        except Exception as e:
            logger.error(f"Error deleting product data for {product_id}: {e}", exc_info=True)
            raise

    async def search_products(self, search_params: SearchParams) -> List[Dict[str, Any]]:
        """
        Unified search function handling all search scenarios.
        """
        try:
            # Build Weaviate filter from filter dictionary
            weaviate_filter = None
            if search_params.get("filters"):
                weaviate_filter = self.query_builder.build_weaviate_filter(search_params["filters"])
                logger.info(f"Built Weaviate filter: {weaviate_filter.__dict__ if weaviate_filter else None}")

            # Get search parameters
            search_type = search_params.get("search_type", "semantic")
            limit = search_params.get("limit", 5)
            query = search_params.get("query")

            # Get sort configuration
            sort_configs = self._normalize_sort_config(search_params.get("sort"))

            # If no query is provided for semantic/hybrid search, fall back to filtered
            if not query and search_type in ("semantic", "hybrid"):
                logger.warning(f"No query provided for {search_type} search, falling back to filtered search")
                search_type = "filtered"

            # Get properties to return
            return_properties = self.wi.product_service.get_properties()

            # Execute search based on type
            if search_type == "semantic":
                results = await self.wi.product_service.semantic_search(
                    query_text=query, limit=limit, filters=weaviate_filter, return_properties=return_properties
                )
            elif search_type == "hybrid":
                results = await self.wi.product_service.hybrid_search(
                    query_text=query, limit=limit, filters=weaviate_filter, return_properties=return_properties
                )
            else:
                # Direct filtered query with sorting
                results = await self._execute_sorted_query(
                    filters=weaviate_filter,
                    sort_configs=sort_configs,
                    limit=limit,
                )

            # Post-process results
            processed_results = self._post_process_results(results, sort_configs)

            # Add search metadata
            for result in processed_results:
                result["_search_metadata"] = {
                    "search_type": search_type,
                    "applied_filters": search_params.get("filters", {}),
                    "sort_config": (
                        [{"field": sc.field, "order": sc.order.value, "weight": sc.weight} for sc in sort_configs]
                        if sort_configs
                        else None
                    ),
                }

            return processed_results

        except Exception as e:
            logger.error(f"Error in search_products: {str(e)}", exc_info=True)
            raise

    async def _execute_sorted_query(
        self,
        filters: Optional[Filter] = None,  # Updated type hint to Filter
        sort_configs: Optional[List[SortConfig]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Execute query with sorting capabilities."""
        try:
            return_properties = self.wi.product_service.get_properties()

            if not sort_configs:
                return await self.wi.product_service.get_all(
                    limit=limit, filters=filters, return_properties=return_properties
                )

            # For single sort condition
            if len(sort_configs) == 1:
                sort_config = sort_configs[0]
                return await self.wi.product_service.get_sorted(
                    filters=filters,
                    sort_by=sort_config.field,
                    sort_order=sort_config.order.value,
                    limit=limit,
                    return_properties=return_properties,
                )

            # For multiple sort conditions, fetch extra results to ensure accurate sorting
            fetch_limit = min(limit * 2, 100)
            results = await self.wi.product_service.get_all(
                limit=fetch_limit, filters=filters, return_properties=return_properties
            )

            # Apply multiple sorts and return requested limit
            sorted_results = self._apply_multiple_sorts(results, sort_configs)
            return sorted_results[:limit]

        except Exception as e:
            logger.error(f"Error in _execute_sorted_query: {str(e)}", exc_info=True)
            raise

    def _normalize_sort_config(
        self, sort_config: Optional[Union[SortConfig, List[SortConfig], Dict[str, Any]]]
    ) -> List[SortConfig]:
        """Normalizes various sort config input formats into a list of SortConfig objects"""
        if not sort_config:
            return []

        if isinstance(sort_config, SortConfig):
            return [sort_config]

        if isinstance(sort_config, dict):
            # Handle legacy format {"field": "...", "order": "..."}
            return [SortConfig(field=sort_config["field"], order=SortOrder(sort_config["order"].lower()), weight=1.0)]

        if isinstance(sort_config, list):
            return [
                (
                    conf
                    if isinstance(conf, SortConfig)
                    else SortConfig(
                        field=conf["field"], order=SortOrder(conf["order"].lower()), weight=conf.get("weight", 1.0)
                    )
                )
                for conf in sort_config
            ]

        raise ValueError(f"Invalid sort configuration format: {sort_config}")

    def _apply_multiple_sorts(
        self, results: List[Dict[str, Any]], sort_configs: List[SortConfig]
    ) -> List[Dict[str, Any]]:
        """Applies multiple sort conditions with weights"""

        def sort_key(item):
            # Create a tuple of weighted values for sorting
            return tuple(
                (
                    config.weight * float(item.get(config.field, 0))
                    if config.order == SortOrder.ASC
                    else -config.weight * float(item.get(config.field, 0))
                )
                for config in sort_configs
            )

        return sorted(results, key=sort_key)

    def _post_process_results(
        self, results: List[Dict[str, Any]], sort_configs: List[SortConfig]
    ) -> List[Dict[str, Any]]:
        """Post-process results to include sort-related metadata"""
        if not results:
            return []

        # Add sorting metadata to help with response generation
        for result in results:
            result["_sort_values"] = {config.field: result.get(config.field) for config in sort_configs}

        return results
