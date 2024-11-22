import logging
import socketio
from dateutil.parser import isoparse
from core.models.message import RequestMessage, ResponseMessage
from core import SessionManager, MessageProcessor
import datetime
from config import config


logger = logging.getLogger(__name__)


class SocketIOHandler:
    def __init__(self, session_manager: SessionManager, message_processor: MessageProcessor):
        self.session_manager = session_manager
        self.message_processor = message_processor

        # Configure CORS for socket.io
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=[
                "http://localhost:3000",
                f"http://{config.IP_ADDRESS}:3000",
                "https://api.boardbot.ai",
                "https://boardbot.ai",
            ],
            allow_credentials=True,
        )
        self.socket_app = socketio.ASGIApp(self.sio)
        self.setup_event_handlers()

    def setup_event_handlers(self):
        @self.sio.on("connect")
        async def connect(sid, env):
            logger.info(f"New Client Connected: {sid}")

        @self.sio.on("disconnect")
        async def disconnect(sid):
            logger.info(f"Client Disconnected: {sid}")

        @self.sio.on("connection_init")
        async def handle_connection_init(sid):
            await self.sio.emit("connection_ack", room=sid)

        @self.sio.on("session_init")
        async def handle_session_init(sid, data):
            await self.initialize_session(sid, data)

        @self.sio.on("text_message")
        async def handle_chat_message(sid, data):
            await self.process_message(sid, data)

    async def initialize_session(self, sid, data):
        session_id = data.get("session_id")
        self.session_manager.initialize_session(session_id)
        logger.info(f"Session {session_id} initialized for {sid}")
        chat_history = self.session_manager.get_chat_history(session_id, "keep-all")
        formatted_chat_history = self.session_manager.format_chat_history(chat_history)
        await self.sio.emit(
            "session_init", {"session_id": session_id, "chat_history": formatted_chat_history}, room=sid
        )

    async def process_message(self, sid, data):
        logger.info(f"\n\n ===:> Received message from {sid}: {data}\n\n")

        # Validate model choice
        model = data.get("model")
        if not model:
            await self.sio.emit(
                "error",
                {"message": "Model choice is required"},
                room=sid
            )
            return

        if not (model.startswith(("gpt-", "text-", "claude-"))):
            await self.sio.emit(
                "error",
                {"message": f"Unsupported model: {model}"},
                room=sid
            )
            return

        message = RequestMessage(
            id=data.get("message_id"),
            message=data.get("message"),
            timestamp=self.get_timestamp(data.get("timestamp", None)),
            session_id=data.get("session_id"),
            model=model,
            architecture_choice=data.get("architecture_choice"),
            history_management_choice=data.get("history_management_choice"),
            is_user_message=True,
        )
        response = await self.message_processor.process_message(message)
        response_dict = response.to_dict()
        logger.info(f"Response sent to {sid}: {response_dict}")
        await self.sio.emit("text_response", response_dict, room=sid)
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
