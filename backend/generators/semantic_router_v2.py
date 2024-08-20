import json
import logging
import time
from typing import Any, Dict, List, Tuple
from core.session_manager import SessionManager
from models.message import Message
from models.product import Product
from generators.agent_v1 import AgentV1
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class SemanticRouterV2:

    def __init__(
        self,
        session_manager: SessionManager,
        openai_service: OpenAIService,
        weaviate_service: WeaviateService,
        agent_v1: AgentV1,
        prompt_manager: PromptManager,
    ):
        self.session_manager = session_manager
        self.openai_service = openai_service
        self.weaviate_service = weaviate_service
        self.agent_v1 = agent_v1
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()

    async def run(self, message: Message) -> Tuple[str, Dict[str, int]]:
        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )
        classification, input_tokens, output_tokens, time_taken = await self.determine_route(
            message.content, json.dumps(chat_history)
        )
        response = await self.handle_route(
            classification, message, json.dumps(chat_history), input_tokens, output_tokens, time_taken
        )
        return json.dumps(response, indent=2), {
            "input_token_count": sum(response["input_token_usage"].values()),
            "output_token_count": sum(response["output_token_usage"].values()),
        }

    async def determine_route(
        self, query: str, chat_history: List[Dict[str, str]]
    ) -> Tuple[Dict[str, Any], int, int, float]:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_route_classification_prompt(query, chat_history)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model="gpt-4o"
        )

        classification = self._clean_response(response)
        logger.info(f"Route determined: {classification}")
        return classification, input_tokens, output_tokens, time.time() - start_time

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
        system_message, user_message = self.prompt_manager.get_low_confidence_prompt(
            message.content, chat_history, classification
        )

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

    async def handle_politics(self, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
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
        system_message, user_message = self.prompt_manager.get_chitchat_prompt(message.content, chat_history)

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
        start_time = time.time()
        search_result = await self.weaviate_service.search_products(message.content)
        products = [Product(**product) for product in search_result]

        system_message, user_message = self.prompt_manager.get_vague_intent_product_prompt(
            message.content, chat_history, products
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=message.model,
        )

        base_metadata["input_token_usage"]["generate"] = input_tokens
        base_metadata["output_token_usage"]["generate"] = output_tokens
        base_metadata["time_taken"]["generate"] = time.time() - start_time

        return self.response_formatter.format_response("vague_intent_product", response, base_metadata)

    async def handle_clear_intent(
        self, message: Message, chat_history: List[Dict[str, str]], base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        agent_response, agent_stats = await self.agent_v1.run(message, chat_history)
        agent_response_dict = json.loads(agent_response)

        base_metadata["input_token_usage"].update(agent_stats["input_token_usage"])
        base_metadata["output_token_usage"].update(agent_stats["output_token_usage"])
        base_metadata["time_taken"].update(agent_stats["time_taken"])

        return self.response_formatter.format_response(
            "clear_intent_product", json.dumps(agent_response_dict), base_metadata
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

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            return json.loads(response.replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
