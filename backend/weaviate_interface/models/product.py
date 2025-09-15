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
    
    permalink: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class Product(NewProduct):
    id: str


attribute_descriptions = {
    "name": {
        "description": "The official name of the product. Return type: string. (e.g., AIMB, SOM, ASMB, PCM, ARK, MIO, RSB, RASPBERRY-PI MODEL B, VENICE GW, AIMB-275, EDHMIC, COM-EXPRESS COMPACT, COM-EXPRESS BASIC, TREK, MIC, EMETXEI, PCA, UNOG, AIMB-580, CONGATC, COM MODULES, PCEGA, ARKL, CONGATS, EMETXEIM, VENICE GW SINGLE BOARD, PCEGAE, COM-EXPRESS MINI, SOM COM-EXPRESS COMPACT, AGS GPU SERVER, SOM INTEL ATOMCELERON PROCESSOR COM-EXPRESS MINI, CONGASA, MIO EXTENSION SBC, COMPUTE, ARKDS, RASPBERRY-PI COMPUTE, CONGATCA, ROCK PI N, UBIQUITOUS TOUCH, IBASE IBAF, AIMB-225, MIOJUAE, ODYSSEY XJ, ROCK PI S, ROM Q7, AIMB KIOSK, EMNANOAM, CONGAMA, KINODH)",
        "return_type": "string"
    },
    "manufacturer": {
        "description": "The company that produces the product. Return type: string. (e.g., ADVANTECH, IEI, CONGATEC, KONTRON, VERSALOGIC, ADLINK TECHNOLOGY, IBASE, ARBOR TECHNOLOGY, IWAVE SYSTEMS, RASPBERRY PI, SOLIDRUN, KARO ELECTRONICS, MYIR ELECTRONICS, AXIOMTEK, GATEWORKS, EUROTECH, PHOENIX CONTACT, EDA TECHNOLOGY CO LTD, SECO, NEXCOBOT, DIGI INTERNATIONAL, GIGAIPC, FORLINX EMBEDDED TECHNOLOGY, SEEEDSTUDIO, RADXA, ASUS, NVIDIA, AAEON, OLIMEX, ESPRESSIF, NXP, GOOGLE, KUNBUS, MIXTILE, D SYSTEMS, GUMSTIX, BOUNDARY DEVICES, ACURA EMBEDDED SYSTEMS, INTEL, STARTECHCOM, BEACON EMBEDDEDWORKS, MOXA, TOYBRICK, NEXCOM, INTRINSYC TECHNOLOGIES, NORDIC SEMICONDUCTOR, AIM, MICROSOFT, SCIOSENSE)",
        "return_type": "string"
    },
    "form_factor": {
        "description": "The single, primary physical form factor or standard of the product. Return type: string. (e.g., COM EXPRESS, SBC, MINI-ITX, ATX, SMARC, BOX PC, QSEVEN, MICRO-ATX, PICO-ITX, SOM, RASPBERRY PI, SODIMM, DIN RAIL, EBX, PCPLUS, EPIC, EMBEDDED, HALF-SIZE, QFN, ETX, PICMG, COM, RACKMOUNT, ALL-IN-ONE, THIN MINI-ITX, COMPACT, MIO, PROPRIETARY, COMPACT PCI, REGULAR SIZE, PC104, PC, PALMSIZE, SLOT SBC, PANEL PC, PCI, DEVELOPMENT BOARD, SMALL SIZE, MINI PCIE, COMPACT IN-VEHICLE COMPUTING BOX, MICROSOM, DIGI SMTPLUS, SMALL ENCLOSURE, COMHPC, COMPACT VISION SYSTEM, MODULAR IPC, MXM, COMHPC SIZE A, PCI-ISA, EPIC SBC)",
        "return_type": "string"
    },
    "evaluation_or_commercialization": {
        "description": "Indicates if the product is for evaluation or commercial use (True for evaluation, False for commercial). Return type: boolean.",
        "return_type": "boolean"
    },
    "processor_architecture": {
        "description": "The architecture/family of the processor (canonical primary label). Return type: string. (e.g., X86, ARM, X86-64, INTEL ATOM, INTEL CORE, AMD ZEN, RISC-V, XTENSA, ARM CORTEX-A53, ARMV8, INTEL XEON, etc.)",
        "return_type": "string"
    },
    "processor_core_count": {
        "description": "The number of cores or specified range (keep text if a range is given). Return type: string. (e.g., 4, 8, 1-16, 2-32)",
        "return_type": "string"
    },
    "processor_manufacturer": {
        "description": "The company that manufactures the processor. Return type: string. (e.g., INTEL, AMD, NXP, BROADCOM, NVIDIA, QUALCOMM, ROCKCHIP, STMICROELECTRONICS)",
        "return_type": "string"
    },
    "processor_tdp": {
        "description": "Thermal Design Power as stated, including units or ranges. Return type: string. (e.g., 6.0W, 15.0W-45.0W, LOW POWER)",
        "return_type": "string"
    },
    "memory": {
        "description": "RAM size/type/speed summary as stated. Return type: string. (e.g., 8.0GB DDR4, 4.0GB LPDDR4, UP TO 64GB)",
        "return_type": "string"
    },
    "onboard_storage": {
        "description": "Built-in storage type/size as stated. Return type: string. (e.g., 64GB eMMC, NVMe SSD, mSATA supported)",
        "return_type": "string"
    },
    "input_voltage": {
        "description": "Required input voltage or range as stated (include units/AC/DC as given). Return type: string. (e.g., 12.0V, 9.0V-36.0V, AC 100-240V)",
        "return_type": "string"
    },
    "io_count": {
        "description": "List of I/O counts/types in concise tokens. Return type: string_array. (e.g., [\"2×GbE\", \"4×USB 3.0\", \"1×HDMI\"])",
        "return_type": "string_array"
    },
    "wireless": {
        "description": "List of wireless capabilities/standards. Return type: string_array. (e.g., [\"Wi-Fi 6\", \"Bluetooth 5.2\", \"LTE\"])",
        "return_type": "string_array"
    },
    "operating_system_bsp": {
        "description": "List of supported OS/BSPs as stated. Return type: string_array. (e.g., [\"Ubuntu 22.04\", \"Windows 10 IoT\", \"Yocto\"])",
        "return_type": "string_array"
    },
    "operating_temperature_max": {
        "description": "Maximum operating temperature with unit. Return type: string. (e.g., 85°C, +80℃)",
        "return_type": "string"
    },
    "operating_temperature_min": {
        "description": "Minimum operating temperature with unit. Return type: string. (e.g., -40°C, -20℃)",
        "return_type": "string"
    },
    "certifications": {
        "description": "List of certifications/compliance standards. Return type: string_array. (e.g., [\"CE\", \"FCC\", \"RoHS\", \"EN 50155\"])",
        "return_type": "string_array"
    },
    "price": {
        "description": "Price string as stated (include currency/symbols if present). Return type: string.",
        "return_type": "string"
    },
    "stock_availability": {
        "description": "Current stock status as stated. Return type: string. (e.g., In Stock, Out of Stock, Backorder)",
        "return_type": "string"
    },
    "lead_time": {
        "description": "Fulfillment lead time as stated. Return type: string. (e.g., 2–4 weeks)",
        "return_type": "string"
    },
    "categories": {
        "description": "One or more categories/taxonomy tags it belongs to. Return type: string_array.",
        "return_type": "string_array"
    },
    "image_url": {
        "description": "Product image URL as stated. Return type: string (URL).",
        "return_type": "string"
    },
    "permalink": {
        "description": "Product page URL as stated. Return type: string (URL).",
        "return_type": "string"
    },
    "category": {
        "description": "High-level category (canonical singular). Return type: string. (e.g., Single Board Computer)",
        "return_type": "string"
    },
    "sub_category": {
        "description": "Sub-category under the main category (canonical singular). Return type: string. (e.g., Mini-ITX SBC)",
        "return_type": "string"
    },
    "description": {
        "description": "The product description text as provided (verbatim, if available). Return type: string.",
        "return_type": "string"
    }
    # If you later re-enable:
    # "short_summary": {"description": "Concise 1–2 line value prop. Return type: string.", "return_type": "string"},
    # "full_summary": {"description": "3–5 line capabilities overview. Return type: string.", "return_type": "string"},
    # "full_product_description": {"description": "In-depth, text-only summary compiled from source. Return type: string.", "return_type": "string"},
    # "target_applications": {"description": "Intended use cases/industries. Return type: string_array.", "return_type": "string_array"},
}

