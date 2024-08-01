from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    name: str
    summary: str
    form: Optional[str] = None
    io: Optional[str] = None
    manufacturer: Optional[str] = None
    memory: Optional[str] = None
    processor: Optional[str] = None
    size: Optional[str] = None
