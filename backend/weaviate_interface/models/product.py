from typing import List, Optional
from pydantic import BaseModel, field_validator


def convert_not_available(v):
    return None if v.lower() == "not available" else v


class BaseInfo(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def check_not_available(cls, v):
        return convert_not_available(v)


class NewProduct(BaseModel):
    product_id: str
    duplicate_ids: Optional[List[str]] = None
    name: str
    manufacturer: Optional[str] = None
    form_factor: Optional[str] = None
    evaluation_or_commercialization: Optional[str] = None
    processor_architecture: Optional[str] = None
    processor_core_count: Optional[str] = None
    processor_manufacturer: Optional[str] = None
    processor_tdp: Optional[str] = None
    memory: Optional[str] = None
    onboard_storage: Optional[str] = None
    input_voltage: Optional[str] = None
    io_count: Optional[List[str]] = None
    wireless: Optional[List[str]] = None
    operating_system_bsp: Optional[List[str]] = None
    operating_temperature_max: Optional[str] = None
    operating_temperature_min: Optional[str] = None
    certifications: Optional[List[str]] = None
    price: Optional[str] = None
    stock_availability: Optional[str] = None
    lead_time: Optional[str] = None

    # Additional features
    short_summary: Optional[str] = None
    full_summary: Optional[str] = None
    full_product_description: Optional[str] = None
    target_applications: Optional[List[str]] = None


class Product(NewProduct):
    id: str  # the product uuid created in weaviate


attribute_descriptions = {
    "name": "The official name of the product.",
    "manufacturer": "The company that produces the product.",
    "form_factor": "The single, primary physical form factor or standard of the product (e.g., 'ATX', 'Mini-ITX', 'Raspberry Pi').",
    "evaluation_or_commercialization": "Indicates if the product is for evaluation or commercial use (Evaluation for evaluation, Commercial for commercial).",
    "processor_architecture": "The architecture of the processor (e.g., ARM, x86).",
    "processor_core_count": "The number of cores in the processor.",
    "processor_manufacturer": "The company that manufactures the processor.",
    "processor_tdp": "The Thermal Design Power of the processor.",
    "memory": "The size and type of RAM in the product.",
    "onboard_storage": "The amount and type of built-in storage.",
    "input_voltage": "The required input voltage for operation.",
    "io_count": "The count and types of Input/Output interfaces.",
    "wireless": "Wireless capabilities (e.g., Wi-Fi, Bluetooth).",
    "operating_system_bsp": "Supported operating systems or Board Support Packages.",
    "operating_temperature_max": "The maximum operating temperature.",
    "operating_temperature_min": "The minimum operating temperature.",
    "certifications": "Certifications and compliance standards met.",
    "price": "The cost of the product.",
    "stock_availability": "Current stock status (e.g., In Stock, Out of Stock).",
    "lead_time": "Time required to fulfill an order.",
    "short_summary": "A concise description highlighting key features.",
    "full_summary": "A detailed overview of the product's capabilities.",
    "full_product_description": "An in-depth description including specifications.",
    "target_applications": "Intended use cases or industries for the product.",
}
