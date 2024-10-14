import json
import logging
import time
from typing import Any, Dict, List, Tuple
from core.session_manager import SessionManager
from core.models.message import Message
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from .utils.response_formatter import ResponseFormatter
from generators.clear_intent_agent import ClearIntentAgent
from generators.vague_intent_agent import VagueIntentAgent

logger = logging.getLogger(__name__)


class BaseRouter:
    def __init__(
        self,
        session_manager: SessionManager,
        openai_service: OpenAIService,
        weaviate_service: WeaviateService,
        clear_intent_agent: ClearIntentAgent,
        vague_intent_agent: VagueIntentAgent,
        prompt_manager: PromptManager,
    ):
        self.session_manager = session_manager
        self.openai_service = openai_service
        self.weaviate_service = weaviate_service
        self.clear_intent_agent = clear_intent_agent
        self.vague_intent_agent = vague_intent_agent
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()

    async def run(self, message: Message) -> Dict[str, Any]:
        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )
        classification, input_tokens, output_tokens, time_taken = await self.determine_route(
            message, chat_history  # Pass as list of dicts
        )
        response = await self.handle_route(
            classification, message, chat_history, input_tokens, output_tokens, time_taken
        )
        return response

    async def determine_route(
        self,
        message: Message,
        chat_history: List[Dict[str, str]],
    ) -> Tuple[Dict[str, Any], int, int, float]:
        raise NotImplementedError("Subclasses must implement determine_route method")

    async def handle_route(
        self,
        classification: Dict[str, Any],
        message: Message,
        chat_history: List[Dict[str, str]],
        input_tokens: int,
        output_tokens: int,
        time_taken: float,
    ) -> Dict[str, Any]:
        route = classification["category"]
        confidence = classification["confidence"]

        base_metadata = {
            "classification_result": classification,
            "input_token_usage": {"classification": input_tokens},
            "output_token_usage": {"classification": output_tokens},
            "time_taken": {"classification": time_taken},
        }

        if confidence < 50:
            return await self.handle_low_confidence_query(message, chat_history, classification, base_metadata)

        route_handlers = {
            "politics": self.handle_politics,
            "chitchat": self.handle_chitchat,
            "vague_intent_product": self.handle_vague_intent,
            "clear_intent_product": self.handle_clear_intent,
            "do_not_respond": self.handle_do_not_respond,
        }

        handler = route_handlers.get(route, self.handle_unknown_route)
        return await handler(message, chat_history, base_metadata)

    async def handle_low_confidence_query(
        self,
        message: Message,
        chat_history: List[Dict[str, str]],
        classification: Dict[str, Any],
        base_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_low_confidence_prompt(message.message, classification)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=message.model,
        )

        base_metadata["input_token_usage"]["generate"] = input_tokens
        base_metadata["output_token_usage"]["generate"] = output_tokens
        base_metadata["time_taken"]["generate"] = time.time() - start_time

        return self.response_formatter.format_response("low_confidence", response, base_metadata)

    async def handle_politics(
        self, message: Message, chat_history: List[Dict[str, str]], base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self.response_formatter.format_response(
            "politics",
            json.dumps(
                {
                    "message": "I'm sorry, but I don't discuss politics.",
                    "follow_up_question": "Can I help you with anything related to computer hardware?",
                }
            ),
            base_metadata,
        )

    async def handle_chitchat(
        self, message: Message, chat_history: List[Dict[str, str]], base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_chitchat_prompt(message.message)
        print("system_message", system_message)
        print("user_message", user_message)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=message.model,
        )

        base_metadata["input_token_usage"]["generate"] = input_tokens
        base_metadata["output_token_usage"]["generate"] = output_tokens
        base_metadata["time_taken"]["generate"] = time.time() - start_time

        return self.response_formatter.format_response("chitchat", response, base_metadata)

    async def handle_vague_intent(
        self, message: Message, chat_history: List[Dict[str, str]], base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = await self.vague_intent_agent.run(message, chat_history)

        base_metadata["filters"] = response["filters"]
        base_metadata["input_token_usage"].update(response["input_tokens"])
        base_metadata["output_token_usage"].update(response["output_tokens"])
        base_metadata["time_taken"].update(response["time_taken"])

        return self.response_formatter.format_response(
            "vague_intent_product", response["output"], base_metadata, response["search_results"]
        )

    async def handle_clear_intent(
        self, message: Message, chat_history: List[Dict[str, str]], base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = await self.clear_intent_agent.run(message, chat_history)

        base_metadata["filters"] = response["filters"]
        base_metadata["input_token_usage"].update(response["input_tokens"])
        base_metadata["output_token_usage"].update(response["output_tokens"])
        base_metadata["time_taken"].update(response["time_taken"])

        return self.response_formatter.format_response(
            "clear_intent_product", response["output"], base_metadata, response["search_results"]
        )

    async def handle_do_not_respond(self, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        return self.response_formatter.format_response(
            "do_not_respond",
            json.dumps(
                {
                    "message": "I'm sorry, but I can't help with that type of request.",
                    "follow_up_question": "Is there anything related to computer hardware that I can assist you with?",
                }
            ),
            base_metadata,
        )

    async def handle_unknown_route(self, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        logger.error(f"Unknown route encountered: {base_metadata['classification_result']['category']}")
        return self.response_formatter.format_error_response("An error occurred while processing your request.")
