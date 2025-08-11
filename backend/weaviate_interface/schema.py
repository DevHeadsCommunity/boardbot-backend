from weaviate.classes.config import Property, DataType, Tokenization, Configure

SCHEMA = {
    "classes": [
        {
            "class": "RawProductData",
            "description": "Initial raw data for a product",
            "properties": [
                Property(
                    name="wp_product_id",
                    description="The unique identifier of the product",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="raw_data",
                    description="The full raw data for the product",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
            ],
        },
        {
            "class": "ProductSearchResult",
            "description": "Search results for a product",
            "properties": [
                Property(
                    name="wp_product_id",
                    description="The unique identifier of the product",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="search_query",
                    description="The query used for this search",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="search_result",
                    description="The full search result",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
                Property(
                    name="data_source",
                    description="The source of the search result",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
            ],
        },
        {
            "class": "ProductDataChunk",
            "description": "Chunked data for a product",
            "properties": [
                Property(
                    name="chunk_text",
                    description="The text content of the chunk",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
                Property(
                    name="wp_product_id",
                    description="The unique identifier of the product",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="source_type",
                    description="The type of source this chunk came from (raw_data or search_result)",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="source_id",
                    description="The ID of the source (either RawProductData or ProductSearchResult)",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
            ],
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
            ),
            "generative_config": Configure.Generative.openai(),
        },
        {
            "class": "Product",
            "description": "A class representing hardware products with enhanced sorting capabilities.",
            "properties": [
                Property(
                    name="wp_product_id",
                    description="Original WordPress product ID",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="name",
                    description="Name of the product",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="slug",
                    description="URL-friendly identifier",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="permalink",
                    description="Full URL to access the product",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
                Property(
                    name="sku",
                    description="Stock Keeping Unit",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="price",
                    description="Current price of the product",
                    data_type=DataType.NUMBER,
                    index_filterable=True,
                ),
                Property(
                    name="regular_price",
                    description="Regular (non-discounted) price",
                    data_type=DataType.NUMBER,
                    index_filterable=True
                ),
                Property(
                    name="sale_price",
                    description="Discounted sale price, if any",
                    data_type=DataType.NUMBER,
                    index_filterable=True,
                ),
                Property(
                    name="status",
                    description="Publication status (e.g., 'publish')",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="description",
                    description="Complete product description",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
                Property(
                    name="short_description",
                    description="Brief summary of the product",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
                Property(
                    name="type",
                    description="Product type (e.g., 'simple', 'variable')",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="stock_status",
                    description="Inventory status (e.g., 'instock')",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="total_sales",
                    description="Total number of times the item has been sold",
                    data_type=DataType.INT,
                    index_filterable=True,
                ),
                Property(
                    name="downloadable",
                    description="Whether the product is downloadable (boolean)",
                    data_type=DataType.BOOL,
                    index_filterable=True,
                ),
                Property(
                    name="virtual",
                    description="Whether the product is virtual (boolean)",
                    data_type=DataType.BOOL,
                    index_filterable=True,
                ),
                Property(
                    name="download_url",
                    description="URL to download the product file",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                ),
                Property(
                    name="image_url",
                    description="URL of the product’s primary image",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=True,
                ),
                Property(
                    name="date_created",
                    description="Date when the product was first created in WordPress",
                    data_type=DataType.DATE,
                    index_filterable=True,
                ),
                Property(
                    name="date_modified",
                    description="Date when the product was last modified in WordPress",
                    data_type=DataType.DATE,
                    index_filterable=True,
                    index_searchable=False,
                ),
                Property(
                    name="createdAt",
                    description="Local database record creation timestamp",
                    data_type=DataType.DATE,
                    index_filterable=True,
                ),
                Property(
                    name="updatedAt",
                    description="Local database record update timestamp",
                    data_type=DataType.DATE,
                    index_filterable=True,
                ),
            ],
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",  # Consider using a more recent and powerful model
            ),
            "generative_config": Configure.Generative.openai(),
        },
        {
            "class": "Route",
            "description": "A class representing a route with multiple descriptive aspects.",
            "properties": [
                Property(
                    name="route",
                    description="The route to follow",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    tokenization=Tokenization.WORD,
                ),
                Property(
                    name="description",
                    description="Route description capturing different aspects of the route",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    tokenization=Tokenization.WORD,
                ),
            ],
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
            ),
            "generative_config": Configure.Generative.openai(),
        },
    ]
}
