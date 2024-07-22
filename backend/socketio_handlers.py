import time
import socketio
from typing import Dict, List
from agent_v1 import AgentV1
from agent_v2 import AgentV2
from openai_client import OpenAIClient
from tools import initialize_weaviate, product_search
from weaviate.weaviate_interface import WeaviateInterface
from tavily import TavilyClient
from config import Config


class SocketIOHandler:
    def __init__(self, weaviate_interface: WeaviateInterface):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        initialize_weaviate(weaviate_interface)
        self.wi = weaviate_interface
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        self.socket_app = socketio.ASGIApp(self.sio)
        self.openai_client = OpenAIClient()
        self.agent_v1 = AgentV1([product_search])
        self.tavily_client = TavilyClient(api_key=Config().TAVILY_API_KEY)
        self.agent_v2 = AgentV2(self.wi, self.tavily_client, self.openai_client)
        self.setup_event_handlers()

    def setup_event_handlers(self):
        @self.sio.on("connect")
        async def connect(sid, env):
            print(f"New Client Connected: {sid}")

        @self.sio.on("disconnect")
        async def disconnect(sid):
            print(f"Client Disconnected: {sid}")

        @self.sio.on("connectionInit")
        async def handle_connection_init(sid):
            await self.sio.emit("connectionAck", room=sid)

        @self.sio.on("sessionInit")
        async def handle_session_init(sid, data):
            await self.initialize_session(sid, data)

        @self.sio.on("textMessage")
        async def handle_chat_message(sid, data):
            await self.process_message(sid, data)

    async def initialize_session(self, sid, data):
        session_id = data.get("sessionId")
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        print(f"Session {session_id} initialized for {sid}")
        await self.sio.emit(
            "sessionInit", {"sessionId": session_id, "chatHistory": self.sessions[session_id]}, room=sid
        )

    async def process_message(self, sid, data):
        print(f"Received message from {sid}: {data}")
        session_id = data.get("sessionId")
        if not session_id or session_id not in self.sessions:
            raise Exception(f"Invalid session: {session_id}")

        received_message = self.format_received_message(data)
        self.sessions[session_id].append(received_message)

        architecture_choice = data.get("architectureChoice", "semantic_router")
        history_management_choice = data.get("historyManagementChoice", "all_history")

        if received_message["architectureChoice"] == "semantic-router-v1":
            route = await self.determine_route(data.get("message"))
            response_message, stats = await self.handle_route(route, session_id, received_message)
        elif received_message["architectureChoice"] == "agentic-v1":
            response_message, stats = await self.handle_agent(data, session_id, history_management_choice)
        elif received_message["architectureChoice"] == "agentic-v2":
            response_message, stats = await self.handle_advanced_agent(data, session_id, history_management_choice)
        else:
            raise ValueError(f"Unknown architecture choice: {architecture_choice}")

        response = self.format_response(data, response_message, stats)
        await self.sio.emit("textResponse", response, room=sid)
        print(f"Response sent to {sid}: {response}")
        self.sessions[session_id].append(response)

    async def handle_agent(self, data, session_id, history_management_choice):
        start_time = time.time()
        chat_history = self.get_chat_history(session_id, history_management_choice)
        response = await self.agent_manager.run(data.get("message"), chat_history)
        stats = self.calculate_stats(data.get("message"), response, start_time)
        return self.clean_response(response), stats

    async def handle_advanced_agent(self, data, session_id, history_management_choice):
        start_time = time.time()
        chat_history = self.get_chat_history(session_id, history_management_choice)
        response = await self.agent_v2.run(data.get("message"), chat_history)
        stats = self.calculate_stats(data.get("message"), response, start_time)
        return self.clean_response(response), stats

    def get_chat_history(self, session_id, history_management_choice):
        if history_management_choice == "keep-all":
            return self.sessions[session_id]
        elif history_management_choice == "keep-none":
            return self.sessions[session_id][-5:]
        elif history_management_choice == "keep-last-5":
            return []
        else:
            raise ValueError(f"Unknown history management choice: {history_management_choice}")

    def format_received_message(self, data):
        return {
            "id": data.get("id"),
            "message": data.get("message"),
            "isUserMessage": True,
            "timestamp": data.get("timestamp"),
            "model": data.get("model"),
            "architectureChoice": data.get("architectureChoice"),
            "historyManagementChoice": data.get("historyManagementChoice"),
        }

    async def determine_route(self, query):
        routes = await self.wi.route.search(query, ["route"], limit=1)
        if not routes:
            raise Exception(f"No route found for query: {query}")
        return routes[0].get("route")

    async def handle_route(self, route, session_id, data):
        start_time = time.time()
        if route == "politics":
            response = """{"message": "I'm sorry, I'm not programmed to discuss politics."}"""
            stats = self.calculate_stats("", response, start_time)
        elif route == "chitchat":
            response, stats = await self.handle_chitchat(data, session_id, start_time)
        elif route == "vague_intent_product":
            response, stats = await self.handle_vague_intent(data, session_id, start_time)
        elif route == "clear_intent_product":
            response, stats = await self.handle_clear_intent(data, session_id, start_time)
        else:
            raise Exception(f"Unknown route: {route}")
        return response, stats

    async def handle_chitchat(self, session_id, start_time, data):
        chat_history = self.get_chat_history(session_id, data["historyManagementChoice"])
        response, input_tokens, output_tokens = self.openai_client.generate_response(
            data["message"], history=chat_history
        )
        stats = self.calculate_stats(data.get("message"), response, start_time, input_tokens, output_tokens)
        return self.clean_response(response), stats

    async def handle_vague_intent(self, data, session_id, start_time, history_management_choice):
        context = await self.wi.product.search(
            data.get("message"),
            ["name", "type", "feature", "specification", "description", "summary"],
        )
        chat_history = self.get_chat_history(session_id, history_management_choice)
        response, input_tokens, output_tokens = self.openai_client.generate_response(
            data.get("message"), context, chat_history
        )
        stats = self.calculate_stats(data.get("message"), response, start_time, input_tokens, output_tokens)
        return self.clean_response(response), stats

    async def handle_clear_intent(self, data, session_id, start_time):
        chat_history = self.get_chat_history(session_id, data["historyManagementChoice"])
        response = await self.agent_manager.run(data["message"], chat_history)
        stats = self.calculate_stats(data["message"], response, start_time)
        return self.clean_response(response), stats

    def clean_response(self, response):
        return response.replace("```", "").replace("json", "").replace("\n", "").strip()

    def calculate_stats(self, input_text, output_text, start_time, input_tokens=None, output_tokens=None):
        if input_tokens is None:
            input_tokens = len(self.openai_client.encoder.encode(input_text))
        if output_tokens is None:
            output_tokens = len(self.openai_client.encoder.encode(output_text))
        elapsed_time = time.time() - start_time
        return {
            "inputTokenCount": input_tokens,
            "outputTokenCount": output_tokens,
            "elapsedTime": elapsed_time,
        }

    def format_response(self, data, response_message, stats):
        return {
            "id": f"{data.get('id')}_response",
            "textResponse": response_message,
            "isUserMessage": False,
            "timestamp": data.get("timestamp"),
            "isComplete": True,
            **stats,
        }
