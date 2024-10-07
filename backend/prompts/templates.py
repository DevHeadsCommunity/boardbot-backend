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
        1. politics
        2. chitchat
        3. vague_intent_product
        4. clear_intent_product
        5. do_not_respond

        Provide your classification in JSON format as follows:
        {{
            "category": "category_name",
            "justification": "A brief explanation for this classification",
            "confidence": 85
        }}

        Category Definitions:
        - politics: Queries primarily related to political topics or figures.
        - chitchat: General conversation or small talk unrelated to products.
        - vague_intent_product: Product-related queries that lack specific technical criteria.
        - clear_intent_product: Product-related queries with at least two specific technical criteria or constraints.
        - do_not_respond: Queries that are inappropriate, offensive, or completely unrelated to our domain.

        Guidelines:
        - For clear_intent_product, look for specific technical specifications (e.g., processor type, RAM size, interface types).
        - The mere mention of a product category or a request for a list without specifications is vague_intent_product.
        - The number of products requested does not count as a specific criterion for clear intent.
        - Be decisive - choose the most appropriate category even for ambiguous queries.
        - Provide a confidence score (0-100) for your classification.
        - In the justification, briefly explain why you chose this category over others.

        Examples:
        - Clear intent: "Find a board with an Intel processor and at least 8GB of RAM"
        - Vague intent: "Tell me about single board computers" or "List 5 microcontrollers"
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

        Perform the following tasks:
        1. Extract relevant product attributes mentioned or implied in the query. Use these to create filters.
        2. Generate {num_expansions} expanded queries that could help find relevant products. These should be based on the original query and the extracted attributes.
        3. Identify any additional query context, such as the number of products requested or any sorting preferences.

        Respond in JSON format as follows:
        {{
            "filters": {{
                // Include only relevant attributes from the provided list
                // If an attribute is not mentioned or cannot be inferred, do not include it
                // Use exact values where possible, or ranges if a specific value is not given
            }},
            "expanded_queries": [
                // List of {num_expansions} expanded queries
            ],
            "query_context": {{
                "num_products_requested": 5, // Default to 5 if not specified in the query
                "sort_preference": null // Any sorting preference mentioned (e.g., "cheapest", "newest"), or null if not specified
            }}
        }}

        Guidelines:
        - Only use attribute names from the provided list for filters.
        - Ensure all filter values are specific and aligned with our product database format.
        - Use technical specifications and numeric values where applicable.
        - For numeric attributes, use ranges when a specific value is not given (e.g., "processor_speed": ">=2.5 GHz").
        - Always include "num_products_requested" in query_context, defaulting to 5 if not specified in the query.
        - Expanded queries should provide variations that might help in finding relevant products, considering different phrasings or related terms.
        - If the query is very specific, some expanded queries can be more general to broaden the search.
        - If the query is vague, some expanded queries should attempt to be more specific based on common use cases or popular configurations.
        """
        )
        human_template = """
        Attribute list:
        {attribute_descriptions}

        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "num_expansions", "attribute_descriptions"])


class ProductRerankingPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to rerank the given products based on their relevance to the user query and the specified filters.

        Instructions:
        1. Analyze each product against ALL criteria specified in the user query and filters.
        2. Rank products based on how closely they match the criteria.
        3. Return the top {top_k} most relevant products.
        4. Provide a clear justification for the ranking of each product.

        Use the following attribute mapping for evaluation:
        {attribute_mapping_str}

        Filters to consider:
        {filters}

        Query context:
        {query_context}

        Return the reranked products and justification in the following JSON format:
        {{
            "products": [
                {{
                    "name": "Product Name",
                    "relevance_score": 0.95,
                    "matching_criteria": ["List of criteria that this product matches"],
                    "missing_criteria": ["List of criteria that this product doesn't match, if any"]
                }},
                // ... more products
            ],
            "justification": "Clear, concise explanation of the ranking, addressing each criterion from the query and filters."
        }}

        Guidelines:
        - Prioritize exact matches of specified criteria over general relevance.
        - For numerical criteria (e.g., processor frequency, memory size), the product must meet or exceed the specified value.
        - If no products fully match all criteria, include partial matches and clearly explain the mismatches.
        - Provide a relevance score (0-1) for each product, where 1 is a perfect match and 0 is completely irrelevant.
        - In the justification, explain why products are included or excluded, addressing each criterion from the query and filters.
        - If no products match any criteria, return an empty product list and explain why in the justification.
        - Consider the query context (e.g., number of products requested, sort preference) in your ranking.
        """
        )

        human_template = """
        User Query: {query}
        Products to Rerank: {products}

        Reranked Products:
        """
        super().__init__(
            system_template,
            human_template,
            ["query", "products", "attribute_mapping_str", "filters", "query_context", "top_k"],
        )


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
        Your task is to engage in casual conversation while maintaining a friendly and professional tone. If appropriate, be prepared to smoothly transition into product-related topics.

        Instructions:
        1. Analyze the user's message and determine the most appropriate response.
        2. Generate a friendly and engaging response that addresses the user's input.
        3. If possible, include a subtle reference or transition to product-related topics.
        4. Formulate a follow-up question to continue the conversation.

        Respond in the following JSON format:
        {{
            "message": "Your friendly response to the user's message",
            "follow_up_question": "A question to keep the conversation going or transition to product-related topics"
        }}

        Guidelines:
        - Maintain a friendly, conversational tone in your responses.
        - The message should directly address the user's input in a natural, conversational manner.
        - Do not force product information into the conversation if it's not relevant or appropriate.
        - The follow-up question should aim to either continue the current topic of conversation or smoothly transition to product-related topics if appropriate.
        - If the user expresses interest in product-related topics, use that opportunity to transition into your area of expertise.
        - Be mindful of context and previous messages in the conversation if provided.
        """
        )
        human_template = """
        User Message: {query}

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
        Your task is to generate an informative response to a vague product-related query using the provided search results.

        Instructions:
        1. Analyze the user's query and the provided product search results.
        2. Generate a response that provides general information related to the query.
        3. Suggest a few relevant products that may interest the user.
        4. Provide reasoning for your suggestions and information.
        5. Formulate a follow-up question to help the user specify their requirements.

        Respond in the following JSON format:
        {{
            "message": "An informative message addressing the user's query, providing general product category information, and any additional context",
            "products": [
                {{
                    "name": "Product Name"
                }},
                // ... 2-3 more products if applicable
            ],
            "reasoning": "Explanation of why these products were suggested and how they relate to the query. Include any additional general information about the product category or technology here.",
            "follow_up_question": "A question to help the user specify their requirements or narrow down their search"
        }}

        Guidelines:
        - The message should provide an overview of the product category or technology mentioned in the query, along with any relevant general information.
        - Include 2-4 relevant products in the products list.
        - In the reasoning, explain why each product was suggested and how it relates to the query. Also include any additional context or explanations about the product category here.
        - Avoid making assumptions about specific requirements the user hasn't mentioned.
        - The follow-up question should aim to clarify the user's needs or use case.
        - If the query is extremely vague, focus on providing general information in the message and reasoning, and ask clarifying questions.
        - Maintain a helpful and informative tone, encouraging the user to provide more details.
        """
        )
        human_template = """
        User Query: {query}
        Relevant Products: {products}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "products"])


class ClearIntentResponsePrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Your task is to generate a comprehensive response to a clear intent product query based on the provided reranking results and relevant products.

        Instructions:
        1. Analyze the user's query and the reranking results.
        2. Generate a response that directly addresses the user's specific requirements.
        3. Only include products that FULLY match ALL criteria specified in the user's query.
        4. Provide clear reasoning for product inclusion or exclusion.

        Respond in the following JSON format:
        {{
            "message": "A concise introductory message addressing the user's query",
            "products": [
                {{
                    "name": "Product Name" // only the name of the product
                }},
                // ... more products if applicable
            ],
            "reasoning": "Clear explanation of product selection, including why products were included or excluded",
            "follow_up_question": "A single, relevant follow-up question based on the query and results"
        }}

        Guidelines:
        - Ensure absolute accuracy in matching products to the query criteria.
        - Do NOT confuse processor manufacturer with product manufacturer, or any other attributes.
        - If no products fully match ALL criteria, return an empty product list and explain why in the reasoning.
        - For products that match some but not all criteria, mention them in the reasoning but do not include in the product list.
        - The introductory message should be concise but informative, directly addressing the user's requirements.
        - The reasoning should be clear and detailed, explaining how each included product meets the criteria.
        - The follow-up question should aim to clarify or refine the user's requirements if needed.
        """
        )
        human_template = """
        User Query: {query}
        Reranking Result: {reranking_result}
        Relevant Products: {products}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "reranking_result", "products"])


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
        You are an intelligent assistant specialized in extracting detailed information from raw product data for computer hardware, particularly embedded systems, development kits, and industrial communication devices. Your goal is to identify and extract specific attributes related to a product. Follow these guidelines:

        1. Extract information for each attribute listed below.
        2. Each extracted feature should contain a single, distinct piece of information.
        3. Ensure consistency across all features - avoid contradictions.
        4. If information for an attribute is not available or not applicable, use 'Not available'.
        5. For list-type attributes, provide items as a JSON array, even if there's only one item.
        6. Use the exact attribute names as provided in the JSON structure below.

        Extract the following attributes:
        {attribute_descriptions}

        Ensure the extracted information is accurate, well-formatted, and provided in the exact JSON structure as shown above.
        """
        human_template = "Raw product data: {raw_data}"
        super().__init__(system_template, human_template, ["raw_data"])


class DataExtractionPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an intelligent assistant specialized in extracting detailed information from raw product data for computer hardware, particularly embedded systems, development kits, and industrial communication devices. Your goal is to identify and extract specific attributes related to a product. Follow these guidelines:

        1. Extract information for each attribute listed below.
        2. Each extracted feature should contain a single, distinct piece of information, with confidence score.
        3. Ensure consistency across all features - avoid contradictions.
        4. For names, like product name, or manufacturer name, ensure it is in clear, capital case, singular, without special characters. (Only the official name, dont include Code Name, or any other variant)
        5. If information for an attribute is not available or not applicable, use 'Not available' with a confidence score of 0.
        6. For each attribute, provide:
           - "value": the extracted information.
           - "confidence": a score between 0 and 1 indicating confidence in the extraction.
        7. For list-type attributes:
           - If data is available, provide items as a JSON array.
           - If data is not available, use 'Not available' (as a string).
        8. Use the exact attribute names as provided in the JSON structure below.

        Extract the following attributes:
        {attribute_descriptions}

        Ensure the extracted information is accurate, well-formatted, and provided in the exact nested JSON structure as shown above, with confidence score for each attribute
        """
        human_template = "Raw product data: {raw_data}"
        super().__init__(system_template, human_template, ["raw_data", "attribute_descriptions"])


class MissingFeatureExtractionPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an AI assistant specialized in extracting product information from context.
        Your task is to identify and extract **only** the following specific attributes, provided in the nested JSON structure below. Ensure the extracted information is accurate and provided in the same nested JSON format.

        For each attribute, provide:
        - "value": the extracted information.
        - "confidence": a score between 0 and 1.
        If information for an attribute is not found, use 'Not available' with a confidence score of 0.

        Attributes to extract:
        {features_to_extract}
        """
        human_template = """
        Context:
        {context}

        Extracted features so far:
        {extracted_features}

        Please provide **only** the missing features based on the given context, following the same nested JSON structure as provided in 'Attributes to extract'.

        Response:
        """
        super().__init__(
            system_template,
            human_template,
            ["context", "extracted_features", "features_to_extract"],
        )


class LowConfidenceFeatureRefinementPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = """
        You are an AI assistant specialized in refining product information from context.
        Your task is to refine **only** the following specific attributes, provided in the nested JSON structure below. Ensure the refined information is accurate and provided in the same nested JSON format.

        For each attribute, provide:
        - "value": the refined information.
        - "confidence": a score between 0 and 1.
        If a feature cannot be refined, keep its current value and confidence score.

        Attributes to refine:
        {features_to_refine}
        """
        human_template = """
        Context:
        {context}

        Extracted features so far:
        {extracted_features}

        Please refine the following low-confidence features based on the given context, following the same nested JSON structure as provided in 'Attributes to refine'.

        Response:
        """
        super().__init__(
            system_template,
            human_template,
            ["context", "extracted_features", "features_to_refine"],
        )
