import logging
from services.openai_service import OpenAIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureExtractor:
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service

    async def extract_data(self, text: str) -> str:
        system_message = self._get_data_extraction_system_message()
        user_message = f"Raw product data: {text}"
        return await self.openai_service.generate_response(user_message, system_message, max_tokens=4096)

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
