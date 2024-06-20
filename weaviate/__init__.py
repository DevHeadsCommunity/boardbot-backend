import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
from .weaviate_interface import WeaviateInterface

load_dotenv()


async def setup_weaviate_interface_async() -> WeaviateInterface:
    openai_key = os.getenv("OPENAI_API_KEY")
    weaviate_url = os.getenv("WEAVIATE_URL", "http://0.0.0.0:8080")
    schema_file = "./weaviate/schema.json"

    if not openai_key or not weaviate_url:
        raise Exception("Missing OPENAI_API_KEY or WEAVIATE_URL")

    weaviate_interface = WeaviateInterface(weaviate_url, openai_key, schema_file)
    await weaviate_interface.async_init()
    return weaviate_interface


def setup_weaviate_interface():
    loop = asyncio.get_event_loop()
    if loop.is_running():
        task = asyncio.create_task(setup_weaviate_interface_async())
        return task
    else:
        return loop.run_until_complete(setup_weaviate_interface_async())


async def initialize_weaviate():
    reset = False
    weaviate_interface = await setup_weaviate_interface()
    if not (await weaviate_interface.schema.is_valid()) or reset:
        await weaviate_interface.schema.reset()

        # Load and insert products data
        products = pd.read_csv("data/clean_products.csv")
        products = products.drop(columns=["raw_data", "id", "raw_length"])
        products_data = products.to_dict(orient="records")

        # loop through the products in batches of 20
        for i in range(0, len(products_data), 20):
            try:
                await weaviate_interface.product.batch_upsert(products_data[i : i + 20])
            except Exception as e:
                print(f"Error inserting products at index {i}: {e}")

        chitchat_data = pd.read_csv("data/chitchat.csv")
        chitchat_prompts = chitchat_data["prompt"].tolist()

        political_data = pd.read_csv("data/politics.csv")
        political_prompts = political_data["prompt"].tolist()

        clear_intent_data = pd.read_csv("data/clear_intent.csv")
        clear_intent_prompts = clear_intent_data["prompt"].tolist()

        vague_intent_data = pd.read_csv("data/vague_intent.csv")
        vague_intent_prompts = vague_intent_data["prompt"].tolist()

        # Load and insert routes data
        routes_data = {
            "politics": political_prompts,
            "chitchat": chitchat_prompts,
            "clear_intent_product": clear_intent_prompts,
            "vague_intent_product": vague_intent_prompts,
        }

        for route, prompts in routes_data.items():
            route_data = [{"prompt": message, "route": route} for message in prompts]
            await weaviate_interface.route.batch_upsert(route_data)

    is_valid = await weaviate_interface.schema.is_valid()
    info = await weaviate_interface.schema.info()
    print(f" Weaviate schema is valid: {is_valid}")
    print(f" Weaviate schema info: {info}")

    return weaviate_interface
