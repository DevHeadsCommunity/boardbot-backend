from generators.agent_v1 import AgentV1
from models.message import Message
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService


class SemanticRouterV1:

    def __init__(
        self,
        openai_service: OpenAIService,
        weaviate_service: WeaviateService,
        agent_v1: AgentV1,
    ):
        self.openai_service = openai_service
        self.weaviate_service = weaviate_service
        self.agent_v1 = agent_v1

    async def run(self, message: Message, chat_history: list[Message]):
        route = await self.determine_route(message.content)
        return await self.handle_route(route, message, chat_history)

    async def determine_route(self, query: str) -> str:
        routes = await self.weaviate_service.search_routes(query)
        if not routes:
            raise Exception(f"No route found for query: {query}")
        print(f"Found routes: {routes}")
        return routes

    async def handle_route(self, route: str, message: Message, chat_history: list[Message]):
        if route == "politics":
            return '{"message": "I\'m sorry, I\'m not programmed to discuss politics."}', {
                "input_token_count": 0,
                "output_token_count": 0,
            }
        elif route == "chitchat":
            return await self.handle_chitchat(message, chat_history)
        elif route == "vague_intent_product":
            return await self.handle_vague_intent(message, chat_history)
        elif route == "clear_intent_product":
            return await self.handle_vague_intent(message, chat_history)
            # return await self.agent_v1.run(message.content, chat_history)
        else:
            raise Exception(f"Unknown route: {route}")

    async def handle_chitchat(self, message: Message, chat_history: list[Message]):
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            message.content, history=chat_history, model=message.model
        )
        return response, {"input_token_count": input_tokens, "output_token_count": output_tokens}

    async def handle_vague_intent(self, message: Message, chat_history: list[Message]):
        context = await self.weaviate_service.search_products(
            message.content,
        )
        print(f"Found context: {context}")
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            message.content, context, chat_history, model=message.model
        )
        return response, {"input_token_count": input_tokens, "output_token_count": output_tokens}
