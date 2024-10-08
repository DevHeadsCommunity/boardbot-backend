import pytest
from feature_extraction.utils.feature_utils import (
    get_missing_features,
    get_low_confidence_features,
    filter_features_by_confidence,
    build_missing_features_structure,
)


@pytest.fixture
def sample_extracted_features():
    return {
        "name": {"value": "SLOT SBC PASSIVE BACKPLANES", "confidence": 0.9},
        "processor": {
            "manufacturer": {"value": "INTEL", "confidence": 0.9},
            "model": {"value": "XEON X, CORE, PENTIUM G", "confidence": 0.8},
            "speed": {"value": "2.6 GHz - 3.6 GHz", "confidence": 0.8},
            "max_speed": {"value": "Not available", "confidence": 0},
            "core_count": {"value": "Not available", "confidence": 0},
        },
        "storage": {
            "storage_type": {"value": "SATA II", "confidence": 0.9},
            "storage_capacity": {"value": "Not available", "confidence": 0},
        },
    }


# @pytest.fixture
# def sample_extracted_features():
#     return (
#         {
#             "name": {"value": "ASMB-GAE", "confidence": 0.9},
#             "manufacturer": {"value": "ADVANTECH", "confidence": 0.9},
#             "is_prototype": {"value": False, "confidence": 1},
#             "form_factor": {"value": "ATX", "confidence": 0.9},
#             "processor": {
#                 "manufacturer": {"value": "INTEL", "confidence": 0.9},
#                 "model": {"value": "XEON E, E V, 2ND 3RD GENERATION CORE, PENTIUM", "confidence": 0.9},
#                 "speed": "Not Available",
#                 "max_speed": "Not Available",
#                 "core_count": "Not Available",
#                 "thread_count": "Not Available",
#                 "architecture": "Not Available",
#                 "features": "Not Available",
#                 "tdp": {"value": "160W", "confidence": 0.9},
#             },
#             "memory": {
#                 "ram_type": {"value": "DDR3", "confidence": 0.9},
#                 "ram_speed": {"value": "1600 MHz", "confidence": 0.9},
#                 "ram_capacity": {"value": "Up to 32 GB", "confidence": 0.9},
#                 "ram_configuration": {"value": "8 DDR4 DIMM", "confidence": 0.9},
#             },
#             "storage": {
#                 "storage_type": {"value": "SATA II, SATA III", "confidence": 0.9},
#                 "storage_capacity": {"value": "8 SATA3 6 Gb/s ports", "confidence": 0.9},
#             },
#             "gpu_model": {"value": "INTEL HD GRAPHICS", "confidence": 0.9},
#             "interfaces": {
#                 "display_outputs": {"value": ["DVI-D", "VGA"], "confidence": 0.9},
#                 "ethernet_ports": {"value": ["4x GbE LAN"], "confidence": 0.9},
#                 "usb_ports": {"value": ["4x USB 3.0"], "confidence": 0.9},
#                 "serial_ports": {"value": ["1x RS-232"], "confidence": 0.9},
#                 "pcie_slots": {"value": ["2x PCIe x16 Gen 3", "2x PCIe x1 Gen 2"], "confidence": 0.9},
#                 "storage_interfaces": {"value": ["SATA II", "SATA III"], "confidence": 0.9},
#                 "other_io": {"value": ["LPT", "Audio"], "confidence": 0.9},
#             },
#             "wireless_connectivity": "Not Available",
#             "operating_system_support": {"value": ["Windows"], "confidence": 0.9},
#             "power": {"power_input": "Not Available", "power_consumption": "Not Available"},
#             "environmental_specifications": {
#                 "cooling_method": {"value": "CPU cooler", "confidence": 0.9},
#                 "operating_temperature": {"value": "0°C to 60°C", "confidence": 0.9},
#                 "storage_temperature": "Not Available",
#                 "operating_humidity": {"value": "Non-condensing", "confidence": 0.9},
#                 "shock_resistance": "Not Available",
#                 "vibration_resistance": "Not Available",
#             },
#             "ip_rating": "Not Available",
#             "certifications": "Not Available",
#             "target_applications": "Not Available",
#             "short_summary": {
#                 "value": "The ASMB-GAE is an ATX form factor server board from Advantech, featuring Intel Xeon E, E v, 2nd 3rd Generation Core, Pentium processors, DDR3 memory, and multiple I/O options.",
#                 "confidence": 0.9,
#             },
#             "full_summary": {
#                 "value": "The ASMB-GAE is a high-performance server board in ATX form factor, designed by Advantech. It supports Intel Xeon E, E v, 2nd 3rd Generation Core, Pentium processors, and up to 32GB of DDR3 memory. The board offers multiple I/O options including 4x GbE LAN, 4x USB 3.0, and various PCIe slots. It is suitable for a wide range of server applications.",
#                 "confidence": 0.9,
#             },
#             "full_product_description": {
#                 "value": "The ASMB-GAE from Advantech is a server board in ATX form factor. It is designed to support Intel Xeon E, E v, 2nd 3rd Generation Core, Pentium processors, providing high performance for server applications. The board supports up to 32GB of DDR3 memory, and offers multiple I/O options including 4x GbE LAN, 4x USB 3.0, and various PCIe slots. It also features Intel HD Graphics for visual applications. The board is designed for Windows operating system.",
#                 "confidence": 0.9,
#             },
#         },
#     )


def test_get_missing_features(sample_extracted_features):
    missing = get_missing_features(sample_extracted_features)
    assert set(missing) == {"processor.max_speed", "processor.core_count", "storage.storage_capacity"}


def test_get_low_confidence_features(sample_extracted_features):
    low_confidence = get_low_confidence_features(sample_extracted_features, 0.85)
    assert set(low_confidence) == {"processor.model", "processor.speed"}


def test_filter_features_by_confidence(sample_extracted_features):
    filtered = filter_features_by_confidence(sample_extracted_features, 0.85)
    assert filtered == {
        "name": "SLOT SBC PASSIVE BACKPLANES",
        "processor": {
            "manufacturer": "INTEL",
            "model": "Not Available",
            "speed": "Not Available",
            "max_speed": "Not Available",
            "core_count": "Not Available",
        },
        "storage": {"storage_type": "SATA II", "storage_capacity": "Not Available"},
    }


def test_build_missing_features_structure():
    missing_features = [
        "processor.core_count",
        "processor.thread_count",
        "processor.architecture",
        "processor.tdp",
        "memory.ram_speed",
        "memory.ram_capacity",
        "storage.storage_capacity",
        "wireless_connectivity",
        "power.power_consumption",
        "environmental_specifications.storage_temperature",
        "environmental_specifications.shock_resistance",
        "environmental_specifications.vibration_resistance",
        "ip_rating",
        "certifications",
        "target_applications",
    ]

    missing_features_structure = build_missing_features_structure(missing_features)
    assert missing_features_structure == {
        "processor": {
            "core_count": "Not Available",
            "thread_count": "Not Available",
            "architecture": "Not Available",
            "tdp": "Not Available",
        },
        "memory": {
            "ram_speed": "Not Available",
            "ram_capacity": "Not Available",
        },
        "storage": {
            "storage_capacity": "Not Available",
        },
        "wireless_connectivity": "Not Available",
        "power": {
            "power_consumption": "Not Available",
        },
        "environmental_specifications": {
            "storage_temperature": "Not Available",
            "shock_resistance": "Not Available",
            "vibration_resistance": "Not Available",
        },
        "ip_rating": "Not Available",
        "certifications": "Not Available",
        "target_applications": "Not Available",
    }


if __name__ == "__main__":
    pytest.main([__file__])
