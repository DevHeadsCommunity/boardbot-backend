import json
import logging
import time
from typing import List, Tuple, Dict, Any
from models.message import Message
from models.product import Product
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, END


logger = logging.getLogger(__name__)


class AgentState(Dict[str, Any]):
    model_name: str = "gpt-4o"
    chat_history: List[Dict[str, str]]
    current_message: str
    agent_scratchpad: List[BaseMessage]
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
    output: str = ""


class AgentV1:
    def __init__(
        self,
        weaviate_service: WeaviateService,
        query_processor: QueryProcessor,
        openai_service: OpenAIService,
    ):
        self.weaviate_service = weaviate_service
        self.query_processor = query_processor
        self.openai_service = openai_service
        self.workflow = self.setup_workflow()

    def setup_workflow(self) -> StateGraph:
        logger.info("Setting up workflow")
        workflow = StateGraph(AgentState)

        workflow.add_node("query_expansion", self.query_expansion_node)
        workflow.add_node("product_search", self.product_search_node)
        workflow.add_node("result_reranking", self.result_reranking_node)
        workflow.add_node("response_generation", self.response_generation_node)

        workflow.add_edge("query_expansion", "product_search")
        workflow.add_edge("product_search", "result_reranking")
        workflow.add_edge("result_reranking", "response_generation")
        workflow.add_edge("response_generation", END)

        workflow.set_entry_point("query_expansion")

        logger.info("Workflow setup complete")
        return workflow.compile()

    def generate_semantic_search_queries(self, comprehensive_result: Dict[str, Any]) -> List[str]:
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

    async def query_expansion_node(self, state: AgentState) -> AgentState:
        logger.info("Entering query_expansion_node")
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

    async def product_search_node(self, state: AgentState) -> AgentState:
        logger.info("Entering product_search_node")
        start_time = time.time()
        all_results = []
        for query in [state["current_message"]] + state["expanded_queries"]:
            results = await self.weaviate_service.search_products(query, limit=5)
            all_results.extend(results)

        unique_results = {}
        for result in all_results:
            if result["name"] not in unique_results:
                unique_results[result["name"]] = Product(**result)

        state["search_results"] = list(unique_results.values())
        state["time_taken"]["search"] = time.time() - start_time
        logger.info(f"Found {len(state['search_results'])} unique products")
        return state

    async def result_reranking_node(self, state: AgentState) -> AgentState:
        logger.info("Entering result_reranking_node")
        start_time = time.time()
        products_for_reranking = [
            {"name": p.name, **{attr: getattr(p, attr) for attr in state["attributes"]}}
            for p in state["search_results"]
        ]
        reranked_result, input_tokens, output_tokens = await self.query_processor.rerank_products(
            state["current_message"], products_for_reranking, top_k=10, model=state["model_name"]
        )

        # Store the full reranking result
        state["reranking_result"] = reranked_result

        # Reorder the full Product objects based on the reranked names
        logging.info(f"Reranked products: {reranked_result['products']}")
        name_to_product = {p.name: p for p in state["search_results"]}
        state["final_results"] = [
            name_to_product[p["name"]] for p in reranked_result["products"] if p["name"] in name_to_product
        ]
        state["input_tokens"]["rerank"] = input_tokens
        state["output_tokens"]["rerank"] = output_tokens
        state["time_taken"]["rerank"] = time.time() - start_time

        logger.info(f"Reranked results: {[p.name for p in state['final_results']]}")
        return state

    async def response_generation_node(self, state: AgentState) -> AgentState:
        logger.info("Entering response_generation_node")
        start_time = time.time()
        system_message = self.get_system_message()
        user_message = f"""
        User Query: {state['current_message']}

        Chat History:
        {json.dumps(state['chat_history'], indent=2)}

        Reranking Result:
        {json.dumps(state['reranking_result'], indent=2)}

        Relevant Products:
        {json.dumps([{"name": p.name, **{attr: getattr(p, attr) for attr in state["attributes"]}, "summary": p.full_product_description} for p in state['final_results']], indent=2)}

        Please provide a response to the user's query based on the reranking result and relevant products found.
        Use the justification and product-specific information from the reranking result to explain why certain products are included or excluded.
        Ensure that only products that fully match ALL criteria specified in the user's query are included in the final list.
        If no products match ALL criteria, explain why using the information from the reranking result.
        Include a single, clear follow-up question based on the user's query and the products found.
        """

        logging.info(f"+++user_message: {user_message}")

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model=state["model_name"]
        )

        state["input_tokens"]["generate"] = input_tokens
        state["output_tokens"]["generate"] = output_tokens
        state["output"] = self.format_response(response, state)
        state["time_taken"]["generate"] = time.time() - start_time
        logger.info(f"+++Generated response: {state['output']}")
        return state

    def get_system_message(self) -> str:
        return """You are ThroughPut assistant. Your main task is to help users with their queries about products.
        Analyze the user's query and the relevant products found, then provide a comprehensive and helpful response.
        Your response should be clear, informative, and directly address the user's query.
        IMPORTANT:
        1. Only include products that FULLY match ALL criteria specified in the user's query.
        2. Pay special attention to the user's query, and the specifications of the products.
        3. Do NOT confuse the processor manufacturer with the product manufacturer. This applies to all attributes.
        4. If no products match ALL criteria, return an empty list of products.
        Always respond in JSON format with the following structure:
        {
            "message": "A concise introductory message addressing the user's query",
            "products": [
                {
                    "name": "Product Name", // We only need the name of the product
                },
                // ... more products if applicable
            ],
            "reasoning": "Clear and concise reasoning for the provided response and product selection",
            "follow_up_question": "A single, clear follow-up question based on the user's query and the products found"
        }
        """

    def format_response(self, llm_output: str, state: AgentState) -> Dict[str, Any]:
        llm_response = self._clean_response(llm_output)

        response = {
            "type": "clear_intent_product",
            "message": llm_response["message"],
            "products": [
                product.__dict__
                for product in state["final_results"]
                if product.name in [p["name"] for p in llm_response.get("products", [])]
            ],
            "reasoning": llm_response["reasoning"],
            "follow_up_question": llm_response["follow_up_question"],
            "metadata": {
                "classification_result": llm_response["classification_result"],
                "reranking_result": state["reranking_result"],
            },
            "input_token_usage": {
                "expansion": state["input_tokens"]["expansion"],
                "rerank": state["input_tokens"]["rerank"],
                "generate": state["input_tokens"]["generate"],
            },
            "output_token_usage": {
                "expansion": state["output_tokens"]["expansion"],
                "rerank": state["output_tokens"]["rerank"],
                "generate": state["output_tokens"]["generate"],
            },
            "time_taken": {
                "expansion": state["time_taken"]["expansion"],
                "search": state["time_taken"]["search"],
                "rerank": state["time_taken"]["rerank"],
                "generate": state["time_taken"]["generate"],
            },
        }
        return response

    async def run(self, message: Message, chat_history: List[Message]) -> Tuple[str, Dict[str, int]]:
        logger.info(f"Running agent with message: {message}")

        initial_state = AgentState(
            model_name=message.model,
            chat_history=chat_history,
            current_message=message.content,
            agent_scratchpad=[],
            expanded_queries=[],
            search_results=[],
            final_results=[],
        )

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info(f"Workflow execution completed: final state: {final_state}")

            output = json.dumps(final_state["output"], indent=2)

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            output = json.dumps(
                {
                    "response_type": "error",
                    "message": "An error occurred while processing your request.",
                    "products": [],
                    "reasoning": "There was an unexpected error in the system.",
                    "follow_up_question": "Would you like to try your query again?",
                    "metadata": {},
                    "token_usage": {},
                },
                indent=2,
            )

        return output

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
