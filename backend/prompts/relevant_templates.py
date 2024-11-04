import json
import logging
from typing import Dict, Any, List
from .base import USER_FACING_BASE, PROCESSING_BASE
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

logger = logging.getLogger(__name__)


class BaseChatPrompt:
    def __init__(self, system_template: str, human_template: str, input_variables: List[str]):
        self.template = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template(human_template),
            ]
        )
        self.input_variables = input_variables

    def format(self, **kwargs: Any) -> List[Dict[str, str]]:
        return self.template.format_messages(**kwargs)


class DynamicAnalysisPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to analyze queries about computer hardware and either:
        1. Extract specific product requirements and filters
        2. Generate a product search for general product queries
        3. Generate a direct response only for non-product queries

        General Guidelines:
        1. ANY mention of product categories (boards, modules, kits, etc.) should trigger a product search
        2. Only use direct responses for completely non-product queries (greetings, general questions)
        3. When in doubt, prefer returning products over a direct response


        Guidelines for Filter Extraction:
        1. Use only attribute names from the provided list for filters.
        2. Include only explicitly mentioned attributes.
        3. Use standardized values from the examples.
        4. Distinguish between 'manufacturer' (company making the product) and 'processor_manufacturer' (company making the CPU).
        5. For processor architecture, use exact terms (e.g., "ARM Cortex-A53", "X86-64").
        6. For ranges, use format "min_value-max_value" with units.
        7. Identify the number of products requested (default: 5).

        Guidelines for Direct Response:
        1. For queries without clear product requirements, generate a direct response in a conversational tone.
        2. Frame follow-up questions to better understand user requirements.

        Respond in this JSON format:

        For specific product queries:
        {{
            "filters": {{
                // Extracted filters using exact attribute names
            }},
            "query_context": {{
                "num_products_requested": <number>,
                "sort_preference": null
            }}
        }}

        For general product queries:
        {{
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        For non-product queries:
        {{
            "direct_response": {{
                "message": "Your conversational response",
                "follow_up_question": "A relevant follow-up question"
            }}
        }}


        Examples:

        Query: "Find COM Express modules with Intel Core i7 CPUs and at least 16GB DDR4 RAM"
        Response:
        {{
            "filters": {{
                "form_factor": "COM EXPRESS",
                "processor_manufacturer": "INTEL",
                "processor_architecture": "X86-64",
                "memory": "16.0GB-64.0GB DDR4"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}


        Query: "Tell me about development boards"
        Response:
        {{
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Query: "How are you doing today?"
        Response:
        {{
            "direct_response": {{
                "message": "I'm functioning well and ready to assist you with any questions about computer hardware, particularly embedded systems and development kits.",
                "follow_up_question": "What kind of hardware solutions are you interested in learning more about?"
            }}
        }}
        """
        )

        human_template = """
        Attribute list for filters:
        {attribute_descriptions}

        User Query: {query}
        Chat History: {chat_history}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history", "attribute_descriptions"])


class DynamicResponsePrompt(BaseChatPrompt):
    def __init__(self):
        # Define common guidelines and structure
        self.base_guidelines = """
        Your task is to generate an short, engaging, informative response incorporating product from search result.

        Guidelines:
        - Keep responses concise but informative
        - Present technical information in an accessible way
        - Include all provided products, ordered by relevance
        - Compare products based on key technical specifications
        - Highlight trade-offs between different options
        - Include relevant technical context for specifications
        - Group similar products and explain differences
        - For partial matches, naturally explain how they relate to the query
        - Frame follow-up questions to better understand user requirements
        - If products don't perfectly match all criteria, acknowledge this constructively
        - Maintain thread of conversation by referencing chat history when relevant
        """

        # Define specific guidelines for each search method
        self.search_guidelines = {
            "filtered": {
                "focus": "Filtered product search based on specific user criteria",
                "key_points": [
                    "Focus on how well products match the specified criteria",
                    "Highlight any important trade-offs between requirements",
                    "Mention only the most critical specifications",
                    "If some products only partially match, briefly explain why they're still relevant",
                ],
                "example": """{{
                    "message": "Found 3 boards matching your Intel CPU and memory requirements, with RAM ranging from 16GB to 32GB DDR4.",
                    "products": [
                        {{
                        "product_id": "example_id"
                        }}
                    ],
                    "reasoning": "Selected based on exact CPU match and memory specifications above minimum requirement.",
                    "follow_up_question": "Would you prefer boards optimized for performance or power efficiency?"
                    }}""",
            },
            "semantic": {
                "focus": "Semantic search based on general query understanding",
                "key_points": [
                    "Provide a brief category overview",
                    "Highlight the range of options available",
                    "Focus on distinctive features across products",
                    "Avoid detailed individual product descriptions",
                ],
                "example": """{{
                    "message": "We offer a diverse range of development boards, from entry-level ARM-based solutions to high-performance x86 platforms.",
                    "products": [
                        {{
                        "product_id": "example_id"
                        }}
                    ],
                    "reasoning": "Selected to showcase the variety of architectures and capabilities available.",
                    "follow_up_question": "What specific features are most important for your project?"
                    }}""",
            },
            "hybrid": {
                "focus": "Combined filtered and semantic search results",
                "key_points": [
                    "Acknowledge both exact and partial matches",
                    "Highlight the most relevant features",
                    "Keep focus on user's primary requirements",
                    "Explain value of alternative options briefly",
                ],
                "example": """{{
                    "message": "Found 2 boards exactly matching your specifications, plus 3 alternative options with comparable processing power.",
                    "products": [
                        {{
                        "product_id": "example_id"
                        }}
                    ],
                    "reasoning": "Included both exact CPU matches and boards with similar performance characteristics.",
                    "follow_up_question": "Would you like to focus on the exact matches or explore the alternatives?"
                    }}""",
            },
        }

        # Define templates
        human_template = """
        User Query: {query}
        Applied Filters: {filters}
        Product Results: {products}

        Response:
        """

        # Initialize with default template
        super().__init__(
            self._build_system_template("semantic"), human_template, ["query", "filters", "products", "search_method"]
        )

    def _build_system_template(self, search_method: str) -> str:
        """Build the system template for a specific search method."""
        method = self.search_guidelines.get(search_method, self.search_guidelines["semantic"])

        template = f"""{USER_FACING_BASE}
        {self.base_guidelines}

        Search Method: {method['focus']}

        Key Requirements:
        {self._format_list(method['key_points'])}

        Expected Response Format:
        {method['example']}

        Please provide your response in the exact JSON format shown above, keeping responses focused and concise.
        """
        return template

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as bullet points."""
        return "\n".join(f"- {item}" for item in items)

    def format(self, **kwargs: Any) -> List[Dict[str, str]]:
        """Override format to use the appropriate template based on search method."""
        search_method = kwargs.get("search_method", "semantic")
        self.template.messages[0].prompt.template = self._build_system_template(search_method)
        return super().format(**kwargs)
