from enum import Enum
from typing import List
from pydantic import BaseModel


class FeatureExtractorType(str, Enum):
    agentic = "agentic"
    simple = "simple"


class Product(BaseModel):
    id: str
    name: str
    ids: str
    manufacturer: str
    form_factor: str
    processor: str
    core_count: str
    processor_tdp: str
    memory: str
    io: str
    operating_system: str
    environmentals: str
    certifications: str
    short_summary: str
    full_summary: str
    full_product_description: str


class NewProduct(BaseModel):
    name: str
    ids: str
    manufacturer: str
    form_factor: str
    processor: str
    core_count: str
    processor_tdp: str
    memory: str
    io: str
    operating_system: str
    environmentals: str
    certifications: str
    short_summary: str
    full_summary: str
    full_product_description: str


class RawProductInput(BaseModel):
    raw_data: str
    ids: str
    extractor_type: FeatureExtractorType


class BatchProductItem(BaseModel):
    ids: str
    raw_data: str


class BatchProductInput(BaseModel):
    products: List[BatchProductItem]
    extractor_type: FeatureExtractorType


attribute_descriptions = {
    "name": "The official name of the product (e.g., 'SOM Intel 11th Gen Core Processors', 'ET COM Express').",
    "manufacturer": "The company or brand responsible for manufacturing the product (e.g., 'Advantech', 'ARBOR Technology', 'IBASE').",
    "form_factor": "The physical dimensions or standard that defines the module's shape and size (e.g., 'COM Express Basic Module Type 6', '125mm x 95mm').",
    "processor": "The specific processor model used in the product, including its generation or architecture (e.g., 'Intel 11th Gen Core Processors (Tiger Lake-H)', 'Intel Xeon D Processor Code Name Ice Lake-D LCC').",
    "core_count": "The number of cores in the processor (e.g., '8Core/16T', 'Quad/Dual Cores').",
    "processor_tdp": "The Thermal Design Power (TDP) rating of the processor, indicating power consumption and heat output (e.g., 'Up to 45W', 'Max TDP 65W').",
    "memory": "The type, configuration, and maximum capacity of the memory supported by the product (e.g., 'Dual channel DDR4, Max 64GB, SODIMM, ECC support', 'DDR4 3200MHz, up to 128GB, ECC/non-ECC').",
    "io": "The available input/output interfaces and connections provided by the product (e.g., 'PCIe x16 Gen4, USB 3.2 Gen2, GbE, SATA III, TPM', '4x USB 2.0, 4x USB 3.0, 2x UART ports, 4x PCIe x1 lanes').",
    "operating_system": "The operating systems or software environments supported by the product (e.g., 'Windows 10, Windows 11, Ubuntu', 'Windows IoT Enterprise LTSB').",
    "environmentals": "Environmental operating conditions, such as temperature and humidity ranges (e.g., 'Operating Temperature: 0°C to 60°C, Storage Temperature: -40°C to 85°C, Humidity: 10% to 90% non-condensing').",
    "certifications": "Any industry or safety certifications the product has obtained (e.g., 'CE, FCC Class B, RoHS', 'IPC-A-610 Class 3, MIL-STD-810G').",
    "short_summary": "A concise description of the product's key features (e.g., 'SOM Intel 11th Gen Core Processors with Tiger Lake-H architecture, supporting up to 64GB DDR4 memory, multiple I/O interfaces, and various operating systems').",
    "full_summary": "A more detailed overview of the product's main features and capabilities (e.g., 'The SOM Intel 11th Gen Core Processors module, based on the Tiger Lake-H architecture, offers high performance with support for up to 64GB DDR4 memory, multiple I/O interfaces including PCIe x16 Gen4, USB 3.2 Gen2, GbE, SATA III, TPM, and NVMe SSD').",
    "full_product_description": "A comprehensive, in-depth description of the product, including its technical specifications, use cases, and design considerations (e.g., 'The SOM Intel 11th Gen Core Processors module, also known as the Tiger Lake-H COM Express Basic Type Module, is designed for high-performance computing applications. It supports up to 64GB of dual-channel DDR4 memory with ECC support, and offers a variety of I/O interfaces...').",
}
