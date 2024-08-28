import logging
import weaviate
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from weaviate.weaviate_interface import WeaviateInterface


logger = logging.getLogger(__name__)
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


class WeaviateService:
    def __init__(self):
        self.wi = None

    async def initialize_weaviate(self, openai_key: str, weaviate_url: str, reset: bool = False) -> WeaviateInterface:
        print("===:> Initializing Weaviate")
        weaviate_interface = await weaviate.setup_weaviate_interface(openai_key, weaviate_url)
        if not (await weaviate_interface.schema.is_valid()) or reset:
            await weaviate_interface.schema.reset()

            # Load and insert products data
            products = pd.read_csv("data/extracted_data_grouped.csv")
            # products = products.drop(columns=["raw_data", "id", "raw_length"])
            products_data = products.to_dict(orient="records")

            # loop through the products in batches of 20
            for i in range(0, len(products_data), 20):
                try:
                    await weaviate_interface.product.batch_upsert(products_data[i : i + 20])
                except Exception as e:
                    print(f"Error inserting products at index {i}: {e}")

            for route, descriptions in route_descriptions.items():
                route_data = [
                    {
                        "route": route,
                        "description": desc,
                    }
                    for desc in descriptions
                ]
                await weaviate_interface.route.batch_upsert(route_data)

        is_valid = await weaviate_interface.schema.is_valid()
        info = await weaviate_interface.schema.info()
        logging.info(f" Weaviate schema is valid: {is_valid}")
        logging.info(f" Weaviate schema info: {info}")

        self.wi = weaviate_interface

    async def search_routes(self, query: str) -> List[Tuple[str, float]]:
        routes = await self.wi.route.search(query, ["route"], limit=1)
        # print(f"Found routes: {routes}")
        return routes

    async def search_products(self, query: str, limit: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        try:
            products = await self.wi.product.search(query, limit=limit)
            # logger.info(f"Found products: {products}")
            return products
        except Exception as e:
            print(f"Error in Weaviate search: {str(e)}")
            raise

    async def get_all_products(self) -> List[Dict[str, Any]]:
        return await self.wi.product.get_all()

    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        return await self.wi.product.get(product_id)

    async def add_product(self, product_data: Dict[str, Any]) -> str:
        return await self.wi.product.upsert(product_data)

    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        return await self.wi.product.update(product_id, product_data)

    async def delete_product(self, product_id: str) -> bool:
        return await self.wi.product.delete(product_id)
