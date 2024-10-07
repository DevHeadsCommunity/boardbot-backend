from .weaviate_interface import WeaviateInterface
from .models.product import NewProduct, Product, attribute_descriptions
from .models.route import route_descriptions

__all__ = ["WeaviateInterface", "NewProduct", "Product", "attribute_descriptions", "route_descriptions"]
