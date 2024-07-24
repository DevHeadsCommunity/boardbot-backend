from typing import List, Tuple, Dict, Any
from langgraph.graph import StateGraph, END
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from models.message import Message
from generators.base_agent import BaseAgent
from services.weaviate_service import WeaviateService
from langgraph.prebuilt import ToolExecutor
from langchain.schema import HumanMessage, AIMessage, BaseMessage, FunctionMessage


class AgentState(Dict[str, Any]):
    input: str
    chat_history: List[BaseMessage]
    agent_scratchpad: List[BaseMessage]
    output: str = ""


class AgentV1(BaseAgent):
    def __init__(self, weaviate_service: WeaviateService):
        self.weaviate_service = weaviate_service
        super().__init__()

    def setup_workflow(self) -> StateGraph:
        tools = [
            Tool(
                name="product_search",
                func=self.product_search,
                description="Search for products in Weaviate vector search",
            )
        ]
        tool_executor = ToolExecutor(tools)
        model = ChatOpenAI(model="gpt-4", temperature=0)

        prompt = self.create_prompt(
            "You are a helpful assistant for product queries. Use the product_search tool when you need to find information about products."
        )

        workflow = StateGraph(AgentState)

        workflow.add_node("agent", lambda state: self.agent_node(state, model, prompt, tools))
        workflow.add_node("action", lambda state: self.tool_node(state, tool_executor))

        workflow.add_conditional_edges("agent", self.should_continue, {True: "action", False: END})
        workflow.add_edge("action", "agent")

        workflow.set_entry_point("agent")

        return workflow.compile()

    def should_continue(self, state: AgentState) -> bool:
        return len(state.messages[-1].tool_calls) > 0 if state.messages else False

    async def product_search(self, query: str, limit: int = 5) -> str:
        """Search for products in Weaviate vector search"""
        features = ["name", "size", "form", "processor", "memory", "io", "manufacturer", "summary"]
        results = await self.weaviate_service.search_products(query, features, limit)
        return str(results)

    def final_output_node(self, state: AgentState) -> Dict[str, Any]:
        return {"output": state["final_response"]}

    async def run(self, message: str, chat_history: List[Message]) -> Tuple[str, Dict[str, int]]:
        chat_history_messages = [
            HumanMessage(content=msg.content) if msg.is_user_message else AIMessage(content=msg.content)
            for msg in chat_history
        ]

        print(f"Running agent with message: {message}")
        initial_state = AgentState(
            input=message,
            chat_history=chat_history_messages,
            agent_scratchpad=[],
            final_response="",
        )

        try:
            result = await self.workflow.ainvoke(initial_state)
            output = result["output"]
        except Exception as e:
            print(f"Error during workflow execution: {str(e)}")
            output = "An error occurred while processing your request."

        print(f"Agent output: {output}")
        input_tokens = len(message.split())
        output_tokens = len(output.split())

        return output, {
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
        }
