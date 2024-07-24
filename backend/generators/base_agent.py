from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, FunctionMessage
from models.message import Message


class BaseAgent(ABC):
    def __init__(self):
        self.workflow = self.setup_workflow()

    @abstractmethod
    def setup_workflow(self) -> StateGraph:
        pass

    @abstractmethod
    async def run(self, message: str, chat_history: List[Message]) -> Tuple[str, Dict[str, int]]:
        pass

    def create_prompt(self, system_message: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    async def agent_node(self, state: Dict[str, Any], model: ChatOpenAI, prompt: ChatPromptTemplate, tools: List[Any]):
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

    async def tool_node(self, state: Dict[str, Any], tool_executor: ToolExecutor):
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
