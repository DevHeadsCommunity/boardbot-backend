import json
import time
import logging
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


class ClearIntentState(Dict[str, Any]):
    model_name: str = "gpt-4o"
    chat_history: List[Dict[str, str]]
    current_message: str
    expanded_queries: List[str]
    filters: Dict[str, Any]
    query_context: Dict[str, Any]
    search_results: List[Tuple[Product, float]]
    reranking_result: Dict[str, Any]
    final_results: List[Tuple[Product, float]]
    input_tokens: Dict[str, int] = {
        "query_processing": 0,
        "rerank": 0,
        "generate": 0,
    }
    output_tokens: Dict[str, int] = {
        "query_processing": 0,
        "rerank": 0,
        "generate": 0,
    }
    time_taken: Dict[str, float] = {
        "query_processing": 0.0,
        "search": 0.0,
        "rerank": 0.0,
        "generate": 0.0,
    }
    output: Dict[str, Any] = {}


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
        self.workflow = self.setup_workflow()
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(ClearIntentState)

        workflow.add_node("query_processing", self.query_processing_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("result_reranking", self.result_reranking_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.add_edge("query_processing", "product_search")
        workflow.add_edge("product_search", "result_reranking")
        workflow.add_edge("result_reranking", "response_generation")
        workflow.add_edge("response_generation", END)

        workflow.set_entry_point("query_processing")

        return workflow.compile()

    async def query_processing_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        query_result, input_tokens, output_tokens = await self.query_processor.process_query_comprehensive(
            state["current_message"], state["chat_history"], model=state["model_name"]
        )

        state["expanded_queries"] = query_result["expanded_queries"]
        state["filters"] = query_result["filters"]
        state["query_context"] = query_result["query_context"]
        state["input_tokens"]["query_processing"] = input_tokens
        state["output_tokens"]["query_processing"] = output_tokens
        state["time_taken"]["query_processing"] = time.time() - start_time

        logger.info(f"Query processing result: {query_result}")
        return state

    async def product_search_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        results = await self.weaviate_service.search_products(
            state["current_message"],
            state["expanded_queries"],
            state["filters"],
            limit=state["query_context"]["num_products_requested"],
        )

        state["search_results"] = results
        state["time_taken"]["search"] = time.time() - start_time

        logger.info(f"\n\n\nFound {len(state['search_results'])} unique products\n\n\n")
        return state

    async def result_reranking_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        products_for_reranking = [
            {
                "name": p.get("name", "Unknown"),  # Use .get() method with a default value
                **{attr: p.get(attr, "Not specified") for attr in state["filters"].keys()},
                "certainty": certainty,
            }
            for p, certainty in state["search_results"]
        ]
        reranked_result, input_tokens, output_tokens = await self.query_processor.rerank_products(
            state["current_message"],
            state["chat_history"],
            products_for_reranking,
            state["filters"],
            state["query_context"],
            top_k=10,
            model=state["model_name"],
        )

        state["reranking_result"] = reranked_result
        name_to_product = {p.get("name", "Unknown"): (p, certainty) for p, certainty in state["search_results"]}
        state["final_results"] = [
            name_to_product.get(p["name"], (p, 0.0))
            for p in reranked_result["products"]
            if p["name"] in name_to_product
        ]
        state["input_tokens"]["rerank"] = input_tokens
        state["output_tokens"]["rerank"] = output_tokens
        state["time_taken"]["rerank"] = time.time() - start_time

        logger.info(f"Reranked results: {state['reranking_result']}")
        return state

    async def response_generation_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()

        relevant_products = json.dumps(
            [
                {
                    "name": p.name,
                    **{attr: getattr(p, attr) for attr in state["filters"].keys()},
                    "summary": p.full_product_description,
                    "certainty": certainty,
                }
                for p, certainty in state["final_results"]
            ],
            indent=2,
        )

        system_message, user_message = self.prompt_manager.get_clear_intent_response_prompt(
            state["current_message"],
            relevant_products,
            state["reranking_result"],
            state["filters"],
            state["query_context"],
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

    async def run(self, message: Message, chat_history: List[Message]) -> ClearIntentState:
        logger.info(f"\n\n\nRunning agent with message: {message}\n\n\n")

        initial_state = ClearIntentState(
            model_name=message.model,
            chat_history=chat_history,
            current_message=message.message,
            expanded_queries=[],
            filters={},
            query_context={},
            search_results=[],
            final_results=[],
            reranking_result={},
            input_tokens={"query_processing": 0, "rerank": 0, "generate": 0},
            output_tokens={"query_processing": 0, "rerank": 0, "generate": 0},
            time_taken={"query_processing": 0.0, "search": 0.0, "rerank": 0.0, "generate": 0.0},
        )

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed")

        except Exception as e:
            logger.error(f"Error running agent: {e}")
            final_state = initial_state
            final_state["output"] = json.dumps(
                {
                    "message": f"An error occurred while processing your request. {str(e)}",
                }
            )

        logger.info(f"Final state: {final_state}")
        logger.info(f"Final state type: {type(final_state)}")

        return final_state
