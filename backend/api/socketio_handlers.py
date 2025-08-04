import json
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
        print("🧭 FUNCTION NAME: setup_event_handlers, FILE_NAME: backend/api/socketio_handlers.py")

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
        print("🧭 FUNCTION NAME: initialize_session, FILE_NAME: backend/api/socketio_handlers.py")
        session_id = data.get("session_id")
        self.session_manager.initialize_session(session_id)
        logger.info(f"Session {session_id} initialized for {sid}")
        chat_history = self.session_manager.get_chat_history(session_id, "keep-all")
        formatted_chat_history = self.session_manager.format_chat_history(chat_history)
        await self.sio.emit(
            "session_init", {"session_id": session_id, "chat_history": formatted_chat_history}, room=sid
        )

    async def process_message(self, sid, data):
        print("🧭 FUNCTION NAME: process_message, FILE_NAME: backend/api/socketio_handlers.py - start")
        logger.info(f"\n\n ===:> Received message from {sid}: {data}\n\n")

        # Validate model choice
        model = data.get("model")
        if not model:
            print("🛑 No model provided in request")
            await self.sio.emit(
                "error",
                {"message": "Model choice is required"},
                room=sid
            )
            return

        if not (model.startswith(("gpt-", "text-", "claude-"))):
            print(f"🛑 Unsupported model: {model}")
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
        print("📨 Constructed RequestMessage:", message)
        response = await self.message_processor.process_message(message, data.get("sql_mode", True))
        response_dict = response.to_dict()
        # print("!>! BEFORE Fallback response_dict:", response_dict)
        logger.info(f"Response object before fallback: {response_dict}")

        if not response_dict.get("products"):
            print("⚠️ No products in response, injecting hardcoded fallback product")
            hardcoded_full = {
                "product_id": "FAKE-001",
                "name": "COM Express Test Module",
                "form_factor": "COM EXPRESS",
                "price": 999,
                "stock_status": "In Stock",
                "full_product_description": "Це тестовий модуль для перевірки відображення таблиці.",
            }
            response_dict["products"] = [{"product_id": hardcoded_full["product_id"]}]
            response_dict["_debug_full_products"] = [hardcoded_full]
            response_dict["response"] = (
                "Не вдалося отримати справжні продукти, тому підставляю тимчасовий приклад для перевірки."
            )

            # print("🔧 After injecting fallback product, products field:", response_dict["products"])
            # print("🔧 _debug_full_products:", response_dict["_debug_full_products"])
            # print("🔧 response message overwritten to:", response_dict["response"])

            try:
                inner = json.loads(response_dict.get("message", "{}"))
                # print("🧩 Parsed inner message before mutation:", inner)
                inner["products"] = response_dict["_debug_full_products"]
                inner["_debug_full_products"] = response_dict["_debug_full_products"]
                # За потреби оновлюємо текст всередині
                if "message" in inner:
                    inner["message"] = response_dict.get("response", inner.get("message", ""))
                response_dict["message"] = json.dumps(inner)
                # print("🧩 Updated inner message JSON:", inner)
            except json.JSONDecodeError:
                print("❗ Failed to parse existing inner message JSON, creating fallback inner structure")
                fallback_inner = {
                    "message": response_dict.get("response", ""),
                    "products": response_dict["_debug_full_products"],
                    "_debug_full_products": response_dict["_debug_full_products"],
                    "reasoning": "",
                    "follow_up_suggestions": "",
                }
                response_dict["message"] = json.dumps(fallback_inner)
                # print("🧩 Fallback inner message JSON:", fallback_inner)

        # print("!>! FINAL response_dict to send:", response_dict)
        logger.info(f"Response sent to {sid}: {response_dict}")
        await self.sio.emit("text_response", response_dict, room=sid)
        self.session_manager.add_message(message)
        self.session_manager.add_message(response)
        print("🧭 FUNCTION NAME: process_message - end")

    def get_timestamp(self, timestamp: str) -> str:
        print("🧭 FUNCTION NAME: get_timestamp, FILE_NAME: backend/api/socketio_handlers.py")
        try:
            parsed_timestamp = isoparse(timestamp)
        except Exception as e:
            print(f"Error parsing timestamp: {timestamp}, Error: {e}")
            # Fallback to the current timestamp in case of parsing error
            parsed_timestamp = datetime.now()

        return parsed_timestamp
