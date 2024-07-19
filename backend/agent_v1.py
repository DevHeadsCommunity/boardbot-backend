from langchain_openai import ChatOpenAI
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents import create_openai_functions_agent
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from typing import TypedDict, Union, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


class AgentV1:
    def __init__(self, tools, model_name="gpt-4"):
        self.model = ChatOpenAI(model=model_name, temperature=0)
        self.tools = tools
        self.setup_agent()

    def setup_agent(self):
        assistant_system_message = """You are a helpful assistant.
        Use tools (only if necessary) to best answer the users questions.
        When giving a direct answer, respond in JSON format.
        When giving a direct answer, if the user asked for 5 products, in your response, provide the top 5 products."""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", assistant_system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent_runnable = create_openai_functions_agent(self.model, self.tools, prompt)
        self.tool_executor = ToolExecutor(self.tools)

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

    async def run(self, user_input, chat_history):
        inputs = {
            "input": user_input,
            "chat_history": chat_history,
        }
        async for s in self.agent.astream(inputs):
            res = list(s.values())[0]
            if "agent_outcome" in res and isinstance(res["agent_outcome"], AgentFinish):
                return res["agent_outcome"].return_values["output"]
        return "An error occurred while processing your request."
