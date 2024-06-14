import uvicorn
import socketio
from fastapi import FastAPI
from typing import Dict, List
from weaviate import setup_weaviate_interface
from contextlib import asynccontextmanager
import pandas as pd
from openai import OpenAI

# Weaviate Interface (initially set to None)
weaviate_interface = None
client = OpenAI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global weaviate_interface
    # Startup tasks
    weaviate_interface = await setup_weaviate_interface()
    await weaviate_interface.schema.reset()

    # products
    products = pd.read_csv("data/clean_products.csv")
    products = products.drop(columns=["raw_data", "id"])
    products_data = products.to_dict(orient="records")
    await weaviate_interface.product.batch_upsert(products_data)

    # routes
    politics = [
        "isn't politics the best thing ever",
        "why don't you tell me about your political opinions",
        "don't you just love the president",
        "don't you just hate the president",
        "they're going to destroy this country!",
        "they will save the country!",
        "I'm going to vote for them",
    ]
    politics_data = [{"prompt": message, "route": "politics"} for message in politics]
    await weaviate_interface.route.batch_upsert(politics_data)

    chitchat = [
        "Who let the dogs out?",
        "What is the purpose of life?",
        "how's the weather today?",
        "how are things going?",
        "lovely weather today",
        "the weather is horrendous",
        "let's go to the chippy",
        "I'm going to the cinema",
    ]
    chitchat_data = [{"prompt": message, "route": "chitchat"} for message in chitchat]
    await weaviate_interface.route.batch_upsert(chitchat_data)

    clear_Intent_product_prompts = [
        "Top 10 Single Board Computers for automotive applications.",
        "5 boards compatible with Linux's Debian distro.",
        "List of 3 computer on modules that work best with cellular connectivity.",
        "20 SBC's that perform better than Raspberry Pi.",
        "Edge AI boards with built-in cryptographic chips that support root-of-trust. Mention any 5.",
    ]
    clear_Intent_product_prompts_data = [
        {"prompt": message, "route": "clear_Intent_product"} for message in clear_Intent_product_prompts
    ]
    await weaviate_interface.route.batch_upsert(clear_Intent_product_prompts_data)

    vague_Intent_product_prompts = [
        "What is a Single Board Computer?",
        "Best devkits for motor-control applications with high voltage supply.",
        "Advanced single board computers with edge capabilities for ML applications.",
        "Computer on modules with an integrated NPU.",
        "Single board computers with provision of adding camera for computer vision applications",
    ]
    vague_Intent_product_prompts_data = [
        {"prompt": message, "route": "vague_Intent_product"} for message in vague_Intent_product_prompts
    ]
    await weaviate_interface.route.batch_upsert(vague_Intent_product_prompts_data)

    is_valid = await weaviate_interface.schema.is_valid()
    info = await weaviate_interface.schema.info()
    print(f" Weaviate schema is valid: {is_valid}")
    print(f" Weaviate schema info: {info}")
    yield

    # Shutdown tasks
    # (Add any cleanup code here if needed)


def generate_response(user_message: str, context: str = None) -> str:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"You are TeamMate. TeamMate is a helpful assistant. Use the following context: {context}",
            },
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


# Fast API application with Lifespan context
app = FastAPI(lifespan=lifespan)

# Socket io (sio) create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
# wrap with ASGI application
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)

# Dictionary to store session data
sessions: Dict[str, List[Dict[str, str]]] = {}


# Print {"Hello":"World"} on localhost:7777
@app.get("/")
def read_root():
    return {"Hello": "World"}


@sio.on("connect")
async def connect(sid, env):
    print("New Client Connected to This id :" + " " + str(sid))


@sio.on("disconnect")
async def disconnect(sid):
    print("Client Disconnected: " + " " + str(sid))


@sio.on("connectionInit")
async def handle_connection_init(sid):
    await sio.emit("connectionAck", room=sid)


@sio.on("sessionInit")
async def handle_session_init(sid, data):
    print(f"===> Session {sid} initialized")
    session_id = data.get("sessionId")
    if session_id not in sessions:
        sessions[session_id] = []
    print(f"**** Session {session_id} initialized for {sid} session data: {sessions[session_id]}")
    await sio.emit("sessionInit", {"sessionId": session_id, "chatHistory": sessions[session_id]}, room=sid)


# Handle incoming chat messages
@sio.on("textMessage")
async def handle_chat_message(sid, data):
    print(f"Message from {sid}: {data}")
    session_id = data.get("sessionId")
    if session_id:
        if session_id not in sessions:
            raise Exception(f"Session {session_id} not found")
        received_message = {
            "id": data.get("id"),
            "message": data.get("message"),
            "isUserMessage": True,
            "timestamp": data.get("timestamp"),
        }
        sessions[session_id].append(received_message)

        # route
        route_query = data.get("message")
        routes = await weaviate_interface.route.search(route_query, ["route"], limit=1)
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
            response_message = generate_response(data.get("message"))
        elif user_route == "clear_Intent_product":
            context = await weaviate_interface.product.search(
                data.get("message"), ["description", "price", "feature", "specification", "location", "summary"]
            )
            response_message = generate_response(data.get("message"), context)
        elif user_route == "vague_Intent_product":
            context = await weaviate_interface.product.search(
                data.get("message"), ["description", "price", "feature", "specification", "location", "summary"]
            )
            response_message = generate_response(data.get("message"), context)

        print(f"Response for {data.get('message')}: {response_message}")

        response = {
            "id": data.get("id") + "_response",
            "textResponse": response_message,
            "isUserMessage": False,
            "timestamp": data.get("timestamp"),
            "isComplete": True,
        }
        await sio.emit("textResponse", response, room=sid)
        sessions[session_id].append(response)

        print(f"Message from {sid} in session {session_id}: {data.get('message')}")
    else:
        print(f"No session ID provided by {sid}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6789, lifespan="on", reload=True)
