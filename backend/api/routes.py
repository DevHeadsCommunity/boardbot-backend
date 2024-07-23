from fastapi import APIRouter

router = APIRouter()


@router.post("/product")
async def add_product():
    return {"message": "Hello World"}


@router.post("/products")
async def add_products():
    return {"message": "Hello World"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}
