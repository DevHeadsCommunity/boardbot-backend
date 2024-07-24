import tiktoken
import logging
from openai import AsyncOpenAI
from typing import List, Optional, Tuple
from config import Config
from models.message import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self, api_key: str, config: Config):
        self.client = AsyncOpenAI(api_key=api_key)
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self.config = config

    async def generate_response(
        self,
        user_message: str,
        context: Optional[str] = None,
        history: Optional[List[Message]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
    ) -> Tuple[str, int, int]:
        try:
            messages = self._prepare_messages(user_message, context, history)
            input_token_count = len(self.encoder.encode(str(messages)))
            logger.info(f"Input token count: {input_token_count}")

            response = await self.client.chat.completions.create(
                model=model or self.config.DEFAULT_MODEL,
                messages=messages,
                temperature=temperature or 0,
                max_tokens=max_tokens or 2400,
                top_p=top_p or 1,
                stream=stream,
            )
            output_token_count = len(self.encoder.encode(response.choices[0].message.content))
            logger.info(f"Output token count: {output_token_count}")

            return response.choices[0].message.content, input_token_count, output_token_count
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            raise

    def _prepare_messages(
        self, user_message: str, context: Optional[str], history: Optional[List[Message]]
    ) -> List[dict]:
        messages = []

        if context:
            system_message = self._get_system_message_with_context(context)
            messages.append({"role": "system", "content": system_message})

        if history:
            for message in history[-5:]:  # Only keep the last 5 messages
                role = "user" if message.is_user_message else "assistant"
                messages.append({"role": role, "content": message.content})

        messages.append({"role": "user", "content": user_message})
        return messages

    def _get_system_message_with_context(self, context: str) -> str:
        return (
            f"""You are ThroughPut assistant. Your main task is to help users with their queries about the product. Always respond in JSON format.
                   The context that is provided is product data, in the form of name, size, form, processor, core, frequency, memory, voltage, io, thermal, feature, type, specification, manufacturer, location, description, and summary.
                   In your response, synthesize the information from the context into a clear, simple, and easy-to-understand response to the user.
                   Use the following context: {context}

                   Make sure your response is in a JSON format.
            """
            + """
                   Example:
                   {
                       "response_description": "The product is a computer with a 15-inch display, Intel Core i7 processor, 16GB RAM, and 512GB SSD storage."
                       "response_justification": "The response is accurate and concise, providing key details about the product."
                       "products": [
                                        {
                                        "name": "Not available",
                                        "form": "COM Express Basic Module",
                                        "processor": "Intel Xeon D (Ice Lake-D)",
                                        "memory": "DDR4, Max Capacity: 128 GB, Socket: 2 x 260P SODIMM, Dual Channel, ECC/Non-ECC",
                                        "io": "4 x SATA Ports (6 Gbps), 8 x USB Ports (4 x USB 3.0, 4 x USB 2.0), 1 x LPC, 1 x SPI Bus, 1 x GPIO (8-bit), 1 x Watchdog Timer, 2 x COM Ports, 2 x Ethernet (10GBASE-KR, 1GBASE-T), 32 x PCIe Gen3 lanes",
                                        "manufacturer": "Advantech",
                                        "size": "95 mm x 125 mm",
                                        "summary": "High-performance COM Express Basic Module with Intel Xeon D processors, extensive I/O, and robust thermal management."
                                        },
                                        {
                                        "name": "ET COM Express",
                                        "form": "COM Express Type 6",
                                        "processor": "8th Generation Intel Xeon E & Core i3/i5/i7",
                                        "memory": "2 x DDR4 SODIMM, Max 32GB",
                                        "io": "4 x USB 3.1, 8 x USB 2.0, 4 x COM, 4 x SATA III, 2 x PCIe x4, 1 x PCIe x16, 2 x GbE LAN",
                                        "manufacturer": "IBASE",
                                        "size": "95 mm x 125 mm",
                                        "summary": "High-performance COM Express Type 6 modules with 8th Generation Intel Xeon E & Core i3/i5/i7 processors, extensive I/O, and display support."
                                        },
                                    ]
                    }
            """
        )

    def extract_data(self, text: str) -> str:
        system_message = self._get_data_extraction_system_message()
        user_message = f"Raw product data: {text}"
        messages = [self.format_message("system", system_message), self.format_message("user", user_message)]
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
