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

    async def process_query_comprehensive(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        num_expansions: int = 3,
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        prompt = f"""
        You are an AI assistant specializing in computer hardware, particularly embedded systems, development kits, and industrial communication devices. Our product database contains detailed information about various hardware products. Here's a description of the key features and data types stored for each product:

        1. name: String, the full name of the product (e.g., "ZumLink Series OEM ZPC ZPCSR", "Zoom AM Experimenter Kit")
        2. manufacturer: String, the company that produces the product (e.g., "FreeWave Technologies", "Logic Product Development")
        3. form_factor: String, physical dimensions or form factor, can be specific measurements or general descriptions (e.g., "63.5 x 38.1 x 10.2 mm", "Prototyping form-factor")
        4. processor: String, the type or model of processor used (e.g., "ARM Cortex-A8 1 GHz", "Texas Instruments AM Processor")
        5. core_count: String or Integer, the number of processor cores if available
        6. processor_tdp: String, the thermal design power of the processor if available
        7. memory: String, describing RAM and storage capacities (e.g., "RAM: 512 MB, Storage: 4 GB", "32 MB SDRAM, 64 MB NAND Flash")
        8. io: String, listing various input/output interfaces (e.g., "Ethernet, Power, Serial, USB", "UARTs, I2C, SPI, 10-bit ADC, GPIO")
        9. operating_system: String, the OS or software environment (e.g., "Debian-based Linux", "Embedded Linux")
        10. environmentals: String, operating conditions like temperature and humidity ranges
        11. certifications: String, listing any relevant certifications (e.g., "Class I Division 2 certified, UL, RoHS")
        12. short_summary: String, a brief description of the product
        13. full_summary: String, a more detailed summary of the product
        14. full_product_description: String, comprehensive description of the product's features and capabilities

        Now, analyze the following user query and chat history to improve product search results:

        User Query: {query}

        Chat History:
        {json.dumps(chat_history, indent=2)}

        Perform the following tasks:
        1. Extract relevant product attributes mentioned or implied in the query, focusing on the features described above.
        2. Generate {num_expansions} expanded queries that could help find relevant products, using specific technical terms and values where possible.
        3. Generate search parameters based on the query and extracted attributes, aligning with our product data format.

        Return a JSON object with the following structure. Do not add any thing else in the response:
        {{
            "extracted_attributes": {{
                // Include only relevant, non-null attributes
                "manufacturer": string,
                "form_factor": string,
                "processor": string,
                "memory": string,
                "io": string,
                "operating_system": string,
                "environmentals": string,
                "certifications": string,
            }},
            "expanded_queries": [string],
            "search_params": {{
                // Include only relevant, non-null attributes
                "manufacturer": string,
                "form_factor": string,
                "processor": string,
                "memory": string,
                "io": string,
                "operating_system": string,
                "environmentals": string,
                "certifications": string,
            }}
        }}

        Ensure all values are specific and aligned with our product database format. Use technical specifications and numeric values where applicable, rather than general terms like "high" or "large".
        """

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            prompt, temperature=temperature, model=model
        )
        processed_response = self._clean_response(response)
        return processed_response, input_tokens, output_tokens

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
