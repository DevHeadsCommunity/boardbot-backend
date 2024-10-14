import json
import logging
from pydantic import BaseModel, ValidationError
from typing import Optional, List
from feature_extraction import ConfigSchema
from services.weaviate_service import WeaviateService
from fastapi import APIRouter, Depends, HTTPException, Query
from weaviate_interface.models.product import NewProduct, Product, attribute_descriptions
from services.feature_extraction_service import BatchFeatureExtractionService, FeatureExtractionService
from dependencies import (
    get_weaviate_service,
    get_feature_extraction_service,
    get_batch_feature_extraction_service,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api")


class FilterParams(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)
    filter: Optional[str] = None


class RawProductInput(BaseModel):
    product_id: str
    raw_data: str
    max_missing_feature_attempts: Optional[int] = 0
    max_low_confidence_attempts: Optional[int] = 0
    max_no_progress_attempts: Optional[int] = 0
    confidence_threshold: Optional[float] = 0.7


class BatchProductItem(BaseModel):
    product_id: str
    raw_data: str


class BatchProductInput(BaseModel):
    products: List[BatchProductItem]
    batch_size: Optional[int] = 5
    max_missing_feature_attempts: Optional[int] = 0
    max_low_confidence_attempts: Optional[int] = 0
    max_no_progress_attempts: Optional[int] = 0
    confidence_threshold: Optional[float] = 0.7


def filter_internal_fields(product_dict):
    internal_fields = ["short_summary", "full_summary", "full_product_description", "target_applications"]
    return {k: v for k, v in product_dict.items() if k not in internal_fields}


@api_router.get("/products")
async def get_products(
    params: FilterParams = Depends(),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
):
    logger.info(f"Getting products with params: {params}")
    offset = (params.page - 1) * params.page_size

    filter_dict = json.loads(params.filter) if params.filter else None

    products, total_count = await weaviate_service.get_products(params.page_size, offset, filter_dict)
    filtered_products = [filter_internal_fields(product) for product in products]

    logger.info(f"Found {len(filtered_products)} products")
    return {"total": total_count, "page": params.page, "page_size": params.page_size, "products": filtered_products}


@api_router.get("/products/{id}")
async def get_product(id: str, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    product = await weaviate_service.get_product(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    filtered_product = filter_internal_fields(product)
    return filtered_product


@api_router.post("/products")
async def add_product(product: NewProduct, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    try:
        logger.info(f"Adding product: {filter_internal_fields(product.dict())}")
        product_id = await weaviate_service.add_product(product.dict())
        return {"id": product_id}
    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/products/{id}")
async def update_product(id: str, product: Product, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    try:
        await weaviate_service.update_product(id, product.dict())
        return {"message": "Product updated successfully"}
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/products/{id}")
async def delete_product(id: str, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    try:
        await weaviate_service.delete_product(id)
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/products/raw")
async def add_raw_product(
    input_data: RawProductInput,
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    feature_extraction_service: FeatureExtractionService = Depends(get_feature_extraction_service),
):
    try:
        extractor_config = ConfigSchema(
            max_missing_feature_attempts=input_data.max_missing_feature_attempts,
            max_low_confidence_attempts=input_data.max_low_confidence_attempts,
            max_no_progress_attempts=input_data.max_no_progress_attempts,
            confidence_threshold=input_data.confidence_threshold,
        )

        extracted_data = await feature_extraction_service.extract_features(
            input_data.raw_data, input_data.product_id, extractor_config
        )

        if "error" in extracted_data:
            raise HTTPException(status_code=500, detail=f"Feature extraction failed: {extracted_data['error']}")

        product = extracted_data["extracted_data"]
        product["product_id"] = input_data.product_id

        # Ensure all required fields are present
        required_fields = ["name", "product_id"]  # Add other required fields here
        for field in required_fields:
            if field not in product:
                product[field] = f"Default {field.capitalize()} for {input_data.product_id}"

        new_product = NewProduct(**product)
        id = await weaviate_service.add_product(new_product.dict())
        return {"id": id}
    except Exception as e:
        logger.error(f"Error adding raw product: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/products/batch/raw")
async def add_products_batch_raw(
    input_data: BatchProductInput,
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    batch_feature_extraction_service: BatchFeatureExtractionService = Depends(get_batch_feature_extraction_service),
):
    try:
        extractor_config = ConfigSchema(
            max_missing_feature_attempts=input_data.max_missing_feature_attempts,
            max_low_confidence_attempts=input_data.max_low_confidence_attempts,
            max_no_progress_attempts=input_data.max_no_progress_attempts,
            confidence_threshold=input_data.confidence_threshold,
        )

        batch = [{"product_id": item.product_id, "raw_data": item.raw_data} for item in input_data.products]
        extracted_data_list = await batch_feature_extraction_service.process_batch(batch, extractor_config)

        product_ids = []
        for extracted_data in extracted_data_list:
            if "error" in extracted_data:
                logger.error(f"Error processing product {extracted_data['id']}: {extracted_data['error']}")
                continue

            product = extracted_data["extracted_data"]
            product["product_id"] = extracted_data["id"]

            # Ensure all required fields are present
            required_fields = ["name", "product_id"]  # Add other required fields here
            for field in required_fields:
                if field not in product:
                    product[field] = f"Default {field.capitalize()} for {extracted_data['id']}"

            try:
                new_product = NewProduct(**product)
                id = await weaviate_service.add_product(new_product.dict())
                product_ids.append({"id": id})
            except ValidationError as ve:
                logger.error(f"Validation error for product {extracted_data['id']}: {str(ve)}")
                continue

        return {"products": product_ids}
    except Exception as e:
        logger.error(f"Error adding products batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
