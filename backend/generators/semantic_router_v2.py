import json
import logging
import time
from typing import Any, Dict, List
from backend.models.product import Product
from models.message import Message
from generators.agent_v1 import AgentV1
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService

logger = logging.getLogger(__name__)


class SemanticRouterV2:
    def __init__(
        self,
        openai_service: OpenAIService,
        weaviate_service: WeaviateService,
        agent_v1: AgentV1,
    ):
        self.openai_service = openai_service
        self.weaviate_service = weaviate_service
        self.agent_v1 = agent_v1

    async def run(self, message: Message, chat_history: List[Dict[str, str]]):
        classification, input_tokens, output_tokens, time_taken = await self.determine_route(
            message.content, chat_history
        )
        return await self.handle_route(classification, message, chat_history, input_tokens, output_tokens, time_taken)

    async def determine_route(self, query: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        start_time = time.time()
        system_message = """
        You are a routing assistant for a specialized product information system focusing on computer hardware, particularly embedded systems, development kits, and industrial communication devices. Your task is to categorize the given query, considering the current query and recent chat history, into one of the following categories:

        1. politics - for queries related to political topics.
        2. chitchat - for general conversation or small talk.
        3. vague_intent_product - for product-related queries that are general or lack specific criteria.
        4. clear_intent_product - for product-related queries with specific criteria or constraints.
        5. do_not_respond - for queries that are inappropriate, offensive, or outside the system's scope.

        Provide your classification along with a brief justification and a confidence score (0-100).

        Respond in JSON format as follows:
        {
            "category": "category_name",
            "justification": "A brief explanation for this classification",
            "confidence": 85
        }

        Guidelines and examples:
        - clear_intent_product: Queries with specific criteria about products.
        Examples:
            - "Find me a board with an Intel processor and at least 8GB of RAM"
            - "List Single Board Computers with a processor frequency of 1.5 GHz or higher"
            - "What are the top 5 ARM-based development kits with built-in Wi-Fi?"

        - vague_intent_product: General product queries without specific criteria.
        Examples:
            - "Tell me about single board computers"
            - "What are some good development kits?"
            - "I'm looking for industrial communication devices"

        - If a query contains any clear product-related intent or specific criteria, classify it as clear_intent_product, regardless of other elements in the query.
        - Consider the chat history when making your classification. A vague query might become clear in the context of previous messages.
        - Classify as politics only if the query is primarily about political topics.
        - Use do_not_respond for queries that are inappropriate, offensive, or completely unrelated to computer hardware and embedded systems.
        - Be decisive - always choose the most appropriate category even if the query is ambiguous.
        """

        # Format the chat history, including only the last 5 user messages
        formatted_history = "\n".join([f"User: {msg['content']}" for msg in chat_history[-5:] if msg["role"] == "user"])

        user_message = f"""
        Chat History:
        {formatted_history}

        Current Query: {query}

        Please categorize the current query, taking into account the chat history provided above.
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model="gpt-4o"
        )

        logging.info(f"===:> Route determined: {response}")

        classification = self._clean_response(response)
        return classification, input_tokens, output_tokens, time.time() - start_time

    async def handle_route(
        self,
        classification: Dict[str, Any],
        message: Message,
        chat_history: List[Dict[str, str]],
        input_tokens: int,
        output_tokens: int,
        time_taken: float,
    ):
        route = classification["category"]
        confidence = classification["confidence"]
        justification = classification["justification"]

        if confidence < 50:
            response = await self.handle_low_confidence_query(message, chat_history, classification)
            response["metadata"]["input_token_usage"]["classification"] = input_tokens
            response["metadata"]["output_token_usage"]["classification"] = output_tokens
            response["metadata"]["time_taken"]["classification"] = time_taken
            return response

        if route == "politics":
            return {
                "type": "politics",
                "message": "I'm sorry, but I don't discuss politics.",
                "products": [],
                "reasoning": justification,
                "follow_up_question": "Can I help you with anything else?",
                "metadata": {
                    "classification_result": {
                        "confidence": confidence,
                    }
                },
                "input_token_usage": {
                    "classification": input_tokens,
                },
                "output_token_usage": {
                    "classification": output_tokens,
                },
                "time_taken": {
                    "classification": time_taken,
                },
            }

        elif route == "chitchat":
            response = await self.handle_chitchat(message, chat_history)
            response["metadata"]["classification_result"] = {
                "confidence": confidence,
                "justification": justification,
            }
            response["metadata"]["input_token_usage"]["classification"] = input_tokens
            response["metadata"]["output_token_usage"]["classification"] = output_tokens
            response["metadata"]["time_taken"]["classification"] = time_taken
            return response

        elif route == "vague_intent_product":
            response = await self.handle_vague_intent(message, chat_history)
            response["metadata"]["classification_result"] = {
                "confidence": confidence,
                "justification": justification,
            }
            response["metadata"]["input_token_usage"]["classification"] = input_tokens
            response["metadata"]["output_token_usage"]["classification"] = output_tokens
            response["metadata"]["time_taken"]["classification"] = time_taken
            return response

        elif route == "clear_intent_product":
            response = await self.agent_v1.run(message, chat_history)
            response["metadata"]["classification_result"] = {
                "confidence": confidence,
                "justification": justification,
            }
            response["metadata"]["input_token_usage"]["classification"] = input_tokens
            response["metadata"]["output_token_usage"]["classification"] = output_tokens
            response["metadata"]["time_taken"]["classification"] = time_taken
            return response

        elif route == "do_not_respond":
            return {
                "type": "do_not_respond",
                "message": "I'm sorry, but I can't help with that.",
                "products": [],
                "reasoning": justification,
                "follow_up_question": "Can I help you with anything else?",
                "metadata": {
                    "classification_result": {
                        "confidence": confidence,
                    }
                },
                "input_token_usage": {
                    "classification": input_tokens,
                },
                "output_token_usage": {
                    "classification": output_tokens,
                },
                "time_taken": {
                    "classification": time_taken,
                },
            }
        else:
            raise Exception(f"Unknown route: {route}")

    async def handle_low_confidence_query(
        self, message: Message, chat_history: List[Dict[str, str]], classification: Dict[str, Any]
    ):
        start_time = time.time()
        system_message = self._get_low_confidence_system_message()

        user_message = f"""
            User Query: {message.content}

            Chat History:
                {json.dumps(chat_history, indent=2)}

            Classification result:
                Category: {classification['category']}
                Confidence: {classification['confidence']}
                Justification: {classification['justification']}

        Please provide a response that acknowledges the uncertainty and asks for clarification from the user.
        """
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=message.model,
        )
        return {
            "type": "low_confidence",
            "message": response["message"],
            "products": [],
            "reasoning": response["reasoning"],
            "follow_up_question": response["follow_up_question"],
            "metadata": {
                "classification_result": classification,
            },
            "input_token_usage": {
                "generate": input_tokens,
            },
            "output_token_usage": {
                "generate": output_tokens,
            },
            "time_taken": {
                "generate": time.time() - start_time,
            },
        }

    async def handle_chitchat(self, message: Message, chat_history: List[Dict[str, str]]):
        start_time = time.time()
        system_message = self._get_chitchat_system_message()

        user_message = f"""
            User Query: {message.content}

            Chat History:
                {json.dumps(chat_history, indent=2)}
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=message.model,
        )
        return {
            "type": "chitchat",
            "message": response["response"],
            "products": [],
            "follow_up_question": response["follow_up_question"],
            "metadata": {},
            "input_token_usage": {
                "generate": input_tokens,
            },
            "output_token_usage": {
                "generate": output_tokens,
            },
            "time_taken": {
                "generate": time.time() - start_time,
            },
        }

    async def handle_vague_intent(self, message: Message, chat_history: List[Dict[str, str]]):
        start_time = time.time()
        search_result = await self.weaviate_service.search_products(message.content)
        products = [Product(**product) for product in search_result]
        system_message = self._get_vague_intent_system_message()

        user_message = f"""
            User Query: {message.content}

            Chat History: {chat_history}

            Relevant Products:
            {json.dumps([{"name": p.name, "summary": p.full_product_description} for p in products], indent=2)}

            Please provide a response that includes the relevant products found, a clear reasoning for the selection, and a follow-up question.
            Ensure that only products that fully match ALL criteria specified in the user's query are included in the final list.
            If no products match ALL criteria, explain why using the information from the reranking result.
            Include a single, clear follow-up question based on the user's query and the products found.
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=message.model,
        )
        return {
            "type": "vague_intent_product",
            "message": response["message"],
            "products": [
                product.__dict__
                for product in products
                if product.name in [p["name"] for p in response.get("products", [])]
            ],
            "reasoning": response["reasoning"],
            "follow_up_question": response["follow_up_question"],
            "metadata": {},
            "input_token_usage": {
                "generate": input_tokens,
            },
            "output_token_usage": {
                "generate": output_tokens,
            },
            "time_taken": {
                "generate": time.time() - start_time,
            },
        }

    def _get_chitchat_system_message(self) -> str:
        return """You are ThroughPut assistant. Your main task is to help users with their queries about products. Always respond in JSON format.
                    The user is engaging in casual conversation with you. Respond naturally and politely to the user's message.
                    Make sure your response is in a JSON format with the following structure:
                    {
                        "response": "Your response to the user's message."
                        "follow_up_question": "A question to keep the conversation going."
                    }
                    """

    def _get_vague_intent_system_message(self) -> str:
        return """You are ThroughPut assistant. Your main task is to help users with their queries about products. Always respond in JSON format.
        Analyze the user's query and the relevant products found, then provide a comprehensive and helpful response.
        Your response should be clear, informative, and directly address the user's query.
        IMPORTANT:
        1. Only include products that FULLY match ALL criteria specified in the user's query.
        2. Pay special attention to the user's query, and the specifications of the products.
        3. Do NOT confuse the processor manufacturer with the product manufacturer. This applies to all attributes.
        4. If no products match ALL criteria, return an empty list of products.
        Always respond in JSON format with the following structure:
            {
                "message": "A concise introductory message addressing the user's query",
                "products": [
                    {
                        "name": "Product Name", // We only need the name of the product
                    },
                    // ... more products if applicable
                ],
                "reasoning": "Clear and concise reasoning for the provided response and product selection",
                "follow_up_question": "A single, clear follow-up question based on the user's query and the products found"
            }
        """

    def _get_low_confidence_system_message(self) -> str:
        return """You are ThroughPut assistant. Your main task is to help users with their queries about products. Always respond in JSON format.
        We classified the user's query into three categories: clear_intent_product, vague_intent_product, and chitchat.
        The system is not confident about how to categorize this query. Provide a response that acknowledges the uncertainty and asks for clarification from the user.
        Always respond in JSON format with the following structure:
            {
                "message": "Your response to the user's message."
                "follow_up_question": "A question to keep the conversation going."
            }
        """

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
