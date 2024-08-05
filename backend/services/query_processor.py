from typing import List, Dict, Any
import json
from services.openai_service import OpenAIService


class QueryProcessor:
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service

    async def expand_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        num_expansions: int = 3,
        model: str = "gpt-4o",
        temperature: float = 0.1,
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
            prompt, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        return response, input_tokens, output_tokens

    async def generate_search_queries(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        num_queries: int = 3,
        model: str = "gpt-4o",
        temperature: float = 0.1,
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

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        return response, input_tokens, output_tokens

    async def extract_product_attributes(
        self,
        query: str,
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        prompt = f"""
        Extract product attributes from the given query. Return the attributes as a JSON object.
        If an attribute is not mentioned, do not include it in the response.

        Possible attributes: category, brand, size, color, price_range, features

        Query: {query}

        Extracted Attributes:
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        return response, input_tokens, output_tokens

    async def rerank_products(
        self,
        query: str,
        products: List[Dict[str, Any]],
        top_k: int = 5,
        model: str = "gpt-4o",
        temperature: float = 0.1,
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

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        print(f"rerank_products response from OpenAI: {response}")
        return [product["name"] for product in response[:top_k]], input_tokens, output_tokens

    async def generate_faceted_search_params(
        self,
        query: str,
        available_facets: List[str],
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, List[str]]:
        prompt = f"""
        Generate faceted search parameters based on the user query.
        Return a JSON object where keys are facet names and values are lists of possible values for each facet.

        User Query: {query}

        Available Facets: {', '.join(available_facets)}

        Faceted Search Parameters:
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        return response, input_tokens, output_tokens

    async def generate_query_clarification(
        self,
        query: str,
        chat_history: List[dict],
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> str:
        prompt = f"""
        Based on the user query and chat history, generate a clarification question to ask the user.
        This question should help narrow down the search or resolve any ambiguities in the query.
        Return a JSON object with the clarification question.

        User Query: {query}

        Chat History:
        {json.dumps(chat_history, indent=2)}

        Clarification Question:
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        return response, input_tokens, output_tokens

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
