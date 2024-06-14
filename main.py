import uvicorn
from fastapi import FastAPI
from weaviate import initialize_weaviate
from contextlib import asynccontextmanager
from socketio_handlers import SocketIOHandler

# FastAPI application with Lifespan context
app = FastAPI()

# Define global variables
socket_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global socket_handler
    # Startup tasks
    weaviate_interface = await initialize_weaviate()
    socket_handler = SocketIOHandler(weaviate_interface)
    app.mount("/", socket_handler.socket_app)
    yield
    # Shutdown tasks (Add any cleanup code here if needed)


# Assign the lifespan to the app
app.router.lifespan_context = lifespan


# Print {"Hello":"World"} on localhost:7777
@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6789, lifespan="on", reload=True)
