import asyncio
from dotenv import load_dotenv
from .weaviate_interface import WeaviateInterface

load_dotenv()


async def setup_weaviate_interface_async(openai_key: str, weaviate_url: str) -> WeaviateInterface:
    schema_file = "./weaviate/schema.json"

    if not openai_key or not weaviate_url:
        raise Exception("Missing OPENAI_API_KEY or WEAVIATE_URL")

    weaviate_interface = WeaviateInterface(weaviate_url, openai_key, schema_file)
    await weaviate_interface.async_init()
    return weaviate_interface


def setup_weaviate_interface(openai_key: str, weaviate_url: str) -> WeaviateInterface:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        task = asyncio.create_task(setup_weaviate_interface_async(openai_key, weaviate_url))
        return task
    else:
        return loop.run_until_complete(setup_weaviate_interface_async(openai_key, weaviate_url))
