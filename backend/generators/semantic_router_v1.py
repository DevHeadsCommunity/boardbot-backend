from typing import Dict, List
from models.message import Message
from generators.agent_v1 import AgentV1
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

    async def run(self, message: Message, chat_history: List[Dict[str, str]]):
        route = await self.determine_route(message.content)
        return await self.handle_route(route, message, chat_history)

    async def determine_route(self, query: str) -> str:
        routes = await self.weaviate_service.search_routes(query)
        if not routes:
            raise Exception(f"No route found for query: {query}")
        print(f"Found routes: {routes}")
        return routes

    async def handle_route(self, route: str, message: Message, chat_history: List[Dict[str, str]]):
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
            return await self.agent_v1.run(message, chat_history)
        else:
            raise Exception(f"Unknown route: {route}")

    async def handle_chitchat(self, message: Message, chat_history: List[Dict[str, str]]):
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            message.content, history=chat_history, model=message.model
        )
        return response, {"input_token_count": input_tokens, "output_token_count": output_tokens}

    async def handle_vague_intent(self, message: Message, chat_history: List[Dict[str, str]]):
        context = await self.weaviate_service.search_products(
            message.content,
        )
        print(f"Found context: {context}")
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            message.content, context, chat_history, model=message.model
        )
        return response, {"input_token_count": input_tokens, "output_token_count": output_tokens}

    def _get_system_message_with_context(self, context: str) -> str:
        return (
            f"""You are ThroughPut assistant. Your main task is to help users with their queries about the product. Always respond in JSON format.
                   The context that is provided is product data, in the form of name, size, form, processor, core, frequency, memory, voltage, io, thermal, feature, type, specification, manufacturer, location, description, and summary.
                   In your response, synthesize the information from the context into a clear, simple, and easy-to-understand response to the user.
                   Use the following context: {context}

                   Make sure your response is in a JSON format.
            """
            + """
                   Example:
                   {
                       "response_description": "The product is a computer with a 15-inch display, Intel Core i7 processor, 16GB RAM, and 512GB SSD storage."
                       "response_justification": "The response is accurate and concise, providing key details about the product."
                       "products": [
                                        {
                                            "name": "Not available",
                                            "form": "COM Express Basic Module",
                                            "processor": "Intel Xeon D (Ice Lake-D)",
                                            "memory": "DDR4, Max Capacity: 128 GB, Socket: 2 x 260P SODIMM, Dual Channel, ECC/Non-ECC",
                                            "io": "4 x SATA Ports (6 Gbps), 8 x USB Ports (4 x USB 3.0, 4 x USB 2.0), 1 x LPC, 1 x SPI Bus, 1 x GPIO (8-bit), 1 x Watchdog Timer, 2 x COM Ports, 2 x Ethernet (10GBASE-KR, 1GBASE-T), 32 x PCIe Gen3 lanes",
                                            "manufacturer": "Advantech",
                                            "size": "95 mm x 125 mm",
                                            "summary": "High-performance COM Express Basic Module with Intel Xeon D processors, extensive I/O, and robust thermal management."
                                        },
                                        {
                                            "name": "ET COM Express",
                                            "form": "COM Express Type 6",
                                            "processor": "8th Generation Intel Xeon E & Core i3/i5/i7",
                                            "memory": "2 x DDR4 SODIMM, Max 32GB",
                                            "io": "4 x USB 3.1, 8 x USB 2.0, 4 x COM, 4 x SATA III, 2 x PCIe x4, 1 x PCIe x16, 2 x GbE LAN",
                                            "manufacturer": "IBASE",
                                            "size": "95 mm x 125 mm",
                                            "summary": "High-performance COM Express Type 6 modules with 8th Generation Intel Xeon E & Core i3/i5/i7 processors, extensive I/O, and display support."
                                        },
                                    ]
                    }
            """
        )
