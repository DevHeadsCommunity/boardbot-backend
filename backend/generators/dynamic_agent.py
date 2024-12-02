import time
import logging
import json
import traceback
from langgraph.graph import StateGraph, END
from core.models.message import Message
from core.session_manager import SessionManager
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from services.anthropic_service import AnthropicService
from .utils.response_formatter import ResponseFormatter
from typing import List, Dict, Any, Literal, Tuple, TypedDict, Optional, Annotated, Callable, Union
from functools import wraps

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


def format_log_data(data: Dict[str, Any]) -> str:
    """Helper to format dictionary data for logging"""
    if data is None:
        return "null"
    return json.dumps(data, indent=2, default=str)


def format_exception(e: Exception) -> str:
    """Format exception with traceback for logging"""
    return "".join(traceback.format_exception(type(e), e, e.__traceback__))


class DynamicAgentState(TypedDict):
    model_name: str
    current_message: str
    chat_history: List[Dict[str, str]]
    filters: Optional[Dict[str, Any]]
    entities: Optional[Dict[str, List[str]]]
    sort_context: Optional[Dict[str, Any]]
    num_products_requested: int
    search_results: Optional[List[Dict[str, Any]]]
    search_method: Optional[Literal["sorted_query", "hybrid", "semantic"]]
    final_response: Optional[Dict[str, Any]]
    input_tokens: Annotated[Dict[str, int], merge_dict]
    output_tokens: Annotated[Dict[str, int], merge_dict]
    time_taken: Annotated[Dict[str, float], merge_dict]
    security_flag: Optional[str]


class LogConfig:
    def __init__(self, before: Optional[List[str]] = None, after: Optional[List[str]] = None, log_result: bool = False):
        self.before = before or []
        self.after = after or []
        self.log_result = log_result


def log_node(node_name: str, config: Optional[Union[LogConfig, Dict[str, List[str]]]] = None):
    """
    Enhanced decorator for logging node execution with separate before/after state logging

    Args:
        node_name: Name of the node for logging
        config: Either a LogConfig object or a dict with {'before': [...], 'after': [...]}
    """
    if isinstance(config, dict):
        config = LogConfig(**config)
    config = config or LogConfig()

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, state: Dict[str, Any], *args, **kwargs):
            def log_state(attributes: List[str]):
                for attr in attributes:
                    if attr in state:
                        friendly_name = attr.replace("_", " ").title()
                        value = state[attr]
                        logger.info(f"║ {friendly_name}: {format_log_data(value)}")

            # Log before execution
            if config.before:
                logger.info("╔══════════════════════════════════════════")
                logger.info(f"║ Starting {node_name}")
                log_state(config.before)

            try:
                start_time = time.time()
                result = await func(self, state, *args, **kwargs)
                execution_time = time.time() - start_time

                # Log after execution
                if config.after or config.log_result:
                    if not config.before:  # Only print header if not already printed
                        logger.info("╔══════════════════════════════════════════")
                        logger.info(f"║ Completed {node_name}")
                    log_state(config.after)
                    if config.log_result:
                        logger.info(f"║ Result: {format_log_data(result)}")
                    logger.info(f"║ Execution Time: {execution_time:.2f}s")

                if config.before or config.after or config.log_result:
                    logger.info("╚══════════════════════════════════════════")

                return result

            except Exception as e:
                logger.error("╔══════════════════════════════════════════")
                logger.error(f"║ ❌ Error in {node_name}")
                logger.error(f"║ Type: {type(e).__name__}")
                logger.error(f"║ Message: {str(e)}")
                logger.error("║ Traceback:")
                for line in format_exception(e).split("\n"):
                    if line.strip():
                        logger.error(f"║ {line}")
                logger.error("╚══════════════════════════════════════════")
                raise

        return wrapper

    return decorator


