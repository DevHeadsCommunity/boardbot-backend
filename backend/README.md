# **BoardBot Backend**

## **Overview**

BoardBot is an AI-powered assistant designed to help users with queries about computer hardware products, focusing on embedded systems, development kits, and industrial communication devices. This backend provides the core functionality for processing user queries, managing product data, and generating relevant, accurate responses.

---

## **Table of Contents**

- [**BoardBot Backend**](#boardbot-backend)
  - [**Overview**](#overview)
  - [**Table of Contents**](#table-of-contents)
  - [**Project Structure**](#project-structure)
  - [**Architecture Overview**](#architecture-overview)
    - [**1. API Layer**](#1-api-layer)
    - [**2. Core Components**](#2-core-components)
    - [**3. Generators**](#3-generators)
    - [**4. Services**](#4-services)
    - [**5. Prompt Management**](#5-prompt-management)
    - [**6. Weaviate Interface**](#6-weaviate-interface)
  - [**Feature Extraction Process**](#feature-extraction-process)
    - [**Extraction Workflow**](#extraction-workflow)
  - [**Prompt Classification**](#prompt-classification)
    - [**Classification Categories**](#classification-categories)
  - [**Request Types and Responses**](#request-types-and-responses)
    - [**WebSocket Requests**](#websocket-requests)
      - [**1. Text Message Request**](#1-text-message-request)
      - [**Response**](#response)
    - [**HTTP Requests**](#http-requests)
      - [**1. Get Products (with pagination)**](#1-get-products-with-pagination)
      - [**2. Add Raw Product**](#2-add-raw-product)
  - [**Product Data**](#product-data)
  - [**Response Generation Architectures**](#response-generation-architectures)
  - [**Weaviate Vector Store**](#weaviate-vector-store)
  - [**Setup and Configuration**](#setup-and-configuration)
    - [**Prerequisites**](#prerequisites)
    - [**Installation**](#installation)
    - [**Environment Variables**](#environment-variables)
  - [**Running the Application**](#running-the-application)
  - [**Contributing**](#contributing)
  - [**License**](#license)
  - [**Acknowledgements**](#acknowledgements)

---

## **Project Structure**

```
[FastAPI Application]
|
+-- api/
|   +-- routes.py
|   +-- socketio_handlers.py
|
+-- core/
|   +-- message_processor.py
|   +-- session_manager.py
|
+-- generators/
|   +-- base_router.py
|   +-- clear_intent_agent.py
|   +-- dynamic_agent.py
|   +-- hybrid_router.py
|   +-- llm_router.py
|   +-- semantic_router.py
|   +-- vague_intent_agent.py
|
+-- services/
|   +-- openai_service.py
|   +-- query_processor.py
|   +-- tavily_service.py
|   +-- weaviate_service.py
|
+-- feature_extraction/
|   +-- agentic_feature_extractor.py
|   +-- config_schema.py
|
+-- prompts/
|   +-- prompt_manager.py
|   +-- templates.py
|
+-- models/
|   +-- message.py
|   +-- product.py
|
+-- weaviate_interface/
|   +-- weaviate_interface.py
|   +-- weaviate_client.py
|   +-- schema_manager.py
|   +-- product_service.py
|   +-- route_service.py
|   +-- http_client.py
|   +-- models/
|       +-- product.py
|   +-- utils/
|       +-- graphql_query_builder.py
|       +-- where_clause_builder.py
|
+-- utils/
|   +-- response_formatter.py
|
+-- config.py
+-- containers.py
+-- dependencies.py
+-- main.py
```

---

## **Architecture Overview**

The backend is built using FastAPI and follows a modular, scalable architecture with the following main components:

### **1. API Layer**

- **FastAPI Application**: The main entry point for the backend.
- **Socket.IO**: Manages real-time communication with the frontend for chat functionalities.

### **2. Core Components**

- **Session Manager**: Manages user sessions and chat history.
- **Message Processor**: Processes incoming messages and routes them to the appropriate generators.

### **3. Generators**

The `generators` subpackage contains agents responsible for processing user queries and generating responses. These agents have been refactored to follow best practices, including immutable state and pure function nodes.

- **LLMRouter**: Uses language models to classify queries and route them appropriately.
- **SemanticRouter**: Employs semantic search for quick query classification.
- **HybridRouter**: Combines LLM and semantic search for efficient and accurate routing.
- **ClearIntentAgent**: Handles queries with clear, specific product intents.
- **VagueIntentAgent**: Processes queries with vague or general product intents.
- **DynamicAgent**: An adaptive agent that decides its actions based on the context of the query.
- **BaseRouter**: The base class for routers, providing common functionalities.

### **4. Services**

- **OpenAIService**: Interacts with OpenAI's language models for generating responses.
- **WeaviateService**: Manages operations with the Weaviate vector database.
- **TavilyService**: Provides internet search capabilities for additional context.
- **QueryProcessor**: Processes and expands user queries to improve search results.

### **5. Prompt Management**

- **PromptManager**: Centralizes the management of prompts used across different agents and services, ensuring consistency and ease of updates.

### **6. Weaviate Interface**

- **WeaviateInterface**: Provides a unified interface for interacting with the Weaviate vector database.
- **ProductService**: Manages product data within Weaviate.
- **RouteService**: Handles routing data for query classification.

---

## **Feature Extraction Process**

The `AgenticFeatureExtractor` has been significantly improved to follow best practices, including:

- **Immutable State**: Uses immutable state management for reliability.
- **Pure Function Nodes**: Each node in the extraction workflow is a pure function, enhancing testability and predictability.
- **Asynchronous Design**: Fully async-compatible, improving performance for long-running tasks.
- **Configurable Behavior**: Exposes configurable parameters via a schema, allowing easy adjustments.

### **Extraction Workflow**

1. **Initial Extraction**: Extracts features from raw product data using AI prompts.
2. **Identify Missing Features**: Determines which features are missing or have low confidence.
3. **Context Gathering**: Uses internet search (via TavilyService) to gather additional information.
4. **Refinement**: Re-extracts features using the additional context.
5. **Iteration**: Repeats steps 2-4 until all features are satisfactorily extracted or maximum attempts are reached.

---

## **Prompt Classification**

BoardBot employs an advanced prompt classification system to route user queries effectively. The classification ensures that queries are handled by the most suitable agent.

### **Classification Categories**

1. **Politics**

   - Queries related to political topics.
   - Example: "What do you think about the latest election results?"

2. **Chitchat**

   - General conversation or small talk.
   - Example: "How are you today?"

3. **Vague Intent Product**

   - Product-related queries lacking specific criteria.
   - Examples:
     - "Tell me about development kits."
     - "I'm interested in industrial communication devices."

4. **Clear Intent Product**

   - Product-related queries with specific requirements.
   - Examples:
     - "Find boards with at least 8GB RAM and an ARM processor."
     - "List single-board computers with built-in Wi-Fi under $200."

5. **Do Not Respond**

   - Inappropriate or off-topic queries.
   - Example: "Can you help me hack into a server?"

---

## **Request Types and Responses**

### **WebSocket Requests**

The backend primarily communicates with the frontend via WebSocket connections, facilitating real-time interactions.

#### **1. Text Message Request**

```json
{
  "type": "textMessage",
  "session_id": "unique_session_id",
  "message_id": "unique_message_id",
  "message": "User's query text",
  "is_complete": true,
  "timestamp": "2024-08-21T07:12:16.535Z",
  "model": "gpt-4",
  "architecture_choice": "dynamic-agent",
  "history_management_choice": "keep-all"
}
```

#### **Response**

```json
{
  "session_id": "unique_session_id",
  "message_id": "unique_message_id_response",
  "message": {
    "type": "clear_intent_product",
    "response": "Here are some products matching your criteria...",
    "products": [
      {
        "id": "product_uuid",
        "product_id": "product_id_from_frontend",
        "name": "Product Name",
        "manufacturer": "Manufacturer Name",
        "form_factor": "Form Factor",
        "processor_architecture": "ARM",
        "memory": "8GB",
        "wireless": "Wi-Fi",
        "price": "$199"
      }
    ],
    "reasoning": "Based on your requirements for an ARM processor and at least 8GB RAM...",
    "follow_up_question": "Would you like more information on any of these products?",
    "metadata": {
      "classification_result": {},
      "input_token_usage": {
        "query_processing": 150,
        "rerank": 80,
        "generate": 200
      },
      "output_token_usage": {
        "query_processing": 100,
        "rerank": 50,
        "generate": 150
      },
      "time_taken": {
        "query_processing": 0.6,
        "search": 0.3,
        "rerank": 0.4,
        "generate": 1.2
      }
    }
  },
  "timestamp": "2024-08-21T07:12:18.123Z",
  "is_complete": true,
  "model": "gpt-4",
  "architecture_choice": "dynamic-agent"
}
```

### **HTTP Requests**

The backend provides RESTful APIs for product management and feature extraction.

#### **1. Get Products (with pagination)**

```
GET /api/products?page=1&page_size=10
```

**Response:**

```json
{
  "total": 1000,
  "page": 1,
  "page_size": 10,
  "products": [
    {
      "id": "product_uuid",
      "product_id": "product_id_from_frontend",
      "name": "Product Name",
      "manufacturer": "Manufacturer Name",
      "form_factor": "Form Factor",
      "processor_architecture": "ARM",
      "memory": "8GB",
      "wireless": "Wi-Fi",
      "price": "$199"
    }
    // ...additional products
  ]
}
```

#### **2. Add Raw Product**

```
POST /api/products/raw
Content-Type: application/json

{
  "product_id": "product_id_from_frontend",
  "raw_data": "Raw product description text",
  "max_missing_feature_attempts": 2,
  "max_low_confidence_attempts": 1
}
```

**Response:**

```json
{
  "id": "newly_created_product_uuid"
}
```

---

## **Product Data**

Each product entry includes detailed attributes extracted and stored in the Weaviate vector database:

- **id**: Weaviate-generated UUID.
- **product_id**: Identifier from the frontend or source system.
- **name**: Official product name.
- **manufacturer**: Company that produces the product.
- **form_factor**: Physical dimensions or standard.
- **evaluation_or_commercialization**: Indicates if the product is for evaluation or commercial use.
- **processor_architecture**: Processor architecture (e.g., ARM, x86).
- **processor_core_count**: Number of processor cores.
- **processor_manufacturer**: Manufacturer of the processor.
- **processor_tdp**: Thermal Design Power.
- **memory**: RAM specifications.
- **onboard_storage**: Built-in storage details.
- **input_voltage**: Required input voltage.
- **io_count**: Input/Output interfaces count.
- **wireless**: Wireless capabilities.
- **operating_system_bsp**: Supported operating systems or BSPs.
- **operating_temperature_max/min**: Operating temperature range.
- **certifications**: Certifications and compliance standards.
- **price**: Product price.
- **stock_availability**: Current stock status.
- **lead_time**: Time required to fulfill an order.
- **short_summary**: Concise product description.
- **full_summary**: Detailed product overview.
- **full_product_description**: In-depth product information.
- **target_applications**: Intended use cases or industries.

---

## **Response Generation Architectures**

The backend supports several architectures for response generation, updated to align with best practices:

1. **LLMRouter**

   - Uses language models for query classification.
   - Provides deep contextual understanding.
   - Refactored to use immutable state and pure functions.

2. **SemanticRouter**

   - Employs semantic search for quick classification.
   - Fast but may lack depth for complex queries.
   - Updated to follow the new design pattern.

3. **HybridRouter**

   - Combines LLM and semantic search.
   - Balances speed and accuracy.
   - Follows best practices in its implementation.

4. **DynamicAgent**

   - Adapts actions based on query context.
   - Uses a workflow of pure function nodes.
   - Implements error handling, retry policies, and configuration schemas.

---

## **Weaviate Vector Store**

The backend utilizes Weaviate as a vector database for efficient data storage and retrieval:

1. **Product**

   - Stores structured product information with both `product_id` and Weaviate-generated `id`.

2. **RawProductData**

   - Contains initial raw data for products.

3. **ProductDataChunk**

   - Holds chunked data from raw product descriptions and search results.

4. **ProductSearchResult**

   - Stores results from internet searches related to products.

5. **Route**

   - Contains routing data for query classification examples.

**Schema and Data Handling:**

- **WeaviateService**: Manages all interactions with Weaviate, ensuring both `product_id` and `id` are correctly handled.
- **Data Integrity**: Updated methods to accommodate the new feature set and maintain data consistency.

---

## **Setup and Configuration**

### **Prerequisites**

- **Python 3.8+**
- **Weaviate Instance**: Local or hosted Weaviate server.
- **OpenAI API Key**: Required for language model interactions.
- **Tavily API Key**: Required for internet search capabilities.

### **Installation**

1. **Clone the Repository**

   ```bash
   git clone https://github.com/get10acious/ThroughPut.git
   cd ThroughPut/backend
   ```

2. **Set Up Virtual Environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

### **Environment Variables**

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
WEAVIATE_URL=your_weaviate_url
RESET_WEAVIATE=False  # Set to True to reset the Weaviate schema
DEFAULT_MODEL=gpt-4   # Default model to use for OpenAI
```

---

## **Running the Application**

To start the BoardBot backend server:

```bash
python main.py
```

This will launch the FastAPI server with Socket.IO support on `http://0.0.0.0:5678`.

---

## **Contributing**

We welcome contributions to improve BoardBot. To contribute:

1. **Fork the Repository**

   Click the "Fork" button at the top of the repository page.

2. **Create a New Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**

   Ensure code follows best practices and includes necessary documentation.

4. **Commit Your Changes**

   ```bash
   git commit -m "Description of your changes"
   ```

5. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Submit a Pull Request**

   Open a pull request to the `main` branch of the original repository.

---

## **License**

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

## **Acknowledgements**

We appreciate all contributors and users who have helped improve BoardBot. Special thanks to the development team for implementing the latest architectural improvements.
