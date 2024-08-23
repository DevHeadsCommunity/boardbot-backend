import asyncio
import json
import logging
import time
from typing import List, Tuple, Dict, Any
from models.message import Message
from models.product import Product
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class ClearIntentState(Dict[str, Any]):
    model_name: str = "gpt-4o"
    chat_history: List[Dict[str, str]]
    current_message: str
    expanded_queries: List[str]
    attributes: List[str]
    search_results: List[Product]
    reranking_result: Dict[str, Any]
    final_results: List[Product]
    input_tokens: Dict[str, int] = {
        "expansion": 0,
        "rerank": 0,
        "generate": 0,
    }
    output_tokens: Dict[str, int] = {
        "expansion": 0,
        "rerank": 0,
        "generate": 0,
    }
    time_taken: Dict[str, float] = {
        "expansion": 0.0,
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

        workflow.add_node("query_expansion", self.query_expansion_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("result_reranking", self.result_reranking_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.add_edge("query_expansion", "product_search")
        workflow.add_edge("product_search", "result_reranking")
        workflow.add_edge("result_reranking", "response_generation")
        workflow.add_edge("response_generation", END)

        workflow.set_entry_point("query_expansion")

        return workflow.compile()

    async def query_expansion_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        result, input_tokens, output_tokens = await self.query_processor.process_query_comprehensive(
            state["current_message"], state["chat_history"], num_expansions=3, model=state["model_name"]
        )
        expanded_queries, attributes = self.generate_semantic_search_queries(result)

        state["expanded_queries"] = expanded_queries
        state["attributes"] = attributes
        state["input_tokens"]["expansion"] = input_tokens
        state["output_tokens"]["expansion"] = output_tokens
        state["time_taken"]["expansion"] = time.time() - start_time

        logger.info(f"Expanded queries: {expanded_queries}")
        return state

    async def product_search_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        queries = [state["current_message"]] + state["expanded_queries"]
        results = await asyncio.gather(*[self.weaviate_service.search_products(query, limit=5) for query in queries])
        all_results = [item for sublist in results for item in sublist]

        unique_results = {}
        for result in all_results:
            if result["name"] not in unique_results:
                unique_results[result["name"]] = Product(**result)

        state["search_results"] = list(unique_results.values())
        state["time_taken"]["search"] = time.time() - start_time

        logger.info(f"Found {len(state['search_results'])} unique products")
        return state

    async def result_reranking_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        products_for_reranking = [
            {"name": p.name, **{attr: getattr(p, attr) for attr in state["attributes"]}}
            for p in state["search_results"]
        ]
        reranked_result, input_tokens, output_tokens = await self.query_processor.rerank_products(
            state["current_message"], state["chat_history"], products_for_reranking, top_k=10, model=state["model_name"]
        )

        state["reranking_result"] = reranked_result
        name_to_product = {p.name: p for p in state["search_results"]}
        state["final_results"] = [
            name_to_product[p["name"]] for p in reranked_result["products"] if p["name"] in name_to_product
        ]
        state["input_tokens"]["rerank"] = input_tokens
        state["output_tokens"]["rerank"] = output_tokens
        state["time_taken"]["rerank"] = time.time() - start_time

        logger.info(f"Reranked results: {[p.name for p in state['final_results']]}")
        return state

    async def response_generation_node(self, state: ClearIntentState) -> ClearIntentState:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_clear_intent_product_prompt(
            state["current_message"],
            state["chat_history"],
            state["final_results"],
            state["reranking_result"],
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model=state["model_name"]
        )

        state["input_tokens"]["generate"] = input_tokens
        state["output_tokens"]["generate"] = output_tokens
        state["time_taken"]["generate"] = time.time() - start_time

        metadata = {
            "reranking_result": state["reranking_result"],
            "input_token_usage": state["input_tokens"],
            "output_token_usage": state["output_tokens"],
            "time_taken": state["time_taken"],
        }

        state["output"] = self.response_formatter.format_response("clear_intent_product", response, metadata)

        logger.info(f"Generated response: {state['output']}")
        return state

    def generate_semantic_search_queries(self, comprehensive_result: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        expanded_queries = comprehensive_result["expanded_queries"]
        search_params = comprehensive_result["search_params"]
        extracted_attributes = comprehensive_result["extracted_attributes"]

        queries = expanded_queries.copy()
        search_param_query = ", ".join([f"{key}: {', '.join(value)}" for key, value in search_params.items()])
        queries.append(search_param_query)
        extracted_attributes_query = ", ".join([f"{key}: {value}" for key, value in extracted_attributes.items()])
        queries.append(extracted_attributes_query)

        attributes = list(extracted_attributes.keys())
        return queries, attributes

    async def run(self, message: Message, chat_history: List[Message]) -> Tuple[str, Dict[str, Any]]:
        logger.info(f"Running agent with message: {message}")

        initial_state = ClearIntentState(
            model_name=message.model,
            chat_history=chat_history,
            current_message=message.content,
            expanded_queries=[],
            search_results=[],
            final_results=[],
        )

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed")

            output = json.dumps(final_state["output"], indent=2)
            stats = {
                "input_token_usage": final_state["input_tokens"],
                "output_token_usage": final_state["output_tokens"],
                "time_taken": final_state["time_taken"],
            }

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            output = json.dumps(
                self.response_formatter.format_error_response("An unexpected error occurred during processing.")
            )
            stats = {
                "input_token_usage": {"total": 0},
                "output_token_usage": {"total": 0},
                "time_taken": {"total": 0},
            }

        return output, stats
