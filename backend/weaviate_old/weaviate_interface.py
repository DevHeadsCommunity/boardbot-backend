from weaviate_old.product_service import ProductService
from weaviate_old.route_service import RouteService
from weaviate_old.schema_manager import SchemaManager
from weaviate_old.weaviate_client import WeaviateClient
from .http_client import HttpClient, HttpHandler


class WeaviateInterface:
    def __init__(self, url: str, openai_key: str, schema_file: str):
        self.http_handler = HttpHandler(HttpClient(url, {"X-OpenAI-Api-Key": openai_key}))
        self.client = WeaviateClient(self.http_handler)
        self.schema = SchemaManager(self.client, schema_file)
        self.product = ProductService(self.client)
        self.route = RouteService(self.client)

    async def async_init(self):
        """
        Asynchronous initialization tasks for WeaviateInterface.
        """
        if not await self.schema.is_valid():
            await self.schema.reset()
