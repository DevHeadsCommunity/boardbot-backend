# ThroughPut

ThroughPut is an advanced AI-powered project designed to assist users with their queries about products using Large Language Models (LLMs) and semantic search capabilities.

## Table of Contents

- [ThroughPut](#throughput)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Key Features](#key-features)
  - [Project Structure](#project-structure)
  - [Setup Instructions](#setup-instructions)
  - [Running the Project](#running-the-project)
  - [Usage](#usage)
  - [Architecture Choices](#architecture-choices)
  - [Schema Overview](#schema-overview)
    - [Example Schema (schema.json)](#example-schema-schemajson)
  - [Contributing](#contributing)
  - [License](#license)

## Project Overview

ThroughPut leverages OpenAI's language models, Weaviate's vector search capabilities, and Tavily's internet search to provide intelligent responses to user queries about various products. The system categorizes queries into different types and processes them using flexible agent architectures.

## Key Features

- Real-time communication using Socket.IO
- Semantic search capabilities with Weaviate
- Integration with OpenAI's GPT models
- Internet search validation using Tavily
- Flexible agent architectures for query processing
- Session management and chat history handling
- Modular and extensible design

## Project Structure

The project is organized into the following main directories:

```
ThroughPut/
├── api/
│   ├── routes.py
│   └── socketio_handlers.py
├── core/
│   ├── message_processor.py
│   └── session_manager.py
├── generators/
│   ├── semantic_router_v1.py
│   ├── agent_v1.py
│   └── agent_v2.py
├── services/
│   ├── openai_service.py
│   ├── tavily_service.py
│   └── weaviate_service.py
├── agents/
│   ├── base_agent.py
│   ├── agent_v1.py
│   └── agent_v2.py
├── models/
│   └── message.py
├── notebooks/
├── weaviate/
├── config.py
├── dependencies.py
├── main.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone the repository:

   ```
   git clone https://github.com/eandualem/ThroughPut
   cd ThroughPut
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

5. Initialize Weaviate (if not already set up):
   Follow Weaviate's documentation to set up and run a Weaviate instance.

## Running the Project

To run the project, execute:

```
python main.py
```

This will start the FastAPI server with Socket.IO support.

## Usage

The system handles different types of user queries:

- Product information requests
- Chitchat conversations
- Queries requiring internet validation

Clients can connect to the server using Socket.IO and send messages with specified architecture choices and history management options.

## Architecture Choices

The project supports multiple architecture choices:

1. `semantic-router-v1`: Uses a semantic router to categorize queries and process them accordingly.
2. `agentic-v1`: Employs a basic agent architecture for product searches and response generation.
3. `agentic-v2`: Utilizes an advanced agent with multiple tools, including internet search validation.

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

Contributions to ThroughPut are welcome! Please refer to the `CONTRIBUTING.md` file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
