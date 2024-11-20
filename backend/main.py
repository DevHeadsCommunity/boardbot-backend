import logging
from api import api_router
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.types import ASGIApp, Receive, Scope, Send
from dependencies import container, get_socket_handler, get_weaviate_service, get_openai_service

from config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# CORS configuration
origins = [
    "http://localhost:3000",
    f"http://{config.IP_ADDRESS}:3000",
    "https://api.boardbot.ai",
    "https://boardbot.ai",
]


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
    weaviate_service = get_weaviate_service()
    await weaviate_service.initialize_weaviate(container.config.RESET_WEAVIATE())

    openai_service = get_openai_service()
    await openai_service.initialize()

    socket_handler = get_socket_handler()

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
