from config import Config
from containers import Container
from services.anthropic_service import AnthropicService

container = Container()
container.config.from_dict(Config().model_dump())


def get_session_manager():
    print("FUNCTION NAME: get_session_manager, FILE PATH: backend/dependencies.py")
    return container.session_manager()


def get_message_processor():
    print("FUNCTION NAME: get_message_processor, FILE PATH: backend/dependencies.py")

    return container.message_processor()


def get_socket_handler():
    print("FUNCTION NAME: get_socket_handler, FILE PATH: backend/dependencies.py")

    return container.socket_handler()


def get_weaviate_service():
    print("FUNCTION NAME: get_weaviate_service, FILE PATH: backend/dependencies.py")

    return container.weaviate_service()


def get_feature_extraction_service():
    print("FUNCTION NAME: get_feature_extraction_service, FILE PATH: backend/dependencies.py")

    return container.feature_extraction_service()


def get_batch_feature_extraction_service():
    print("FUNCTION NAME: get_batch_feature_extraction_service, FILE PATH: backend/dependencies.py")

    return container.batch_feature_extraction_service()


def get_openai_service():
    print("FUNCTION NAME: get_openai_service, FILE PATH: backend/dependencies.py")
    return container.openai_service()


def get_anthropic_service() -> AnthropicService:
    print("FUNCTION NAME: get_anthropic_service, FILE PATH: backend/dependencies.py")
    return container.anthropic_service()
