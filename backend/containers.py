from dependency_injector import containers, providers
from prompts.prompt_manager import PromptManager
from core.session_manager import SessionManager
from core.message_processor import MessageProcessor
from services.openai_service import OpenAIService
from services.tavily_service import TavilyService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from generators.llm_router import LLMRouter
from generators.dynamic_agent import DynamicAgent
from generators.hybrid_router import HybridRouter
from generators.semantic_router import SemanticRouter
from generators.clear_intent_agent import ClearIntentAgent
from generators.vague_intent_agent import VagueIntentAgent
from feature_extraction import AgenticFeatureExtractor, ConfigSchema


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    prompt_manager = providers.Singleton(PromptManager)
    session_manager = providers.Singleton(SessionManager)
    openai_service = providers.Singleton(OpenAIService, api_key=config.OPENAI_API_KEY, config=config)
    tavily_service = providers.Singleton(TavilyService, api_key=config.TAVILY_API_KEY)

    weaviate_service = providers.Singleton(
        WeaviateService,
        openai_key=config.OPENAI_API_KEY,
        weaviate_url=config.WEAVIATE_URL,
    )

    query_processor = providers.Singleton(
        QueryProcessor,
        openai_service=openai_service,
        prompt_manager=prompt_manager,
    )

    clear_intent_agent = providers.Singleton(
        ClearIntentAgent,
        openai_service=openai_service,
        prompt_manager=prompt_manager,
        query_processor=query_processor,
        weaviate_service=weaviate_service,
    )

    vague_intent_agent = providers.Singleton(
        VagueIntentAgent,
        openai_service=openai_service,
        prompt_manager=prompt_manager,
        query_processor=query_processor,
        weaviate_service=weaviate_service,
    )

    llm_router = providers.Singleton(
        LLMRouter,
        session_manager=session_manager,
        openai_service=openai_service,
        weaviate_service=weaviate_service,
        clear_intent_agent=clear_intent_agent,
        vague_intent_agent=vague_intent_agent,
        prompt_manager=prompt_manager,
    )

    semantic_router = providers.Singleton(
        SemanticRouter,
        session_manager=session_manager,
        openai_service=openai_service,
        weaviate_service=weaviate_service,
        clear_intent_agent=clear_intent_agent,
        vague_intent_agent=vague_intent_agent,
        prompt_manager=prompt_manager,
    )

    hybrid_router = providers.Singleton(
        HybridRouter,
        session_manager=session_manager,
        openai_service=openai_service,
        weaviate_service=weaviate_service,
        clear_intent_agent=clear_intent_agent,
        vague_intent_agent=vague_intent_agent,
        prompt_manager=prompt_manager,
    )

    dynamic_agent = providers.Singleton(
        DynamicAgent,
        session_manager=session_manager,
        openai_service=openai_service,
        weaviate_service=weaviate_service,
        query_processor=query_processor,
        prompt_manager=prompt_manager,
    )

    message_processor = providers.Singleton(
        MessageProcessor,
        llm_router=llm_router,
        semantic_router=semantic_router,
        hybrid_router=hybrid_router,
        dynamic_agent=dynamic_agent,
    )

    agentic_feature_extractor = providers.Singleton(
        AgenticFeatureExtractor,
        openai_service=openai_service,
        tavily_service=tavily_service,
        prompt_manager=prompt_manager,
    )

    agentic_feature_extractor = providers.Singleton(
        AgenticFeatureExtractor,
        services={
            "openai_service": openai_service,
            "tavily_service": tavily_service,
            "weaviate_service": weaviate_service,
        },
        prompt_manager=prompt_manager,
        config=ConfigSchema(),
    )
