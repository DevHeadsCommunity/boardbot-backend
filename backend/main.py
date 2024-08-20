import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api import SocketIOHandler, api_router
from dependencies import container
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    weaviate_service = container.weaviate_service()
    await weaviate_service.initialize_weaviate(
        container.config.OPENAI_API_KEY(), container.config.WEAVIATE_URL(), container.config.RESET_WEAVIATE()
    )
    session_manager = container.session_manager()
    message_processor = container.message_processor()
    socket_handler = SocketIOHandler(session_manager, message_processor)
    app.mount("/socket.io", socket_handler.socket_app)
    yield


app.router.lifespan_context = lifespan

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5678, reload=True)
