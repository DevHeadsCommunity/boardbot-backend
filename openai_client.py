from openai import OpenAI
from config import Config


class OpenAIClient:
    def __init__(self):
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def format_user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def format_system_message(
        self,
        message: str,
    ) -> dict:
        return {"role": "system", "content": message}

    def get_response(self, messages, model, temperature=0, max_tokens=2400, top_p=1, stream=False):
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
            )
            return response
        except Exception as e:
            raise ValueError(str(e))

    def generate_response(self, user_message: str, context: str = None) -> str:
        response = self._client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are ThroughPut assistant. Your main task is to help users with their queries about the product.
                                   The context that is provided is product data, in the form of name, size, form, processor, core, frequency, memory, voltage, io, thermal, feature, type, specification, manufacturer, location, description, and summary.
                                   In your response, synthesize the information from the context into a clear, simple, and easy-to-understand response to the user.
                                   make sure your response is in a JSON format.
                                   Use the following context: {context}""",
                },
                {"role": "user", "content": user_message},
            ],
            max_tokens=3600,
        )
        return response.choices[0].message.content

    def extract_data(self, text):
        system_message = """
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
        user_message = "Raw product data: " + text
        messages = [self.format_system_message(system_message), self.format_user_message(user_message)]
        response = self.get_response(messages, model="gpt-4o", max_tokens=4096)
        return response.choices[0].message.content
