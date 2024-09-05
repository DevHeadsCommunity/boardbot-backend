import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api import SocketIOHandler, api_router
from dependencies import container
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.93.59:3000"],  # Add your frontend URL
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    error_details = []
    for error in exc.errors():
        error_details.append({"loc": error["loc"], "msg": error["msg"], "type": error["type"]})
    return JSONResponse(status_code=422, content={"detail": "Validation Error", "errors": error_details})


app.router.lifespan_context = lifespan

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5678, reload=True)
