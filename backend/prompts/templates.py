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


test_prompts = [
    {
        "prompt": "List Single Board Computers with a processor frequency of 1.5 GHz or higher and manufactured by Broadcom",
        "variations": [
            "List Single Board Computers with a processor frequency of 1.5 GHz or higher and manufactured by Broadcom",
            "Show Broadcom Single Board Computers with processors running at least 1.5 GHz",
            "Display SBCs made by Broadcom with CPU speeds of 1.5 GHz or above",
            "Enumerate Broadcom-manufactured Single Board Computers featuring 1.5+ GHz processors",
            "Find SBCs from Broadcom with processor frequencies of 1.5 GHz and higher",
        ],
    },
    {
        "prompt": "What are the available Computers on Module (COM) with DDR4 memory support and comes with an Intel processor?",
        "variations": [
            "What are the available Computers on Module (COM) with DDR4 memory support and comes with an Intel processor?",
            "List COMs featuring Intel processors and DDR4 memory compatibility",
            "Show Computers on Module with Intel CPUs and DDR4 RAM support",
            "Display available COMs that have Intel processors and DDR4 memory",
            "Enumerate Intel-based Computers on Module supporting DDR4 memory",
        ],
    },
    {
        "prompt": "Show Devkits that include FPGA and are manufactured by Microsemi Corporation.",
        "variations": [
            "Show Devkits that include FPGA and are manufactured by Microsemi Corporation.",
            "List Microsemi Corporation development boards featuring FPGAs",
            "Display FPGA-equipped devkits produced by Microsemi Corporation",
            "Enumerate Microsemi-made development kits that incorporate FPGAs",
            "Find Microsemi Corporation devkits with integrated FPGA technology",
        ],
    },
    {
        "prompt": "Find all SBCs that support PCIe Gen3 interface and have more than 8 cores",
        "variations": [
            "Find all SBCs that support PCIe Gen3 interface and have more than 8 cores",
            "List Single Board Computers with PCIe Gen3 support and over 8 processor cores",
            "Show SBCs featuring PCIe Gen3 compatibility and exceeding 8 CPU cores",
            "Display all Single Board Computers with PCIe Gen3 interface and 9+ cores",
            "Enumerate SBCs offering PCIe Gen3 and more than 8 processor cores",
        ],
    },
    {
        "prompt": "Provide a list of products with ARM Cortex processors that are available in a COM Express Basic form factor.",
        "variations": [
            "Provide a list of products with ARM Cortex processors that are available in a COM Express Basic form factor.",
            "Show COM Express Basic modules featuring ARM Cortex processors",
            "List products using ARM Cortex CPUs in COM Express Basic form factor",
            "Display ARM Cortex-based devices available in COM Express Basic format",
            "Enumerate COM Express Basic offerings equipped with ARM Cortex processors",
        ],
    },
    {
        "prompt": "Identify all hardware components manufactured by Broadcom Corporation that include ARM processors.",
        "variations": [
            "Identify all hardware components manufactured by Broadcom Corporation that include ARM processors.",
            "List Broadcom Corporation products featuring ARM processor architecture",
            "Show hardware components from Broadcom with ARM-based CPUs",
            "Display all ARM processor-equipped devices produced by Broadcom Corporation",
            "Enumerate Broadcom-made hardware incorporating ARM processor architecture",
        ],
    },
    {
        "prompt": "Which Advantech Computer on Modules support USB 3.0 interface?",
        "variations": [
            "Which Advantech Computer on Modules support USB 3.0 interface?",
            "List Advantech COMs that offer USB 3.0 compatibility",
            "Show Computer on Modules from Advantech with USB 3.0 support",
            "Display Advantech-manufactured COMs featuring USB 3.0 interfaces",
            "Enumerate Advantech Computer on Modules equipped with USB 3.0 ports",
        ],
    },
    {
        "prompt": "List all Single Board Computers with a memory capacity of 128GB or more with more than 2 USB ports.",
        "variations": [
            "List all Single Board Computers with a memory capacity of 128GB or more with more than 2 USB ports.",
            "Show SBCs featuring 128GB+ memory and 3 or more USB interfaces",
            "Display Single Board Computers with at least 128GB RAM and over 2 USB ports",
            "Enumerate SBCs that have 128GB or higher memory capacity and 3+ USB connections",
            "Find Single Board Computers with 128GB+ memory and more than two USB interfaces",
        ],
    },
    {
        "prompt": "What are the available NXP powered Computer on Module products that include SATA 3.0 interface?",
        "variations": [
            "What are the available NXP powered Computer on Module products that include SATA 3.0 interface?",
            "List COMs with NXP processors featuring SATA 3.0 support",
            "Show NXP-based Computer on Modules that offer SATA 3.0 connectivity",
            "Display Computer on Module products using NXP chips and including SATA 3.0 interfaces",
            "Enumerate NXP-powered COMs equipped with SATA 3.0 ports",
        ],
    },
    {
        "prompt": "Find Single Board Computers with a form factor smaller than 100mm x 100mm and RAM more 256 MB",
        "variations": [
            "Find Single Board Computers with a form factor smaller than 100mm x 100mm and RAM more 256 MB",
            "List SBCs smaller than 100x100mm with over 256MB of memory",
            "Show compact Single Board Computers (sub-100x100mm) featuring more than 256MB RAM",
            "Display SBCs with form factors under 100mm x 100mm and memory exceeding 256MB",
            "Enumerate Single Board Computers smaller than 100x100mm that have 256MB+ RAM",
        ],
    },
    {
        "prompt": "List all devices that support voltage ranges from 1.2V to 3.3V.",
        "variations": [
            "List all devices that support voltage ranges from 1.2V to 3.3V.",
            "Show hardware components with input voltage support between 1.2V and 3.3V",
            "Display devices operating within 1.2V to 3.3V input voltage range",
            "Enumerate products compatible with 1.2V-3.3V power input",
            "Find all components functioning with input voltages from 1.2V up to 3.3V",
        ],
    },
    {
        "prompt": "Show products that include an Intel Xeon Processor D and support Embedded Software API.",
        "variations": [
            "Show products that include an Intel Xeon Processor D and support Embedded Software API.",
            "List devices featuring Intel Xeon D CPUs with Embedded Software API compatibility",
            "Display hardware with Intel Xeon Processor D that supports Embedded Software API",
            "Enumerate products using Intel Xeon D chips and offering Embedded Software API",
            "Find items combining Intel Xeon Processor D with Embedded Software API support",
        ],
    },
    {
        "prompt": "Which products offer a high-performance FPGA feature and are suitable for embedded development?",
        "variations": [
            "Which products offer a high-performance FPGA feature and are suitable for embedded development?",
            "List high-performance FPGA products designed for embedded systems development",
            "Show devices with powerful FPGAs tailored for embedded development",
            "Display products combining high-performance FPGAs with embedded development capabilities",
            "Enumerate FPGA-based hardware suitable for high-performance embedded development",
        ],
    },
    {
        "prompt": "Provide a list of Single Board Computers that can operate at a frequency up to 2.7 GHz with MiniITX form factor.",
        "variations": [
            "Provide a list of Single Board Computers that can operate at a frequency up to 2.7 GHz with MiniITX form factor.",
            "Show Mini-ITX SBCs capable of running at frequencies up to 2.7 GHz",
            "List Single Board Computers in Mini-ITX form factor with max 2.7 GHz processor speed",
            "Display Mini-ITX format SBCs that can reach 2.7 GHz operating frequency",
            "Enumerate Mini-ITX Single Board Computers with processors up to 2.7 GHz",
        ],
    },
    {
        "prompt": "What components are available with embedded nonvolatile flash memory and at least 4GB of RAM?",
        "variations": [
            "What components are available with embedded nonvolatile flash memory and at least 4GB of RAM?",
            "List hardware featuring built-in nonvolatile flash memory and 4GB or more RAM",
            "Show products that include embedded nonvolatile flash memory and a minimum of 4GB RAM",
            "Display components offering integrated nonvolatile flash memory capabilities with 4GB+ memory",
            "Enumerate devices equipped with on-board nonvolatile flash memory and at least 4GB of RAM",
        ],
    },
    {
        "prompt": 'Identify all products with a "Customizable System-on-Chip (cSoC)" type with ARM Cortex processor.',
        "variations": [
            'Identify all products with a "Customizable System-on-Chip (cSoC)" type with ARM Cortex processor.',
            "List ARM Cortex-based Customizable System-on-Chip (cSoC) offerings",
            "Show cSoC products featuring ARM Cortex processors",
            "Display all ARM Cortex-powered Customizable System-on-Chip solutions",
            "Enumerate Customizable SoC devices with ARM Cortex CPU architecture",
        ],
    },
    {
        "prompt": "Top 5 Single Board Computers products that support dual Gigabit Ethernet and SATA.",
        "variations": [
            "Top 5 Single Board Computers products that support dual Gigabit Ethernet and SATA.",
            "List best 5 SBCs featuring both dual Gigabit Ethernet and SATA interfaces",
            "Show top 5 Single Board Computers with dual GbE and SATA support",
            "Display 5 premium SBCs offering dual Gigabit Ethernet and SATA connectivity",
            "Enumerate 5 leading Single Board Computers equipped with dual GbE and SATA",
        ],
    },
    {
        "prompt": "Which products offer up to 16 cores and 2.3 GHz frequency in their processors?",
        "variations": [
            "Which products offer up to 16 cores and 2.3 GHz frequency in their processors?",
            "List devices featuring processors with up to 16 cores and 2.3 GHz clock speed",
            "Show products with CPUs offering maximum 16 cores and 2.3 GHz frequency",
            "Display items with processors supporting up to 16 cores and 2.3 GHz clock rate",
            "Enumerate hardware using processors that have up to 16 cores and 2.3 GHz speed",
        ],
    },
    {
        "prompt": "Find Kontron products that include both ECC and non-ECC memory options.",
        "variations": [
            "Find Kontron products that include both ECC and non-ECC memory options.",
            "List Kontron devices supporting both ECC and non-ECC RAM",
            "Show Kontron hardware with ECC and non-ECC memory compatibility",
            "Display Kontron products that provide ECC and non-ECC memory choices",
            "Enumerate Kontron offerings featuring both ECC and non-ECC memory support",
        ],
    },
    {
        "prompt": "List all hardware platforms with on-chip frame memory and supports a TFT-LCD controller.",
        "variations": [
            "List all hardware platforms with on-chip frame memory and supports a TFT-LCD controller.",
            "Show devices featuring on-chip frame memory and TFT-LCD controller support",
            "Display hardware solutions with integrated frame memory and TFT-LCD controller",
            "Enumerate platforms that include on-chip frame memory and TFT-LCD controller capabilities",
            "Find products combining on-chip frame memory with TFT-LCD controller functionality",
        ],
    },
    {
        "prompt": "Provide a list of Single Board Computers manufactured by Advantech that include USB 3.0 support.",
        "variations": [
            "Provide a list of Single Board Computers manufactured by Advantech that include USB 3.0 support.",
            "Show Advantech-made SBCs featuring USB 3.0 interfaces",
            "List Advantech Single Board Computers with USB 3.0 compatibility",
            "Display Advantech-manufactured SBCs equipped with USB 3.0 ports",
            "Enumerate Advantech Single Board Computers offering USB 3.0 support",
        ],
    },
    {
        "prompt": "Which devices support Intel Hyper-Threading Technology with mATX form factor?",
        "variations": [
            "Which devices support Intel Hyper-Threading Technology with mATX form factor?",
            "List mATX form factor products featuring Intel Hyper-Threading Technology",
            "Show hardware in mATX format that includes Intel Hyper-Threading support",
            "Display mATX devices compatible with Intel Hyper-Threading Technology",
            "Enumerate mATX form factor items offering Intel Hyper-Threading capabilities",
        ],
    },
    {
        "prompt": "Identify products that include programmable analog components and embedded nonvolatile memory.",
        "variations": [
            "Identify products that include programmable analog components and embedded nonvolatile memory.",
            "List devices featuring both programmable analog elements and embedded nonvolatile memory",
            "Show hardware solutions combining programmable analog capabilities with embedded nonvolatile memory",
            "Display products that offer programmable analog components alongside embedded nonvolatile memory",
            "Enumerate items integrating programmable analog features and embedded nonvolatile memory",
        ],
    },
    {
        "prompt": "What are the available hardware platforms with built-in Intel Turbo Boost Technology and Hyper-Threading Technology?",
        "variations": [
            "What are the available hardware platforms with built-in Intel Turbo Boost Technology and Hyper-Threading Technology?",
            "List devices featuring both Intel Turbo Boost and Hyper-Threading Technologies",
            "Show hardware solutions that incorporate Intel Turbo Boost and Hyper-Threading capabilities",
            "Display products offering built-in support for Intel Turbo Boost and Hyper-Threading",
            "Enumerate platforms equipped with Intel Turbo Boost and Hyper-Threading Technologies",
        ],
    },
    {
        "prompt": "Show all SBCs supporting Verilog and C with detailed specifications for FPGA integration.",
        "variations": [
            "List Single Board Computers compatible with Verilog and C for FPGA development",
            "Display SBCs that support both Verilog and C languages for FPGA integration",
            "Enumerate Single Board Computers offering Verilog and C compatibility for FPGA projects",
            "Find SBCs with FPGA integration capabilities supporting Verilog and C programming",
        ],
    },
]
