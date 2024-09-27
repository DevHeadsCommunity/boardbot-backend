import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import SocketIOHandler, api_router
from dependencies import container
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# CORS configuration
origins = ["http://localhost:3000", "http://192.168.65.59:3000", "https://api.boardbot.ai"]


class CustomCORSMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        if b"origin" not in headers:
            await self.app(scope, receive, send)
            return

        async def custom_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers = [h for h in headers if h[0].lower() != b"access-control-allow-origin"]
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, custom_send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    weaviate_service = container.weaviate_service()
    await weaviate_service.initialize_weaviate(
        container.config.OPENAI_API_KEY(), container.config.WEAVIATE_URL(), container.config.RESET_WEAVIATE()
    )
    session_manager = container.session_manager()
    message_processor = container.message_processor()
    socket_handler = SocketIOHandler(session_manager, message_processor)

    # Apply custom CORS middleware to socket.io app
    socket_app_with_cors = CustomCORSMiddleware(socket_handler.socket_app)

    # Mount the socket.io app with custom CORS middleware
    app.mount("/socket.io", socket_app_with_cors)
    yield


# Create the FastAPI app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    error_details = []
    for error in exc.errors():
        error_details.append({"loc": error["loc"], "msg": error["msg"], "type": error["type"]})
    return JSONResponse(status_code=422, content={"detail": "Validation Error", "errors": error_details})


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5678, reload=True)
