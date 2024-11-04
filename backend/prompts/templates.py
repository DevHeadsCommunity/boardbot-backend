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
        Your task is to process queries about computer hardware, focusing on embedded systems, development kits, and related products. Extract relevant product attributes to create search filters.

        **Guidelines:**
        1. **Use only attribute names from the provided list for filters.**
        2. **Include only attributes explicitly mentioned in the query. Do not include attributes that are implied or inferred.**
        3. **Map user terminology directly to standardized attribute values using the examples provided in the attribute list.**
        4. **If the user's term doesn't exactly match a standardized value, choose the closest matching standardized value only if the mapping is clear. If mapping is unclear, omit the attribute.**
        5. **Use standardized values from the attribute list examples where applicable (e.g., "INTEL" for processor_manufacturer, "X86-64" for processor_architecture).**
        6. **Distinguish between 'manufacturer' and 'processor_manufacturer':**
            - **If a company is mentioned as producing the product, map it to 'manufacturer'.**
            - **If a company is mentioned as producing the processor or chipset, map it to 'processor_manufacturer'.**
        7. **For processor architecture, use specific terms like "ARM Cortex-A53" or "X86-64" as stated in the query. Do not generalize or infer.**
        8. **Be specific when the query is specific (e.g., "8.0GB DDR4"), and general when the query is general (e.g., "DDR4").**
        9. **For multi-value attributes, provide a list of standardized values (e.g., ["WI-FI 6", "BLUETOOTH 5+"] for wireless).**
        10. **For range values, use the format "min_value-max_value" with units included (e.g., "0.256GB-64.0GB" for memory).**
        11. **Convert units when necessary to match standardized units (e.g., MB to GB).**
        12. **Do not include filters for implied features unless they are explicitly stated in the query.**
        13. **For memory, combine size and type into a single string when both are specified (e.g., "8.0GB DDR4").**
        14. **Include units for measurements (e.g., "W" for TDP, "V" for voltage, "°C" for temperature).**
        15. **Identify the number of products requested, defaulting to 5 if not specified.**
        16. **When mapping form factors, use standardized values and map common terms accordingly:**
            - **"Computer on Module" → "COM"**
            - **"COM Express" → "COM EXPRESS"**
            - **"Single Board Computer" or "SBC" → "SBC"**
        17. **If a term does not match any standardized value and mapping is unclear, omit the attribute. Do not guess or infer.**
        18. **Do not include comments in the JSON response.**

        Respond in this JSON format:
        {{
            "filters": {{
                // Include only relevant attributes
                // Omit attributes not mentioned or implied
            }},
            "query_context": {{
                "num_products_requested": <number>,
                "sort_preference": null
            }}
        }}

        Examples:

        Query: "List COM Express modules with Intel Core i7 CPUs and at least 16GB DDR4 RAM"
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

        Query: "Show 3 Microsemi development kits supporting 9V to 36V input voltage with Wi-Fi 6 and Bluetooth 5+"
        Response:
        {{
            "filters": {{
                "manufacturer": "MICROSEMI",
                "form_factor": "DEVELOPMENT BOARD",
                "input_voltage": "9V-36V",
                "wireless": ["WI-FI 6", "BLUETOOTH 5+"]
            }},
            "query_context": {{
                "num_products_requested": 3,
                "sort_preference": null
            }}
        }}

        Query: "List products with ARM Cortex-A53 processors manufactured by Broadcom with 4GB LPDDR4 memory"
        Response:
        {{
            "filters": {{
                "processor_manufacturer": "BROADCOM",
                "processor_architecture": "ARM Cortex-A53",
                "memory": "4.0GB LPDDR4"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}


        Query: "Show FPGA-based products for embedded development with 64GB eMMC storage and operating temperature range from -40°C to 85°C"
        Response:
        {{
            "filters": {{
                "processor_architecture": "FPGA",
                "form_factor": "DEVELOPMENT BOARD",
                "onboard_storage": "64.0GB EMMC",
                "operating_temperature_min": "-40°C",
                "operating_temperature_max": "85°C"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Query: "List Single Board Computers, manufactured by Broadcom Corporation, featuring ARM processor architecture, with RAM more than 256MB"
        Response:
        {{
            "filters": {{
                "manufacturer": "BROADCOM",
                "form_factor": "SBC",
                "processor_architecture": "ARM",
                "memory": "0.256GB-64.0GB"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Query: "Show products with Broadcom processors, ARM architecture, and at least 1GB of RAM"
        Response:
        {{
            "filters": {{
                "processor_manufacturer": "BROADCOM",
                "processor_architecture": "ARM",
                "memory": "1.0GB-64.0GB"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        """
        )
        human_template = """
        Attribute list with examples:
        {attribute_descriptions}

        User Query: {query}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "attribute_descriptions"])


class ProductRerankingPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to rerank the given products based on their relevance to the user query and the specified filters.

        Instructions:
        1. Analyze each product against the criteria specified in the filters.
        2. Rank products based on how closely they match the criteria in the filters.
        3. Include ALL products that match at least one criterion, sorted by relevance.
        4. If fewer than {top_k} products match any criteria, include all matching products.
        5. If more than {top_k} products match at least one criterion, return the top {top_k} most relevant products.
        6. Provide a clear justification for the ranking of each product.

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
                    "product_id": "Product ID",
                    "relevance_score": 0.95,
                    "matching_criteria": ["List of criteria from the filters that this product matches"],
                    "missing_criteria": ["List of criteria from the filters that this product doesn't match"]
                }},
                // ... more products
            ],
            "justification": "Clear, concise explanation of the ranking, addressing the criteria from the filters."
        }}

        Guidelines:
        - Include ALL products that match at least one criterion, up to {top_k} products.
        - Sort products by relevance, with those matching more criteria ranked higher.
        - Provide a relevance score (0-1) for each product, where 1 is a perfect match and 0 is completely irrelevant.
        - In the justification, explain the overall ranking and mention if some products only partially match the criteria.
        - If no products match any criteria, return an empty product list and explain why in the justification.
        - Completely disregard any criteria or attributes not present in the filters, even if they seem relevant to the query.
        """
        )

        human_template = """
        Filters: {filters}
        Products to Rerank: {products}

        Reranked Products:
        """
        super().__init__(
            system_template,
            human_template,
            ["products", "attribute_mapping_str", "filters", "query_context", "top_k"],
        )


class SemanticSearchQueryPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            PROCESSING_BASE
            + """
        Your task is to generate a semantic search query based on the user's product-related question and extract relevant product attributes to create search filters.

        Guidelines:
        1. Generate a focused semantic search query that captures the main intent of the user's question.
        2. Use only attribute names from the provided list for filters.
        3. Include attributes explicitly mentioned or strongly implied in the query.
        4. Use standardized values from the attribute list examples where applicable (e.g., "INTEL" for processor_manufacturer, "X86-64" for processor_architecture).
        5. Distinguish between manufacturer (e.g., "ADVANTECH", "CONGATEC") and processor_manufacturer (e.g., "INTEL", "AMD") attributes.
        6. For processor architecture, use specific terms like "ARM" or "X86-64" rather than brand names.
        7. Be specific when the query is specific (e.g., "8.0GB DDR4"), and general when the query is general (e.g., just "DDR4").
        8. For multi-value attributes, use comma-separated values (e.g., "WI-FI 6, BLUETOOTH 5+" for wireless).
        9. For range values, use the format "min-max" (e.g., "9.0V-36.0V" for input_voltage).
        10. Do not include filters for implied features unless explicitly stated in the query.
        11. For memory, combine size and type into a single string, when both are specified. (e.g., "8.0GB DDR4").
        12. Include units for measurements (e.g., "W" for TDP, "V" for voltage, "°C" for temperature).
        13. Identify the number of products requested, defaulting to 5 if not specified.

        Respond in this JSON format:
        {{
            "query": "The generated semantic search query",
            "filters": {{
                // Include only relevant attributes
                // Omit attributes not mentioned or implied
            }},
            "product_count": <number>  // Number of products to return, default to 5 if not specified
        }}

        Examples:

        User Query: "Find COM Express modules with Intel Core i7 CPUs and at least 16GB DDR4 RAM"
        Response:
        {{
            "query": "COM Express modules Intel Core i7 16GB DDR4 RAM",
            "filters": {{
                "form_factor": "COM EXPRESS",
                "processor_manufacturer": "INTEL",
                "processor_architecture": "X86-64",
                "memory": "16.0GB-64.0GB DDR4"
            }},
            "product_count": 5
        }}

        User Query: "Show 3 Microsemi development kits supporting 9V to 36V input voltage with Wi-Fi 6 and Bluetooth 5+"
        Response:
        {{
            "query": "Microsemi development kits 9V to 36V input voltage Wi-Fi 6 Bluetooth 5+",
            "filters": {{
                "manufacturer": "MICROSEMI",
                "form_factor": "DEVELOPMENT BOARD",
                "input_voltage": "9V-36V",
                "wireless": ["WI-FI 6", "BLUETOOTH 5+"]
            }},
            "product_count": 3
        }}
        """
        )

        human_template = """
        Attribute list for filters:
        {attribute_descriptions}

        User Query: {query}

        Generated Search Query and Filters:
        """
        super().__init__(system_template, human_template, ["query", "attribute_descriptions"])


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
        3. Select exactly {product_count} products that best answer the user's query. Include all {product_count} products, even if some only partially match the query.
        4. Sort the products by relevance to the query, with the most relevant products first.
        5. Provide reasoning for your selection and information.
        6. Formulate a follow-up question to help the user specify their requirements.

        Respond in the following JSON format:
        {{
            "message": "An informative message addressing the user's query, providing general product category information, and any additional context",
            "products": [
                {{
                    "product_id": "Product ID" // We only need product id
                }},
                // ... Exactly {product_count} products
            ],
            "reasoning": "Explanation of why these products were selected and how they relate to the query. Include any additional general information about the product category or technology here. If some products only partially match the query, explain this.",
            "follow_up_question": "A question to help the user specify their requirements or narrow down their search"
        }}

        Guidelines:
        - The message should provide an overview of the product category or technology mentioned in the query, along with any relevant general information.
        - Include exactly {product_count} products in the products list, sorted by relevance to the query.
        - In the reasoning, explain the overall selection and mention if some products only partially match the query.
        - Maintain a helpful and informative tone, providing answers rather than suggestions.
        - Ensure that the response adheres strictly to the specified JSON format.
        - Frame the follow-up question as a curious inquiry to learn more about the user's needs or preferences.
        """
        )
        human_template = """
        User Query: {query}
        Relevant Products: {products}
        Number of Products to Return: {product_count}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "products", "product_count"])


class ClearIntentResponsePrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        Your task is to generate an engaging and conversational response to a clear intent product query based on the provided search results and filters.

        Instructions:
        1. Analyze the user's query, the search results, and the filters used.
        2. Generate a response that addresses the user's requirements in a natural, conversational tone.
        3. Include ALL products provided in the search results, sorted by their relevance to the query and filters.
        4. Discuss the products that best match the criteria and those that partially match in a flowing, engaging manner.
        5. Avoid explicitly categorizing products as "perfect matches" or "partial matches". Instead, weave this information into the conversation naturally.

        Respond in the following JSON format:
        {{
            "message": "An engaging, conversational message addressing the query results, highlighting relevant products and their features",
            "products": [
                {{
                    "product_id": "Product ID"
                }},
                // ... include all products from the search results
            ],
            "reasoning": "A natural explanation of the product selection and how they relate to the user's needs",
            "follow_up_question": "A conversational follow-up question to further assist the user"
        }}

        Guidelines:
        - Write in a friendly, approachable tone as if you're having a conversation with the user.
        - Keep the "message" concise and focused, ideally not exceeding a few sentences.
        - Highlight the most relevant products first, mentioning key features that align with the user's needs and the applied filters.
        - Include ALL products from the search results, even if some only partially match the criteria.
        - Ensure the response is engaging and human-like, avoiding robotic or overly formal language.
        - If no products perfectly match all criteria, acknowledge this in a positive way and focus on the closest matches.
        - Frame the follow-up question as a curious inquiry to learn more about the user's needs or preferences.
        - If fewer products are returned than requested, acknowledge this and explain potential reasons (e.g., specific requirements limiting the options).
        """
        )
        human_template = """
        User Query: {query}
        Applied Filters: {filters}
        Search Results: {products}

        Response:
        """
        super().__init__(system_template, human_template, ["query", "filters", "products"])


class DynamicAgentPrompt(BaseChatPrompt):
    def __init__(self):
        system_template = (
            USER_FACING_BASE
            + """
        You are an AI assistant specializing in computer hardware, particularly embedded systems, development kits, and industrial communication devices. Your task is to assist users with their queries about these products.

        You have access to the following tools:

        1. direct_search:
        - Input: {{"query": "search query", "limit": 5}}
        - Description: Performs a semantic search to find products matching the query.
        - When to use: For straightforward queries or when the user is not specific.

        2. expanded_search:
        - Input: {{"query": "search query", "limit": 10}}
        - Description: Expands the query, generates filters, performs searches, and reranks results.
        - When to use: For complex queries or when the user provides specific criteria.

        When you decide to use a tool, respond with the following format:
        {{
            "action": "tool",
            "tool": "tool_name",
            "input": {{
                "query": "search query",
                "limit": 5  // Use 5 as default, or the number specified by the user
            }}
        }}

        After receiving the tool output, analyze it and decide whether to use another tool or provide the final answer.

        When you are ready to provide the final answer, respond with:

        {{
            "message": "Your response to the user",
            "products": [
                {{
                    "product_id": "Product ID"
                }},
                // ... Include all products from the search results, up to the requested limit
            ],
            "reasoning": "Your reasoning or additional information",
            "follow_up_question": "A question to engage the user further"
        }}
        Always ensure your responses are in valid JSON format.

        Guidelines:
        - Use tools when necessary to retrieve information needed to answer the user's query.
        - Do not mention the tools or the fact that you are using them in the final answer.
        - Be concise and informative in your responses.
        - Maintain a professional and friendly tone.
        - Include all products returned by the search, up to the limit specified by the user or 5 if not specified.
        - Sort products by relevance, mentioning the most relevant ones first in your response.
        - If some products only partially match the query, acknowledge this in your response.
        - Frame the follow-up question as a curious inquiry to learn more about the user's needs or preferences.
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
        5. The following attributes should always be single values, not lists: name, manufacturer, form_factor, processor_architecture, processor_manufacturer, input_voltage, operating_temperature_max, operating_temperature_min.
        6. If information for an attribute is not available or not applicable, use 'Not available' with a confidence score of 0.
        7. For each attribute, provide:
           - "value": the extracted information.
           - "confidence": a score between 0 and 1 indicating confidence in the extraction.
        8. For list-type attributes:
           - If data is available, provide items as a JSON array.
           - If data is not available, use 'Not available' (as a string).
        9. Use the exact attribute names as provided in the JSON structure below.

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
        Ensure that attributes like name, manufacturer, form_factor, processor_architecture, processor_manufacturer, input_voltage, operating_temperature_max, and operating_temperature_min are always single string values, not lists.

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


        Guidelines for Direct Response:
        1. For queries without clear product requirements, generate a direct response in a conversational tone.
        2. Frame follow-up questions to better understand user requirements.

        Guidelines for Filter Extraction:
        1. Use ONLY attribute names from the provided list for filters
        2. Include ONLY explicitly mentioned attributes - do not infer
        3. Use standardized values (e.g., "INTEL" for processor_manufacturer)
        4. Distinguish between manufacturer and processor_manufacturer:
           - manufacturer: company making the product
           - processor_manufacturer: company making the CPU
        5. For processor architecture, use exact terms (e.g., "ARM Cortex-A53", "X86-64")
        6. For memory, combine size and type when both specified (e.g., "8.0GB DDR4")
        7. For ranges, use format "min_value-max_value" with units
        8. Include units for measurements (W for TDP, V for voltage, °C for temperature)
        9. For multi-value attributes, use arrays (e.g., ["WI-FI 6", "BLUETOOTH 5+"])
        10. Map form factors consistently:
            - "Computer on Module" → "COM"
            - "COM Express" → "COM EXPRESS"
            - "Single Board Computer" → "SBC"

        Respond in this JSON format:

        For specific product queries:
        {{
            "filters": {{
                // Only include explicitly mentioned attributes
                // Use exact attribute names and standardized values
            }},
            "query_context": {{
                "num_products_requested": <number>, // Default to 5 if not specified
                "sort_preference": null
            }}
        }}

        For general product queries:
        {{
            "query_context": {{
                "num_products_requested": 5, // Default to 5 if not specified
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


        Examples for Filter Extraction:

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

        Query: "Show FPGA-based products for embedded development with 64GB eMMC storage and operating temperature range from -40°C to 85°C"
        Response:
        {{
            "filters": {{
                "processor_architecture": "FPGA",
                "form_factor": "DEVELOPMENT BOARD",
                "onboard_storage": "64.0GB EMMC",
                "operating_temperature_min": "-40°C",
                "operating_temperature_max": "85°C"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Query: "List Single Board Computers, manufactured by Broadcom Corporation, featuring ARM processor architecture, with RAM more than 256MB"
        Response:
        {{
            "filters": {{
                "manufacturer": "BROADCOM",
                "form_factor": "SBC",
                "processor_architecture": "ARM",
                "memory": "0.256GB-64.0GB"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Query: "Show products with Broadcom processors, ARM architecture, and at least 1GB of RAM"
        Response:
        {{
            "filters": {{
                "processor_manufacturer": "BROADCOM",
                "processor_architecture": "ARM",
                "memory": "1.0GB-64.0GB"
            }},
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Examples for general product queries:

        Query: "Tell me about development boards"
        Response:
        {{
            "query_context": {{
                "num_products_requested": 5,
                "sort_preference": null
            }}
        }}

        Examples for Non-Product Queries:

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
        self.base_guidelines = """
        Your task is to generate concise, informative responses about hardware products.

        Core Response Requirements:
        - Maximum 2-3 sentences for the main message
        - Focus on addressing the query's core intent
        - Keep technical details focused on relevant specifications
        - Maintain natural, conversational tone
        - CRITICAL: You must include EVERY SINGLE product provided in the Product Results in your response's products list, maintaining their exact order
        - Each product in the results must be included in your response, even if it doesn't perfectly match the search criteria
        - Never filter, exclude, or omit any products from your response
        - When products have identical names but different product_ids, include all of them

        Response Structure:
        1. Opening statement addressing query intent and total number of products found
        2. Brief technical insights focusing on the best matches
        3. Acknowledge partial matches if present
        4. Include a follow-up question about user requirements

        Technical Details Guidelines:
        - Only mention specs relevant to the query
        - Use standardized units and terminology
        - Prioritize user-specified requirements
        - When discussing multiple similar products, focus on key differentiators
        """

        self.search_guidelines = {
            "filtered": {
                "focus": "Exact technical requirement matches",
                "key_points": [
                    "Start with total number of products found",
                    "Lead with products that match specified requirements",
                    "Acknowledge products that partially match requirements",
                    "Include ALL products in the response, even those with minimal relevance",
                ],
                "example": """{{
                    "message": "Found 5 boards in total, with 2 fully matching your Intel CPU and DDR4 requirements, and 3 offering alternative configurations that might interest you.",
                    "products": [
                        // MUST include ALL products from Product Results in the same order
                        {{"product_id": "product1"}},
                        {{"product_id": "product2"}},
                        {{"product_id": "product3"}},
                        {{"product_id": "product4"}},
                        {{"product_id": "product5"}}
                    ],
                    "reasoning": "Listed all available products, with product1 and product2 being exact matches for your requirements, while the others offer different specifications that might be suitable alternatives.",
                    "follow_up_question": "Would you like more details about specific features of any of these boards?"
                }}""",
            },
            "semantic": {
                "focus": "Category and capability overview",
                "key_points": [
                    "Start with total number of products found",
                    "Highlight range of capabilities across all products",
                    "Emphasize distinct features across selection",
                    "Include ALL products in the response",
                ],
                "example": """{{
                    "message": "Found 5 development boards in total, ranging from compact ARM solutions to full-featured x86 platforms, offering diverse connectivity options.",
                    "products": [
                        // MUST include ALL products from Product Results in the same order
                        {{"product_id": "product1"}},
                        {{"product_id": "product2"}},
                        {{"product_id": "product3"}},
                        {{"product_id": "product4"}},
                        {{"product_id": "product5"}}
                    ],
                    "reasoning": "Listed all available products, showcasing the full range of architectures and capabilities in our catalog.",
                    "follow_up_question": "Which processor architecture interests you most?"
                }}""",
            },
            "hybrid": {
                "focus": "Balanced exact and similar matches",
                "key_points": [
                    "Start with total number of products found",
                    "Present exact matches first",
                    "Include relevant alternatives",
                    "Include ALL products in the response",
                ],
                "example": """{{
                    "message": "Found 5 boards in total: 2 exactly matching your specifications, plus 3 alternatives with complementary features.",
                    "products": [
                        // MUST include ALL products from Product Results in the same order
                        {{"product_id": "product1"}},
                        {{"product_id": "product2"}},
                        {{"product_id": "product3"}},
                        {{"product_id": "product4"}},
                        {{"product_id": "product5"}}
                    ],
                    "reasoning": "Listed all available products, combining exact requirement matches with relevant alternatives that offer additional features.",
                    "follow_up_question": "Would you like to explore the additional features of the alternative options?"
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

        Current Search Context: {method['focus']}

        Response Priorities:
        {self._format_list(method['key_points'])}

        Expected Response Format:
        {method['example']}

        Remember:
        - Keep responses focused and concise
        - Maintain technical accuracy
        - Use conversational but professional tone
        - Address core user needs first
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
