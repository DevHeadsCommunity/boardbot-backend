import logging
import json
from models.message import Message
from models.product import Product
from typing import List, Tuple, Dict, Any
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor
from services.weaviate_service import WeaviateService
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AgentState(Dict[str, Any]):
    model_name: str = "gpt-4o"
    chat_history: List[Dict[str, str]]
    current_message: str
    agent_scratchpad: List[BaseMessage]
    expanded_queries: List[str]
    search_results: List[Product]
    final_results: List[Product]
    expansion_input_tokens: int = 0
    expansion_output_tokens: int = 0
    rerank_input_tokens: int = 0
    rerank_output_tokens: int = 0
    generate_input_tokens: int = 0
    generate_output_tokens: int = 0
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

    async def query_expansion_node(self, state: AgentState) -> AgentState:
        logger.info("Entering query_expansion_node")
        expanded_queries, input_tokens, output_tokens = await self.query_processor.expand_query(
            state["current_message"], state["chat_history"], num_expansions=5, model=state["model_name"]
        )
        state["expanded_queries"] = expanded_queries
        state["expansion_input_tokens"] = input_tokens
        state["expansion_output_tokens"] = output_tokens
        logger.info(f"Expanded queries: {expanded_queries}")
        return state

    async def product_search_node(self, state: AgentState) -> AgentState:
        logger.info("Entering product_search_node")
        all_results = []
        for query in [state["current_message"]] + state["expanded_queries"]:
            results = await self.weaviate_service.search_products(query, limit=5)
            all_results.extend(results)

        # Remove duplicates and create Product objects
        unique_results = {}
        for result in all_results:
            if result["name"] not in unique_results:
                unique_results[result["name"]] = Product(
                    name=result["name"],
                    summary=result["summary"],
                    form=result.get("form"),
                    io=result.get("io"),
                    manufacturer=result.get("manufacturer"),
                    memory=result.get("memory"),
                    processor=result.get("processor"),
                    size=result.get("size"),
                )

        state["search_results"] = list(unique_results.values())
        logger.info(f"Found {len(state['search_results'])} unique products")
        return state

    async def result_reranking_node(self, state: AgentState) -> AgentState:
        logger.info("Entering result_reranking_node")
        products_for_reranking = [{"name": p.name, "summary": p.summary} for p in state["search_results"]]
        reranked_names, input_tokens, output_tokens = await self.query_processor.rerank_products(
            state["current_message"], products_for_reranking, top_k=10, model=state["model_name"]
        )

        # Reorder the full Product objects based on the reranked names
        logging.info(f"Reranked names: {reranked_names}")
        name_to_product = {p.name: p for p in state["search_results"]}
        logging.info(f"Name to product: {name_to_product}")
        state["final_results"] = [name_to_product[name] for name in reranked_names if name in name_to_product]
        state["rerank_input_tokens"] = input_tokens
        state["rerank_output_tokens"] = output_tokens

        logger.info(f"Reranked results: {[p.name for p in state['final_results']]}")
        return state

    async def response_generation_node(self, state: AgentState) -> AgentState:
        logger.info("Entering response_generation_node")
        system_message = self.get_system_message()
        user_message = f"""
        User Query: {state['current_message']}

        Relevant Products:
        {json.dumps([{"name": p.name, "summary": p.summary} for p in state['final_results']], indent=2)}

        Please provide a response to the user's query based on the relevant products found.
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model=state["model_name"]
        )
        response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
        state["output"] = response
        state["generate_input_tokens"] = input_tokens
        state["generate_output_tokens"] = output_tokens
        logger.info(f"Generated response: {response}")
        return state

    def get_system_message(self) -> str:
        return """You are ThroughPut assistant. Your main task is to help users with their queries about products.
        Analyze the user's query and the relevant products found, then provide a comprehensive and helpful response.
        Your response should be clear, informative, and directly address the user's query.
        If the products don't fully answer the query, suggest ways the user could refine their search or ask for more information.
        Always respond in JSON format with the following structure. Your response should include Names of top five most relevant products in a descending order in terms of relevance.
        For products only include the name of the product.
        {
            "response_description": "A concise description of the products that match the user's query.",
            "response_justification": "Explanation of why this response is appropriate.",
            "products": [
                {
                    "name": "Product Name",
                },
                // ... more products if applicable
            ],
            "additional_info": "Any additional information or suggestions for the user"
        }
        """

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

        logging.info(f"initial state: {initial_state}")

        try:
            logger.info("Starting workflow execution")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info(f"===:> Workflow execution completed: final state: {final_state}")
            llm_output = json.loads(final_state["output"])

            # Add full product details to the output
            product_details = []
            for product in final_state["final_results"]:
                if product.name in [p["name"] for p in llm_output["products"]]:
                    product_details.append(product.__dict__)

            llm_output["products"] = product_details
            output = json.dumps(llm_output, indent=2)

            input_tokens = (
                final_state["expansion_input_tokens"]
                + final_state["rerank_input_tokens"]
                + final_state["generate_input_tokens"]
            )
            output_tokens = (
                final_state["expansion_output_tokens"]
                + final_state["rerank_output_tokens"]
                + final_state["generate_output_tokens"]
            )

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            output = json.dumps(
                {
                    "response_description": "An error occurred while processing your request.",
                    "response_justification": "There was an unexpected error in the system.",
                    "products": [],
                    "additional_info": "Please try your query again or contact support if the problem persists.",
                }
            )

        logger.info(f"Run completed. Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        return output, {
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
        }
