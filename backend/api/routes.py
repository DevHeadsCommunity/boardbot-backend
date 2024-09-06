import csv
from io import StringIO
import logging
from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from models.product import NewProduct, Product, RawProductInput, BatchProductInput
from services.weaviate_service import WeaviateService
from services.simple_feature_extractor import SimpleFeatureExtractor
from services.agentic_feature_extractor import AgenticFeatureExtractor
from dependencies import get_weaviate_service, get_agentic_feature_extractor, get_simple_feature_extractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api")


class FeatureExtractorType(str, Enum):
    agentic = "agentic"
    simple = "simple"


class FilterParams(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)
    filter: Optional[str] = None


@api_router.get("/products")
async def get_products(
    params: FilterParams = Depends(),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
):
    logger.info(f"Getting products with params: {params}")
    offset = (params.page - 1) * params.page_size
    filter_dict = params.filter

    products, total_count = await weaviate_service.get_products(params.page_size, offset, filter_dict)
    logger.info(f"Found {len(products)} products")
    return {"total": total_count, "page": params.page, "page_size": params.page_size, "products": products}


@api_router.get("/products/{product_id}")
async def get_product(product_id: str, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    product = await weaviate_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@api_router.post("/products")
async def add_product(product: NewProduct, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    try:
        logger.info(f"Adding product: {product.dict()}")
        product_id = await weaviate_service.add_product(product.dict())
        return {"id": product_id}
    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/products/{product_id}")
async def update_product(
    product_id: str, product: Product, weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    try:
        success = await weaviate_service.update_product(product_id, product.dict())
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product updated successfully"}
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    try:
        success = await weaviate_service.delete_product(product_id)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/products/raw")
async def add_raw_product(
    input_data: RawProductInput,
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    agentic_feature_extractor: AgenticFeatureExtractor = Depends(get_agentic_feature_extractor),
    simple_feature_extractor: SimpleFeatureExtractor = Depends(get_simple_feature_extractor),
):
    try:
        logger.info(f"Adding raw product with ids: {input_data.ids}, extractor_type: {input_data.extractor_type}")
        logger.debug(f"Raw data: {input_data.raw_data}")

        extractor = (
            agentic_feature_extractor
            if input_data.extractor_type == FeatureExtractorType.agentic
            else simple_feature_extractor
        )
        extracted_data = await extractor.extract_data(input_data.raw_data)

        extracted_data["ids"] = input_data.ids
        logger.info(f"Extracted data: {extracted_data}")

        product_id = await weaviate_service.add_product(extracted_data)
        return {"id": product_id}
    except Exception as e:
        logger.error(f"Error adding raw product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/products/batch")
async def add_products_batch(
    file: UploadFile = File(...),
    extractor_type: FeatureExtractorType = Query(FeatureExtractorType.agentic),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    agentic_feature_extractor: AgenticFeatureExtractor = Depends(get_agentic_feature_extractor),
    simple_feature_extractor: SimpleFeatureExtractor = Depends(get_simple_feature_extractor),
):
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
        csv_file = StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)

        extractor = (
            agentic_feature_extractor if extractor_type == FeatureExtractorType.agentic else simple_feature_extractor
        )

        product_ids = []
        for row in csv_reader:
            ids = row["ids"]
            raw_data = row["raw_data"]

            extracted_data = await extractor.extract_data(raw_data)
            extracted_data["ids"] = ids  # Preserve the original source ID

            product_id = await weaviate_service.add_product(extracted_data)
            product_ids.append({"source_id": ids, "new_id": product_id})

        return {"products": product_ids}
    except Exception as e:
        logger.error(f"Error adding products batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/products/batch/parsed")
async def add_products_batch_parsed(
    input_data: BatchProductInput,
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    agentic_feature_extractor: AgenticFeatureExtractor = Depends(get_agentic_feature_extractor),
    simple_feature_extractor: SimpleFeatureExtractor = Depends(get_simple_feature_extractor),
):
    try:
        extractor = (
            agentic_feature_extractor
            if input_data.extractor_type == FeatureExtractorType.agentic
            else simple_feature_extractor
        )

        product_ids = []
        for product in input_data.products:
            extracted_data = await extractor.extract_data(product.raw_data)
            extracted_data["ids"] = product.ids  # Preserve the original source ID

            product_id = await weaviate_service.add_product(extracted_data)
            product_ids.append({"source_id": product.ids, "new_id": product_id})

        return {"products": product_ids}
    except Exception as e:
        logger.error(f"Error adding products batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
