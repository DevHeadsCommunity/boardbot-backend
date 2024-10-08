# Agentic Feature Extractor Documentation

## Overview

The **Agentic Feature Extractor** is a sophisticated system designed to extract detailed product information from raw textual data, with a focus on computer hardware such as embedded systems, development kits, and industrial communication devices. It leverages a combination of advanced language models (like GPT-4), search services, and a structured workflow to iteratively extract, refine, and validate product features, ensuring high accuracy and completeness of the extracted data.

## Objectives

- **Accurate Feature Extraction**: Extract detailed product attributes with associated confidence scores.
- **Iterative Improvement**: Refine low-confidence or missing features through additional context and search results.
- **Structured Data Output**: Provide the extracted features in a consistent, structured format suitable for downstream applications.
- **Efficient Data Management**: Store and retrieve product data, search results, and chunks efficiently using Weaviate for improved feature extraction.

## Architecture

The Agentic Feature Extractor is built upon several key components:

- **Workflow Engine**: Utilizes `langgraph` to define a stateful workflow (`StateGraph`) that orchestrates the extraction process.
- **Nodes**: Individual processing steps within the workflow that perform specific tasks (e.g., extracting features, searching for missing data).
- **Prompts**: Carefully crafted instructions provided to the language model to guide the extraction and refinement process.
- **Services**: External services such as OpenAI's GPT models, the Tavily search API, and Weaviate for data storage and retrieval.
- **Configurations**: Settings that control the behavior of the extractor, such as model names, confidence thresholds, and maximum attempt counts.
- **Weaviate Interface**: Provides access to the Weaviate vector database for efficient storage and retrieval of product data, search results, and chunks.

## Data Model

The system uses Weaviate to store and manage product data with the following classes:

1. **RawProductData**:

   - `product_id`: Unique identifier for the product
   - `raw_data`: The full raw data for the product

2. **ProductSearchResult**:

   - `product_id`: Unique identifier for the product
   - `search_query`: The query used for this search
   - `search_result`: The full search result
   - `data_source`: The source of the search result

3. **ProductDataChunk**:
   - `chunk_text`: The text content of the chunk
   - `product_id`: Unique identifier for the product
   - `source_type`: Indicates whether the chunk is from raw data or search result
   - `source_id`: ID of the source (either RawProductData or ProductSearchResult)

## Execution Flow

The extraction process follows a defined sequence of steps within the workflow:

1. **Store and Chunk Data (`store_and_chunk_data_node`)**:

   - Stores raw data in Weaviate and creates chunks.

2. **Initial Feature Extraction (`extract_features_node`)**:

   - Retrieves relevant chunks from Weaviate.
   - Extracts features from the chunks using a language model.
   - Assigns confidence scores to each extracted feature.

3. **Determine Next Steps (`should_continue`)**:

   - Checks for missing or low-confidence features.
   - Decides whether to search for missing features, refine low-confidence features, or end the workflow.

4. **Search for Missing Features (`search_missing_features_node`)**:

   - Constructs a search query based on existing and missing features.
   - Uses Tavily service to perform search and stores results in Weaviate.

5. **Generate Missing Features (`generate_missing_features_node`)**:

   - Retrieves relevant chunks from Weaviate.
   - Uses the chunks to attempt extraction of missing features.
   - Merges new features with existing ones, preserving higher confidence scores.

6. **Search for Low-Confidence Features (`search_low_confidence_features_node`)**:

   - Similar to searching for missing features, but focuses on low-confidence features.

7. **Refine Low-Confidence Features (`refine_low_confidence_features_node`)**:

   - Retrieves relevant chunks for low-confidence features.
   - Refines these features using the additional context.
   - Updates the features in the state with improvements.

8. **Repeat or Terminate**:

   - Loops back to step 3 if further iterations are allowed.
   - Ends the workflow when no further actions are required or maximum attempts are reached.

9. **Final Output**:
   - Filters extracted features based on the confidence threshold.
   - Returns the final structured data, setting features below the threshold to "Not Available".

## Key Components

### 1. Workflow Nodes

Each node in the workflow is implemented as an asynchronous function that processes the current state and returns an updated state.

### 2. Prompts

Prompts are templates that guide the language model in generating the desired outputs. The system uses three main types of prompts:

- `DataExtractionPrompt`
- `MissingFeatureExtractionPrompt`
- `LowConfidenceFeatureRefinementPrompt`

### 3. Services

#### a. OpenAI Service (`openai_service`)

- Interfaces with OpenAI's language models to generate responses based on prompts.

#### b. Tavily Service (`tavily_service`)

- Performs semantic search to retrieve relevant documents or data based on constructed queries.

#### c. Weaviate Service (`weaviate_service`)

- Manages interactions with the Weaviate vector database for storing and retrieving product data, search results, and chunks.

### 4. Configurations

The `AgentConfig` class defines parameters that control the behavior of the extractor, including:

- `model_name`
- `max_missing_feature_attempts`
- `max_low_confidence_attempts`
- `confidence_threshold`

### 5. Data Structures

#### a. State (`ExtractorState`)

- Represents the current state of the extraction process, including extracted features, missing features, and usage data.

#### b. Feature Representation

- Features are represented as nested dictionaries with `value` and `confidence` scores.

### 6. Helper Functions

Various helper functions are implemented to support the extraction process, including:

- `flatten_feature_keys`
- `get_feature_value`
- `merge_dicts`
- `get_low_confidence_features`
- `filter_features_by_confidence`

## Error Handling and Logging

- Detailed logging is implemented at various levels (INFO, DEBUG) to trace the execution flow and record important information.
- Error handling is in place for API calls, Weaviate operations, and parsing of model responses.
- Usage data is recorded for monitoring costs and performance.

## Conclusion

The Agentic Feature Extractor provides a robust, iterative approach to extracting detailed product features from raw textual data. By leveraging advanced language models, a structured workflow, and efficient data management through Weaviate, it ensures high accuracy and completeness in the extracted data. The system's design allows for flexibility in handling missing or uncertain information, making it suitable for applications that require precise and reliable product information.
