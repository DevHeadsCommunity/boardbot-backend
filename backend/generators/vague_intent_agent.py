import json
import logging
import time
from core.models.message import Message
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from .utils.response_formatter import ResponseFormatter
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from typing import List, Dict, Any, TypedDict, Annotated

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
        limit = state["product_count"]
        filters = state.get("filters", {})

        logger.info(f"Filters: {filters}")
        logger.info(f"Semantic search query: {state['semantic_search_query']}")

        unique_results = {}

        # If filters exist, start with hybrid search
        if filters:
            filter_query = " ".join([f"{key}:{value}" for key, value in filters.items()])
            hybrid_results = await self.weaviate_service.search_products(
                {"query": filter_query, "filters": filters, "limit": limit * 2, "search_type": "hybrid"}
            )

            for result in hybrid_results:
                if len(unique_results) >= limit:
                    break
                unique_results[result["product_id"]] = result

            # If not enough results, perform partial hybrid searches
            if len(unique_results) < limit:
                for key, value in filters.items():
                    if len(unique_results) >= limit:
                        break
                    partial_results = await self.weaviate_service.search_products(
                        {
                            "query": f"{key}:{value}",
                            "filters": {key: value},
                            "limit": limit - len(unique_results),
                            "search_type": "hybrid",
                        }
                    )
                    for result in partial_results:
                        if result["product_id"] not in unique_results:
                            unique_results[result["product_id"]] = result
                            if len(unique_results) >= limit:
                                break

        # If still not enough results or no filters, use direct semantic search
        if len(unique_results) < limit:
            semantic_results = await self.weaviate_service.search_products(
                {
                    "query": state["semantic_search_query"],
                    "limit": limit * 2 - len(unique_results),
                    "search_type": "semantic",
                }
            )

            for result in semantic_results:
                if result["product_id"] not in unique_results:
                    unique_results[result["product_id"]] = result
                    if len(unique_results) >= limit:
                        break

        final_results = list(unique_results.values())[:limit]

        logger.info(f"\n\n===:> Final results: {final_results}\n\n")
        logger.info(f"Number of products found: {len(final_results)}")

        return {
            "search_results": final_results,
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
