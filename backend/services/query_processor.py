from typing import List, Dict, Any
import json
from services.openai_service import OpenAIService


class QueryProcessor:
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service

    async def expand_query(
        self, query: str, chat_history: List[Dict[str, str]], num_expansions: int = 3, model: str = "gpt-4o"
    ) -> List[str]:
        prompt = f"""
        Given the following user query and chat history, expand the query to improve product search results.
        Generate {num_expansions} different expanded queries, each adding relevant terms, synonyms, or attributes that might be implied by the query or context.
        Return the expanded queries as a JSON list of strings.

        User Query: {query}

        Chat History:
        {json.dumps(chat_history, indent=2)}

        Expanded Queries:
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=1, model=model
        )
        response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
        print(f"expand_query response from OpenAI: {response}")

        expanded_queries = json.loads(response.strip())
        return expanded_queries, input_tokens, output_tokens

    async def generate_search_queries(
        self, query: str, chat_history: List[Dict[str, str]], num_queries: int = 3, model: str = "gpt-4o"
    ) -> List[str]:
        prompt = f"""
        Based on the user query and chat history, generate {num_queries} search queries that could be used to find relevant products.
        These queries should be variations that capture different aspects or interpretations of the user's intent.
        Return the search queries as a JSON list of strings.

        User Query: {query}

        Chat History:
        {json.dumps(chat_history, indent=2)}

        Search Queries:
        """

        response, _, _ = await self.openai_service.generate_response(prompt, model=model)
        response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
        print(f"generate_search_queries response from OpenAI: {response}")

        search_queries = json.loads(response.strip())
        return search_queries

    async def extract_product_attributes(self, query: str) -> Dict[str, Any]:
        prompt = f"""
        Extract product attributes from the given query. Return the attributes as a JSON object.
        If an attribute is not mentioned, do not include it in the response.

        Possible attributes: category, brand, size, color, price_range, features

        Query: {query}

        Extracted Attributes:
        """

        response, _, _ = await self.openai_service.generate_response(prompt)
        attributes = json.loads(response.strip())
        return attributes

    async def rerank_products(
        self, query: str, products: List[Dict[str, Any]], top_k: int = 5, model: str = "gpt-4o"
    ) -> List[Dict[str, Any]]:
        prompt = f"""
        Rerank the given products based on their relevance to the user query.
        Return the top {top_k} most relevant products as a JSON list, ordered by relevance.
        Include a 'relevance_score' key for each product with a float value between 0 and 1.
        Do not include product summaries in the response, only product names are sufficient.

        User Query: {query}

        Products:
        {json.dumps(products, indent=2)}

        Reranked Products:
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(prompt, model=model)
        response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
        print(f"rerank_products response from OpenAI: {response}")
        reranked_products = json.loads(response.strip())
        return [product["name"] for product in reranked_products[:top_k]], input_tokens, output_tokens

    async def generate_faceted_search_params(self, query: str, available_facets: List[str]) -> Dict[str, List[str]]:
        prompt = f"""
        Generate faceted search parameters based on the user query.
        Return a JSON object where keys are facet names and values are lists of possible values for each facet.

        User Query: {query}

        Available Facets: {', '.join(available_facets)}

        Faceted Search Parameters:
        """

        response, _, _ = await self.openai_service.generate_response(prompt)
        faceted_search_params = json.loads(response.strip())
        return faceted_search_params

    async def generate_query_clarification(self, query: str, chat_history: List[dict]) -> str:
        prompt = f"""
        Based on the user query and chat history, generate a clarification question to ask the user.
        This question should help narrow down the search or resolve any ambiguities in the query.

        User Query: {query}

        Chat History:
        {json.dumps(chat_history, indent=2)}

        Clarification Question:
        """

        response, _, _ = await self.openai_service.generate_response(prompt)
        return response.strip()

    async def process_query(self, query: str, chat_history: List[dict], **kwargs) -> Dict[str, Any]:
        expanded_queries = await self.expand_query(query, chat_history, num_expansions=kwargs.get("num_expansions", 3))
        search_queries = await self.generate_search_queries(
            query, chat_history, num_queries=kwargs.get("num_search_queries", 3)
        )
        attributes = await self.extract_product_attributes(query)

        return {
            "original_query": query,
            "expanded_queries": expanded_queries,
            "search_queries": search_queries,
            "extracted_attributes": attributes,
        }
