from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
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
