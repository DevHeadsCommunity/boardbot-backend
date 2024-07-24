from typing import List, Tuple, Dict, Any
from langgraph.graph import StateGraph, END
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from models.message import Message
from generators.base_agent import BaseAgent
from services.tavily_service import TavilyService
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from langgraph.prebuilt import ToolExecutor


class AgentV2(BaseAgent):
    def __init__(self, weaviate_service: WeaviateService, tavily_service: TavilyService, openai_service: OpenAIService):
        self.weaviate_service = weaviate_service
        self.tavily_service = tavily_service
        self.openai_service = openai_service
        super().__init__()

    def setup_workflow(self) -> StateGraph:
        tools = [
            Tool(
                name="product_search",
                func=self.product_search,
                description="Search for products in Weaviate vector search",
            ),
            Tool(
                name="internet_search",
                func=self.internet_search,
                description="Perform an internet search using Tavily to validate or find additional information.",
            ),
            Tool(
                name="generate_response",
                func=self.generate_response,
                description="Generate a final response based on semantic search results and internet search validation.",
            ),
        ]
        tool_executor = ToolExecutor(tools)
        model = ChatOpenAI(model="gpt-4", temperature=0)

        prompt = self.create_prompt(
            "You are an advanced AI assistant for product queries. Use the provided tools to find information and generate comprehensive responses. Use product_search for product information, internet_search for validation, and generate_response for final answers."
        )

        workflow = StateGraph(AgentState)

        workflow.add_node("agent", lambda state: self.agent_node(state, model, prompt, tools))
        workflow.add_node("tool", lambda state: self.tool_node(state, tool_executor))
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
        features = ["name", "type", "feature", "specification", "description", "summary"]
        results = await self.weaviate_service.search_products(query, features, limit)
        return str(results)

    async def internet_search(self, query: str) -> str:
        """Perform an internet search using Tavily to validate or find additional information."""
        results = await self.tavily_service.search(query)
        return str(results)

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

        print(f"Running agent with message: {message}")
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

        print(f"Agent output: {output}")
        input_tokens = len(message.split())
        output_tokens = len(output.split())

        return output, {
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
        }


class AgentState(Dict[str, Any]):
    pass
