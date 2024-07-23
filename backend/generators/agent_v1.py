from datetime import datetime
from typing import List, Tuple, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, FunctionMessage
from models.message import Message, ResponseMessage
from generators.base_agent import BaseAgent
from services.weaviate_service import WeaviateService


class AgentV1(BaseAgent):
    def __init__(self, weaviate_service: WeaviateService):
        self.weaviate_service = weaviate_service
        self.workflow = self.setup_workflow()

    def setup_workflow(self):
        tools = [
            Tool(
                name="product_search",
                func=self.product_search,
                description="Search for products in Weaviate vector search",
            )
        ]
        tool_executor = ToolExecutor(tools)
        model = ChatOpenAI(model="gpt-4", temperature=0)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant for product queries. Use the product_search tool when you need to find information about products.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        async def agent_node(state):
            try:
                messages = prompt.format_messages(
                    input=state["input"],
                    chat_history=state.get("chat_history", []),
                    agent_scratchpad=state.get("agent_scratchpad", []),
                )

                response = await model.ainvoke(messages, functions=tools)

                if response.additional_kwargs.get("function_call"):
                    return {
                        "next": "tool",
                        "tool": response.additional_kwargs["function_call"]["name"],
                        "tool_input": response.additional_kwargs["function_call"]["arguments"],
                    }
                else:
                    return {"next": "output", "output": response.content}
            except Exception as e:
                print(f"Error in agent_node: {str(e)}")
                return {"next": "output", "output": "An error occurred while processing your request."}

        async def tool_node(state):
            try:
                result = await tool_executor.aexecute(state["tool"], state["tool_input"])
                return {
                    "next": "agent",
                    "agent_scratchpad": state.get("agent_scratchpad", [])
                    + [FunctionMessage(content=f"{state['tool']} result: {str(result)}")],
                }
            except Exception as e:
                print(f"Error in tool_node: {str(e)}")
                return {"next": "output", "output": "An error occurred while executing the tool."}

        workflow = StateGraph(AgentState)

        workflow.add_node("agent", agent_node)
        workflow.add_node("tool", tool_node)
        workflow.add_node("output", lambda x: {"next": END, "output": x["output"]})

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            lambda x: x["next"],
            {
                "tool": "tool",
                "output": "output",
            },
        )
        workflow.add_conditional_edges(
            "tool",
            lambda x: x["next"],
            {
                "agent": "agent",
                "output": "output",
            },
        )

        return workflow.compile()

    async def product_search(self, query: str, limit: int = 5) -> str:
        """Search for products in Weaviate vector search"""
        features = ["name", "size", "form", "processor", "memory", "io", "manufacturer", "summary"]
        results = await self.weaviate_service.search_products(query, features, limit)
        return str(results)

    async def run(self, message: str, chat_history: List[Message]) -> ResponseMessage:
        start_time = datetime.utcnow()
        chat_history_messages = [
            HumanMessage(content=msg.content) if msg.is_user_message else AIMessage(content=msg.content)
            for msg in chat_history
        ]

        initial_state = {
            "input": message,
            "chat_history": chat_history_messages,
        }

        try:
            result = await self.workflow.ainvoke(initial_state)
            output = result["output"]
        except Exception as e:
            print(f"Error during workflow execution: {str(e)}")
            output = "An error occurred while processing your request."

        end_time = datetime.utcnow()
        elapsed_time = (end_time - start_time).total_seconds()

        input_tokens = len(message.split())
        output_tokens = len(output.split())

        return ResponseMessage(
            id="new_id",
            content=output,
            timestamp=end_time,
            is_complete=True,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            elapsed_time=elapsed_time,
        )


class AgentState(Dict[str, Any]):
    next: Annotated[str, "The next node to call"]
