from config import Config
from containers import Container
from services.anthropic_service import AnthropicService

container = Container()
container.config.from_dict(Config().model_dump())


def get_session_manager():
    return container.session_manager()


def get_message_processor():
    return container.message_processor()


def get_socket_handler():
    return container.socket_handler()


def get_weaviate_service():
    return container.weaviate_service()


def get_feature_extraction_service():
    return container.feature_extraction_service()


def get_batch_feature_extraction_service():
    return container.batch_feature_extraction_service()


def get_openai_service():
    return container.openai_service()


def get_anthropic_service() -> AnthropicService:
    return container.anthropic_service()
