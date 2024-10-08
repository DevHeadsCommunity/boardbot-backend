import csv
import asyncio
from socketio_handlers import SocketIOHandler
from weaviate_old import initialize_weaviate
from openai_client import OpenAIClient


async def test_semantic_router():
    # Initialize necessary components
    weaviate_interface = await initialize_weaviate()
    socket_handler = SocketIOHandler(weaviate_interface)
    openai_client = OpenAIClient()

    # Initialize counters
    route_counts = {"politics": 0, "chitchat": 0, "vague_intent_product": 0, "clear_intent_product": 0, "unknown": 0}

    total_queries = 0
    correct_predictions = 0

    # Read the test file
    with open("./data/test_file3.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            total_queries += 1
            original_query = row["prompt"]
            expected_route = row["expected_route"]

            # Clarify the query using OpenAI
            # clarified_query, _, _ = openai_client.generate_response(
            #     f"Clarify the following query concisely: {original_query}"
            # )

            # Determine the route using the existing implementation
            route = await socket_handler.determine_route(original_query)

            # Update counters
            route_counts[route] = route_counts.get(route, 0) + 1
            if route == expected_route:
                correct_predictions += 1

            print(f"Query: {original_query}")
            # print(f"Clarified: {clarified_query}")
            print(f"Expected Route: {expected_route}")
            print(f"Predicted Route: {route}")
            print("--------------------")

    # Calculate accuracy
    accuracy = (correct_predictions / total_queries) * 100

    # Print results
    print("\nResults:")
    for route, count in route_counts.items():
        print(f"{route}: {count}")
    print(f"\nTotal Queries: {total_queries}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    asyncio.run(test_semantic_router())
