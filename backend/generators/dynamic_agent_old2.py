import json
import time
import logging
from core.models.message import Message
from core.session_manager import SessionManager
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from .utils.response_formatter import ResponseFormatter
from langgraph.graph import StateGraph, END
from typing import List, Dict, Any, TypedDict, Optional, Annotated

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


class DynamicAgentState(TypedDict):
    model_name: str
    current_message: str
    chat_history: List[Dict[str, str]]
    filters: Optional[Dict[str, Any]]
    query_context: Dict[str, Any]
    search_results: Optional[List[Dict[str, Any]]]
    final_response: Optional[Dict[str, Any]]
    input_tokens: Annotated[Dict[str, int], merge_dict]
    output_tokens: Annotated[Dict[str, int], merge_dict]
    time_taken: Annotated[Dict[str, float], merge_dict]


class DynamicAgent:
    def __init__(
        self,
        session_manager: SessionManager,
        weaviate_service: WeaviateService,
        openai_service: OpenAIService,
        prompt_manager: PromptManager,
    ):
        logger.info("Initializing DynamicAgent")
        self.session_manager = session_manager
        self.weaviate_service = weaviate_service
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()
        self.workflow = self.setup_workflow()
        logger.debug("DynamicAgent initialization complete")

    def setup_workflow(self) -> StateGraph:
        logger.info("Setting up DynamicAgent workflow")
        workflow = StateGraph(DynamicAgentState)

        # Core nodes
        workflow.add_node("initial_analysis", self.initial_analysis_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("response_generation", self.response_generation_node)

        # Entry point
        workflow.set_entry_point("initial_analysis")

        # Conditional edges based on filter presence
        workflow.add_conditional_edges(
            "initial_analysis",
            self.route_by_filters,
            {"has_filters": "product_search", "no_filters": END},
        )

        workflow.add_edge("product_search", "response_generation")
        workflow.add_edge("response_generation", END)

        logger.debug("Workflow setup complete")
        return workflow.compile()

    def route_by_filters(self, state: DynamicAgentState) -> str:
        has_filters = "has_filters" if state.get("filters") else "no_filters"
        logger.info(f"Routing workflow: {has_filters} (filters: {state.get('filters')})")
        return has_filters

    async def initial_analysis_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info(f"Starting initial analysis for message: {state['current_message'][:100]}...")
        start_time = time.time()

        logger.debug("Generating analysis prompts")
        system_message, user_message = self.prompt_manager.get_dynamic_analysis_prompt(
            query=state["current_message"], chat_history=state["chat_history"]
        )

        logger.debug(f"Sending request to OpenAI (model: {state['model_name']})")
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            model=state["model_name"],
            temperature=0.1,
        )

        try:
            logger.debug(f"Raw OpenAI response: {response}")
            parsed_response = self.response_formatter._clean_response(response)
            logger.info(f"Parsed analysis result: {json.dumps(parsed_response, indent=2)}")
        except ValueError as e:
            logger.error(f"Failed to parse initial analysis response: {e}", exc_info=True)
            raise

        logger.info(f"Initial analysis complete in {time.time() - start_time:.2f}s")

        # if parsed_response.get("direct_response") is not None:
        filters = parsed_response.get("filters")
        if filters:
            return {
                "filters": filters,
                "query_context": parsed_response.get("query_context"),
                "input_tokens": {"analysis": input_tokens},
                "output_tokens": {"analysis": output_tokens},
                "time_taken": {"analysis": time.time() - start_time},
            }

        return {
            "final_response": parsed_response.get("direct_response"),
            "input_tokens": {"analysis": input_tokens},
            "output_tokens": {"analysis": output_tokens},
            "time_taken": {"analysis": time.time() - start_time},
        }

    async def product_search_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info("Starting product search")
        start_time = time.time()

        limit = state["query_context"].get("num_products_requested", 5)
        filters = state["filters"]
        logger.debug(f"Search parameters - Limit: {limit}, Filters: {json.dumps(filters, indent=2)}")

        # Construct query for hybrid search based on filters
        filter_query = " ".join([f"{key}:{value}" for key, value in filters.items()])

        unique_results = {}

        # Perform hybrid search with all filters
        initial_results = await self.weaviate_service.search_products(
            query=filter_query, limit=limit * 2, filters=filters, search_type="hybrid"
        )

        for result in initial_results:
            if len(unique_results) >= limit:
                break
            unique_results[result["product_id"]] = result

        # If not enough results, perform partial hybrid searches
        if len(unique_results) < limit:
            for key, value in filters.items():
                partial_results = await self.weaviate_service.search_products(
                    query=f"{key}:{value}", limit=limit, filters={key: value}, search_type="hybrid"
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
        logger.debug(f"Final results: {json.dumps(final_results, indent=2)}")

        logger.info(
            f"Product search complete. Found {len(final_results)} unique products in {time.time() - start_time:.2f}s"
        )

        return {
            "search_results": final_results,
            "time_taken": {"search": time.time() - start_time},
        }

    async def response_generation_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info("Starting response generation")
        start_time = time.time()

        # Generate response incorporating product search results
        system_message, user_message = self.prompt_manager.get_dynamic_response_prompt(
            query=state["current_message"],
            products=json.dumps(state.get("search_results", [])),
            filters=json.dumps(state.get("filters", {})),
        )

        logger.debug("Generated response prompts")

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            model=state["model_name"],
        )

        logger.debug(f"Raw OpenAI response: {response}")

        try:
            final_response = self.response_formatter._clean_response(response)
            logger.info("Successfully parsed response")
            logger.debug(f"Parsed response: {json.dumps(final_response, indent=2)}")
        except ValueError as e:
            logger.error("Failed to parse response generation result", exc_info=True)
            raise

        logger.info(f"Response generation complete in {time.time() - start_time:.2f}s")

        return {
            "final_response": final_response,
            "input_tokens": {"generate": input_tokens if "input_tokens" in locals() else 0},
            "output_tokens": {"generate": output_tokens if "output_tokens" in locals() else 0},
            "time_taken": {"generate": time.time() - start_time},
        }

    async def run(self, message: Message) -> Dict[str, Any]:
        logger.info(f"Starting new DynamicAgent run for session {message.session_id}")
        logger.debug(f"Full message details: {message}")

        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )

        initial_state: DynamicAgentState = {
            "model_name": message.model,
            "chat_history": chat_history,
            "current_message": message.message,
            "filters": None,
            "query_context": None,
            "search_results": None,
            "final_response": None,
            "input_tokens": {},
            "output_tokens": {},
            "time_taken": {},
        }

        try:
            logger.info("Beginning workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed successfully")
            logger.debug(f"Final state: {json.dumps(final_state, indent=2)}")

            return self.format_final_response(final_state)
        except Exception as e:
            logger.error("Error in DynamicAgent execution", exc_info=True)
            return self.response_formatter.format_error_response(str(e))

    def format_final_response(self, final_state: DynamicAgentState) -> Dict[str, Any]:
        """Format the final response using the ResponseFormatter"""
        if final_state.get("final_response"):
            return self.response_formatter.format_response(
                "dynamic_agent",
                final_state["final_response"],
                {
                    "input_token_usage": final_state["input_tokens"],
                    "output_token_usage": final_state["output_tokens"],
                    "time_taken": final_state["time_taken"],
                },
                products=final_state.get("search_results", []),
            )
        else:
            raise ValueError("No final response generated")
