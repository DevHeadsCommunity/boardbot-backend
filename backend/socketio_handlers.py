import socketio
import operator
from langchain.tools import tool
from openai_client import OpenAIClient
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from weaviate.weaviate_interface import WeaviateInterface
from langchain_core.agents import AgentAction, AgentFinish
from typing import Dict, List, TypedDict, Union, Annotated
from langchain.agents import create_openai_functions_agent
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

wi: WeaviateInterface = None


class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


@tool("product_search", return_direct=True)
async def product_search(message: str, limit: int) -> str:
    """Search for products in Weaviate vector search
    Args:
        message (str): Reformated user message, to improve semantic search results. The user message should be reformated to include only the relevant information for the search, and words that are not relevant, or that may skew the search results should be removed. For example, if the user asks "20 SBC's that perform better than Raspberry Pi.", the message should be reformated to "High performance SBC's"
        limit (int): the number of results to return
    """
    features = [
        "name",
        "size",
        "form",
        "processor",
        "core",
        "frequency",
        "memory",
        "voltage",
        "io",
        "thermal",
        "feature",
        "type",
        "specification",
        "manufacturer",
        "location",
        "description",
        "summary",
    ]
    context = await wi.product.search(message, features, limit)
    # print(f"Product Search Context: {context}")
    return context


class SocketIOHandler:
    def __init__(self, weaviate_interface: WeaviateInterface):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        global wi
        wi = weaviate_interface

        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        self.socket_app = socketio.ASGIApp(self.sio)
        self.openai_client = OpenAIClient()

        tools = [product_search]
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        assistant_system_message = """You are a helpful assistant. \
        Use tools (only if necessary) to best answer the users questions. \
        When giving a direct answer, respond in JSON format.
        When giving a direct answer, if the user asked for 5 products, in your response, provide the top 5 products. \
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", assistant_system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent_runnable = create_openai_functions_agent(model, tools, prompt)
        self.tool_executor = ToolExecutor(tools)

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self.run_agent)
        workflow.add_node("action", self.execute_tools)
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "action",
                "end": END,
            },
        )
        workflow.add_edge("action", "agent")
        self.agent = workflow.compile()

        @self.sio.on("connect")
        async def connect(sid, env):
            print("New Client Connected to This id :" + " " + str(sid))

        @self.sio.on("disconnect")
        async def disconnect(sid):
            print("Client Disconnected: " + " " + str(sid))

        @self.sio.on("connectionInit")
        async def handle_connection_init(sid):
            await self.sio.emit("connectionAck", room=sid)

        @self.sio.on("sessionInit")
        async def handle_session_init(sid, data):
            print(f"===> Session {sid} initialized")
            session_id = data.get("sessionId")
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            print(f"**** Session {session_id} initialized for {sid} session data: {self.sessions[session_id]}")
            await self.sio.emit(
                "sessionInit", {"sessionId": session_id, "chatHistory": self.sessions[session_id]}, room=sid
            )

        @self.sio.on("textMessage")
        async def handle_chat_message(sid, data):
            session_id = data.get("sessionId")
            if session_id:
                if session_id not in self.sessions:
                    raise Exception(f"Session {session_id} not found")

                # Append the received message to the session chat history
                received_message = {
                    "id": data.get("id"),
                    "message": data.get("message"),
                    "isUserMessage": True,
                    "timestamp": data.get("timestamp"),
                }
                self.sessions[session_id].append(received_message)

                # Determine route and handle message based on route
                route_query = data.get("message")
                routes = await wi.route.search(route_query, ["route"], limit=1)
                if not routes:
                    raise Exception(f"No route found for query: {route_query}")

                route = routes[0]
                user_route = route.get("route")
                print(f"===:> Route for query {route_query}: {user_route}")

                response_message = ""

                if user_route == "politics":
                    response_message = """{"message": "I'm sorry, I'm not programmed to discuss politics."}"""
                elif user_route == "chitchat":
                    res = self.openai_client.generate_response(data.get("message"), history=self.sessions[session_id])
                    response_message = res.replace("```", "").replace("json", "").replace("\n", "").strip()
                elif user_route == "vague_intent_product":
                    context = await wi.product.search(
                        data.get("message"),
                        ["name", "type", "feature", "specification", "description", "summary"],
                    )
                    res = self.openai_client.generate_response(data.get("message"), context, self.sessions[session_id])
                    response_message = res.replace("```", "").replace("json", "").replace("\n", "").strip()
                elif user_route == "clear_intent_product":
                    inputs = {
                        "input": data.get("message"),
                        "chat_history": [
                            (
                                self.openai_client.format_user_message(msg["message"])
                                if msg["isUserMessage"]
                                else self.openai_client.format_system_message(msg["textResponse"])
                            )
                            for msg in self.sessions[session_id]
                        ],
                    }
                    async for s in self.agent.astream(inputs):
                        res = list(s.values())[0]
                        if "agent_outcome" in res and isinstance(res["agent_outcome"], AgentFinish):
                            response_message = (
                                res["agent_outcome"]
                                .return_values["output"]
                                .replace("```", "")
                                .replace("json", "")
                                .replace("\n", "")
                                .strip()
                            )

                print(f"Final response: {response_message}")

                response = {
                    "id": data.get("id") + "_response",
                    "textResponse": response_message,
                    "isUserMessage": False,
                    "timestamp": data.get("timestamp"),
                    "isComplete": True,
                }
                await self.sio.emit("textResponse", response, room=sid)
                self.sessions[session_id].append(response)

                print(f"Message from {sid} in session {session_id}: {data.get('message')}")
            else:
                print(f"No session ID provided by {sid}")

    async def run_agent(self, data):
        agent_outcome = await self.agent_runnable.ainvoke(data)
        return {"agent_outcome": agent_outcome}

    async def execute_tools(self, data):
        agent_action = data["agent_outcome"]
        output = await self.tool_executor.ainvoke(agent_action)
        return {"intermediate_steps": [(agent_action, str(output))]}

    def should_continue(self, data):
        if isinstance(data["agent_outcome"], AgentFinish):
            return "end"
        else:
            return "continue"
