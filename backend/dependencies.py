from containers import Container
from config import Config

container = Container()
container.config.from_dict(Config().dict())


def get_session_manager():
    return container.session_manager()


async def get_message_processor():
    return container.message_processor()


def get_weaviate_service():
    return container.weaviate_service()


def get_agentic_feature_extractor():
    return container.agentic_feature_extractor()


graph = container.dynamic_agent().workflow
