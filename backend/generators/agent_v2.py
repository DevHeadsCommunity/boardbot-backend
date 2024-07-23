from typing import List, Tuple, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, FunctionMessage
from models.message import Message
from generators.base_agent import BaseAgent
from services.tavily_service import TavilyService
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService


class AgentV2(BaseAgent):
    def __init__(self, weaviate_service: WeaviateService, tavily_service: TavilyService, openai_service: OpenAIService):
        self.weaviate_service = weaviate_service
        self.tavily_service = tavily_service
        self.openai_service = openai_service
        self.workflow = self.setup_workflow()

    def setup_workflow(self):
        tools = [self.product_search, self.internet_search, self.generate_response]
        tool_executor = ToolExecutor(tools)
        model = ChatOpenAI(model="gpt-4", temperature=0)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an advanced AI assistant for product queries. Use the provided tools to find information and generate comprehensive responses. Use product_search for product information, internet_search for validation, and generate_response for final answers.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        def agent_node(state):
            messages = prompt.format_messages(
                input=state["input"],
                chat_history=state.get("chat_history", []),
                agent_scratchpad=state.get("agent_scratchpad", []),
            )

            response = model.predict_messages(messages, functions=tools)

            if response.additional_kwargs.get("function_call"):
                return {
                    "next": "tool",
                    "tool": response.additional_kwargs["function_call"]["name"],
                    "tool_input": response.additional_kwargs["function_call"]["arguments"],
                }
            else:
                return {"next": "output", "output": response.content}

        def tool_node(state):
            result = tool_executor.execute(state["tool"], state["tool_input"])
            return {
                "next": "agent",
                "agent_scratchpad": state.get("agent_scratchpad", [])
                + [FunctionMessage(content=f"{state['tool']} result: {str(result)}")],
            }

        workflow = StateGraph(AgentState)

        workflow.add_node("agent", agent_node)
        workflow.add_node("tool", tool_node)
        workflow.add_node("output", lambda x: x)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges("agent", lambda x: x["next"], {"tool": "tool", "output": "output"})
        workflow.add_conditional_edges("tool", lambda x: x["next"], {"agent": "agent"})
        workflow.add_edge("output", END)

        return workflow.compile()

    @tool
    async def product_search(self, query: str, limit: int = 5) -> str:
        """Search for products in Weaviate vector search"""
        features = ["name", "type", "feature", "specification", "description", "summary"]
        results = await self.weaviate_service.search_products(query, features, limit)
        return str(results)

    @tool
    async def internet_search(self, query: str) -> str:
        """Perform an internet search using Tavily to validate or find additional information."""
        results = await self.tavily_service.search(query)
        return str(results)

    @tool
    async def generate_response(self, query: str, semantic_results: str, internet_results: str) -> str:
        """Generate a final response based on semantic search results and internet search validation."""
        prompt = f"""
        Given the user query: "{query}"
        And the semantic search results: {semantic_results}
        And the internet search results: {internet_results}

        Generate a comprehensive response that answers the user's query. The response should:
        1. Be based primarily on the semantic search results (product information).
        2. Use the internet search results to validate or supplement the product information.
        3. Be clear, concise, and directly address the user's query.
        4. Be formatted as a valid JSON object with a 'message' key containing the response text.

        If the semantic search results don't adequately answer the query, suggest refining the search.
        """
        response, _, _ = await self.openai_service.generate_response(prompt)
        return response

    async def run(self, message: str, chat_history: List[Message]) -> Tuple[str, Dict[str, int]]:
        chat_history_messages = [
            HumanMessage(content=msg.content) if msg.is_user_message else AIMessage(content=msg.content)
            for msg in chat_history
        ]

        initial_state = {
            "input": message,
            "chat_history": chat_history_messages,
        }

        result = await self.workflow.ainvoke(initial_state)

        output = result["output"]

        input_tokens = len(message.split())
        output_tokens = len(output.split())

        return output, {
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
        }


class AgentState(Dict[str, Any]):
    next: Annotated[str, "The next node to call"]
