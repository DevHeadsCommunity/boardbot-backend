# ThroughPut

ThroughPut is a project designed to assist users with their queries about products using LLM and semantic search capabilities.

## Table of Contents

- [ThroughPut](#throughput)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Folder Structure](#folder-structure)
  - [Setup Instructions](#setup-instructions)
    - [Repository Clone](#repository-clone)
    - [Weaviate Setup](#weaviate-setup)
    - [Project Setup](#project-setup)
  - [Running the Project](#running-the-project)
  - [Schema Overview](#schema-overview)
    - [Example Schema (schema.json)](#example-schema-schemajson)
  - [Usage](#usage)
    - [Example Query Handling](#example-query-handling)

## Project Overview

ThroughPut leverages OpenAI's language models and Weaviate's vector search capabilities to provide intelligent responses to user queries about various products. The system categorizes queries into different types such as politics, chitchat, vague intent, and clear intent, and processes them accordingly.

## Folder Structure

The project directory is organized as follows:

```
ThroughPut
├── 1. munging.ipynb
├── 2. exploration.ipynb
├── README.md
├── config.py
├── data
│   ├── chitchat.csv
│   ├── clean_products.csv
│   ├── clear_intent.csv
│   ├── final_products_data.json
│   ├── politics.csv
│   └── vague_intent.csv
├── main.py
├── openai_client.py
├── requirements.txt
├── socketio_handlers.py
└── weaviate
    ├── __init__.py
    ├── docker-compose.yml
    ├── http_client.py
    ├── product_service.py
    ├── route_service.py
    ├── schema.json
    ├── schema_manager.py
    ├── utils
    │   ├── graphql_query_builder.py
    │   └── where_clause_builder.py
    ├── weaviate_client.py
    ├── weaviate_interface.py
    └── weaviate_service.py
```

## Setup Instructions

### Repository Clone

First, clone the repository and navigate to the project directory:

```sh
git clone https://github.com/eandualem/ThroughPut
cd ThroughPut
```

### Weaviate Setup

To set up Weaviate, navigate to the `weaviate` directory and start the services using Docker Compose:

```sh
cd weaviate
docker-compose up
```

### Project Setup

Set up a virtual environment and install the required packages:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
WEAVIATE_URL=http://localhost:8080
```

## Running the Project

To run the project, execute the following command:

```sh
python main.py
```

This will start the FastAPI server and set up the necessary Socket.IO handlers.

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

## Usage

Once the server is running, it will handle different types of user queries:

- **Politics**: The system responds with a message that it cannot discuss politics.
- **Chitchat**: The system uses OpenAI to generate a conversational response.
- **Vague Intent Product**: The system performs a semantic search based on the user's vague query and provides relevant product information.
- **Clear Intent Product**: The system refines the user's query and performs a detailed semantic search to find and present specific product information.

### Example Query Handling

- **Input**: "20 SBC's that perform better than Raspberry Pi."
- **Refined Query**: "High performance SBC's"
- **Output**: JSON formatted list of SBCs that meet the criteria.

For more details on how to interact with the system and customize its behavior, refer to the individual scripts and their respective docstrings.
