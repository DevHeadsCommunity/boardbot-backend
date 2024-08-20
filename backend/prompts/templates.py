from typing import Dict, Any, List
from base import USER_FACING_BASE, PROCESSING_BASE
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


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


class RouteClassificationPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to categorize the given query into one of the following categories:
        1. politics - for queries related to political topics.
        2. chitchat - for general conversation or small talk.
        3. vague_intent_product - for product-related queries that are general or lack specific criteria.
        4. clear_intent_product - for product-related queries with specific criteria or constraints.
        5. do_not_respond - for queries that are inappropriate, offensive, or outside the system's scope.

        Provide your classification along with a brief justification and a confidence score (0-100).

        Respond in JSON format as follows:
        {{
            "category": "category_name",
            "justification": "A brief explanation for this classification",
            "confidence": 85
        }}

        Guidelines:
        - If a query contains any clear product-related intent or specific criteria, classify it as clear_intent_product, regardless of other elements in the query.
        - Consider the chat history when making your classification. A vague query might become clear in the context of previous messages.
        - Classify as politics only if the query is primarily about political topics.
        - Use do_not_respond for queries that are inappropriate, offensive, or completely unrelated to computer hardware and embedded systems.
        - Be decisive - always choose the most appropriate category even if the query is ambiguous.

        Examples:
        - clear_intent_product: Queries with specific criteria about products.
            - "Find me a board with an Intel processor and at least 8GB of RAM"
            - "List Single Board Computers with a processor frequency of 1.5 GHz or higher"
            - "What are the top 5 ARM-based development kits with built-in Wi-Fi?"

        - vague_intent_product: General product queries without specific criteria.
            - "Tell me about single board computers"
            - "What are some good development kits?"
            - "I'm looking for industrial communication devices"

        """
        )

        human_template = """
        Chat History: {chat_history}
        User Query: {query}

        Classification:
        """
        super().__init__(system_template, human_template, ["query", "chat_history"])


class QueryProcessorPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to process and expand the given query to improve product search results.
        Generate expanded queries and extract relevant product attributes.

        Here's a description of the key features and data types stored for each product:
        {attribute_descriptions}

        Perform the following tasks:
        1. Extract relevant product attributes mentioned or implied in the query.
        2. Generate {num_expansions} expanded queries that could help find relevant products.
        3. Generate search parameters based on the query and extracted attributes.

        Respond in JSON format as follows:
        {{
            "extracted_attributes": {{
                // Include only relevant, non-null attributes
            }},
            "expanded_queries": [
                // List of expanded queries
            ],
            "search_params": {{
                // Include only relevant, non-null attributes
            }}
        }}

        Ensure all values are specific and aligned with our product database format. Use technical specifications and numeric values where applicable, rather than general terms like "high" or "large".
        """
        )
        human_template = """
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(
            system_template, human_template, ["query", "chat_history", "num_expansions", "attribute_descriptions"]
        )


class ProductRerankingPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Rerank the given products based on their relevance to the user query.
        Focus on exact matching of specified criteria rather than general relevance.
        Carefully evaluate each product against ALL criteria specified in the user query. A product must match EVERY single criterion to be included.
        Do NOT confuse different attributes (e.g., processor manufacturer vs product manufacturer).
        Return the top {top_k} products based on relevance.

        When evaluating products, use the following attribute mapping:
        {attribute_mapping_str}

        For any numerical criteria (e.g., processor frequency, memory size), ensure the product meets or exceeds the specified value.

        Return the list of matching products and justification in the following format:
        {{
            "products": [
                {{
                    "name": "Product Name",
                    "relevance_score": 0.95,
                    "score_explanation": "Brief explanation of this score",
                    "matching_criteria": ["List of criteria that this product matches"],
                    "missing_criteria": ["List of criteria that this product doesn't match, if any"]
                }},
                // ... more products if applicable
            ],
            "justification": "Clear, concise list or bullet points explaining why products are included or excluded, addressing each criterion from the query."
        }}

        If no products match, return: {{"products": [], "justification": "Detailed explanation why no products match, addressing each criterion from the query"}}
        """
        )

        human_template = """
        Relevant Products: {products}
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(
            system_template, human_template, ["query", "chat_history", "products", "attribute_mapping_str", "top_k"]
        )


class ChitchatPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Engage in casual conversation while maintaining a friendly and professional tone.
        If the conversation steers towards product-related topics, be prepared to seamlessly transition
        into providing relevant information or assistance.

        Always respond in JSON format with the following structure:
        {{
            "message": "Your response to the user's message.",
            "follow_up_question": "A question to keep the conversation going."
        }}
        """
        )
        human_template = """
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history"])


class LowConfidencePrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        The system classifies queries into three different categories to provide the most relevant responses.
        These categories are:
          1. chitchat - for general conversation or small talk.
          2. vague intent about product
          3. clear intent about product

        However, with the current query, the system is uncertain about the correct classification.
        Provide a response that acknowledges the uncertainty and asks for clarification from the user.

        Always respond in JSON format with the following structure:
        {{
            "message": "Your response acknowledging the uncertainty and asking for clarification.",
            "follow_up_question": "A question to help clarify the user's intent."
        }}
        """
        )
        human_template = """
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history"])


class VagueIntentProductPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        For queries without specific criteria:
        1. Provide a general overview of relevant product categories.
        2. Highlight key factors to consider when choosing products in this domain.
        3. Suggest follow-up questions to help narrow down the user's needs.

        Your response should be clear, informative, and directly address the user's query.

        Always respond in JSON format with the following structure:
        {{
            "message": "A concise introductory message addressing the user's query",
            "products": [
                {{
                    "name": "Product Name", // We only need the name of the product
                }}
                // ... more products if applicable
            ],
            "reasoning": "Clear and concise reasoning for the provided response and product selection",
            "follow_up_question": "A single, clear follow-up question based on the user's query and the products found"
        }}
        """
        )
        human_template = """
        Relevant Products: {products}
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history", "products"])


class ClearIntentProductPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Analyze the user's query and the relevant products found, then provide a comprehensive and helpful response.
        Your response should be clear, informative, and directly address the user's query.

        IMPORTANT:
        1. Only include products that FULLY match ALL criteria specified in the user's query.
        2. Pay special attention to the user's query, and the specifications of the products.
        3. Do NOT confuse the processor manufacturer with the product manufacturer. This applies to all attributes.
        4. If no products match ALL criteria, return an empty list of products and explain why.

        Always respond in JSON format with the following structure:
        {{
            "message": "A concise introductory message addressing the user's query",
            "products": [
                {{
                    "name": "Product Name" // We only need the name of the product
                }}
                // ... more products if applicable
            ],
            "reasoning": "Clear and concise reasoning for the provided response and product selection",
            "follow_up_question": "A single, clear follow-up question based on the user's query and the products found"
        }}
        """
        )
        human_template = """
        Reranking Result: {reranking_result}
        Relevant Products: {products}
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history", "products", "reranking_result"])
