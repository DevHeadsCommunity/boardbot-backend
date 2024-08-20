import pandas as pd
from io import StringIO
from models.product import Product
from services.weaviate_service import WeaviateService
from services.feature_extractor_agent_v2 import FeatureExtractor
from dependencies import get_weaviate_service, get_feature_extractor
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

router = APIRouter()


@router.get("/products")
async def get_all_products(weaviate_service: WeaviateService = Depends(get_weaviate_service)):
    return await weaviate_service.get_all_products()


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
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    feature_extractor: FeatureExtractor = Depends(get_feature_extractor),
):
    extracted_data = await feature_extractor.extract_data(raw_data)
    product_id = await weaviate_service.add_product(extracted_data)
    return {"id": product_id}


@router.post("/products/batch")
async def add_products_batch(
    file: UploadFile = File(...),
    weaviate_service: WeaviateService = Depends(get_weaviate_service),
    feature_extractor: FeatureExtractor = Depends(get_feature_extractor),
):
    content = await file.read()
    csv_content = content.decode("utf-8")
    df = pd.read_csv(StringIO(csv_content))

    product_ids = []
    for _, row in df.iterrows():
        raw_data = row["raw_data"]
        extracted_data = await feature_extractor.extract_data(raw_data)
        product_id = await weaviate_service.add_product(extracted_data)
        product_ids.append(product_id)

    return {"ids": product_ids}
