import json
import logging
from enum import Enum
from typing import Optional
import pandas as pd
from io import StringIO
from models.product import Product
from services.weaviate_service import WeaviateService
from services.simple_feature_extractor import SimpleFeatureExtractor
from services.agentic_feature_extractor import AgenticFeatureExtractor
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from dependencies import get_weaviate_service, get_agentic_feature_extractor, get_simple_feature_extractor

logger = logging.getLogger(__name__)

router = APIRouter()


class FeatureExtractorType(str, Enum):
    agentic = "agentic"
    simple = "simple"


# @router.get("/products")
# async def get_products(
#     limit: int = Query(10, ge=1, le=100),
#     offset: int = Query(0, ge=0),
#     weaviate_service: WeaviateService = Depends(get_weaviate_service),
# ):
#     logger.info(f"Getting products with limit: {limit}, offset: {offset}")
#     products, total_count = await weaviate_service.get_products(limit, offset)
#     logger.info(f"Found {len(products)} products")
#     return {"total": total_count, "limit": limit, "offset": offset, "products": products}


@router.get("/products")
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filter: Optional[str] = Query(None),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
):
    logger.info(f"Getting products with page: {page}, page_size: {page_size}, filter: {filter}")
    offset = (page - 1) * page_size
    filter_dict = json.loads(filter) if filter else None
    products, total_count = await weaviate_service.get_products(page_size, offset, filter_dict)
    logger.info(f"Found {len(products)} products")
    return {"total": total_count, "page": page, "page_size": page_size, "products": products}


@router.get("/products/{product_id}")
async def get_product(product_id: str, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    product = await weaviate_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products")
async def add_product(product: Product, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    product_id = await weaviate_service.add_product(product.dict())
    return {"id": product_id}


# @router.put("/products/{product_id}")
# async def update_product(
#     product_id: str, product: Product, weaviate_service: WeaviateService = Depends(get_weaviate_service)
# ):
#     success = await weaviate_service.update_product(product_id, product.dict())
#     if not success:
#         raise HTTPException(status_code=404, detail="Product not found")
#     return {"message": "Product updated successfully"}


@router.put("/products/{product_id}")
async def update_product(
    product_id: str, product: Product, weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    success = await weaviate_service.update_product(product_id, product.dict())
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    success = await weaviate_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


@router.post("/products/raw")
async def add_raw_product(
    raw_data: str,
    extractor_type: FeatureExtractorType = Query(
        FeatureExtractorType.agentic, description="The type of feature extractor to use"
    ),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    agentic_feature_extractor: AgenticFeatureExtractor = Depends(get_agentic_feature_extractor),
    simple_feature_extractor: SimpleFeatureExtractor = Depends(get_simple_feature_extractor),
):
    if extractor_type == FeatureExtractorType.agentic:
        extracted_data = await agentic_feature_extractor.extract_data(raw_data)
    else:
        extracted_data = await simple_feature_extractor.extract_data(raw_data)

    product_id = await weaviate_service.add_product(extracted_data)
    return {"id": product_id}


@router.post("/products/batch")
async def add_products_batch(
    file: UploadFile = File(...),
    extractor_type: FeatureExtractorType = Query(
        FeatureExtractorType.agentic, description="The type of feature extractor to use"
    ),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    agentic_feature_extractor: AgenticFeatureExtractor = Depends(get_agentic_feature_extractor),
    simple_feature_extractor: SimpleFeatureExtractor = Depends(get_simple_feature_extractor),
):
    content = await file.read()
    csv_content = content.decode("utf-8")
    df = pd.read_csv(StringIO(csv_content))

    product_ids = []
    for _, row in df.iterrows():
        raw_data = row["raw_data"]
        if extractor_type == FeatureExtractorType.agentic:
            extracted_data = await agentic_feature_extractor.extract_data(raw_data)
        else:
            extracted_data = await simple_feature_extractor.extract_data(raw_data)
        product_id = await weaviate_service.add_product(extracted_data)
        product_ids.append(product_id)

    return {"ids": product_ids}
