import json
import time
import logging
from models.message import Message
from typing import List, Tuple, Dict, Any
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from services.query_processor import QueryProcessor
from utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class DynamicAgentState(Dict[str, Any]):
    model_name: str = "gpt-4o"
    chat_history: List[Dict[str, str]]
    current_message: str
    context: List[Dict[str, Any]] = []
    completed_actions: List[str] = []
    final_response: str = ""
    input_tokens: Dict[str, int] = {}
    output_tokens: Dict[str, int] = {}
    time_taken: Dict[str, float] = {}


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
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(DynamicAgentState)

        workflow.add_node("decide_action", self.decide_action)
        workflow.add_node("expand_query", self.expand_query)
        workflow.add_node("semantic_search", self.semantic_search)
        workflow.add_node("generate_response", self.generate_response)

        workflow.add_edge("decide_action", "expand_query")
        workflow.add_edge("decide_action", "semantic_search")
        workflow.add_edge("decide_action", "generate_response")
        workflow.add_edge("decide_action", END)

        workflow.add_edge("expand_query", "decide_action")
        workflow.add_edge("semantic_search", "decide_action")
        workflow.add_edge("generate_response", END)

        workflow.set_entry_point("decide_action")

        return workflow.compile()

    async def decide_action(self, state: DynamicAgentState) -> DynamicAgentState:
        system_message, user_message = self.prompt_manager.get_dynamic_agent_action_prompt(
            state["current_message"], state["chat_history"], state["context"], state["completed_actions"]
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model=state["model_name"]
        )

        action_decision = json.loads(response)
        next_action = action_decision["next_action"]
        state["completed_actions"].append(next_action)

        state["input_tokens"]["decide_action"] = input_tokens
        state["output_tokens"]["decide_action"] = output_tokens
        state["time_taken"]["decide_action"] = time.time() - state.get("start_time", time.time())

        return next_action, state

    async def expand_query(self, state: DynamicAgentState) -> DynamicAgentState:
        start_time = time.time()
        result, input_tokens, output_tokens = await self.query_processor.process_query_comprehensive(
            state["current_message"], state["chat_history"], num_expansions=3, model=state["model_name"]
        )

        state["context"].append({"action": "expand_query", "result": result})
        state["input_tokens"]["expand_query"] = input_tokens
        state["output_tokens"]["expand_query"] = output_tokens
        state["time_taken"]["expand_query"] = time.time() - start_time

        return state

    async def semantic_search(self, state: DynamicAgentState) -> DynamicAgentState:
        start_time = time.time()
        search_query = state["current_message"]
        if state["context"]:
            last_action = state["context"][-1]
            if last_action["action"] == "expand_query":
                search_query = last_action["result"]["expanded_queries"][0]

        results = await self.weaviate_service.search_products(search_query, limit=5)

        state["context"].append({"action": "semantic_search", "result": results})
        state["time_taken"]["semantic_search"] = time.time() - start_time

        return state

    async def generate_response(self, state: DynamicAgentState) -> DynamicAgentState:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_dynamic_agent_response_prompt(
            state["current_message"], state["chat_history"], state["context"]
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model=state["model_name"]
        )

        state["final_response"] = response
        state["input_tokens"]["generate_response"] = input_tokens
        state["output_tokens"]["generate_response"] = output_tokens
        state["time_taken"]["generate_response"] = time.time() - start_time

        return state

    async def run(self, message: Message, chat_history: List[Message]) -> Tuple[str, Dict[str, Any]]:
        logger.info(f"Running dynamic agent with message: {message}")

        initial_state = DynamicAgentState(
            model_name=message.model,
            chat_history=chat_history,
            current_message=message.content,
            start_time=time.time(),
        )

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Workflow execution completed")

            output = self.response_formatter.format_response(
                "dynamic_agent",
                final_state["final_response"],
                {
                    "context": final_state["context"],
                    "completed_actions": final_state["completed_actions"],
                    "input_token_usage": final_state["input_tokens"],
                    "output_token_usage": final_state["output_tokens"],
                    "time_taken": final_state["time_taken"],
                },
            )

            stats = {
                "input_token_usage": final_state["input_tokens"],
                "output_token_usage": final_state["output_tokens"],
                "time_taken": final_state["time_taken"],
            }

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            output = self.response_formatter.format_error_response("An unexpected error occurred during processing.")
            stats = {
                "input_token_usage": {"total": 0},
                "output_token_usage": {"total": 0},
                "time_taken": {"total": 0},
            }

        return json.dumps(output, indent=2), stats
