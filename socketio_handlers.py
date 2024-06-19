import socketio
import operator
from langchain import hub
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from weaviate.weaviate_interface import WeaviateInterface
from langchain_core.agents import AgentAction, AgentFinish
from typing import Dict, List, TypedDict, Union, Annotated
from langchain.agents import create_openai_functions_agent
from langgraph.prebuilt.tool_executor import ToolExecutor

wi: WeaviateInterface = None


class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


@tool("product_search", return_direct=True)
async def product_search(message: str, features: List[str], limit: int) -> str:
    """Search for products in Weaviate vector search
    Args:
        message (str): Reformated user message, to improve semantic search results
        features (List[str]): the features to search for, all the available features are: ['name', 'size', 'form', 'processor', 'core', 'frequency', 'memory', 'voltage', 'io', 'thermal', 'feature', 'type', 'specification', 'manufacturer', 'location', 'description', 'summary']
        limit (int): the number of results to return
    """
    context = await wi.product.search(message, features, limit)
    print(f"Product Search Context: {context}")
    return context


class SocketIOHandler:
    def __init__(self, weaviate_interface: WeaviateInterface):
        # Dictionary to store session data
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        global wi
        wi = weaviate_interface

        # Socket.io setup
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        self.socket_app = socketio.ASGIApp(self.sio)

        tools = [product_search]
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        prompt = hub.pull("hwchase17/openai-functions-agent")
        self.agent_runnable = create_openai_functions_agent(model, tools, prompt)
        self.tool_executor = ToolExecutor(tools)

        workflow = StateGraph(AgentState)

        # Define the two nodes we will cycle between
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

        # Socket.io event handlers
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
            print(f"Message from {sid}: {data}")
            session_id = data.get("sessionId")
            if session_id:
                if session_id not in self.sessions:
                    raise Exception(f"Session {session_id} not found")
                received_message = {
                    "id": data.get("id"),
                    "message": data.get("message"),
                    "isUserMessage": True,
                    "timestamp": data.get("timestamp"),
                }
                self.sessions[session_id].append(received_message)

                response_message = ""

                inputs = {"input": data.get("message"), "chat_history": []}
                async for s in self.agent.astream(inputs):
                    print("----")
                    res = list(s.values())[0]
                    print(res)
                    print("----")
                    # check if res has key `agent_outcome` and res['agent_outcome'] is an instance of AgentFinish
                    if "agent_outcome" in res and isinstance(res["agent_outcome"], AgentFinish):
                        response_message = res["agent_outcome"].return_values["output"]
                        print(f"Final response: {res['agent_outcome'].return_values}")
                print(f"Final response2: {response_message}")

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
