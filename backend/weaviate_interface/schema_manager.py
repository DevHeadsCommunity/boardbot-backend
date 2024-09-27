import logging
from typing import Any, Dict, List
from weaviate_interface.weaviate_client import WeaviateClient
from weaviate.classes.config import Property

logger = logging.getLogger(__name__)


class SchemaManager:
    def __init__(self, client: WeaviateClient, schema: Dict[str, Any]):
        self.client = client
        self.schema = schema

    async def is_valid(self) -> bool:
        try:
            existing_collections = await self.client.get_schema()
            expected_classes = {cls["class"] for cls in self.schema.get("classes", [])}

            if set(existing_collections.keys()) != expected_classes:
                logger.info(f"Class mismatch: existing {set(existing_collections.keys())}, expected {expected_classes}")
                return False

            for class_config in self.schema.get("classes", []):
                class_name = class_config["class"]
                existing_collection = existing_collections[class_name]

                if not self._compare_properties(existing_collection.properties, class_config["properties"]):
                    logger.info(f"Property mismatch for {class_name}")
                    return False

                if not self._compare_vectorizer_config(
                    existing_collection.vectorizer_config, class_config["vectorizer_config"]
                ):
                    logger.info(f"Vectorizer config mismatch for {class_name}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error validating schema: {e}")
            return False

    def _compare_properties(self, existing_props: List[Property], expected_props: List[Property]) -> bool:
        if len(existing_props) != len(expected_props):
            return False

        for existing, expected in zip(existing_props, expected_props):
            if (
                existing.name != expected.name
                or existing.data_type != expected.dataType
                or existing.index_filterable != expected.indexFilterable
                or existing.index_searchable != expected.indexSearchable
                or existing.tokenization != expected.tokenization
            ):
                logger.info(f"Mismatch in property {existing.name}")
                return False
        return True

    def _compare_vectorizer_config(self, existing_config: Any, expected_config: Any) -> bool:
        return existing_config.vectorizer == expected_config.vectorizer

    async def reset_schema(self) -> None:
        try:
            await self.client.delete_all_collections()

            for class_config in self.schema.get("classes", []):
                await self.client.create_collection(
                    name=class_config["class"],
                    description=class_config["description"],
                    properties=class_config["properties"],
                    vectorizer_config=class_config.get("vectorizer_config"),
                    generative_config=class_config.get("generative_config"),
                )

            logger.info("Schema reset successfully")
        except Exception as e:
            logger.error(f"Error resetting schema: {e}")
            raise

    async def info(self) -> str:
        try:
            schema = await self.client.get_schema()
            info_lines = ["Weaviate Schema Information:", ""]

            for class_name, class_info in schema.items():
                count = await self._get_class_count(class_name)

                info_lines.append(f"Class: {class_name}")
                info_lines.append(f"  Object Count: {count}")

                info_lines.append("  Properties:")
                for prop in class_info.properties:
                    info_lines.append(f"    - {prop.name} (Type: {prop.data_type}) - {prop.description}")

                info_lines.append(f"  Vectorizer: {class_info.vectorizer}")
                info_lines.append("")

            return "\n".join(info_lines)
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return f"Error retrieving schema information: {str(e)}"

    async def _get_class_count(self, class_name: str) -> int:
        try:
            result = await self.client.aggregate(class_name)
            return result.total_count
        except Exception as e:
            logger.error(f"Error getting count for class {class_name}: {e}")
            return 0

    async def initialize_schema(self) -> None:
        try:
            if not await self.is_valid():
                await self.reset_schema()
                logger.info("Schema initialized successfully")
            else:
                logger.info("Schema is valid, no initialization needed")
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise
