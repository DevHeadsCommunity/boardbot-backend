from typing import List
from weaviate_interface.services.base_service import BaseService
from weaviate_interface.weaviate_client import WeaviateClient


class RouteService(BaseService):
    """
    Service for interacting with Route objects in Weaviate.
    """

    def __init__(self, client: WeaviateClient):
        super().__init__(client, "Route")

    def get_properties(self) -> List[str]:
        return [
            "route",
            "description",
        ]
