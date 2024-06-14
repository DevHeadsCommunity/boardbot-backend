import socketio
from typing import Dict, List
from openai_client import OpenAIClient
from weaviate.weaviate_interface import WeaviateInterface


class SocketIOHandler:
    def __init__(self, weaviate_interface: WeaviateInterface):
        # Dictionary to store session data
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.weaviate_interface = weaviate_interface

        # Weaviate Interface and OpenAI Client (initially set to None)
        self.openai_client = OpenAIClient()

        # Socket.io setup
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        self.socket_app = socketio.ASGIApp(self.sio)

        # Socket.io event handlers
        @self.sio.on("connect")
        async def connect(sid, env):
            print("New Client Connected to This id :" + " " + str(sid))

        @self.sio.on("disconnect")
        async def disconnect(sid):
            print("Client Disconnected: " + " " + str(sid))

        @self.sio.on("connectionInit")
        async def handle_connection_init(sid):
            await self.sio.emit("connectionAck", room=sid)

        @self.sio.on("sessionInit")
        async def handle_session_init(sid, data):
            print(f"===> Session {sid} initialized")
            session_id = data.get("sessionId")
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            print(f"**** Session {session_id} initialized for {sid} session data: {self.sessions[session_id]}")
            await self.sio.emit(
                "sessionInit", {"sessionId": session_id, "chatHistory": self.sessions[session_id]}, room=sid
            )

        @self.sio.on("textMessage")
        async def handle_chat_message(sid, data):
            print(f"Message from {sid}: {data}")
            session_id = data.get("sessionId")
            if session_id:
                if session_id not in self.sessions:
                    raise Exception(f"Session {session_id} not found")
                received_message = {
                    "id": data.get("id"),
                    "message": data.get("message"),
                    "isUserMessage": True,
                    "timestamp": data.get("timestamp"),
                }
                self.sessions[session_id].append(received_message)

                # route
                route_query = data.get("message")
                routes = await self.weaviate_interface.route.search(route_query, ["route"], limit=1)
                if not routes:
                    raise Exception(f"No route found for query: {route_query}")
                print(f"Routes for query {route_query}: {routes}")
                route = routes[0]
                user_route = route.get("route")
                print(f"Route for query {route_query}: {user_route}")

                response_message = ""

                if user_route == "politics":
                    response_message = "I'm sorry, I'm not programmed to discuss politics."
                elif user_route == "chitchat":
                    response_message = self.openai_client.generate_response(data.get("message"))
                elif user_route == "clear_Intent_product":
                    context = await self.weaviate_interface.product.search(
                        data.get("message"), ["description", "price", "feature", "specification", "location", "summary"]
                    )
                    response_message = self.openai_client.generate_response(data.get("message"), context)
                elif user_route == "vague_Intent_product":
                    context = await self.weaviate_interface.product.search(
                        data.get("message"), ["description", "price", "feature", "specification", "location", "summary"]
                    )
                    print(f"\n\nContext for {data.get('message')}: {context}\n\n")
                    response_message = self.openai_client.generate_response(data.get("message"), context)

                print(f"Response for {data.get('message')}: {response_message}")

                response = {
                    "id": data.get("id") + "_response",
                    "textResponse": response_message,
                    "isUserMessage": False,
                    "timestamp": data.get("timestamp"),
                    "isComplete": True,
                }
                await self.sio.emit("textResponse", response, room=sid)
                self.sessions[session_id].append(response)

                print(f"Message from {sid} in session {session_id}: {data.get('message')}")
            else:
                print(f"No session ID provided by {sid}")
