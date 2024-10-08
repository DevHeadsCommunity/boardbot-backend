import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from weaviate_interface import WeaviateInterface, route_descriptions
from feature_extraction.product_data_preprocessor import ProductDataProcessor
from weaviate.classes.query import Filter

logger = logging.getLogger(__name__)


class WeaviateService:

    def __init__(self, openai_key: str, weaviate_url: str, product_data_preprocessor: ProductDataProcessor):
        self.connected = False
        self.wi = WeaviateInterface(weaviate_url, openai_key)
        self.data_processor = product_data_preprocessor

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
            processed_data = self.data_processor.load_and_preprocess_data(
                "data/processed_feature_extraction_results.csv"
            )

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

    async def search_products(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None, search_type: str = "semantic"
    ) -> List[Tuple[Dict[str, Any], float]]:
        try:
            weaviate_filter = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(Filter.by_property(key).equal(value))
                weaviate_filter = (
                    Filter.all_of(filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]
                )

            if search_type == "semantic":
                results = await self.wi.product_service.search(query_text=query, limit=limit, filters=weaviate_filter)
            elif search_type == "keyword":
                results = await self.wi.product_service.keyword_search(
                    query_text=query, limit=limit, filters=weaviate_filter
                )
            elif search_type == "hybrid":
                results = await self.wi.product_service.hybrid_search(
                    query_text=query, limit=limit, filters=weaviate_filter
                )
            else:
                raise ValueError(f"Invalid search type: {search_type}")

            return results
        except Exception as e:
            logger.error(f"Error searching products: {e}", exc_info=True)
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
            await self.wi.product_service.update(id, product_data)
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
