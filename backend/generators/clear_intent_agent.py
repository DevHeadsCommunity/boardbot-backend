import json
import time
import logging
from typing import TypedDict, List, Dict, Any, Annotated
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


class ClearIntentState(TypedDict):
    model_name: str
    chat_history: List[Dict[str, str]]
    current_message: str
    filters: Dict[str, Any]
    query_context: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    reranking_result: Dict[str, Any]
    final_results: List[Dict[str, Any]]
    input_tokens: Annotated[Dict[str, int], merge_dict]
    output_tokens: Annotated[Dict[str, int], merge_dict]
    time_taken: Annotated[Dict[str, float], merge_dict]
    output: Dict[str, Any]


class ClearIntentAgent:
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
        workflow = StateGraph(ClearIntentState)

        workflow.add_node("query_processing", self.query_processing_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.set_entry_point("query_processing")

        workflow.add_edge("query_processing", "product_search")
        workflow.add_edge("product_search", "response_generation")
        workflow.add_edge("response_generation", END)

        return workflow.compile()

    async def query_processing_node(self, state: ClearIntentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        query_result, input_tokens, output_tokens = await self.query_processor.process_query_comprehensive(
            state["current_message"], state["chat_history"], model=state["model_name"]
        )
        logger.info(f"Query result: {query_result}")

        return {
            "filters": query_result["filters"],
            "query_context": query_result["query_context"],
            "input_tokens": {"query_processing": input_tokens},
            "output_tokens": {"query_processing": output_tokens},
            "time_taken": {"query_processing": time.time() - start_time},
        }

    async def product_search_node(self, state: ClearIntentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        limit = state["query_context"].get("num_products_requested", 5)
        filters = state["filters"]

        logger.info(f"Filters: {filters}")

        # Construct query for hybrid search based on filters
        filter_query = " ".join([f"{key}:{value}" for key, value in filters.items()])

        unique_results = {}

        # Perform hybrid search with all filters
        initial_results = await self.weaviate_service.search_products(
            {"query": filter_query, "filters": filters, "limit": limit * 2, "search_type": "hybrid"}
        )

        for result in initial_results:
            if len(unique_results) >= limit:
                break
            unique_results[result["product_id"]] = result

        # If not enough results, perform partial hybrid searches
        if len(unique_results) < limit:
            for key, value in filters.items():
                partial_results = await self.weaviate_service.search_products(
                    {"query": f"{key}:{value}", "filters": {key: value}, "limit": limit, "search_type": "hybrid"}
                )
                for result in partial_results:
                    if result["product_id"] not in unique_results:
                        unique_results[result["product_id"]] = result
                        if len(unique_results) >= limit:
                            break
                if len(unique_results) >= limit:
                    break

        final_results = list(unique_results.values())[:limit]

        logger.info(f"\n\n===:> Final results: {final_results}\n\n")

        return {
            "search_results": final_results,
            "time_taken": {"search": time.time() - start_time},
        }

    async def response_generation_node(self, state: ClearIntentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()

        relevant_products = json.dumps(
            [
                {
                    "product_id": p["product_id"],
                    "name": p["name"],
                    **{attr: p.get(attr, "Not specified") for attr in state["filters"].keys()},
                    "summary": p.get("full_product_description", ""),
                }
                for p in state["search_results"]
            ],
            indent=2,
        )

        system_message, user_message = self.prompt_manager.get_clear_intent_response_prompt(
            state["current_message"],
            relevant_products,
            json.dumps(state["filters"], indent=2),
        )

        logger.info(f"\n\nSystem message: {system_message}\n\n")
        logger.info(f"\n\nUser message: {user_message}\n\n")

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            temperature=0.1,
            model=state["model_name"],
        )

        logger.info(f"\n\nResponse: {response}\n\n")

        return {
            "output": response,
            "input_tokens": {"generate": input_tokens},
            "output_tokens": {"generate": output_tokens},
            "time_taken": {"generate": time.time() - start_time},
        }

    async def run(self, message: Message, chat_history: List[Message]) -> Dict[str, Any]:
        logger.info(f"Running ClearIntentAgent with message: {message}")

        initial_state: ClearIntentState = {
            "model_name": message.model,
            "chat_history": chat_history,
            "current_message": message.message,
            "expanded_queries": [],
            "filters": {},
            "query_context": {},
            "search_results": [],
            "final_results": [],
            "reranking_result": {},
            "input_tokens": {},
            "output_tokens": {},
            "time_taken": {},
            "output": {},
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
