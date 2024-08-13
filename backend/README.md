# ThroughPut: AI-Powered Product Query System

## Overview

ThroughPut is an advanced AI-powered system designed to assist users with product queries, particularly focusing on embedded systems, development kits, and industrial communication devices. The system leverages Large Language Models (LLMs), semantic search capabilities, and various AI architectures to provide accurate and relevant responses to user queries.

## Key Features

- Real-time communication using Socket.IO
- Semantic search capabilities with Weaviate
- Integration with OpenAI's GPT models
- Internet search validation using Tavily
- Multiple AI architectures for query processing
- Session management and chat history handling
- Automated testing system for performance evaluation
- Product data management and feature extraction pipeline

## Project Structure

```
ThroughPut/
├── api/                 # API routes and Socket.IO handlers
├── core/                # Core functionality (message processing, session management)
├── data/                # Data files (CSV, JSON) for testing and training
├── generators/          # AI architectures (AgentV1, AgentV2, SemanticRouters)
├── models/              # Data models (Message, Product)
├── notebooks/           # Jupyter notebooks for data exploration and testing
├── services/            # External service integrations (OpenAI, Weaviate, Tavily)
├── test/                # Test files
├── weaviate/            # Weaviate client and related utilities
├── config.py            # Configuration settings
├── containers.py        # Dependency injection container
├── dependencies.py      # Dependency management
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## AI Architectures

ThroughPut implements multiple AI architectures to handle different types of queries:

1. **SemanticRouterV1**: Uses Weaviate for semantic search to categorize queries.
2. **SemanticRouterV2**: Utilizes LLM for query categorization.
3. **AgentV1**: Implements a multi-step workflow for product search and response generation.
4. **AgentV2**: An alternative agent architecture (specifics may vary).

## Setup and Installation

1. Clone the repository:

   ```
   git clone https://github.com/get10acious/ThroughPut
   cd ThroughPut/backend
   ```

2. Set up a virtual environment:

   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:

   ```
   OPENAI_API_KEY=your_openai_api_key
   WEAVIATE_URL=your_weaviate_url
   TAVILY_API_KEY=your_tavily_api_key
   ```

5. Initialize Weaviate:
   Follow Weaviate's documentation to set up and run a Weaviate instance.

## Running the Application

To start the ThroughPut server:

```
python main.py
```

This will start the FastAPI server with Socket.IO support.

## Usage

Clients can connect to the server using Socket.IO and send messages with specified architecture choices and history management options. The system handles different types of queries:

- Product information requests
- Chitchat conversations

## Product Data Management

ThroughPut includes a feature extraction pipeline for processing raw product data. This system allows for:

- Adding new product data
- Automatically extracting features
- Updating the vector store with new products

## Schema Overview

The schema defines the structure of the data stored in Weaviate. It includes definitions for various product attributes such as name, size, form, processor, core, frequency, memory, voltage, IO, thermal, feature, type, specification, manufacturer, location, description, and summary.

### Example Schema (schema.json)

```json
{
  "classes": [
    {
      "class": "Product",
      "properties": [
        {
          "name": "name",
          "dataType": ["string"]
        },
        {
          "name": "size",
          "dataType": ["string"]
        }
      ]
    }
  ]
}
```

## Contributing

Contributions to ThroughPut are welcome! Please refer to the `CONTRIBUTING.md` file (if available) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
