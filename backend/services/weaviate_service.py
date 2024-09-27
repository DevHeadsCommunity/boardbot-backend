import logging
import pandas as pd
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from weaviate_interface.weaviate_interface import WeaviateInterface
from langchain_text_splitters import RecursiveCharacterTextSplitter


route_descriptions = {
    "politics": [
        "Queries related to current political events or situations.",
        "Questions or statements about political figures or parties.",
        "Discussions about government policies or legislation.",
        "Expressions of political opinions or ideologies.",
        "Inquiries about electoral processes or voting.",
        "Debates on political issues or controversies.",
        "Comments on international relations or diplomacy.",
        "Questions about political systems or structures.",
        "Discussions of political history or movements.",
        "Inquiries about political activism or civic engagement.",
    ],
    "chitchat": [
        "General greetings or conversational openers.",
        "Personal questions not related to products or technical topics.",
        "Requests for jokes, fun facts, or casual entertainment.",
        "Comments about weather, time, or general observations.",
        "Expressions of emotions or casual opinions.",
        "Small talk about daily life or common experiences.",
        "Casual questions about the AI's capabilities or personality.",
        "Non-technical questions about general knowledge topics.",
        "Playful or humorous interactions not related to products.",
        "Social pleasantries or polite conversation fillers.",
    ],
    "vague_intent_product": [
        "General inquiries about product categories without specific criteria.",
        "Requests for basic information about types of hardware or systems.",
        "Open-ended questions about product capabilities or use cases.",
        "Broad comparisons between product types or categories.",
        "Queries about trends or developments in hardware technology.",
        "Requests for explanations of technical terms or concepts.",
        "General questions about compatibility or integration.",
        "Inquiries about product availability or market presence.",
        "Requests for recommendations without specific requirements.",
        "Questions about general features common to a product category.",
    ],
    "clear_intent_product": [
        "Requests for products with specific technical specifications.",
        "Queries including numerical criteria for product features.",
        "Inquiries about products with particular processor types or brands.",
        "Questions specifying memory requirements or storage capacities.",
        "Requests for products with specific connectivity or interface requirements.",
        "Queries about products certified for particular standards or environments.",
        "Inquiries specifying power consumption or thermal requirements.",
        "Requests for products with particular physical dimensions or form factors.",
        "Questions about compatibility with specific software or operating systems.",
        "Inquiries about products with particular performance benchmarks or capabilities.",
    ],
    "do_not_respond": [
        "Queries containing offensive or inappropriate language.",
        "Requests for information about illegal activities.",
        "Personal questions that violate privacy or ethical boundaries.",
        "Commands to perform actions outside the AI's capabilities.",
        "Requests for sensitive personal or financial information.",
        "Queries promoting harmful or discriminatory ideologies.",
        "Attempts to engage the AI in role-play scenarios.",
        "Requests for medical or legal advice beyond the AI's scope.",
        "Queries completely unrelated to technology or general knowledge.",
        "Attempts to override or manipulate the AI's ethical guidelines.",
    ],
}


logger = logging.getLogger(__name__)


