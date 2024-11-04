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
from typing import List, Dict, Any, Literal, TypedDict, Optional, Annotated

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
    search_method: Optional[Literal["filtered", "semantic", "hybrid", "direct"]]
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
        workflow.add_node("filtered_product_search", self.filtered_product_search_node)
        workflow.add_node("fill_remaining_products", self.fill_remaining_products_node)
        workflow.add_node("semantic_product_search", self.semantic_product_search_node)
        workflow.add_node("response_generation", self.response_generation_node)

        # Entry point
        workflow.set_entry_point("initial_analysis")

        # Conditional edges based on analysis result
        workflow.add_conditional_edges(
            "initial_analysis",
            self.route_by_analysis,
            {
                "filtered_search": "filtered_product_search",
                "semantic_search": "semantic_product_search",
                "direct_response": "response_generation",
            },
        )

        # Product search paths
        workflow.add_conditional_edges(
            "filtered_product_search",
            self.route_by_remaining_products,
            {
                "remaining_products": "fill_remaining_products",
                "no_remaining_products": "response_generation",
            },
        )
        workflow.add_edge("fill_remaining_products", "response_generation")
        workflow.add_edge("semantic_product_search", "response_generation")
        workflow.add_edge("response_generation", END)

        logger.debug("Workflow setup complete")
        return workflow.compile()

    def route_by_analysis(self, state: DynamicAgentState) -> str:
        logger.info("Routing based on analysis results")

        try:
            # If we have a direct response, route directly to response generation
            if state.get("final_response"):
                logger.debug("Routing to direct response generation")
                return "direct_response"

            # If we have filters, route to filtered search
            if state.get("filters"):
                logger.debug(f"Routing to filtered search with filters: {state.get('filters')}")
                return "filtered_search"

            # If we have a product request without filters, route to semantic search
            if state.get("query_context", {}).get("num_products_requested"):
                logger.debug("Routing to semantic search")
                return "semantic_search"

            # Default fallback to direct response
            logger.debug("Fallback routing to direct response")
            return "direct_response"
        except Exception as e:
            logger.error(f"Error in route_by_analysis: {str(e)}", exc_info=True)
            return "direct_response"

    def route_by_remaining_products(self, state: DynamicAgentState) -> str:
        try:
            remaining_limit = state.get("remaining_limit", 0)
            return "remaining_products" if remaining_limit > 0 else "no_remaining_products"
        except Exception as e:
            logger.error(f"Error in route_by_remaining_products: {str(e)}", exc_info=True)
            return "no_remaining_products"

    async def initial_analysis_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info(f"Starting initial analysis for message: {state['current_message'][:100]}...")
        start_time = time.time()

        try:
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

            logger.debug(f"Raw OpenAI response: {response}")
            parsed_response = self.response_formatter._clean_response(response)
            logger.info(f"Parsed analysis result: {json.dumps(parsed_response, indent=2)}")

            # Ensure query_context is always initialized
            query_context = parsed_response.get("query_context", {})
            if not isinstance(query_context, dict):
                query_context = {"num_products_requested": 5}

            # Ensure num_products_requested is always present
            if "num_products_requested" not in query_context:
                query_context["num_products_requested"] = 5

            return {
                "filters": parsed_response.get("filters"),
                "query_context": query_context,
                "final_response": parsed_response.get("direct_response"),
                "input_tokens": {"analysis": input_tokens},
                "output_tokens": {"analysis": output_tokens},
                "time_taken": {"analysis": time.time() - start_time},
            }
        except Exception as e:
            logger.error(f"Error in initial analysis: {str(e)}", exc_info=True)
            return {
                "filters": None,
                "query_context": {"num_products_requested": 5},
                "final_response": {
                    "message": "I apologize, but I encountered an error while processing your request. Could you please rephrase it?",
                    "follow_up_question": "What specific information would you like to know about our hardware products?",
                },
                "input_tokens": {"analysis": 0},
                "output_tokens": {"analysis": 0},
                "time_taken": {"analysis": time.time() - start_time},
            }

    async def filtered_product_search_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info("Starting filtered product search")
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

        logger.info(f"Found {len(final_results)} products with filters")
        remaining_count = max(0, limit - len(final_results))

        return {
            "search_results": final_results,
            "search_method": "filtered",
            "remaining_limit": remaining_count,
            "time_taken": {"filtered_search": time.time() - start_time},
        }

    async def fill_remaining_products_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info("Starting to fill remaining products")
        start_time = time.time()

        remaining_limit = state.get("remaining_limit", 0)
        if remaining_limit <= 0:
            logger.info("No additional products needed")
            return state

        current_results = state.get("search_results", [])
        existing_ids = {result["product_id"] for result in current_results}

        # Use semantic search without filters to find additional products
        additional_results = await self.weaviate_service.search_products(
            query=state["current_message"],
            limit=remaining_limit * 2,  # Get extra for better matching
            search_type="semantic",
        )

        # Filter out duplicates and add new products
        new_results = []
        for result in additional_results:
            if len(new_results) >= remaining_limit:
                break
            if result["product_id"] not in existing_ids:
                new_results.append(result)
                existing_ids.add(result["product_id"])

        final_results = current_results + new_results

        logger.info(f"Added {len(new_results)} additional products")

        return {
            "search_results": final_results,
            "search_method": "hybrid",
            "time_taken": {"fill_products": time.time() - start_time},
        }

    async def semantic_product_search_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info("Starting semantic product search")
        start_time = time.time()

        limit = state["query_context"].get("num_products_requested", 5)

        # Perform semantic search
        results = await self.weaviate_service.search_products(
            query=state["current_message"],
            limit=limit * 2,  # Get more results for better matching
            search_type="semantic",
        )

        # Deduplicate results
        unique_results = {}
        for result in results:
            if len(unique_results) >= limit:
                break
            unique_results[result["product_id"]] = result

        final_results = list(unique_results.values())[:limit]

        logger.info(f"Found {len(final_results)} products through semantic search")

        return {
            "search_results": final_results,
            "search_method": "semantic",
            "time_taken": {"semantic_search": time.time() - start_time},
        }

    async def response_generation_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        logger.info("Starting response generation")
        start_time = time.time()

        if state.get("final_response"):  # Direct response from initial analysis
            logger.info("Using direct response")
            return {
                "final_response": state["final_response"],
                "input_tokens": {"generate": 0},
                "output_tokens": {"generate": 0},
                "time_taken": {"generate": time.time() - start_time},
            }

        # Prepare product data with safe filter handling
        product_data = []
        filters = state.get("filters", {}) or {}  # Default to empty dict if None

        for p in state["search_results"]:
            product = {
                "product_id": p["product_id"],
                "name": p["name"],
                "summary": p.get("full_product_description", ""),
            }
            # Only add filter attributes if we have filters
            if filters:
                product.update({attr: p.get(attr, "Not specified") for attr in filters.keys()})
            product_data.append(product)

        relevant_products = json.dumps(product_data, indent=2)

        # Generate response incorporating product results
        system_message, user_message = self.prompt_manager.get_dynamic_response_prompt(
            query=state["current_message"],
            products=relevant_products,
            filters=json.dumps(state.get("filters", {})),
            search_method=state.get("search_method", "hybrid"),
        )

        logger.debug(f"\n\nSystem message: {system_message}\n\n")
        logger.debug(f"\n\nUser message: {user_message}\n\n")

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            model=state["model_name"],
        )

        try:
            final_response = self.response_formatter._clean_response(response)
            logger.info("Generated product-based response")
            logger.debug(f"Final response: {json.dumps(final_response, indent=2)}")
        except ValueError as e:
            logger.error("Failed to parse response generation result", exc_info=True)
            raise

        return {
            "final_response": final_response,
            "input_tokens": {"generate": input_tokens},
            "output_tokens": {"generate": output_tokens},
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
                    "filters": final_state.get("filters"),
                    "num_products": final_state["query_context"].get("num_products_requested"),
                    "search_method": final_state.get("search_method"),
                    "input_token_usage": final_state["input_tokens"],
                    "output_token_usage": final_state["output_tokens"],
                    "time_taken": final_state["time_taken"],
                },
                products=final_state.get("search_results", []),
            )
        else:
            raise ValueError("No final response generated")
