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


class SemanticSearchQueryPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to generate a semantic search query based on the user's vague product-related question.
        Also, determine the number of products that should be returned based on the user's query.

        Respond in JSON format as follows:
        {
            "query": "The generated semantic search query",
            "product_count": 5  // Number of products to return, default to 5 if not specified
        }

        Guidelines:
        - The query should be more detailed and specific than the user's original question.
        - Include relevant technical terms and specifications that might help in finding appropriate products.
        - If the user specifies a number of products they want to see, use that number for product_count.
        - If no number is specified, use 5 as the default product_count.
        """
        )

        human_template = """
        Chat History: {chat_history}
        User Query: {query}

        Generated Search Query:
        """
        super().__init__(system_template, human_template, ["query", "chat_history"])


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
        System Classification: {classification}
        Chat History: {chat_history}
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history", "classification"])


class VagueIntentResponsePrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Your task is to generate a response to a user's vague product-related question.
        Use the provided search results to craft an informative and helpful response.

        Always respond in JSON format with the following structure:
        {
            "message": "A concise introductory message addressing the user's query",
            "products": [
                {
                    "name": "Product Name", // We only need the name of the product
                }
                // ... more products if applicable
            ],
            "reasoning": "Clear and concise reasoning for the provided response and product selection",
            "follow_up_question": "A single, clear follow-up question to help narrow down the user's needs"
        }

        Guidelines:
        - Provide a general overview of the product category if applicable.
        - Highlight key factors to consider when choosing products in this domain.
        - Include relevant products from the search results, explaining why they might be of interest.
        - If the search results don't fully address the user's query, acknowledge this and suggest how to refine the search.
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


class DynamicAgentActionPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        You are a dynamic agent capable of deciding the next best action to take in response to a user query.
        Your task is to choose the most appropriate next action based on the current context and the user's query.

        Available actions:
        1. expand_query: Use this when you need more detailed or specific information about the user's request.
        2. semantic_search: Use this when you need to find relevant products or information from the database.
        3. generate_response: Use this when you have enough information to provide a final response to the user.
        4. end: Use this when you've completed all necessary actions and provided a final response.

        Respond in JSON format as follows:
        {
            "next_action": "action_name",
            "reasoning": "A brief explanation for why this action was chosen"
        }

        Consider the following when making your decision:
        - The user's original query
        - The chat history
        - The current context (results of previous actions)
        - The actions you've already completed
        """
        )

        human_template = """
        User Query: {query}
        Chat History: {chat_history}
        Current Context: {context}
        Completed Actions: {completed_actions}

        Decide the next action:
        """
        super().__init__(system_template, human_template, ["query", "chat_history", "context", "completed_actions"])


class DynamicAgentResponsePrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Your task is to generate a final response to the user's query based on all the information gathered.
        Use the current context, which includes the results of query expansion and semantic search, to craft a comprehensive and helpful response.

        Always respond in JSON format with the following structure:
        {
            "message": "Your main response to the user's query",
            "products": [
                {
                    "name": "Product Name",
                    "description": "Brief description of why this product is relevant"
                }
                // ... more products if applicable
            ],
            "reasoning": "Explanation of how you arrived at this response based on the context",
            "follow_up_question": "A relevant follow-up question to continue the conversation"
        }
        """
        )

        human_template = """
        User Query: {query}
        Chat History: {chat_history}
        Current Context: {context}

        Generate the final response:
        """
        super().__init__(system_template, human_template, ["query", "chat_history", "context"])


class SimpleDataExtractionPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an intelligent assistant specialized in extracting detailed information from raw product data. Your goal is to identify and extract specific attributes related to a product. For each attribute, if the information is not available, state 'Not available'. The attributes to be extracted are:

        - name: The name of the product.
        - size: The physical dimensions or form factor of the product.
        - form: The design or configuration of the product (e.g., ATX, mini-ITX).
        - processor: The type or model of the processor used in the product.
        - core: The number of processor cores.
        - frequency: The processor's operating frequency.
        - memory: The type and size of the product's memory.
        - voltage: The input voltage requirements for the product.
        - io: The input/output interfaces available on the product.
        - thermal: Information about the thermal management features of the product.
        - feature: Notable features or functionalities of the product.
        - type: The type of the product (e.g., Single Board Computers, Computer on Modules, Development Kits (Devkits), etc).
        - specification: Detailed technical specifications.
        - manufacturer: The company that makes the product.
        - location: The location (address) of the product or manufacturer.
        - description: A brief description of the product's purpose and capabilities.
        - summary: A concise summary of the product.

        Ensure the extracted information is accurate and well-formatted. Provide the extracted details in JSON format.
        """
        human_template = "Raw product data: {raw_data}"
        super().__init__(system_template, human_template, ["raw_data"])


class DataExtractionPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an AI assistant specialized in extracting detailed product information.
        Your task is to identify and extract specific attributes from raw product data.
        If information for an attribute is not available, use 'Not available'.

        Extract the following attributes:
        - name: Product name (clear, capital case, no special characters, singular)
        - manufacturer: Company name (clear, capital case, no special characters, singular)
        - form_factor: Physical dimensions or form factor
        - processor: Processor type or model
        - core_count: Number of processor cores
        - processor_tdp: Processor's thermal design power
        - memory: Memory type and size
        - io: Input/output interfaces
        - operating_system: Operating system or board support package
        - environmentals: Environmental specifications (e.g., operating temperature)
        - certifications: Product certifications
        - short_summary: Brief product summary
        - full_summary: Comprehensive product summary
        - full_product_description: Complete product description

        For each attribute, provide a value and a confidence score between 0 and 1.
        Provide the extracted details in JSON format.
        """
        human_template = "Raw product data: {raw_data}"
        super().__init__(system_template, human_template, ["raw_data"])


class ContextualExtractionPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an AI assistant specialized in extracting product information from context.
        Your task is to identify and extract the following specific attributes: {features_to_extract}.
        Ensure the extracted information is accurate and provided in JSON format.
        For each attribute, provide a value and a confidence score between 0 and 1.
        If information for an attribute is not found, use 'Not available' with a confidence score of 0.
        """
        human_template = """
        Context: {context}

        Extracted features so far: {extracted_features}

        Please provide the following missing features based on the given context:
        {features_to_extract}

        Format your response as a JSON object containing only the missing features.
        For each feature, provide a value and a confidence score between 0 and 1.
        If a feature is not found in the context, use "Not available" with a confidence score of 0.
        """
        super().__init__(system_template, human_template, ["context", "extracted_features", "features_to_extract"])


class FeatureRefinementPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an AI assistant specialized in refining product information from context.
        Your task is to refine the following specific attributes: {features_to_refine}.
        Ensure the refined information is accurate and provided in JSON format.
        For each attribute, provide a value and a confidence score between 0 and 1.
        If a feature cannot be refined, keep its current value and confidence score.
        """
        human_template = """
        Context: {context}

        Extracted features so far: {extracted_features}

        Please refine the following low confidence features based on the given context:
        {features_to_refine}

        Format your response as a JSON object containing only the refined features.
        For each feature, provide a value and a confidence score between 0 and 1.
        If a feature cannot be refined, keep its current value and confidence score.
        """
        super().__init__(system_template, human_template, ["context", "extracted_features", "features_to_refine"])
