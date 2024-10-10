import json
import logging
import time
import asyncio
from typing import List, Dict, Any, TypedDict, Annotated
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from core.models.message import Message
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from .utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


def merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


class VagueIntentState(TypedDict):
    model_name: str
    chat_history: List[Dict[str, str]]
    current_message: str
    semantic_search_query: str
    product_count: int
    search_results: List[Dict[str, Any]]
    input_tokens: Annotated[Dict[str, int], merge_dict]
    output_tokens: Annotated[Dict[str, int], merge_dict]
    time_taken: Annotated[Dict[str, float], merge_dict]
    output: Dict[str, Any]
    filters: Dict[str, Any]  # Add this line


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
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(VagueIntentState)

        workflow.add_node("query_generation", self.query_generation_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.set_entry_point("query_generation")

        workflow.add_edge("query_generation", "product_search")
        workflow.add_edge("product_search", "response_generation")
        workflow.add_edge("response_generation", END)

        return workflow.compile()

    async def query_generation_node(self, state: VagueIntentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        result, input_tokens, output_tokens = await self.query_processor.generate_semantic_search_query(
            state["current_message"], state["chat_history"], model=state["model_name"]
        )
        logger.info(f"Generated semantic search query: {result['query']}")
        logger.info(f"Generated semantic search filters: {result['filters']}")

        return {
            "semantic_search_query": result["query"],
            "product_count": result.get("product_count", 5),
            "filters": result.get("filters", {}),  # Keep filters in the state
            "input_tokens": {"query_generation": input_tokens},
            "output_tokens": {"query_generation": output_tokens},
            "time_taken": {"query_generation": time.time() - start_time},
        }

    async def product_search_node(self, state: VagueIntentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()

        # Double the limit if there are no filters
        limit = state["product_count"] * 2 if not state["filters"] else state["product_count"]

        async def search_query(query: str, search_type: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
            return await self.weaviate_service.search_products(
                query=query, limit=limit, filters=filters, search_type=search_type
            )

        # Prepare search tasks
        search_tasks = [
            search_query(state["semantic_search_query"], "semantic"),
            search_query(state["semantic_search_query"], "hybrid", state["filters"]),
        ]

        # Run all searches in parallel
        all_search_results = await asyncio.gather(*search_tasks)

        # Combine and deduplicate results
        all_results = [item for sublist in all_search_results for item in sublist]
        unique_results = {result["product_id"]: result for result in all_results}.values()

        # # Sort results by certainty (if available) or any other relevant metric
        # def get_sort_key(x):
        #     certainty = x.get("certainty")
        #     return certainty if certainty is not None else float("-inf")

        # sorted_results = sorted(unique_results, key=get_sort_key, reverse=True)

        # Limit to the requested product count
        # final_results = sorted_results[: state["product_count"]]

        logger.info(f"Found {len(unique_results)} unique products")
        logger.info(f"Final results: {unique_results}")

        return {
            "search_results": list(unique_results),
            "time_taken": {"search": time.time() - start_time},
        }

    async def response_generation_node(self, state: VagueIntentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()

        products_with_certainty = [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                **{attr: p.get(attr, "Not specified") for attr in state["filters"].keys()},
                "summary": p.get("full_product_description", ""),
                "certainty": p.get("certainty", 0),
            }
            for p in state["search_results"]
        ]

        system_message, user_message = self.prompt_manager.get_vague_intent_response_prompt(
            state["current_message"],
            json.dumps(products_with_certainty, indent=2),
            state["product_count"],
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            temperature=0,
            model=state["model_name"],
        )
        logger.info("Generated response for vague intent query")

        return {
            "output": response,
            "input_tokens": {"generate": input_tokens},
            "output_tokens": {"generate": output_tokens},
            "time_taken": {"generate": time.time() - start_time},
        }

    async def run(self, message: Message, chat_history: List[Message]) -> Dict[str, Any]:
        logger.info(f"Running VagueIntentAgent with message: {message}")

        initial_state: VagueIntentState = {
            "model_name": message.model,
            "chat_history": chat_history,
            "current_message": message.message,
            "semantic_search_query": "",
            "product_count": 0,
            "search_results": [],
            "input_tokens": {},
            "output_tokens": {},
            "time_taken": {},
            "output": {},
            "filters": {},  # Add this line
        }

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed")
            return final_state
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            return {
                **initial_state,
                "output": {
                    "message": f"An error occurred while processing your request: {str(e)}",
                    "products": [],
                    "reasoning": "",
                    "follow_up_question": "Would you like to try a different query?",
                },
            }
