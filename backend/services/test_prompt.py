import asyncio

async def test_direct_prompt():
    from backend.services.openai_service import OpenAIService  # підлаштуй шлях
    svc = OpenAIService()

    system = "You are an assistant that only replies with one valid JSON object and nothing else."
    user = """
User question: Which spec describes a module that can operate from −40 °C to +70 °C?

Schema:
{
  "answer_text": string,
  "products": [
    {
      "product_id": string,
      "name": string,
      "specs": object,
      "relevance_score": number
    }
  ]
}

If no matching products, return "products": [].

Example response:
{
  "answer_text": "HummingBoard T matches the temperature range -40°C to 70°C.",
  "products": [
    {
      "product_id": "01b38446-9675-4b71-b87b-b3a82e57ea0f",
      "name": "HUMMINGBOARD T",
      "specs": {
         "operating_temperature_min": "-40°C",
         "operating_temperature_max": "70°C"
      },
      "relevance_score": 0.95
    }
  ]
}
"""

    # перед викликом — залогуй, що саме йде
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    print("=== OUTGOING MESSAGES ===")
    print(messages)

    response = await svc.create_chat_completion(
        model="gpt-4o",
        messages=messages,
        temperature=0,
    )
    raw = response["choices"][0]["message"]["content"]
    print("=== RAW MODEL OUTPUT ===")
    print(raw)

asyncio.run(test_direct_prompt())
