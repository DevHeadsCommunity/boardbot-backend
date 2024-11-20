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
    id: str


attribute_descriptions = {
    "name": "The official name of the product. (e.g., AIMB, SOM, ASMB, PCM, ARK, MIO, RSB, RASPBERRY-PI MODEL B, VENICE GW, AIMB-275, EDHMIC, COM-EXPRESS COMPACT, COM-EXPRESS BASIC, TREK, MIC, EMETXEI, PCA, UNOG, AIMB-580, CONGATC, COM MODULES, PCEGA, ARKL, CONGATS, EMETXEIM, VENICE GW SINGLE BOARD, PCEGAE, COM-EXPRESS MINI, SOM COM-EXPRESS COMPACT, AGS GPU SERVER, SOM INTEL ATOMCELERON PROCESSOR COM-EXPRESS MINI, CONGASA, MIO EXTENSION SBC, COMPUTE, ARKDS, RASPBERRY-PI COMPUTE, CONGATCA, ROCK PI N, UBIQUITOUS TOUCH, IBASE IBAF, AIMB-225, MIOJUAE, ODYSSEY XJ, ROCK PI S, ROM Q7, AIMB KIOSK, EMNANOAM, CONGAMA, KINODH)",
    "manufacturer": "The company that produces the product. (e.g., ADVANTECH, IEI, CONGATEC, KONTRON, VERSALOGIC, ADLINK TECHNOLOGY, IBASE, ARBOR TECHNOLOGY, IWAVE SYSTEMS, RASPBERRY PI, SOLIDRUN, KARO ELECTRONICS, MYIR ELECTRONICS, AXIOMTEK, GATEWORKS, EUROTECH, PHOENIX CONTACT, EDA TECHNOLOGY CO LTD, SECO, NEXCOBOT, DIGI INTERNATIONAL, GIGAIPC, FORLINX EMBEDDED TECHNOLOGY, SEEEDSTUDIO, RADXA, ASUS, NVIDIA, AAEON, OLIMEX, ESPRESSIF, NXP, GOOGLE, KUNBUS, MIXTILE, D SYSTEMS, GUMSTIX, BOUNDARY DEVICES, ACURA EMBEDDED SYSTEMS, INTEL, STARTECHCOM, BEACON EMBEDDEDWORKS, MOXA, TOYBRICK, NEXCOM, INTRINSYC TECHNOLOGIES, NORDIC SEMICONDUCTOR, AIM, MICROSOFT, SCIOSENSE)",
    "form_factor": "The single, primary physical form factor or standard of the product (e.g., COM EXPRESS, SBC, MINI-ITX, ATX, SMARC, BOX PC, QSEVEN, MICRO-ATX, PICO-ITX, SOM, RASPBERRY PI, SODIMM, DIN RAIL, EBX, PCPLUS, EPIC, EMBEDDED, HALF-SIZE, QFN, ETX, PICMG, COM, RACKMOUNT, ALL-IN-ONE, THIN MINI-ITX, COMPACT, MIO, PROPRIETARY, COMPACT PCI, REGULAR SIZE, PC104, PC, PALMSIZE, SLOT SBC, PANEL PC, PCI, DEVELOPMENT BOARD, SMALL SIZE, MINI PCIE, COMPACT IN-VEHICLE COMPUTING BOX, MICROSOM, DIGI SMTPLUS, SMALL ENCLOSURE, COMHPC, COMPACT VISION SYSTEM, MODULAR IPC, MXM, COMHPC SIZE A, PCI-ISA, EPIC SBC)",
    "evaluation_or_commercialization": "Indicates if the product is for evaluation or commercial use (True for evaluation, False for commercial).",
    "processor_architecture": "The architecture of the processor (e.g., X86, ARM, X86-64, INTEL ATOM, INTEL CORE, INTEL HYBRID, AMD ZEN, INTEL, RISC-V, XTENSA, ARM CORTEX-A7, PICMZ, 8-BIT, ARM CORTEX-A53, AMD, ARMV8, INTEL XEON E AND 8TH/9TH GENERATION CORE I3/I5/I7 SERIES, ARM CORTEX-A, 16-BIT)",
    "processor_core_count": "The number of cores in the processor (e.g., 4, 2, 1, 6, 8, 24, 16, 1-14, 14, 1-16, 1-24, 6-10, 12, 1-4, 10, 9, 1-8, 128, 1-6, 1-28, 80, 3, 64, 5, 32, 2-16, 1-60, 20, 1-10, 1-32)",
    "processor_manufacturer": "The company that manufactures the processor (e.g., INTEL, NXP, AMD, BROADCOM, ROCKCHIP, TEXAS INSTRUMENTS, FREESCALE, ARM, ALLWINNER, NVIDIA, DMP, STMICROELECTRONICS, RENESAS, QUALCOMM, XILINX, RABBIT, ESPRESSIF, MARVELL, MEDIATEK, RASPBERRY PI, VIA, MICROCHIP, ATMEL, ADVANTECH, WESTERN DESIGN CENTER, KNERON, STERICSSON)",
    "processor_tdp": "The Thermal Design Power of the processor (e.g., 6.0W, 15.0W, 35.0W, 45.0W, 65.0W, 10.0W, 95.0W, 125.0W, 28.0W, 12.0W, 0.0W-45.0W, 25.0W, 6.0W-12.0W, 35.0W-65.0W, LOW POWER, 5.0W, 205.0W, 12.0W-25.0W, 15.0W-45.0W, 15.0W-25.0W, 6.7W, 9.0W, 6.0W-45.0W, 31.0W, 80.0W, 25.0W-45.0W, 8.0W, 70.0W, 17.0W, 5.0W-10.0W, 6.0W-10.0W, 19.0W, 12.0W-28.0W, 12.0W-54.0W, 77.0W, 1.0W, 10.0W-54.0W, 13.0W, 0.0W-125.0W, 2.0W, 19.5W, 0.0W-13.0W, 100.0W, 0.0W-60.0W, 7.5W, 0.0W-54.0W, 105.0W, 6.0W-8.0W, 160.0W)",
    "memory": "The size and type of RAM in the product (e.g., 8.0GB DDR3, 4.0GB LPDDR4, 4.0GB DDR3, 1.0GB DDR3, 2.0GB LPDDR4, 8.0GB LPDDR4, 0-8.0GB DDR3L, 0-32.0GB DDR4, 0.5GB DDR3, 8.0GB DDR4, 0-32.0GB GBYTE, 0-64.0GB DDR4, 64.0GB DDR4, 2.0GB DDR3, 1.0GB LPDDR4, 0-8.0GB GB, 0.5GB, 0-4.0GB GB, 1.0GB, 32.0GB DDR4, 4.0GB LPDDR3, 0-64.0GB GBYTE, 4.0GB, 0-16.0GB GB, UNKNOWN DDR4, UP TO 64GB, 0-16.0GB DDR3L, 0-2.0GB GB, 0-8.0GB DUAL, 0-8.0GB DDR3, 0.2GB, 0-64.0GB GB, 1.0GB DDR2, 0-4.0GB DDR3, 16.0GB DDR4, 0-32.0GB DDR3, 0-1.0GB GB, 2.0GB DDR4, 0-8.0GB GBYTE, DDR3 2GB, SUPPORTS UP TO 32GB DDR3, UNKNOWN DUAL CHANNEL NON-ECC DDR4, MAX CAPACITY 64GB, 0.0GB, UNKNOWN DDR 333 MHZ, MAX CAPACITY 1 GB, 0.1GB, 4.0GB DDR4, 2.0GB DDR2, 0-8.0GB LPDDR4, 0-0.5GB MB, LPDDR4 8GB, 0-128.0GB DDR4)",
    "onboard_storage": "The amount and type of built-in storage (e.g., 64.0GB EMMC, MSATA, 16 GB EMMC, EMMC, 64 GB EMMC, NVME SSD, 16.0GB EMMC, 8 GB EMMC, 8.0GB EMMC, 32 GB EMMC, 32.0GB EMMC, COMPACTFLASH TYPE III, NON-VOLATILE USER DATA, 64 GBYTE EMMC, 8 GB EMMC NAND FLASH, 32.0GB/S M.2, COMPACTFLASH SOCKET, 128 GB EMMC FLASH, MSATA SUPPORT, MICRO SD CARD SLOT, 64 GB EMMC, 128 GB M.2 SSD, SSD, 64.0GB SSD, EMMC 5.0 HIGH-SPEED DRIVE 32.0GB SOLDERED ON BOARD, 1.0GB, MICROSD CARD SLOT, FLASH (MLC 64.0GB, SLC 32.0GB), 1 TBYTE NVME SSD, CF SOCKET, 4 GB EMMC NAND FLASH, MSATA SUPPORTED, 64.0GB, MSATA AND SATA HDD, 4 GB EMMC FLASH, NVME, 256.0GB, 64 GBYTES EMMC, 16 GBYTES EMMC, CFAST, 4 GB EMMC, CFAST TYPE III, EIGHT SATA 3 AND ONE M.2 CONNECTORS (SATA/PCIE COMPATIBLE), 8.0GB, 16.0GB, 32.0GB, 64.0GB OR 128.0GB EMMC FLASH, 128.0GB EMMC, MLC 8.0GB, SLC 4.0GB, 32 GBYTES EMMC, 8.0GB EMMC NAND FLASH, EMMC 5.1 ON BOARD MASS, 16 GB EMMC NAND FLASH)",
    "input_voltage": "The required input voltage for operation (e.g., 12.0V, 5.0V, 3.3V, 9.0V-36.0V, 24.0V, ATX, 100.0V-240.0V, 12.0V-24.0V, 8.0V-60.0V, 19.0V, 8.0V-30.0V, 3.0V, VARIABLE, AC, 8.5V, 12.0V-28.0V, 36.0V, 12.0V-60.0V, 8.0V, 30.0V, DC POWER INPUT, 7.0V-36.0V, 9.0V-15.0V, 4.2V-5.5V, DC POWER, 7.0V-12.0V, 3.0V-3.6V, 9.0V, 2.8V, 12.0V-48.0V, 48.0V, 2.0V, 9.0V-34.0V, 4.75V-20.0V, VDC, 10% TO 90% OF NOMINAL, 21.0V, 3.6V, 1.2V, 34.0V, 1.7V-5.5V, USB POWERED)",
    "io_count": "The count and types of Input/Output interfaces (e.g., USB, OTHER, SERIAL, ETHERNET, USB 3.0, USB 2.0, DISPLAY, PCIE, SATA, GPIO, USB 3.2, OTHER_BUS, AUDIO, USB 3.1, SATA 3.0, USB 1.0, SATA 6.0, SATA 2.0, USB 4.0, PCIE 4, PCIE 2.0, SATA 1, USB 6, PCIE 3.0, SATA 2, SATA 1.0)",
    "wireless": "Wireless capabilities (e.g., WI-FI, BLUETOOTH, OTHER, WI-FI 5, BLUETOOTH 5+, WI-FI 6, 4G/LTE, CELLULAR, 5G, BLUETOOTH 4, GPS, ZIGBEE, 3G, LORA, NFC)",
    "operating_system_bsp": "Supported operating systems or Board Support Packages (e.g., LINUX, OTHER, WINDOWS, WINDOWS 10, ANDROID, WINDOWS EMBEDDED, WINDOWS IOT, VXWORKS, UBUNTU, QNX, YOCTO LINUX, RASPBERRY PI OS, WINDOWS SERVER, WINDOWS 11, DEBIAN, FEDORA, RED HAT ENTERPRISE LINUX)",
    "operating_temperature_max": "The maximum operating temperature (e.g., 60°C, 85°C, 70°C, 50°C, 40°C, 75°C, 125°C, 55°C, 105°C, 35°C, 100°C, 85℃, 83°C, +80℃, 65°C, 90°C, 45°C, 80°C, 85OC, 95°C, 70℃)",
    "operating_temperature_min": "The minimum operating temperature (e.g., -40°C, 0°C, -20°C, -25°C, -30°C, -10°C, -40℃, 5°C, -40OC, -20℃)",
    "certifications": "Certifications and compliance standards met (e.g., CE, ROHS, OTHER, FCC, UL, FCC CLASS B, CCC, BSMI, FCC CLASS A, MIL-STD-810, CB, REACH, ISO, EN 50155, IEC 60068, RCM, IC, VCCI, KC, TELEC, WEEE)",
    "price": "The cost of the product.",
    "stock_availability": "Current stock status (e.g., In Stock, Out of Stock).",
    "lead_time": "Time required to fulfill an order.",
    # "short_summary": "A concise description highlighting key features.",
    # "full_summary": "A detailed overview of the product's capabilities.",
    # "full_product_description": "An in-depth description including specifications.",
    # "target_applications": "Intended use cases or industries for the product.",
}
