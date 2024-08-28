import json
import logging
import time
import operator
from typing import List, Dict, Any, Tuple, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from models.message import Message
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from services.query_processor import QueryProcessor
from utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager
from models.product import Product

logger = logging.getLogger(__name__)


class AgentState(Dict[str, Any]):
    messages: Annotated[List[AnyMessage], operator.add]
    chat_history: List[Dict[str, str]]
    current_message: str
    model_name: str
    input_tokens: Dict[str, int] = {}
    output_tokens: Dict[str, int] = {}
    time_taken: Dict[str, float] = {}
    output: Dict[str, Any] = {}
    search_results: List[Tuple[Product, float]] = []


class DynamicAgent:
    def __init__(
        self,
        openai_service: OpenAIService,
        weaviate_service: WeaviateService,
        query_processor: QueryProcessor,
        prompt_manager: PromptManager,
    ):
        self.openai_service = openai_service
        self.weaviate_service = weaviate_service
        self.query_processor = query_processor
        self.prompt_manager = prompt_manager
        self.response_formatter = ResponseFormatter()

        self.pipelines = {
            "direct_search": self.direct_search,
            "expanded_search": self.expanded_search,
        }

        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self.agent_step)
        workflow.add_node("pipeline", self.pipeline_step)

        workflow.add_conditional_edges("agent", self.should_use_pipeline, {True: "pipeline", False: END})
        workflow.add_edge("pipeline", "agent")

        workflow.set_entry_point("agent")

        return workflow.compile()

    async def agent_step(self, state: AgentState) -> Dict[str, Any]:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_dynamic_agent_prompt(
            state["current_message"], state["chat_history"]
        )

        messages = [SystemMessage(content=system_message)] + state["messages"]

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=messages,
            model=state["model_name"],
        )

        state["input_tokens"]["agent"] = state["input_tokens"].get("agent", 0) + input_tokens
        state["output_tokens"]["agent"] = state["output_tokens"].get("agent", 0) + output_tokens
        state["time_taken"]["agent"] = state["time_taken"].get("agent", 0) + (time.time() - start_time)

        return {"messages": [HumanMessage(content=response)]}

    def should_use_pipeline(self, state: AgentState) -> bool:
        last_message = state["messages"][-1]
        return "PIPELINE" in last_message.content

    async def pipeline_step(self, state: AgentState) -> Dict[str, Any]:
        start_time = time.time()
        last_message = state["messages"][-1]
        pipeline_content = last_message.content.split("PIPELINE:", 1)[1].strip()

        try:
            pipeline_action = json.loads(pipeline_content)
            pipeline_name = pipeline_action["pipeline"]
            pipeline_input = pipeline_action["input"]
        except json.JSONDecodeError:
            return {"messages": [ToolMessage(content="Invalid pipeline format. Please use valid JSON.")]}

        if pipeline_name not in self.pipelines:
            return {"messages": [ToolMessage(content=f"Unknown pipeline: {pipeline_name}")]}

        result = await self.pipelines[pipeline_name](**pipeline_input)

        state["time_taken"][pipeline_name] = state["time_taken"].get(pipeline_name, 0) + (time.time() - start_time)

        return {"messages": [ToolMessage(content=json.dumps(result))]}

    async def direct_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        results = await self.weaviate_service.search_products(query, limit)
        return {"results": [{"product": product.dict(), "certainty": certainty} for product, certainty in results]}

    async def expanded_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        expanded_result, _, _ = await self.query_processor.process_query_comprehensive(query, [])
        expanded_queries = expanded_result["expanded_queries"]

        all_results = []
        for exp_query in expanded_queries:
            results = await self.weaviate_service.search_products(exp_query, limit)
            all_results.extend(results)

        reranked_results, _, _ = await self.query_processor.rerank_products(query, [], all_results, limit)

        return {"results": reranked_results}

    async def run(self, message: Message) -> Tuple[str, Dict[str, Any]]:
        chat_history = self.session_manager.get_formatted_chat_history(
            message.session_id, message.history_management_choice, "message_only"
        )
        initial_state = AgentState(
            messages=[HumanMessage(content=message.message)],
            chat_history=chat_history,
            current_message=message,
            model_name=message.model_name,
        )

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            response = final_state["messages"][-1].content
            metadata = {
                "input_token_usage": final_state["input_tokens"],
                "output_token_usage": final_state["output_tokens"],
                "time_taken": final_state["time_taken"],
            }

            formatted_response = self.response_formatter.format_response(
                "dynamic_agent", response, metadata, final_state.get("search_results", [])
            )
            return json.dumps(formatted_response, indent=2), metadata

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            error_response = self.response_formatter.format_error_response(
                "An unexpected error occurred during processing."
            )
            return json.dumps(error_response), {
                "input_token_usage": {"total": 0},
                "output_token_usage": {"total": 0},
                "time_taken": {"total": 0},
            }
