from dependency_injector import containers, providers
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from services.tavily_service import TavilyService
from core.session_manager import SessionManager
from core.message_processor import MessageProcessor
from generators.agent_v1 import AgentV1
from generators.agent_v2 import AgentV2
from generators.semantic_router_v1 import SemanticRouterV1
from generators.semantic_router_v2 import SemanticRouterV2
from services.query_processor import QueryProcessor
from services.feature_extractor_agent_v2 import FeatureExtractor


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    prompt_manager = providers.Singleton(PromptManager)

    openai_service = providers.Singleton(OpenAIService, api_key=config.OPENAI_API_KEY, config=config)

    weaviate_service = providers.Singleton(WeaviateService)

    tavily_service = providers.Singleton(TavilyService, api_key=config.TAVILY_API_KEY)

    query_processor = providers.Singleton(QueryProcessor, openai_service=openai_service, prompt_manager=prompt_manager)

    session_manager = providers.Singleton(SessionManager)

    agent_v1 = providers.Singleton(
        AgentV1,
        weaviate_service=weaviate_service,
        query_processor=query_processor,
        openai_service=openai_service,
        prompt_manager=prompt_manager,
    )

    agent_v2 = providers.Singleton(
        AgentV2, weaviate_service=weaviate_service, tavily_service=tavily_service, openai_service=openai_service
    )

    semantic_router_v1 = providers.Singleton(
        SemanticRouterV1, openai_service=openai_service, weaviate_service=weaviate_service, agent_v1=agent_v1
    )

    semantic_router_v2 = providers.Singleton(
        SemanticRouterV2,
        openai_service=openai_service,
        weaviate_service=weaviate_service,
        agent_v1=agent_v1,
        prompt_manager=prompt_manager,
    )

    message_processor = providers.Singleton(
        MessageProcessor,
        semantic_router_v1=semantic_router_v1,
        semantic_router_v2=semantic_router_v2,
        agent_v1=agent_v1,
        agent_v2=agent_v2,
    )

    feature_extractor = providers.Singleton(
        FeatureExtractor, openai_service=openai_service, tavily_service=tavily_service
    )