class DynamicAgent:
    SECURITY_RESPONSES = {
        "exploit": {
            "message": "I cannot assist with system exploitation. I'm designed to help with legitimate hardware queries.",
            "follow_up_question": "What specific hardware information can I help you find?",
        },
        "inappropriate": {
            "message": "I focus on hardware-related queries. Please keep our discussion professional and related to computer hardware.",
            "follow_up_question": "What hardware specifications would you like to learn about?",
        },
        "political": {
            "message": "I specialize in computer hardware discussions. For political topics, please consult appropriate news sources.",
            "follow_up_question": "How can I assist you with your hardware needs?",
        },
    }

    def __init__(
        self,
        session_manager: SessionManager,
        weaviate_service: WeaviateService,
        openai_service: OpenAIService,
        anthropic_service: AnthropicService,
        prompt_manager: PromptManager,
    ):
        self.session_manager = session_manager
        self.weaviate_service = weaviate_service
        self.openai_service = openai_service
        self.anthropic_service = anthropic_service
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(DynamicAgentState)

        # Core nodes
        workflow.add_node("initial_analysis", self.initial_analysis_node)
        workflow.add_node("security_response", self.security_response_node)
        workflow.add_node("direct_response", self.direct_response_node)
        workflow.add_node("sorted_query", self.sorted_query_node)
        workflow.add_node("hybrid_search", self.hybrid_search_node)
        workflow.add_node("semantic_search", self.semantic_search_node)
        workflow.add_node("response_generation", self.response_generation_node)

        # Entry point
        workflow.set_entry_point("initial_analysis")

        # Conditional edges based on analysis result
        workflow.add_conditional_edges(
            "initial_analysis",
            self.route_by_analysis,
            {
                "security_response": "security_response",
                "direct_response": "direct_response",
                "sorted_query": "sorted_query",
                "hybrid_search": "hybrid_search",
                "semantic_search": "semantic_search",
            },
        )

        # Add remaining edges
        workflow.add_edge("security_response", END)
        workflow.add_edge("direct_response", END)
        workflow.add_edge("sorted_query", "response_generation")
        workflow.add_edge("hybrid_search", "response_generation")
        workflow.add_edge("semantic_search", "response_generation")
        workflow.add_edge("response_generation", END)

        return workflow.compile()

    def route_by_analysis(self, state: DynamicAgentState) -> str:
        """Routes analysis results to appropriate handler"""
        # Check security first
        if state.get("security_flag"):
            return "security_response"

        # Check for direct response
        if state.get("final_response"):
            return "direct_response"

        # Check for sort context
        if state.get("sort_context") and isinstance(state["sort_context"], dict) and state["sort_context"]:
            return "sorted_query"

        # Check for filters
        if state.get("filters") and isinstance(state["filters"], dict) and state["filters"]:
            return "hybrid_search"

        # Check for entities
        if state.get("entities") and isinstance(state["entities"], dict) and state["entities"]:
            return "semantic_search"

        # Default to semantic search if only num_products_requested is present
        if state.get("num_products_requested"):
            return "semantic_search"

        raise ValueError("No valid routing option found")

    async def _get_llm_service(self, model_name: str):
        if model_name.startswith(("gpt-", "text-")):
            return self.openai_service
        elif model_name.startswith("claude-"):
            return self.anthropic_service
        else:
            raise ValueError(f"Unsupported model: {model_name}")

    @log_node(
        "Initial Analysis",
        {
            "before": ["current_message", "chat_history"],
            "after": ["security_flag", "filters", "sort_context", "entities", "num_products_requested"],
            "log_result": True,
        },
    )
    async def initial_analysis_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        """Enhanced initial analysis with better context handling and sort extraction"""
        start_time = time.time()
        try:
            # Generate analysis prompts with chat history context
            system_message, user_message = self.prompt_manager.get_dynamic_analysis_prompt(
                query=state["current_message"], chat_history=state["chat_history"]
            )

            llm_service = await self._get_llm_service(state["model_name"])
            response, input_tokens, output_tokens = await llm_service.generate_response(
                user_message=user_message,
                system_message=system_message,
                formatted_chat_history=state["chat_history"],
                model=state["model_name"],
                temperature=0.0,
            )

            parsed_response = self.response_formatter._clean_response(response)
            security_flag = self._check_security(parsed_response)
            final_response = parsed_response.get("direct_response")
            sort_context, filters, entities, num_products_requested = self._process_query_context(parsed_response)

            return {
                "security_flag": security_flag,
                "final_response": final_response,
                "filters": filters,
                "sort_context": sort_context,
                "entities": entities,
                "num_products_requested": num_products_requested,
                "input_tokens": {"analysis": input_tokens},
                "output_tokens": {"analysis": output_tokens},
                "time_taken": {"analysis": time.time() - start_time},
            }
        except Exception as e:  # noqa: F841
            return self._generate_error_state(start_time)

    def _process_query_context(
        self, parsed_response: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], int]:
        query_context = parsed_response.get("query_context", {})
        sort_context = query_context.get("sort")
        filters = query_context.get("filters")
        entities = query_context.get("entities")
        num_products_requested = query_context.get("num_products_requested", 5)
        return sort_context, filters, entities, num_products_requested

    def _check_security(self, response: Dict[str, Any]) -> Optional[str]:
        flags = response.get("security_flags", [])
        for flag in ["exploit", "inappropriate", "political"]:
            if flag in flags:
                return flag
        return None

    @log_node(
        "Sorted Query",
        {
            "before": ["search_method", "sort_context", "filters", "num_products_requested"],
            "after": ["search_results"],
            "log_result": True,
        },
    )
    async def sorted_query_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        """Execute direct database query with sorting for exact product matches."""
        start_time = time.time()

        try:
            # Extract sorting parameters
            sort_context = state["sort_context"]
            if not sort_context or "field" not in sort_context or "order" not in sort_context:
                logger.error("Invalid sort context")
                return self._generate_error_state(start_time, "sort")

            # Create SearchParams for filtered query with sorting
            search_params = self._prepare_search_params(state, "filtered")

            # Execute search
            results = await self.weaviate_service.search_products(search_params)

            return {
                "search_results": results,
                "search_method": "sorted_query",
                "time_taken": {"sorted_query": time.time() - start_time},
            }

        except Exception as e:
            logger.error(f"Error in sorted query: {str(e)}", exc_info=True)
            return self._generate_error_state(start_time, "sort")

    async def security_response_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        security_type = state.get("security_flag", "inappropriate")
        return {
            "final_response": self.SECURITY_RESPONSES[security_type],
            "input_tokens": {"security": 0},
            "output_tokens": {"security": 0},
            "time_taken": {"security": 0},
        }

    def construct_semantic_context(
        self, entities: Optional[Dict[str, List[str]]], filters: Optional[Dict[str, Any]]
    ) -> str:
        """Construct deterministic semantic context"""
        if not entities:
            entities = {}
        if not filters:
            filters = {}
        context_parts = []

        # Normalize and sort entities
        normalized_entities = {}
        for group, values in entities.items():
            normalized_values = [v.lower().strip() for v in values]
            normalized_entities[group.lower().strip()] = sorted(normalized_values)

        # Build context with normalized values
        for entity_group in sorted(normalized_entities.keys()):
            values = normalized_entities[entity_group]
            context_parts.append(f"{entity_group}: {', '.join(values)}")

        # Add normalized filters
        ordered_filters = self._order_filters(filters)
        for key, value in ordered_filters.items():
            if isinstance(value, list):
                value_str = ", ".join(sorted(str(v) for v in value))
            else:
                value_str = str(value)
            context_parts.append(f"{key}: {value_str}")

        return ". ".join(context_parts)

    def _order_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Order filters using attribute ordering from schema"""
        ordered_attributes = [
            "name",
            "manufacturer",
            "form_factor",
            "evaluation_or_commercialization",
            "processor_architecture",
            "processor_core_count",
            "processor_manufacturer",
            "processor_tdp",
            "memory",
            "onboard_storage",
            "input_voltage",
            "io_count",
            "wireless",
            "operating_system_bsp",
            "operating_temperature_min",
            "operating_temperature_max",
            "certifications",
            "price",
            "stock_availability",
            "lead_time",
        ]
        # Add validation and normalization of filter values
        normalized_filters = {}
        for k in ordered_attributes:
            if k in filters:
                # Normalize the value based on type
                value = filters[k]
                if isinstance(value, list):
                    value = sorted(value)  # Sort lists
                elif isinstance(value, str):
                    value = value.lower().strip()  # Normalize strings
                normalized_filters[k] = value
        return normalized_filters

    @log_node(
        "Hybrid Search",
        {
            "before": ["search_method", "filters", "entities", "num_products_requested"],
            "after": ["search_results"],
            "log_result": True,
        },
    )
    async def hybrid_search_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        """Perform hybrid search combining filters and semantic similarity"""
        start_time = time.time()

        try:
            entities = state.get("entities", {})
            # Order filters before constructing semantic context
            ordered_filters = self._order_filters(state.get("filters", {}))
            semantic_context = self.construct_semantic_context(entities, ordered_filters)

            search_params = self._prepare_search_params(state, "hybrid")

            results = await self.weaviate_service.search_products(search_params)

            return {
                "search_results": results,
                "search_method": "hybrid",
                "time_taken": {"hybrid_search": time.time() - start_time},
            }

        except Exception as e:
            return self._generate_error_state(start_time, "search")

    @log_node(
        "Semantic Search",
        {
            "before": ["search_method", "entities", "num_products_requested"],
            "after": ["search_results"],
            "log_result": True,
        },
    )
    async def semantic_search_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        """Execute semantic search using vector similarity"""
        start_time = time.time()
        try:
            entities = state.get("entities", {})
            # Use empty dict for filters but maintain ordering in semantic context
            semantic_context = self.construct_semantic_context(entities, {})

            search_params = self._prepare_search_params(state, "semantic")

            results = await self.weaviate_service.search_products(search_params)

            return {
                "search_results": results,
                "search_method": "semantic",
                "time_taken": {"semantic_search": time.time() - start_time},
            }

        except Exception as e:
            return self._generate_error_state(start_time, "search")

    async def direct_response_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        """Handle direct responses that don't require product search"""
        start_time = time.time()
        return {
            "final_response": state["final_response"],
            "input_tokens": {"direct": 0},
            "output_tokens": {"direct": 0},
            "time_taken": {"direct": time.time() - start_time},
        }

    @log_node(
        "Response Generation",
        {
            "before": ["search_method"],
            "after": ["final_response"],
            "log_result": True,
        },
    )
    async def response_generation_node(self, state: DynamicAgentState) -> Dict[str, Any]:
        """Enhanced response generation with sort awareness"""
        start_time = time.time()

        # Prepare context for response generation
        context = {
            "products": self._prepare_product_data(state),
            "filters": state.get("filters", {}),
            "sort": state.get("sort_context"),
            "entities": state.get("entities", {}),
            "search_method": state.get("search_method", "semantic"),
        }

        system_message, user_message = self.prompt_manager.get_dynamic_response_prompt(
            query=state["current_message"], **context
        )

        # Get the appropriate service based on model name
        llm_service = await self._get_llm_service(state["model_name"])

        response, input_tokens, output_tokens = await llm_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            model=state["model_name"],
            temperature=0.0,
        )

        final_response = self.response_formatter._clean_response(response)

        return {
            "final_response": final_response,
            "input_tokens": {"generate": input_tokens},
            "output_tokens": {"generate": output_tokens},
            "time_taken": {"generate": time.time() - start_time},
        }

    @log_node(
        "DynamicAgent Run",
        {
            "before": ["model_name", "current_message", "session_id"],
            "log_result": True,
        },
    )
    async def run(self, message: Message) -> Dict[str, Any]:

        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )

        initial_state: DynamicAgentState = {
            "model_name": message.model,
            "chat_history": chat_history,
            "current_message": message.message,
            "filters": None,
            "entities": None,
            "sort_context": None,
            "num_products_requested": 5,
            "search_results": None,
            "final_response": None,
            "security_flag": None,
            "input_tokens": {},
            "output_tokens": {},
            "time_taken": {},
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)
            return self.format_final_response(final_state)
        except Exception as e:  # noqa: F841
            return self.response_formatter.format_error_response(str(e))

    def _prepare_product_data(self, state: DynamicAgentState) -> List[Dict[str, Any]]:
        """Prepare product data for response generation"""
        product_data = []
        filters = state.get("filters", {}) or {}
        sort_context = state.get("sort_context")

        for p in state.get("search_results", []):
            product = {
                "product_id": p["product_id"],
                "name": p["name"],
                "summary": p.get("full_product_description", ""),
            }
            # Include filter-relevant attributes
            if filters:
                product.update({attr: p.get(attr) for attr in filters.keys()})
            # Include sort-relevant attributes
            if sort_context:
                product[sort_context["field"]] = p.get(sort_context["field"])
            product_data.append(product)

            logger.info(f"===:> Product: {product}")

        return product_data

    def format_final_response(self, final_state: DynamicAgentState) -> Dict[str, Any]:
        if not final_state.get("final_response"):
            raise ValueError("No final response generated")

        metadata = {
            "filters": final_state.get("filters"),
            "num_products": final_state.get("num_products_requested"),
            "search_method": final_state.get("search_method"),
            "input_token_usage": final_state["input_tokens"],
            "output_token_usage": final_state["output_tokens"],
            "time_taken": final_state["time_taken"],
        }

        # Get search results if available
        products = final_state.get("search_results", [])

        # Format the response using the standard ResponseFormatter
        return self.response_formatter.format_response(
            "dynamic_agent", final_state["final_response"], metadata, products=products
        )

    def _generate_error_state(self, start_time: float, error_type: str = "general") -> Dict[str, Any]:
        error_messages = {
            "general": "I encountered an error while processing your request.",
            "search": "I couldn't find any products matching your criteria.",
            "filter": "Some of your filter criteria may be invalid.",
            "sort": "There was an issue sorting the results.",
        }

        return {
            "final_response": {
                "message": f"{error_messages.get(error_type, error_messages['general'])} Could you please rephrase your request?",
                "follow_up_question": "What specific information would you like to know about our hardware products?",
            },
            "input_tokens": {"analysis": 0},
            "output_tokens": {"analysis": 0},
            "time_taken": {"analysis": time.time() - start_time},
        }

    def _prepare_search_params(self, state: DynamicAgentState, search_type: str) -> Dict[str, Any]:
        """Prepare consistent search parameters"""
        base_params = {"limit": state["num_products_requested"], "search_type": search_type}

        if search_type in ["filtered", "hybrid"]:
            filters = self._order_filters(state.get("filters", {}))
            base_params["filters"] = filters

        if search_type in ["hybrid", "semantic"]:
            entities = state.get("entities", {})
            semantic_context = self.construct_semantic_context(entities, filters if search_type == "hybrid" else {})
            base_params["query"] = semantic_context

        if search_type == "filtered" and state.get("sort_context"):
            base_params["sort"] = {
                "field": state["sort_context"]["field"],
                "order": state["sort_context"]["order"].lower(),
                "weight": 1.0,
            }

        return base_params
