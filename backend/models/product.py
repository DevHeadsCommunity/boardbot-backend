from dataclasses import dataclass


@dataclass
class Product:
    id: str  # This is the UUID of the product in Weaviate
    name: str
    ids: str
    manufacturer: str
    form_factor: str
    processor: str
    core_count: int
    processor_tdp: int
    memory: int
    io: str
    operating_system: str
    environmentals: str
    certifications: str
    short_summary: str
    full_summary: str
    full_product_description: str


ProductAttributes = {
    "id": "Unique identifier of the product",
    "name": "Full name of the product",
    "ids": "Unique identifier(s) for the product",
    "manufacturer": "Company that produces the product",
    "form_factor": "Physical dimensions or form factor of the product",
    "processor": "Type or model of processor used in the product",
    "core_count": "Number of processor cores",
    "processor_tdp": "Thermal Design Power of the processor",
    "memory": "RAM and storage capacity specifications",
    "io": "Input/output interfaces available on the product",
    "operating_system": "Supported operating system(s) or software environment",
    "environmentals": "Operating conditions such as temperature and humidity ranges",
    "certifications": "Relevant certifications for the product",
    "short_summary": "Brief description of the product",
    "full_summary": "Detailed summary of the product's features and capabilities",
    "full_product_description": "Comprehensive description of the product",
}
