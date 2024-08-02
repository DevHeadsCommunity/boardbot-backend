import socketio
from dateutil.parser import isoparse
from models.message import RequestMessage
from core.session_manager import SessionManager
from core.message_processor import MessageProcessor


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
            content=data.get("message"),
            timestamp=isoparse(data.get("timestamp")),
            session_id=data.get("sessionId"),
            model=data.get("model"),
            architecture_choice=data.get("architectureChoice"),
            history_management_choice=data.get("historyManagementChoice"),
        )
        print(f"===> Message279: {message}")
        chat_history = self.session_manager.get_chat_history(message.session_id, message.history_management_choice)
        print(f"Chat history: {chat_history}")
        formatted_chat_history = self.session_manager.format_chat_history(chat_history)
        response = await self.message_processor.process_message(message, formatted_chat_history)

        response_json = {
            "session_id": message.session_id,
            "messageId": response.id,
            "message": response.content,
            "timestamp": response.timestamp.isoformat(),
            "isComplete": response.is_complete,
            "inputTokenCount": response.input_token_count,
            "outputTokenCount": response.output_token_count,
            "elapsedTime": response.elapsed_time,
            "isUserMessage": response.is_user_message,
            "model": response.model,
        }

        print(f"===> Response: {response_json}")

        await self.sio.emit("textResponse", response_json, room=sid)
        print(f"Response sent to {sid}: {response}")
        self.session_manager.add_message(message)
        self.session_manager.add_message(response)
