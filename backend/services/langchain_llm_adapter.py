from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.schema.output import ChatResult, ChatGeneration
from typing import List, Any
from services.openai_service import OpenAIService

class LangchainChatModelAdapter(BaseChatModel):
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service

    @property
    def _llm_type(self) -> str:
        return "custom-openai-adapter"

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: List[str] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Transform LangChain message objects into OpenAI dicts
        formatted_msgs = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "user"
            formatted_msgs.append({"role": role, "content": msg.content})

        content, input_tokens, output_tokens = await self.openai_service.create_chat_completion(
            messages=formatted_msgs,
            **kwargs,
        )

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))],
        )
