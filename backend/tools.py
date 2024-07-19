from langchain.tools import tool
from weaviate.weaviate_interface import WeaviateInterface

wi: WeaviateInterface = None


def initialize_weaviate(weaviate_interface: WeaviateInterface):
    global wi
    wi = weaviate_interface


@tool("product_search", return_direct=True)
async def product_search(message: str, limit: int) -> str:
    """Search for products in Weaviate vector search"""
    features = ["name", "size", "form", "processor", "memory", "io", "manufacturer", "summary"]
    context = await wi.product.search(message, features, limit)
    return context
