import json
import logging
import time
from typing import List, Tuple, Dict, Any
from core.models.message import Message
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager
from langgraph.graph import StateGraph, END

from weaviate_interface.models.product import Product

logger = logging.getLogger(__name__)


class VagueIntentState(Dict[str, Any]):
    model_name: str = "gpt-4o"
    chat_history: List[Dict[str, str]]
    current_message: str
    semantic_search_query: str
    product_count: int
    search_results: List[Tuple[Product, float]]  # Updated to include certainty
    input_tokens: Dict[str, int] = {
        "query_generation": 0,
        "generate": 0,
    }
    output_tokens: Dict[str, int] = {
        "query_generation": 0,
        "generate": 0,
    }
    time_taken: Dict[str, float] = {
        "query_generation": 0.0,
        "search": 0.0,
        "generate": 0.0,
    }
    output: Dict[str, Any] = {}


class VagueIntentAgent:

    def __init__(
        self,
        weaviate_service: WeaviateService,
        query_processor: QueryProcessor,
        openai_service: OpenAIService,
        prompt_manager: PromptManager,
    ):
        self.weaviate_service = weaviate_service
        self.query_processor = query_processor
        self.openai_service = openai_service
        self.workflow = self.setup_workflow()
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(VagueIntentState)

        workflow.add_node("query_generation", self.query_generation_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.add_edge("query_generation", "product_search")
        workflow.add_edge("product_search", "response_generation")
        workflow.add_edge("response_generation", END)

        workflow.set_entry_point("query_generation")

        return workflow.compile()

    async def query_generation_node(self, state: VagueIntentState) -> VagueIntentState:
        start_time = time.time()
        result, input_tokens, output_tokens = await self.query_processor.generate_semantic_search_query(
            state["current_message"], state["chat_history"], model=state["model_name"]
        )

        state["semantic_search_query"] = result["query"]
        state["product_count"] = result.get("product_count", 5)
        state["input_tokens"]["query_generation"] = input_tokens
        state["output_tokens"]["query_generation"] = output_tokens
        state["time_taken"]["query_generation"] = time.time() - start_time

        logger.info(f"Generated semantic search query: {state['semantic_search_query']}")
        logger.info(f"Number of products to search: {state['product_count']}")
        return state

    async def product_search_node(self, state: VagueIntentState) -> VagueIntentState:
        start_time = time.time()
        results = await self.weaviate_service.search_products(
            state["semantic_search_query"], limit=state["product_count"]
        )
        state["search_results"] = [(Product(**result), certainty) for result, certainty in results]
        state["time_taken"]["search"] = time.time() - start_time

        logger.info(f"Found {len(state['search_results'])} products")
        return state

    async def response_generation_node(self, state: VagueIntentState) -> VagueIntentState:
        start_time = time.time()

        logger.info(f"Generating response for:\n\n {state['search_results']}")

        products_with_certainty = [
            {**product.dict(), "certainty": certainty} for product, certainty in state["search_results"]
        ]

        system_message, user_message = self.prompt_manager.get_vague_intent_response_prompt(
            state["current_message"],
            products_with_certainty,
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            temperature=0.1,
            model=state["model_name"],
        )

        state["input_tokens"]["generate"] = input_tokens
        state["output_tokens"]["generate"] = output_tokens
        state["time_taken"]["generate"] = time.time() - start_time

        state["output"] = response

        logger.info(f"Generated response: {state['output']}")
        return state

    async def run(self, message: Message, chat_history: List[Message]) -> VagueIntentState:
        logger.info(f"Running vague intent agent with message: {message}")

        initial_state = VagueIntentState(
            model_name=message.model,
            chat_history=chat_history,
            current_message=message.message,
            search_results=[],
            semantic_search_query="",
            product_count=0,
            input_tokens={"query_generation": 0, "generate": 0},
            output_tokens={"query_generation": 0, "generate": 0},
            time_taken={"query_generation": 0.0, "search": 0.0, "generate": 0.0},
            output={},
        )

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed")

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            final_state = initial_state
            final_state["output"] = json.dumps(
                {
                    "message": f"An error occurred while processing your request. {str(e)}",
                }
            )

        return final_state
