import json
import time
import asyncio
import logging
import uuid
from typing import List, Dict, Any, TypedDict, Annotated
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from core.models.message import Message
from core.session_manager import SessionManager
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from .utils.response_formatter import ResponseFormatter
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage, SystemMessage

logger = logging.getLogger(__name__)


def merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


class DynamicAgentState(TypedDict):
    messages: List[AnyMessage]
    chat_history: List[Dict[str, str]]
    current_message: str
    model_name: str
    input_tokens: Annotated[Dict[str, int], merge_dict]
    output_tokens: Annotated[Dict[str, int], merge_dict]
    time_taken: Annotated[Dict[str, float], merge_dict]
    output: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    last_action: str


class DynamicAgent:
    def __init__(
        self,
        session_manager: SessionManager,
        openai_service: OpenAIService,
        weaviate_service: WeaviateService,
        query_processor: QueryProcessor,
        prompt_manager: PromptManager,
    ):
        self.session_manager = session_manager
        self.openai_service = openai_service
        self.weaviate_service = weaviate_service
        self.query_processor = query_processor
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(DynamicAgentState)

        workflow.add_node("agent", self.agent_step)
        workflow.add_node("pipeline", self.pipeline_step)

        workflow.add_conditional_edges(
            "agent", self.should_use_pipeline, {"use_pipeline": "pipeline", "end": END, "continue": "agent"}
        )
        workflow.add_edge("pipeline", "agent")

        workflow.set_entry_point("agent")

        return workflow.compile()

    async def agent_step(self, state: DynamicAgentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_dynamic_agent_prompt(state["current_message"])

        if state["search_results"]:
            user_message += f"\n\nSearch Results: {json.dumps(state['search_results'], indent=2)}"

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=state["chat_history"],
            model=state["model_name"],
        )

        if response.strip().startswith("ACTION:"):
            response = response.strip()[7:].strip()

        logger.info(f"Agent step response: {response}")

        return {
            "messages": state["messages"] + [HumanMessage(content=response)],
            "input_tokens": {"agent": input_tokens},
            "output_tokens": {"agent": output_tokens},
            "time_taken": {"agent": time.time() - start_time},
            "last_action": "agent",
        }

    def should_use_pipeline(self, state: DynamicAgentState) -> str:
        last_message = state["messages"][-1]
        try:
            action = json.loads(last_message.content)
            if "tool" in action:
                return "use_pipeline"
            elif state["last_action"] == "pipeline":
                return "continue"
            else:
                return "end"
        except json.JSONDecodeError:
            if state["last_action"] == "pipeline":
                return "continue"
            else:
                return "end"

    async def pipeline_step(self, state: DynamicAgentState, config: RunnableConfig) -> Dict[str, Any]:
        start_time = time.time()
        last_message = state["messages"][-1]

        try:
            pipeline_action = json.loads(last_message.content)
            pipeline_name = pipeline_action["tool"]
            pipeline_input = pipeline_action["input"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error in pipeline action: {str(e)}")
            return {
                "messages": state["messages"]
                + [ToolMessage(content=f"Error in pipeline action: {str(e)}", tool_call_id=str(uuid.uuid4()))],
                "time_taken": {"pipeline": time.time() - start_time},
                "last_action": "pipeline",
            }

        if pipeline_name not in ["direct_search", "expanded_search"]:
            logger.warning(f"Unknown pipeline: {pipeline_name}")
            return {
                "messages": state["messages"]
                + [ToolMessage(content=f"Unknown pipeline: {pipeline_name}", tool_call_id=str(uuid.uuid4()))],
                "time_taken": {"pipeline": time.time() - start_time},
                "last_action": "pipeline",
            }

        result = await getattr(self, pipeline_name)(**pipeline_input)
        logger.info(f"Pipeline {pipeline_name} result: {result}")

        return {
            "messages": state["messages"] + [ToolMessage(content=json.dumps(result), tool_call_id=str(uuid.uuid4()))],
            "search_results": result.get("results", []),
            "time_taken": {pipeline_name: time.time() - start_time},
            "last_action": "pipeline",
        }

    async def direct_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        results = await self.weaviate_service.search_products(query, limit)
        return {"results": results}

    async def expanded_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        expanded_result, input_tokens, output_tokens = await self.query_processor.process_query_comprehensive(query, [])
        expanded_queries = expanded_result["expanded_queries"]

        async def search(exp_query):
            return await self.weaviate_service.search_products(exp_query, limit)

        all_results = await asyncio.gather(*[search(q) for q in expanded_queries])
        all_results = [item for sublist in all_results for item in sublist]  # Flatten the list

        reranked_results, rerank_input_tokens, rerank_output_tokens = await self.query_processor.rerank_products(
            query, [], all_results, expanded_result["filters"], expanded_result["query_context"], limit
        )

        return {
            "results": reranked_results["products"],
            "input_tokens": {"expand": input_tokens, "rerank": rerank_input_tokens},
            "output_tokens": {"expand": output_tokens, "rerank": rerank_output_tokens},
        }

    async def run(self, message: Message) -> Dict[str, Any]:
        logger.info(f"Running DynamicAgent with message: {message}")
        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )

        initial_state: DynamicAgentState = {
            "messages": [HumanMessage(content=message.message)],
            "chat_history": chat_history,
            "current_message": message.message,
            "model_name": message.model,
            "input_tokens": {},
            "output_tokens": {},
            "time_taken": {},
            "output": {},
            "search_results": [],
            "last_action": "",
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            response = final_state["messages"][-1].content
            metadata = {
                "input_token_usage": final_state["input_tokens"],
                "output_token_usage": final_state["output_tokens"],
                "time_taken": final_state["time_taken"],
            }

            try:
                parsed_response = json.loads(response)
            except json.JSONDecodeError:
                parsed_response = {"message": response}

            return self.response_formatter.format_response(
                "dynamic_agent", parsed_response, metadata, final_state.get("search_results", [])
            )

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            error_response = self.response_formatter.format_error_response(
                "An unexpected error occurred during processing."
            )
            return error_response
