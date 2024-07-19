import json
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from tavily import TavilyClient


class AgentV2:

    def __init__(self, weaviate_interface, tavily_client: TavilyClient, openai_client):
        self.wi = weaviate_interface
        self.tavily_client = tavily_client
        self.openai_client = openai_client
        self.model = ChatOpenAI(model="gpt-4", temperature=0)
        self.setup_agent()

    def setup_agent(self):
        tools = [self.identify_route, self.semantic_search, self.internet_search, self.generate_response]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an advanced AI assistant. Your task is to process user queries about products by identifying the query type, performing semantic search, validating results with internet search, and generating a final response.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent = create_openai_functions_agent(self.model, tools, prompt)

    @tool
    def identify_route(self, query: str) -> str:
        """Identify the route (query type) for the given query."""
        routes = self.wi.route.search(query, ["route"], limit=1)
        return routes[0].get("route") if routes else "unknown"

    @tool
    def semantic_search(self, query: str, limit: int = 5) -> str:
        """Perform semantic search for products based on the query."""
        features = ["name", "type", "feature", "specification", "description", "summary"]
        results = self.wi.product.search(query, features, limit)
        return json.dumps(results)

    @tool
    def internet_search(self, query: str) -> str:
        """Perform an internet search using Tavily to validate or find additional information."""
        search_result = self.tavily_client.search(query)
        return json.dumps(search_result)

    @tool
    def generate_response(self, query: str, semantic_results: str, internet_results: str) -> str:
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
        response = self.openai_client.generate_response(prompt)
        return response

    async def run(self, user_input, chat_history):
        inputs = {
            "input": user_input,
            "chat_history": chat_history,
        }
        response = await self.agent.ainvoke(inputs)
        return response.get("output", "An error occurred while processing your request.")
