import tiktoken
import datetime
import logging
from openai import OpenAI
from config import Config
from typing import List, Dict, Optional, Tuple


logging.basicConfig(level=logging.INFO)


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

class OpenAIClient:
    def __init__(self):
        self.config = Config()
        self._client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.encoder = tiktoken.encoding_for_model(self.config.DEFAULT_MODEL)

    def format_message(self, role: str, message: str) -> Message:
        return Message(role, message)

    def format_user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def format_system_message(
        self,
        message: str,
    ) -> dict:
        return {"role": "system", "content": message}

    def get_response(self, messages: List[Message], model: Optional[str] = None,
                     temperature: Optional[float] = None, max_tokens: Optional[int] = None,
                     top_p: Optional[float] = None, stream: bool = False):
        try:
            response = self._client.chat.completions.create(
                model=model or self.config.DEFAULT_MODEL,
                messages=[msg.to_dict() for msg in messages],
                temperature=temperature or self.config.DEFAULT_TEMPERATURE,
                max_tokens=max_tokens or self.config.DEFAULT_MAX_TOKENS,
                top_p=top_p or self.config.DEFAULT_TOP_P,
                stream=stream,
            )
            return response
        except Exception as e:
            raise ValueError(f"Error in OpenAI API call: {str(e)}")

    def generate_response(self, user_message: str, context: Optional[str] = None,
                          history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, int, int, float]:
        messages = self._prepare_messages(user_message, context, history)
        input_token_count = len(self.encoder.encode(str(messages)))
        logging.info(f"Input token count: {input_token_count}")

        response = self.get_response(messages)
        output_token_count = len(self.encoder.encode(response.choices[0].message.content))
        logging.info(f"Output token count: {output_token_count}")

        return response.choices[0].message.content, input_token_count, output_token_count

    def _prepare_messages(self, user_message: str, context: Optional[str],
                          history: Optional[List[Dict[str, str]]]) -> List[Message]:
        messages = []

        if context:
            system_message = self._get_system_message_with_context(context)
            messages.append(self.format_message("system", system_message))

        if history:
            for message in history[-5:]:  # Only keep the last 5 messages
                role = "user" if message.get("isUserMessage") else "assistant"
                content = message.get("message") if role == "user" else message.get("textResponse")
                messages.append(self.format_message(role, content))

        messages.append(self.format_message("user", user_message))
        return messages

    def _get_system_message_with_context(self, context: str) -> str:
        return f"""You are ThroughPut assistant. Your main task is to help users with their queries about the product.
                   The context that is provided is product data, in the form of name, size, form, processor, core, frequency, memory, voltage, io, thermal, feature, type, specification, manufacturer, location, description, and summary.
                   In your response, synthesize the information from the context into a clear, simple, and easy-to-understand response to the user.
                   make sure your response is in a JSON format.
                   Use the following context: {context}"""

    def extract_data(self, text: str) -> str:
        system_message = self._get_data_extraction_system_message()
        user_message = f"Raw product data: {text}"
        messages = [
            self.format_message("system", system_message),
            self.format_message("user", user_message)
        ]
        response = self.get_response(messages, max_tokens=4096)
        return response.choices[0].message.content

    def _get_data_extraction_system_message(self) -> str:
        return """
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

            Ensure the extracted information is accurate and well-formatted. Provide the extracted details in the following JSON format:

            {
                "name": "Product Name",
                "size": "Product Size",
                "form": "Product Form Factor",
                "processor": "Product Processor",
                "core": "Product Core Count",
                "frequency": "Product Processor Frequency",
                "memory": "Product Memory",
                "voltage": "Product Input Voltage",
                "io": "Product I/O Count",
                "thermal": "Product Thermal Management",
                "feature": "Product Feature",
                "type": "Product Type",
                "specification": "Product Specification",
                "manufacturer": "Product Manufacturer",
                "location": "Product Location",
                "description": "Product Description",
                "summary": "Product Summary"
            }

            Please make sure the response is formatted as valid JSON.
        """
