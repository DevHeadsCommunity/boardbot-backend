import asyncio
import json
import logging
import time
from typing import List, Dict, Any, TypedDict, Optional, Annotated
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from core.models.message import Message
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from services.query_processor import QueryProcessor
from prompts.prompt_manager import PromptManager
from .utils.response_formatter import ResponseFormatter
from core.session_manager import SessionManager

logger = logging.getLogger(__name__)


def merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


class DynamicAgentState(TypedDict):
    model_name: str
    chat_history: List[Dict[str, str]]
    current_message: str
    action: Optional[Dict[str, Any]]
    tool_output: Optional[Dict[str, Any]]
    final_response: Optional[Dict[str, Any]]
    input_tokens: Annotated[Dict[str, int], merge_dict]
    output_tokens: Annotated[Dict[str, int], merge_dict]
    time_taken: Annotated[Dict[str, float], merge_dict]


class DynamicAgent:
    def __init__(
        self,
        session_manager: SessionManager,
        weaviate_service: WeaviateService,
        query_processor: QueryProcessor,
        openai_service: OpenAIService,
        prompt_manager: PromptManager,
    ):
        self.session_manager = session_manager
        self.weaviate_service = weaviate_service
        self.query_processor = query_processor
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(DynamicAgentState)

        workflow.add_node("decision", self.decision_node)
        workflow.add_node("action_execution", self.action_execution_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.set_entry_point("decision")

        workflow.add_conditional_edges(
            "decision", self.route_decision, {"tool": "action_execution", "response": "response_generation"}
        )
        workflow.add_edge("action_execution", "decision")
        workflow.add_edge("response_generation", END)

        return workflow.compile()

    async def run(self, message: Message) -> Dict[str, Any]:
        logger.info(f"Running DynamicAgent with message: {message}")

        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )

        initial_state: DynamicAgentState = {
            "model_name": message.model,
            "chat_history": chat_history,
            "current_message": message.message,
            "action": None,
            "tool_output": None,
            "final_response": None,
            "input_tokens": {},
            "output_tokens": {},
            "time_taken": {},
        }

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed")

            return self.format_final_response(final_state)
        except Exception as e:
            logger.error(f"Error running DynamicAgent: {e}", exc_info=True)
            return self.response_formatter.format_error_response(str(e))

    def route_decision(self, state: DynamicAgentState, config: RunnableConfig) -> str:
        if state["action"] and state["action"].get("action") == "tool":
            return "tool"
        return "response"

    async def decision_node(self, state: DynamicAgentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("Entered decision_node")

        system_message, user_message = self.prompt_manager.get_dynamic_agent_prompt(state["current_message"])
        chat_history = self.prepare_chat_history(state)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=state["model_name"],
        )

        time_taken = time.time() - start_time

        try:
            action = self.response_formatter._clean_response(response)
            logger.info(f"Action decided by LLM: {action}")
        except ValueError as e:
            logger.error(f"Failed to parse LLM response as JSON: {response}")
            raise ValueError(f"Invalid LLM response: {response}")

        return {
            "action": action,
            "input_tokens": {"decision": input_tokens},
            "output_tokens": {"decision": output_tokens},
            "time_taken": {"decision": time_taken},
        }

    async def action_execution_node(self, state: DynamicAgentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("Entered action_execution_node")

        action = state["action"]
        tool_name = action.get("tool")
        tool_input = action.get("input", {})

        if tool_name == "direct_search":
            return await self.execute_direct_search(state, tool_input)
        elif tool_name == "expanded_search":
            return await self.execute_expanded_search(state, tool_input)
        else:
            logger.error(f"Unknown tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")

    async def response_generation_node(self, state: DynamicAgentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("Entered response_generation_node")

        chat_history = self.prepare_chat_history(state)
        system_message, user_message = self.prompt_manager.get_dynamic_agent_prompt(state["current_message"])

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=state["current_message"],
            system_message=system_message,
            formatted_chat_history=chat_history,
            model=state["model_name"],
        )

        time_taken = time.time() - start_time

        try:
            final_response = self.response_formatter._clean_response(response)
            logger.info(f"Final response generated: {final_response}")
        except ValueError as e:
            logger.error(f"Failed to parse LLM response as JSON: {response}")
            raise ValueError(f"Invalid LLM response: {response}")

        return {
            "final_response": final_response,
            "input_tokens": {"generate": input_tokens},
            "output_tokens": {"generate": output_tokens},
            "time_taken": {"generate": time_taken},
        }

    def prepare_chat_history(self, state: DynamicAgentState) -> List[Dict[str, str]]:
        chat_history = state["chat_history"].copy()
        if state.get("tool_output"):
            tool_output_message = {"role": "assistant", "content": json.dumps(state["tool_output"])}
            chat_history.append(tool_output_message)
        return chat_history

    async def execute_direct_search(self, state: DynamicAgentState, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        query = tool_input.get("query", state["current_message"])
        limit = tool_input.get("limit", 5)
        logger.info(f"Executing direct_search with query: {query} and limit: {limit}")

        results = await self.weaviate_service.search_products(query=query, limit=limit)
        tool_output = {"tool": "direct_search", "output": results}

        return {
            "tool_output": tool_output,
            "input_tokens": {"action_execution": 0},
            "output_tokens": {"action_execution": 0},
            "time_taken": {"action_execution": time.time() - start_time},
        }

    async def execute_expanded_search(self, state: DynamicAgentState, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        query = tool_input.get("query", state["current_message"])
        limit = tool_input.get("limit", 10)
        logger.info(f"Executing expanded_search with query: {query} and limit: {limit}")

        query_result, input_tokens_qp, output_tokens_qp = await self.query_processor.process_query_comprehensive(
            query, state["chat_history"], model=state["model_name"]
        )

        expanded_queries = query_result["expanded_queries"]
        filters = query_result["filters"]
        query_context = query_result["query_context"]

        search_results = await self.perform_searches(query, expanded_queries, limit)
        reranked_result = await self.rerank_results(query, state, search_results, filters, query_context, limit)

        tool_output = {"tool": "expanded_search", "output": reranked_result}

        return {
            "tool_output": tool_output,
            "input_tokens": {"action_execution": input_tokens_qp + reranked_result["input_tokens"]},
            "output_tokens": {"action_execution": output_tokens_qp + reranked_result["output_tokens"]},
            "time_taken": {"action_execution": time.time() - start_time},
        }

    async def perform_searches(
        self, original_query: str, expanded_queries: List[str], limit: int
    ) -> List[Dict[str, Any]]:
        queries = [original_query] + expanded_queries
        search_tasks = [
            self.weaviate_service.search_products(query=q, limit=limit, search_type="semantic") for q in queries
        ]
        all_search_results = await asyncio.gather(*search_tasks)

        all_results = [item for sublist in all_search_results for item in sublist]
        unique_results = {result["product_id"].lower(): result for result in all_results}.values()
        return list(unique_results)

    async def rerank_results(
        self,
        query: str,
        state: DynamicAgentState,
        search_results: List[Dict[str, Any]],
        filters: Dict[str, Any],
        query_context: Dict[str, Any],
        limit: int,
    ) -> Dict[str, Any]:
        products_for_reranking = [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                **{attr: p.get(attr, "Not specified") for attr in filters.keys()},
                "summary": p.get("full_product_description", ""),
            }
            for p in search_results
        ]

        top_k = query_context.get("num_products_requested", limit)
        reranked_result, input_tokens_rr, output_tokens_rr = await self.query_processor.rerank_products(
            query,
            state["chat_history"],
            products_for_reranking,
            filters,
            query_context,
            top_k=top_k,
            model=state["model_name"],
        )

        id_to_product = {p["product_id"]: p for p in search_results}
        final_results = [
            id_to_product.get(p["product_id"], p)
            for p in reranked_result["products"]
            if p["product_id"] in id_to_product
        ]

        return {
            "products": final_results,
            "input_tokens": input_tokens_rr,
            "output_tokens": output_tokens_rr,
        }

    def format_final_response(self, final_state: DynamicAgentState) -> Dict[str, Any]:
        if final_state.get("final_response"):
            return self.response_formatter.format_response(
                "dynamic_agent",
                final_state["final_response"],
                {
                    "input_token_usage": final_state["input_tokens"],
                    "output_token_usage": final_state["output_tokens"],
                    "time_taken": final_state["time_taken"],
                },
                products=final_state.get("tool_output", {}).get("output", []),
            )
        else:
            raise ValueError("No final response generated.")
