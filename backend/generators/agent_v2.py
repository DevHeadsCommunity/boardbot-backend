import logging
import json
from typing import List, Tuple, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, BaseMessage, FunctionMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from models.message import Message
from services.weaviate_service import WeaviateService
from services.tavily_service import TavilyService
from services.openai_service import OpenAIService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AgentState(Dict[str, Any]):
    messages: List[BaseMessage]
    current_message: str
    agent_scratchpad: List[BaseMessage]
    output: str = ""


class AgentV2:
    def __init__(
        self,
        weaviate_service: WeaviateService,
        tavily_service: TavilyService,
        openai_service: OpenAIService,
        model_name: str = "gpt-4",
    ):
        self.weaviate_service = weaviate_service
        self.tavily_service = tavily_service
        self.openai_service = openai_service
        self.model_name = model_name
        logger.info(f"Initializing AgentV2 with model: {model_name}")
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        logger.info("Setting up workflow")
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tool", self.tool_node)

        workflow.add_conditional_edges("agent", self.should_continue, {"continue": "tool", "end": END})
        workflow.add_edge("tool", "agent")

        workflow.set_entry_point("agent")

        logger.info("Workflow setup complete")
        return workflow.compile()

    def get_system_message(self) -> str:
        return r"""You are ThroughPut advanced AI assistant. Your main task is to help users with their queries about products and provide comprehensive information.
        When a user asks about products or related information, you should use the following tools as needed:
        1. product_search: Use this to find information about specific products.
        2. internet_search: Use this to validate or find additional information from the internet.
        3. generate_response: Use this to create a final, comprehensive response based on the gathered information.

        Always respond in JSON format as shown in the example below.

        Example response format:
        {
            "response_description": "A concise description of the information that addresses the user's query.",
            "response_justification": "Explanation of why this response is appropriate and how it combines product and internet information.",
            "products": [
                {
                    "name": "Product Name",
                    "type": "Product Type",
                    "feature": "Key Feature",
                    "specification": "Important Specification",
                    "description": "Brief product description",
                    "summary": "Overall product summary"
                },
                // ... more products if applicable
            ],
            "additional_info": "Any relevant information from internet search",
            "suggested_actions": "Any recommended next steps or further queries for the user"
        }
        """

    async def agent_node(self, state: AgentState) -> AgentState:
        logger.info("Entering agent_node")
        model = ChatOpenAI(model=self.model_name, temperature=0)
        prompt = self.create_prompt()
        logger.info(f"Prompt: {prompt}")

        messages = prompt.format_messages(
            input=state["current_message"],
            chat_history=state["messages"],
            agent_scratchpad=state["agent_scratchpad"],
        )

        logger.info(f"Invoking model with messages: {messages}")
        response = await model.ainvoke(
            messages,
            functions=[
                {
                    "name": "product_search",
                    "description": "Search for products in the vector store",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
                        "required": ["query"],
                    },
                },
                {
                    "name": "internet_search",
                    "description": "Perform an internet search to validate or find additional information",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
                {
                    "name": "generate_response",
                    "description": "Generate a final response based on semantic search results and internet search validation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "semantic_results": {"type": "string"},
                            "internet_results": {"type": "string"},
                        },
                        "required": ["query", "semantic_results", "internet_results"],
                    },
                },
            ],
        )
        logger.info(f"Model response: {response}")

        state["messages"].append(response)
        logger.info("Exiting agent_node")
        return state

    async def tool_node(self, state: AgentState) -> AgentState:
        logger.info("Entering tool_node")
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.additional_kwargs.get("function_call"):
            function_call = last_message.additional_kwargs["function_call"]
            tool_name = function_call["name"]
            tool_args = json.loads(function_call["arguments"])

            logger.info(f"Executing tool: {tool_name} with arguments: {tool_args}")
            if tool_name == "product_search":
                result = await self.product_search(**tool_args)
            elif tool_name == "internet_search":
                result = await self.internet_search(**tool_args)
            elif tool_name == "generate_response":
                result = await self.generate_response(**tool_args)
            else:
                result = "Unknown tool"

            logger.info(f"Tool result: {result}")
            state["agent_scratchpad"].append(FunctionMessage(content=result, name=tool_name))

        logger.info("Exiting tool_node")
        return state

    def should_continue(self, state: AgentState) -> str:
        logger.info("Evaluating whether to continue or end")
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.additional_kwargs.get("function_call"):
            logger.info("Decided to continue")
            return "continue"
        logger.info("Decided to end")
        return "end"

    async def product_search(self, query: str, limit: int = 5) -> str:
        logger.info(f"Performing product search with query: {query}, limit: {limit}")
        features = ["name", "type", "feature", "specification", "description", "summary"]
        results = await self.weaviate_service.search_products(query, features, limit)
        logger.info(f"Product search results: {results}")
        return json.dumps(results)

    async def internet_search(self, query: str) -> str:
        logger.info(f"Performing internet search with query: {query}")
        results = await self.tavily_service.search(query)
        logger.info(f"Internet search results: {results}")
        return json.dumps(results)

    async def generate_response(self, query: str, semantic_results: str, internet_results: str) -> str:
        logger.info(f"Generating response for query: {query}")
        prompt = f"""
        Given the user query: "{query}"
        And the semantic search results: {semantic_results}
        And the internet search results: {internet_results}

        Generate a comprehensive response that answers the user's query. The response should:
        1. Be based primarily on the semantic search results (product information).
        2. Use the internet search results to validate or supplement the product information.
        3. Be clear, concise, and directly address the user's query.
        4. Be formatted as a valid JSON object following the structure specified in the system message.

        If the semantic search results don't adequately answer the query, suggest refining the search.
        """
        response, _, _ = await self.openai_service.generate_response(prompt)
        logger.info(f"Generated response: {response}")
        return response

    def create_prompt(self) -> ChatPromptTemplate:
        logger.info("Creating prompt template")
        return ChatPromptTemplate.from_messages(
            [
                ("system", self.get_system_message()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    async def run(self, message: str, chat_history: List[Message]) -> Tuple[str, Dict[str, int]]:
        logger.info(f"Running agent with message: {message}")
        chat_history_messages = [
            HumanMessage(content=msg.content) if msg.is_user_message else AIMessage(content=msg.content)
            for msg in chat_history
        ]

        initial_state = AgentState(
            messages=chat_history_messages,
            current_message=message,
            agent_scratchpad=[],
        )

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            output = final_state["messages"][-1].content
            logger.info(f"Workflow execution completed. Final output: {output}")
        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            output = json.dumps(
                {
                    "response_description": "An error occurred while processing your request.",
                    "response_justification": "There was an unexpected error in the system.",
                    "products": [],
                    "additional_info": "",
                    "suggested_actions": "Please try your query again or contact support if the problem persists.",
                }
            )

        # Note: This is a simplistic token count. Consider using a proper tokenizer for accuracy.
        input_tokens = len(message.split())
        output_tokens = len(output.split())

        logger.info(f"Run completed. Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        return output, {
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
        }
