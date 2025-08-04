from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.schema.output import ChatResult, ChatGeneration
from typing import List, Any
import asyncio
from .openai_service import OpenAIService


class LangchainChatModelAdapter(BaseChatModel):
    def __init__(self, openai_service, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'openai_service', openai_service)

    @property
    def _llm_type(self) -> str:
        print("🧭 FUNCTION NAME: _llm_type, FILE_NAME: backend/services/langchain_llm_adapter.py")
        return "custom-openai-adapter"

    def _format_messages(self, messages: List[BaseMessage]) -> List[dict]:
        print("🧭 FUNCTION NAME: _format_messages, FILE_NAME: backend/services/langchain_llm_adapter.py")
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
        return formatted_msgs

    async def _agenerate(
            self,
            messages: List[BaseMessage],
            stop: List[str] = None,
            run_manager: Any = None,
            **kwargs: Any,
    ) -> ChatResult:
        print("🧭 FUNCTION NAME: _agenerate, FILE_NAME: backend/services/langchain_llm_adapter.py")
        formatted_msgs = self._format_messages(messages)
        content, input_tokens, output_tokens = await self.openai_service.create_chat_completion(
            messages=formatted_msgs,
            **kwargs,
        )
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )

    # async def _generate(
    #     self,
    #     messages: List[BaseMessage],
    #     stop: List[str] = None,
    #     run_manager: Any = None,
    #     **kwargs: Any,
    # ) -> ChatResult:
    #     formatted_msgs = self._format_messages(messages)
    #     content, input_tokens, output_tokens = await self.openai_service.create_chat_completion(
    #         messages=formatted_msgs,
    #         **kwargs,
    #     )
    #     return ChatResult(
    #         generations=[ChatGeneration(message=AIMessage(content=content))]
    #     )

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: List[str] = None,
            run_manager: Any = None,
            **kwargs: Any,
    ) -> ChatResult:
        print("🧭 FUNCTION NAME: _generate, FILE_NAME: backend/services/langchain_llm_adapter.py")
        formatted_msgs = self._format_messages(messages)

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # This handles nested event loops, e.g., in Jupyter
            content, input_tokens, output_tokens = asyncio.ensure_future(
                self.openai_service.create_chat_completion(messages=formatted_msgs, **kwargs)
            ).result()
        else:
            content, input_tokens, output_tokens = loop.run_until_complete(
                self.openai_service.create_chat_completion(messages=formatted_msgs, **kwargs)
            )

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )
