import json
import logging
from typing import List, Dict, Any, Tuple, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from services.query_processor import QueryProcessor
from utils.response_formatter import ResponseFormatter
from prompts.prompt_manager import PromptManager

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

        self.tools = {
            "semantic_search": self.semantic_search,
            "rerank_products": self.rerank_products,
            "expand_query": self.expand_query,
        }

        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self.agent_step)
        workflow.add_node("tool", self.tool_step)

        workflow.add_conditional_edges("agent", self.should_use_tool, {True: "tool", False: END})
        workflow.add_edge("tool", "agent")

        workflow.set_entry_point("agent")

        return workflow.compile()

    async def agent_step(self, state: AgentState) -> Dict[str, Any]:
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

        return {"messages": [HumanMessage(content=response)]}

    def should_use_tool(self, state: AgentState) -> bool:
        last_message = state["messages"][-1]
        return "ACTION" in last_message.message

    async def tool_step(self, state: AgentState) -> Dict[str, Any]:
        last_message = state["messages"][-1]
        action_content = last_message.message.split("ACTION:", 1)[1].strip()

        try:
            action = json.loads(action_content)
            tool_name = action["tool"]
            tool_input = action["input"]
        except json.JSONDecodeError:
            return {"messages": [ToolMessage(content="Invalid action format. Please use valid JSON.")]}

        if tool_name not in self.tools:
            return {"messages": [ToolMessage(content=f"Unknown tool: {tool_name}")]}

        result = await self.tools[tool_name](**tool_input)
        return {"messages": [ToolMessage(content=json.dumps(result))]}

    async def semantic_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        results = await self.weaviate_service.search_products(query, limit)
        return {"results": results}

    async def rerank_products(self, query: str, products: List[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
        reranked_result, input_tokens, output_tokens = await self.query_processor.rerank_products(
            query, [], products, top_k
        )
        return {"reranked_products": reranked_result, "input_tokens": input_tokens, "output_tokens": output_tokens}

    async def expand_query(self, query: str) -> Dict[str, Any]:
        result, input_tokens, output_tokens = await self.query_processor.process_query_comprehensive(query, [])
        return {
            "expanded_queries": result["expanded_queries"],
            "extracted_attributes": result["extracted_attributes"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    async def run(
        self, message: str, chat_history: List[Dict[str, str]], model_name: str
    ) -> Tuple[str, Dict[str, Any]]:
        initial_state = AgentState(
            messages=[HumanMessage(content=message)],
            chat_history=chat_history,
            current_message=message,
            model_name=model_name,
        )

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            response = final_state["messages"][-1].content
            metadata = {
                "input_token_usage": final_state["input_tokens"],
                "output_token_usage": final_state["output_tokens"],
                "time_taken": final_state["time_taken"],
            }

            formatted_response = self.response_formatter.format_response("dynamic_agent", response, metadata)
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
