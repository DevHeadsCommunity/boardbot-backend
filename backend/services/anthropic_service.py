import logging
from anthropic import AsyncAnthropic
from typing import List, Optional, Tuple, Dict, Any
from services.utils.enhanced_error_logger import create_error_logger
from config import Config

logger = logging.getLogger(__name__)
logger.error = create_error_logger(logger)

class AnthropicService:
    def __init__(self, api_key: str, config: Config):
        self.api_key = api_key
        self.config = config
        self.client = None

    async def initialize(self):
        await self.connect()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self):
        if self.client is None:
            self.client = AsyncAnthropic(api_key=self.api_key)
        logger.debug("Anthropic client connected.")

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None
        logger.debug("Anthropic client closed.")

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
    ) -> Tuple[str, int, int]:
        if self.client is None:
            await self.connect()
        try:
            model = model or self.config.DEFAULT_ANTHROPIC_MODEL
            
            # Convert OpenAI-style messages to Anthropic format
            system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            messages_text = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    continue
                role = "Assistant" if msg["role"] == "assistant" else "Human"
                messages_text += f"\n\n{role}: {msg['content']}"
            
            if system_message:
                messages_text = f"System: {system_message}{messages_text}"

            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": messages_text}],
                "temperature": temperature or self.config.DEFAULT_TEMPERATURE,
                "max_tokens": max_tokens or self.config.DEFAULT_MAX_TOKENS,
                "top_p": top_p or self.config.DEFAULT_TOP_P,
                "stream": stream,
            }

            response = await self.client.messages.create(**kwargs)

            content = response.content[0].text
            # Note: Anthropic doesn't provide token counts directly
            # You might want to implement your own token counting if needed
            input_token_count = 0  # Placeholder
            output_token_count = 0  # Placeholder

            return content, input_token_count, output_token_count

        except Exception as e:
            logger.error(f"Error in Anthropic API call: {str(e)}")
            raise

    async def generate_response(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        formatted_chat_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> Tuple[str, int, int]:
        messages = self._prepare_messages(user_message, system_message, formatted_chat_history)
        logger.info(f"\n\n\nMessages: {messages}\n\n\n")
        return await self.create_chat_completion(messages, **kwargs)

    def _prepare_messages(
        self,
        user_message: str,
        system_message: Optional[str],
        formatted_chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        if formatted_chat_history and isinstance(formatted_chat_history, list):
            messages.extend(formatted_chat_history)

        messages.append({"role": "user", "content": user_message})
        return messages 