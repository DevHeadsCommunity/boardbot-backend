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
    weaviate_interface = await setup_weaviate_interface()
    await weaviate_interface.schema.reset()

    # Load and insert products data
    products = pd.read_csv("data/clean_products.csv")
    products = products.drop(columns=["raw_data", "id", "raw_length"])
    products_data = products.to_dict(orient="records")
    await weaviate_interface.product.batch_upsert(products_data[:20])

    # Load and insert routes data
    routes_data = {
        "politics": [
            "what do you think about the current political situation?",
            "I hate politics",
            "isn't politics the best thing ever",
            "why don't you tell me about your political opinions",
            "don't you just love the president",
            "don't you just hate the president",
            "they're going to destroy this country!",
            "they will save the country!",
            "I'm going to vote for them",
        ],
        "chitchat": [
            "hello",
            "How are you?",
            "How are you doing today?",
            "What's your favorite color?",
            "What can you do for me?",
            "Who let the dogs out?",
            "What is the purpose of life?",
            "how's the weather today?",
            "how are things going?",
            "lovely weather today",
            "the weather is horrendous",
            "let's go to the chippy",
            "I'm going to the cinema",
        ],
        "clear_Intent_product": [
            "Top 10 Single Board Computers for automotive applications.",
            "5 boards compatible with Linux's Debian distro.",
            "List of 3 computer on modules that work best with cellular connectivity.",
            "20 SBC's that perform better than Raspberry Pi.",
            "Edge AI boards with built-in cryptographic chips that support root-of-trust. Mention any 5.",
        ],
        "vague_Intent_product": [
            "Can you tell me a bit about ICES S series COM express",
            "What is a Single Board Computer?",
            "Best devkits for motor-control applications with high voltage supply.",
            "Advanced single board computers with edge capabilities for ML applications.",
            "Computer on modules with an integrated NPU.",
            "Single board computers with provision of adding camera for computer vision applications",
        ],
    }

    for route, prompts in routes_data.items():
        route_data = [{"prompt": message, "route": route} for message in prompts]
        await weaviate_interface.route.batch_upsert(route_data)

    is_valid = await weaviate_interface.schema.is_valid()
    info = await weaviate_interface.schema.info()
    print(f" Weaviate schema is valid: {is_valid}")
    print(f" Weaviate schema info: {info}")

    return weaviate_interface
