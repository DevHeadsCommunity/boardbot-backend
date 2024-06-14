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

    def get_response(self, messages, model, temperature=0):
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2400,
                top_p=1,
                stream=False,
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
                    "content": f"You are ThroughPut assistant. Your mane task is to help users with their queries about the product. The context that is provided is product data, in the form of name, description, feature, specification, location, and summary. In your response, synthesize the information from the context and clear, simple, and easy-to-understand response to the user. Use the following context: {context}",
                },
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    def extract_data(self, text):
        system_message = """
            Extract name, description, feature, specification, location, and summary from the following raw product data. Make sure to include the name, description, feature, specification, location, and summary in the extracted data, and if the data is not present, please mention that it is not available.
            Make sure your response is in the following json format:
            {
                "name": "Product Name",
                "description": "Product Description",
                "feature": "Product Feature",
                "specification": "Product Specification",
                "location": "Product Location",
                "summary": "Product Summary"
            }

            Please make sure the extracted data is in JSON format.
            """
        user_message = "Raw product data: " + text
        messages = [self.format_system_message(system_message), self.format_user_message(user_message)]
        response = self.get_response(messages, model="gpt-4o")
        return response.choices[0].message.content
