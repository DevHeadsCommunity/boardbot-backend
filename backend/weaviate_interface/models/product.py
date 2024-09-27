from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, field_validator


def convert_not_available(v):
    return None if v == "Not available" else v


class BaseInfo(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def check_not_available(cls, v):
        return convert_not_available(v)


class ProcessorInfo(BaseInfo):
    manufacturer: Optional[str] = None
    series: Optional[str] = None
    model: Optional[str] = None
    speed: Optional[str] = None
    max_speed: Optional[str] = None
    core_count: Optional[int] = None
    thread_count: Optional[int] = None
    architecture: Optional[str] = None
    features: Optional[List[str]] = None
    tdp: Optional[str] = None


class MemoryInfo(BaseInfo):
    ram_type: Optional[str] = None
    ram_speed: Optional[str] = None
    ram_capacity: Optional[str] = None
    ram_configuration: Optional[str] = None


class StorageInfo(BaseInfo):
    storage_type: Optional[str] = None
    storage_capacity: Optional[str] = None


class InterfacesInfo(BaseInfo):
    display_outputs: Optional[List[str]] = None
    ethernet_ports: Optional[List[str]] = None
    usb_ports: Optional[List[str]] = None
    serial_ports: Optional[List[str]] = None
    pcie_slots: Optional[List[str]] = None
    storage_interfaces: Optional[List[str]] = None
    other_io: Optional[List[str]] = None


class PowerInfo(BaseInfo):
    power_input: Optional[str] = None
    power_consumption: Optional[str] = None


class EnvironmentalSpecs(BaseInfo):
    cooling_method: Optional[str] = None
    operating_temperature: Optional[str] = None
    storage_temperature: Optional[str] = None
    operating_humidity: Optional[str] = None
    shock_resistance: Optional[str] = None
    vibration_resistance: Optional[str] = None


class NewProduct(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    is_prototype: Optional[bool] = None
    form_factor: Optional[str] = None
    processor: Optional[ProcessorInfo] = None
    memory: Optional[MemoryInfo] = None
    storage: Optional[StorageInfo] = None
    gpu_model: Optional[str] = None
    interfaces: Optional[InterfacesInfo] = None
    wireless_connectivity: Optional[List[str]] = None
    operating_system_support: Optional[List[str]] = None
    power: Optional[PowerInfo] = None
    environmental_specifications: Optional[EnvironmentalSpecs] = None
    ip_rating: Optional[str] = None
    certifications: Optional[List[str]] = None
    target_applications: Optional[List[str]] = None
    short_summary: str
    full_summary: str
    full_product_description: str


class Product(NewProduct):
    id: str


class FeatureExtractorType(str, Enum):
    agentic = "agentic"
    simple = "simple"


class RawProductInput(BaseModel):
    raw_data: str
    extractor_type: FeatureExtractorType


class BatchProductItem(BaseModel):
    raw_data: str


class BatchProductInput(BaseModel):
    products: List[BatchProductItem]
    extractor_type: FeatureExtractorType


attribute_descriptions = {
    "name": "The official name of the product, in clear, capital case, singular, without special characters. (Only the official name, dont include Code Name, or any other variant)",
    "manufacturer": "The company or brand responsible for manufacturing the product, in clear, capital case, singular, without special characters.",
    "is_prototype": "A boolean value (True/False) indicating whether the product is a prototype or a production model.",
    "form_factor": "The physical dimensions, shape, or standard that defines the product's size (e.g., '63.5 x 38.1 x 10.2 mm', '3U VPX').",
    "processor": {
        "manufacturer": "The company that produces the processor (e.g., 'Intel', 'AMD', 'ARM').",
        "model": "The specific model of the processor (e.g., 'i7-1185GRE', 'Cortex-A8').",
        "speed": "The base clock speed of the processor in GHz (e.g., '1.8 GHz').",
        "max_speed": "The maximum turbo or boost clock speed of the processor in GHz, if applicable.",
        "core_count": "The number of physical cores in the processor, as an integer.",
        "thread_count": "The number of threads the processor can handle simultaneously, as an integer.",
        "architecture": "The instruction set architecture of the processor (e.g., 'x86-64', 'ARM', 'RISC-V').",
        "features": "A list of special features or technologies of the processor (e.g., ['Intel vPro', 'AMD-V']).",
        "tdp": "The Thermal Design Power of the processor in watts (e.g., '15W').",
    },
    "memory": {
        "ram_type": "The type of RAM used in the product (e.g., 'DDR4', 'LPDDR4').",
        "ram_speed": "The speed of the RAM in MHz (e.g., '3200 MHz').",
        "ram_capacity": "The total amount of RAM installed or supported (e.g., '8 GB', 'Up to 32 GB').",
        "ram_configuration": "Information about RAM slots or configuration (e.g., '2x SODIMM', 'Soldered').",
    },
    "storage": {
        "storage_type": "The type of storage used in the product (e.g., 'eMMC', 'SSD', 'NAND Flash').",
        "storage_capacity": "The amount of built-in storage (e.g., '256 GB').",
    },
    "gpu_model": "The model of the integrated or discrete GPU, if available.",
    "interfaces": {
        "display_outputs": "A list of types and number of display outputs (e.g., ['1x HDMI', '1x DisplayPort']).",
        "ethernet_ports": "A list of Ethernet ports with their speeds (e.g., ['2x Gigabit Ethernet']).",
        "usb_ports": "A list of USB ports with their types and versions (e.g., ['2x USB 3.2 Gen 2', '2x USB 2.0']).",
        "serial_ports": "A list of serial ports with their types (e.g., ['2x RS-232', '1x RS-485']).",
        "pcie_slots": "A list of PCIe slots with their generations (e.g., ['1x PCIe x16 Gen 3', '2x PCIe x1 Gen 2']).",
        "storage_interfaces": "A list of supported storage interfaces (e.g., ['2x SATA 3.0', '1x M.2 NVMe']).",
        "other_io": "A list of additional input/output interfaces (e.g., ['I2C', 'SPI', 'GPIO']).",
    },
    "wireless_connectivity": "A list of built-in wireless connectivity options (e.g., ['Wi-Fi 6', 'Bluetooth 5.1']).",
    "operating_system_support": "A list of supported operating systems (e.g., ['Windows 10 IoT', 'Ubuntu 20.04 LTS']).",
    "power": {
        "power_input": "The input voltage range or power requirements (e.g., '12V DC', '100-240V AC').",
        "power_consumption": "Typical or maximum power consumption (e.g., '15W typical, 30W max').",
    },
    "environmental_specifications": {
        "cooling_method": "The method used for cooling the device (e.g., 'Fanless', 'Active cooling').",
        "operating_temperature": "The range of temperatures in which the device can operate (e.g., '-40°C to 85°C').",
        "storage_temperature": "The range of temperatures in which the device can be stored (e.g., '-55°C to 105°C').",
        "operating_humidity": "The range of humidity in which the device can operate (e.g., '5% to 95% non-condensing').",
        "shock_resistance": "The level of shock the device can withstand, if available (e.g., '50G, 11ms, half-sine').",
        "vibration_resistance": "The level of vibration the device can withstand, if available (e.g., '5 Grms, 5-500 Hz').",
    },
    "ip_rating": "Ingress Protection rating, if applicable (e.g., 'IP65', 'Not rated').",
    "certifications": "A list of industry certifications and compliance standards (e.g., ['CE', 'FCC Class B', 'MIL-STD-810G']).",
    "target_applications": "A list of intended use cases or industries (e.g., ['Industrial automation', 'Medical devices']).",
    "short_summary": "A concise description of the product's key features and target applications (1-2 sentences).",
    "full_summary": "A more detailed overview of the product's main features, capabilities, and target applications (3-5 sentences).",
    "full_product_description": "A comprehensive description of the product, including technical specifications, use cases, and design considerations.",
}
112 - 166
