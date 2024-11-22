import json
import logging
import datetime
from generators.llm_router import LLMRouter
from generators.dynamic_agent import DynamicAgent
from generators.hybrid_router import HybridRouter
from generators.semantic_router import SemanticRouter
from .models.message import Message, ResponseMessage
from services.anthropic_service import AnthropicService

logger = logging.getLogger(__name__)


class MessageProcessor:

    def __init__(
        self,
        llm_router: LLMRouter,
        semantic_router: SemanticRouter,
        hybrid_router: HybridRouter,
        dynamic_agent: DynamicAgent,
    ):
        self.llm_router = llm_router
        self.semantic_router = semantic_router
        self.hybrid_router = hybrid_router
        self.dynamic_agent = dynamic_agent

    async def process_message(self, message: Message) -> ResponseMessage:
        # Validate model choice
        if message.model.startswith(("gpt-", "text-")):
            service_type = "openai"
        elif message.model.startswith("claude-"):
            service_type = "anthropic"
        else:
            raise ValueError(f"Unsupported model: {message.model}")

        if message.architecture_choice == "llm-router":
            response = await self.llm_router.run(message)
        elif message.architecture_choice == "semantic-router":
            response = await self.semantic_router.run(message)
        elif message.architecture_choice == "hybrid-router":
            response = await self.hybrid_router.run(message)
        elif message.architecture_choice == "dynamic-agent":
            response = await self.dynamic_agent.run(message)
        else:
            raise ValueError(f"Unknown architecture choice: {message.architecture_choice}")

        response_message = ResponseMessage(
            session_id=message.session_id,
            id=f"{message.id}_response",
            message=json.dumps(response),
            is_complete=True,
            model=message.model,
            service_type=service_type,
            architecture_choice=message.architecture_choice,
            history_management_choice=message.history_management_choice,
            timestamp=datetime.datetime.now(),
        )
        return response_message
