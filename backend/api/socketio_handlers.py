import json
import socketio
from dateutil.parser import isoparse
from models.message import RequestMessage
from core.session_manager import SessionManager
from core.message_processor import MessageProcessor
import datetime


class SocketIOHandler:
    def __init__(self, session_manager: SessionManager, message_processor: MessageProcessor):
        self.session_manager = session_manager
        self.message_processor = message_processor
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        self.socket_app = socketio.ASGIApp(self.sio)
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
        self.session_manager.initialize_session(session_id)
        print(f"Session {session_id} initialized for {sid}")
        chat_history = self.session_manager.get_chat_history(session_id, "keep-all")
        formatted_chat_history = self.session_manager.format_chat_history(chat_history)
        await self.sio.emit("sessionInit", {"sessionId": session_id, "chatHistory": formatted_chat_history}, room=sid)

    async def process_message(self, sid, data):
        print(f"Received message from {sid}: {data}")

        message = RequestMessage(
            id=data.get("messageId"),
            message=data.get("message"),
            timestamp=self.get_timestamp(data.get("timestamp", None)),
            session_id=data.get("sessionId"),
            model=data.get("model"),
            architecture_choice=data.get("architectureChoice"),
            history_management_choice=data.get("historyManagementChoice"),
        )
        print(f"===> Message279: {message}")
        response = await self.message_processor.process_message(message)

        await self.sio.emit("textResponse", response.dict(), room=sid)
        print(f"Response sent to {sid}: {response}")
        self.session_manager.add_message(message)
        self.session_manager.add_message(response)

    def get_timestamp(self, timestamp: str) -> str:
        try:
            parsed_timestamp = isoparse(timestamp)
        except Exception as e:
            print(f"Error parsing timestamp: {timestamp}, Error: {e}")
            # Fallback to the current timestamp in case of parsing error
            parsed_timestamp = datetime.now()

        return parsed_timestamp
