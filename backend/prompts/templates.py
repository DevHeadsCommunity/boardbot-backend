from typing import Dict, Any, List
from .base import USER_FACING_BASE, PROCESSING_BASE
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
        3. vague_intent_product - for product-related queries that are general, lack specific criteria, or request listings without detailed specifications.
        4. clear_intent_product - for product-related queries with specific technical criteria or constraints.
        5. do_not_respond - for queries that are inappropriate, offensive, or outside the system's scope.

        Provide your classification along with a brief justification and a confidence score (0-100).

        Respond in JSON format as follows:
        {{
            "category": "category_name",
            "justification": "A brief explanation for this classification",
            "confidence": 85
        }}

        Guidelines:
        - Classify as clear_intent_product only if the query contains specific technical criteria or constraints about product features (e.g., processor type, RAM size, specific interfaces).
        - Classify as vague_intent_product if the query is about products but lacks specific technical criteria, or if it's a request for a list of products without detailed specifications.
        - The number of products requested (e.g., "List 5 products") does not qualify as a specific criterion for clear intent.
        - Consider the chat history when making your classification. A vague query might become clear in the context of previous messages.
        - Classify as politics only if the query is primarily about political topics.
        - Use do_not_respond for queries that are inappropriate, offensive, or completely unrelated to computer hardware and embedded systems.
        - Be decisive - always choose the most appropriate category even if the query is ambiguous.

        Examples:
        - clear_intent_product:
            - "Find me a board with an Intel processor and at least 8GB of RAM"
            - "List Single Board Computers with a processor frequency of 1.5 GHz or higher"
            - "What are the top ARM-based development kits with built-in Wi-Fi and 4GB or more RAM?"

        - vague_intent_product:
            - "Tell me about single board computers"
            - "What are some good development kits?"
            - "I'm looking for industrial communication devices"
            - "List 12 Single Board Computers"
            - "Show me the best microcontrollers"

        """
        )

        human_template = """
        User Query: {query}

        Classification:
        """
        super().__init__(system_template, human_template, ["query"])


class QueryProcessorPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to process and expand the given query to improve product search results.
        Extract relevant product attributes, generate expanded queries, and identify additional query context.

        Here's a description of all the product attributes and data types stored for each product:
        {attribute_descriptions}

        Perform the following tasks:
        1. Extract relevant product attributes mentioned or implied in the query. Only use attributes that are explicitly listed in the product feature descriptions above.
        2. If the query mentions attributes not in the list (e.g., processor frequency), map them to the most relevant existing attribute (e.g., 'processor') and include the specific details in that attribute's value.
        3. Generate {num_expansions} expanded queries that could help find relevant products. These should be based on the original query and the extracted attributes.
        4. Identify any additional query context, such as the number of products requested or any sorting preferences.

        Respond in JSON format as follows:
        {{
            "extracted_attributes": {{
                // Include only relevant attributes that exist in the product feature descriptions
                // If an attribute is not mentioned or cannot be inferred, do not include it
                // For attributes not in the list, map to the most relevant existing attribute
            }},
            "expanded_queries": [
                // List of {num_expansions} expanded queries
            ],
            "query_context": {{
                "num_products_requested": null, // Number of products explicitly requested, or null if not specified
                "sort_preference": null // Any sorting preference mentioned (e.g., "cheapest", "newest"), or null if not specified
            }}
        }}

        Guidelines:
        - Only use attribute names that are explicitly listed in the product feature descriptions.
        - For attributes mentioned in the query but not in our list (e.g., processor frequency), include them in the most relevant existing attribute (e.g., 'processor').
        - Ensure all values are specific and aligned with our product database format.
        - Use technical specifications and numeric values where applicable, rather than general terms like "high" or "large".
        - If the query doesn't provide enough information to extract specific attributes, it's okay to leave the "extracted_attributes" empty.
        - Expanded queries should provide variations that might help in finding relevant products, considering different phrasings or related terms.
        - In the query_context, capture any explicit request for a specific number of products or sorting preference.

        Example:
        For a query like "List Single Board Computers with a processor frequency of 1.5 GHz or higher and manufactured by Broadcom", your response might look like:

        {{
            "extracted_attributes": {{
                "name": "Single Board Computers",
                "manufacturer": "Broadcom",
                "processor": "1.5 GHz or higher"
            }},
            "expanded_queries": [
                "Broadcom Single Board Computers with high-speed processors",
                "Single Board Computers by Broadcom with processors over 1.5 GHz",
                "Fast Broadcom SBCs with 1.5 GHz+ processors"
            ],
            "query_context": {{
                "num_products_requested": null,
                "sort_preference": null
            }}
        }}
        """
        )
        human_template = """
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "num_expansions", "attribute_descriptions"])


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
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "products", "attribute_mapping_str", "top_k"])


class SemanticSearchQueryPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to generate a semantic search query based on the user's vague product-related question.
        Also, determine the number of products that should be returned based on the user's query.

        Respond in JSON format as follows:
        {{
            "query": "The generated semantic search query",
            "product_count": 5  // Number of products to return, default to 5 if not specified
        }}

        Guidelines:
        - The query should be more detailed and specific than the user's original question.
        - Include relevant technical terms and specifications that might help in finding appropriate products.
        - If the user specifies a number of products they want to see, use that number for product_count.
        - If no number is specified, use 5 as the default product_count.
        """
        )

        human_template = """
        User Query: {query}

        Generated Search Query:
        """
        super().__init__(system_template, human_template, ["query"])


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
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query"])


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
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "classification"])


class VagueIntentResponsePrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Generate a response to a user's vague product-related question using the provided search results.
        Your response should be clear, informative, and directly address the user's query.

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
        Relevant Products: {products}
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "products"])


class ClearIntentResponsePrompt(BaseChatPrompt):
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
        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "products", "reranking_result"])


class DynamicAgentPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        You are an AI assistant specializing in computer hardware, particularly embedded systems, development kits, and industrial communication devices. Your task is to assist users with their queries about these products.

        You have access to the following tools:

        1. direct_search:
           - Input: query (string), limit (optional int, default 5)
           - Output: List of products matching the query, each with a certainty score
           - Description: Simple semantic search for products based on the query
           - When to use: For straightforward queries, when the user is not specific about what they are looking for

        2. expanded_search:
           - Input: query (string), limit (optional int, default 10)
           - Output: List of reranked products based on expanded queries, each with a relevance score
           - Description: Expands the query, performs semantic search, and reranks results
           - When to use: For complex queries or when the user is specif about what they are looking for.

        When you need to use a tool, respond with the following format:
        ACTION: {{"tool": "tool_name", "input": {{"param1": "value1", "param2": "value2"}}}}

        If you don't need to use a tool and can respond directly, provide your response in the specified JSON format.

        Always strive to provide accurate, up-to-date information and clarify any ambiguities in user queries.
        Maintain a professional yet approachable tone in your responses.

        After using a tool, analyze the results and provide a comprehensive response to the user's query.
        Include relevant product information, comparisons, and recommendations based on the tool results.

        Guidelines for tool usage:
        - Use direct_search for simple, straightforward queries about specific products
        - Use expanded_search for more complex queries or when you need a broader range of results
        - Use detailed_product_analysis when the user needs in-depth comparisons or detailed recommendations

        Remember to interpret the tool outputs correctly and use the information to formulate your final response to the user.

        IMPORTANT: Always provide your final response in the following JSON format:

        {{
            "message": "A concise response to the user's query",
            "products": [
                {{
                    "name": "Product Name", // We only need the name of the product
                }},
                // ... more products if applicable
            ],
            "reasoning": "Explanation of your thought process and how you arrived at this response",
            "follow_up_question": "A question to clarify the user's needs or to get more information",
        }}

        Ensure all fields are filled appropriately based on the query and tool results. If a field is not applicable, use an empty string, empty list, or empty object as appropriate.
        """
        )

        human_template = """
        User Query: {query}

        Please process this query and respond appropriately, using tools as necessary. Provide your final response in the specified JSON format.
        """
        super().__init__(system_template, human_template, ["query"])


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