class WeaviateService:
    def __init__(self, openai_key: str, weaviate_url: str):
        self.wi = WeaviateInterface(weaviate_url, openai_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            length_function=self.tiktoken_len,
        )

    def tiktoken_len(self, text):
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        return len(tokens)

    async def initialize_weaviate(self, reset: bool = False) -> None:
        logger.info("===:> Initializing Weaviate")
        await self.wi.client.connect()

        try:
            if not (await self.wi.schema.is_valid()) or reset:
                await self.wi.schema.reset_schema()
                # await self._load_initial_data()

            is_valid = await self.wi.schema.is_valid()
            info = await self.wi.schema.info()
            logging.info(f"Weaviate schema is valid: {is_valid}")
            logging.info(f"Weaviate schema info: {info}")
        finally:
            await self.wi.client.close()

    async def _load_initial_data(self):
        # Load and insert products data
        products = pd.read_csv("data/extracted_data_grouped.csv")
        products_data = products.to_dict(orient="records")

        for i in range(0, len(products_data), 20):
            try:
                await self.wi.product_service.batch_create_objects(products_data[i : i + 20])
            except Exception as e:
                logger.error(f"Error inserting products at index {i}: {e}")

        # Insert route data
        for route, descriptions in route_descriptions.items():
            route_data = [{"route": route, "description": desc} for desc in descriptions]
            await self.wi.route_service.batch_create_objects(route_data)

    async def search_routes(self, query: str) -> List[Tuple[str, float]]:
        await self.wi.client.connect()
        try:
            routes = await self.wi.route_service.search(query_text=query, return_properties=["route"], limit=1)
            return [(route["route"], route["certainty"]) for route in routes]
        finally:
            await self.wi.client.close()

    async def search_products(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None, search_type: str = "semantic"
    ) -> List[Tuple[Dict[str, Any], float]]:
        await self.wi.client.connect()
        try:
            if search_type == "semantic":
                results = await self.wi.product_service.search(query_text=query, limit=limit, filters=filters)
            elif search_type == "keyword":
                results = await self.wi.product_service.keyword_search(query_text=query, limit=limit, filters=filters)
            elif search_type == "hybrid":
                results = await self.wi.product_service.hybrid_search(query_text=query, limit=limit, filters=filters)
            else:
                raise ValueError(f"Invalid search type: {search_type}")

            return [(result, result.get("certainty", 0)) for result in results]
        finally:
            await self.wi.client.close()

    async def get_all_products(self) -> List[Dict[str, Any]]:
        await self.wi.client.connect()
        try:
            return await self.wi.product_service.get_all()
        finally:
            await self.wi.client.close()

    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        await self.wi.client.connect()
        try:
            return await self.wi.product_service.get(product_id)
        finally:
            await self.wi.client.close()

    async def add_product(self, product_data: Dict[str, Any]) -> str:
        await self.wi.client.connect()
        try:
            return await self.wi.product_service.create(product_data)
        finally:
            await self.wi.client.close()

    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> None:
        await self.wi.client.connect()
        try:
            await self.wi.product_service.update(product_id, product_data)
        finally:
            await self.wi.client.close()

    async def delete_product(self, product_id: str) -> None:
        await self.wi.client.connect()
        try:
            await self.wi.product_service.delete(product_id)
        finally:
            await self.wi.client.close()

    async def get_products(
        self, limit: int = 10, offset: int = 0, filter_dict: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        await self.wi.client.connect()
        try:
            total_count = await self.wi.product_service.count()
            products = await self.wi.product_service.get_all(limit=limit, offset=offset, filters=filter_dict)

            for product in products:
                product["id"] = product.get("id")  # Assuming the id is already part of the product object

            return products, total_count
        except Exception as e:
            logger.error(f"Error in getting products: {str(e)}")
            raise
        finally:
            await self.wi.client.close()

    async def store_raw_data(self, product_id: str, raw_data: str) -> str:
        await self.wi.client.connect()
        try:
            # Store the raw data
            raw_data_id = await self.wi.raw_product_data_service.create(
                {"product_id": product_id, "raw_data": raw_data}
            )

            # Create and store chunks
            chunks = self.create_chunks(raw_data)
            logger.info(f"Storing {len(chunks)} chunks for product {product_id}")
            await self.store_chunks(product_id, chunks, "raw_data", raw_data_id)

            return raw_data_id
        except Exception as e:
            logger.error(f"Error storing raw data for product {product_id}: {e}")
            raise
        finally:
            await self.wi.client.close()

    async def store_search_results(
        self, product_id: str, search_query: str, search_result: str, data_source: str
    ) -> str:
        await self.wi.client.connect()
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
            chunks = self.create_chunks(search_result)
            await self.store_chunks(product_id, chunks, "search_result", search_result_id)

            return search_result_id
        except Exception as e:
            logger.error(f"Error storing search results for product {product_id}: {e}")
            raise
        finally:
            await self.wi.client.close()

    def create_chunks(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)

    async def store_chunks(self, product_id: str, chunks: List[str], source_type: str, source_id: str) -> List[str]:
        await self.wi.client.connect()
        try:
            return await self.wi.product_data_chunk_service.create_chunks(chunks, product_id, source_type, source_id)
        finally:
            await self.wi.client.close()

    async def get_raw_product_data(self, product_id: str) -> Dict[str, Any]:
        await self.wi.client.connect()
        try:
            return await self.wi.raw_product_data_service.get_by_product_id(product_id)
        finally:
            await self.wi.client.close()

    async def get_search_results(self, product_id: str) -> List[Dict[str, Any]]:
        await self.wi.client.connect()
        try:
            return await self.wi.product_search_result_service.get_by_product_id(product_id)
        finally:
            await self.wi.client.close()

    async def get_relevant_chunks(self, product_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        await self.wi.client.connect()
        try:
            return await self.wi.product_data_chunk_service.semantic_search(
                query=query, product_id=product_id, limit=limit
            )
        finally:
            await self.wi.client.close()

    async def delete_product_data(self, product_id: str) -> None:
        await self.wi.client.connect()
        try:
            await self.wi.raw_product_data_service.delete_by_product_id(product_id)
            await self.wi.product_search_result_service.delete_by_product_id(product_id)
            await self.wi.product_data_chunk_service.delete_by_product_id(product_id)
        finally:
            await self.wi.client.close()
