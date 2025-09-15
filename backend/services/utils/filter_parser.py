from enum import Enum
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from weaviate.classes.query import Filter
import re


class ValueTypes(Enum):
    MEMORY = "memory"
    STORAGE = "storage"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    PROCESSOR_CORES = "processor_cores"
    POWER = "power"


class FeatureValues:
    # Memory and Storage sizes (in GB)
    MEMORY_STORAGE_VALUES = {
        0.1,
        0.2,
        0.5,
        1,
        1.0,
        2,
        2.0,
        4,
        4.0,
        8,
        8.0,
        16,
        16.0,
        32,
        32.0,
        64,
        64.0,
        128,
        128.0,
        256,
        256.0,
        320,
        320.0,
        512,
        512.0,
        1024,
        1024.0,
    }

    # Voltage values (in V)
    VOLTAGE_VALUES = {
        1,
        1.0,
        2,
        2.0,
        3,
        3.0,
        4,
        4.0,
        5,
        5.0,
        7,
        7.0,
        8,
        8.0,
        9,
        9.0,
        12,
        12.0,
        19,
        19.0,
        24,
        24.0,
        30,
        30.0,
        36,
        36.0,
        48,
        48.0,
    }

    # Temperature values (in °C)
    TEMPERATURE_VALUES = {
        -40,
        -40.0,
        -30,
        -30.0,
        -25,
        -25.0,
        -20,
        -20.0,
        -10,
        -10.0,
        0,
        0.0,
        5,
        5.0,
        35,
        35.0,
        40,
        40.0,
        45,
        45.0,
        50,
        50.0,
        55,
        55.0,
        60,
        60.0,
        65,
        65.0,
        70,
        70.0,
        75,
        75.0,
        80,
        80.0,
        85,
        85.0,
        90,
        90.0,
        95,
        95.0,
        100,
        100.0,
        105,
        105.0,
        125,
        125.0,
    }

    # Processor core counts
    PROCESSOR_CORES = {
        1,
        1.0,
        2,
        2.0,
        3,
        3.0,
        4,
        4.0,
        5,
        5.0,
        6,
        6.0,
        8,
        8.0,
        9,
        9.0,
        10,
        10.0,
        12,
        12.0,
        14,
        14.0,
        16,
        16.0,
        20,
        20.0,
        24,
        24.0,
        32,
        32.0,
        64,
        64.0,
        80,
        80.0,
        128,
        128.0,
    }

    # TDP power values (in W)
    POWER_VALUES = {
        1,
        1.0,
        2,
        2.0,
        5,
        5.0,
        6,
        6.0,
        7,
        7.0,
        8,
        8.0,
        9,
        9.0,
        10,
        10.0,
        12,
        12.0,
        13,
        13.0,
        15,
        15.0,
        17,
        17.0,
        19,
        19.0,
        25,
        25.0,
        28,
        28.0,
        31,
        31.0,
        35,
        35.0,
        45,
        45.0,
        65,
        65.0,
        70,
        70.0,
        77,
        77.0,
        80,
        80.0,
        95,
        95.0,
        100,
        100.0,
        105,
        105.0,
        125,
        125.0,
        160,
        160.0,
        205,
        205.0,
    }

    # Feature type mapping
    FEATURE_TYPE_MAP = {
        "memory": ValueTypes.MEMORY,
        "onboard_storage": ValueTypes.STORAGE,
        "input_voltage": ValueTypes.VOLTAGE,
        "operating_temperature_max": ValueTypes.TEMPERATURE,
        "operating_temperature_min": ValueTypes.TEMPERATURE,
        "processor_core_count": ValueTypes.PROCESSOR_CORES,
        "processor_tdp": ValueTypes.POWER,
    }

    @classmethod
    def _get_nearest_valid_values(cls, value: float, valid_set: Set[float], operator: str) -> List[float]:
        """Get nearest valid values based on operator."""
        if operator == ">=":
            return sorted([v for v in valid_set if v >= value])
        else:  # "<="
            return sorted([v for v in valid_set if v <= value])

    @classmethod
    def _format_numeric_values(cls, values: List[float]) -> List[str]:
        """Format numeric values to include both integer and float representations when applicable."""
        result = []
        for v in values:
            v_float = float(v)
            if v_float.is_integer():
                result.extend([f"{int(v_float)}", f"{v_float:.1f}"])
            else:
                result.append(f"{v_float}")
        return result

    @classmethod
    def get_valid_values(cls, feature_name: str, value: str) -> List[str]:
        """Get valid values for a given feature based on its type."""
        feature_type = cls.FEATURE_TYPE_MAP.get(feature_name)
        if not feature_type:
            return [value]

        operator = value[:2]  # '>=' or '<='
        try:
            num_value = float(value[2:])
        except ValueError:
            return [value]

        # Map feature types to their corresponding value sets
        value_set_map = {
            ValueTypes.MEMORY: cls.MEMORY_STORAGE_VALUES,
            ValueTypes.STORAGE: cls.MEMORY_STORAGE_VALUES,
            ValueTypes.VOLTAGE: cls.VOLTAGE_VALUES,
            ValueTypes.TEMPERATURE: cls.TEMPERATURE_VALUES,
            ValueTypes.PROCESSOR_CORES: cls.PROCESSOR_CORES,
            ValueTypes.POWER: cls.POWER_VALUES,
        }

        valid_set = value_set_map.get(feature_type)
        if valid_set is None:
            return [value]

        valid_values = cls._get_nearest_valid_values(num_value, valid_set, operator)
        return cls._format_numeric_values(valid_values)


def _needs_boundary(tok: str) -> bool:
    """
    Decide which tokens require strict boundaries.
    Use a broad rule: alnum-only tokens (e.g., 5G, DDR4, USB, RJ45) are ambiguous.
    """
    return bool(re.fullmatch(r"[A-Z0-9]+", tok))

def _boundary_or_groups_for_token(tok: str) -> List[List[str]]:
    """
    Build two OR-groups:
      - preGroup: token appears after an allowed pre-boundary
      - postGroup: token appears before an allowed post-boundary
    We combine them later with AND to force both sides.
    """
    return [f"* {tok} *", f"*({tok})*", f"*[{tok}]*"]

FAMILY_PATTERNS = [
    ("CPU",        re.compile(r"(processor|cpu|core_count|architecture|tdp|manufacturer)", re.I)),
    ("MEMORY",     re.compile(r"(memory|ram|ddr\d?)", re.I)),
    ("STORAGE",    re.compile(r"(onboard_storage|storage|disk|drive|ssd|hdd|nvme|emmc|flash)", re.I)),
    ("IO",         re.compile(r"(io_count|usb|hdmi|ethernet|gpio|uart|i2c|spi|m\.?2)", re.I)),
    ("POWER",      re.compile(r"(input_voltage|voltage|vdc|vin|watt|power|tdp)", re.I)),
    ("THERMAL",    re.compile(r"(operating_temperature|min|max|°c|celsius|ambient|thermal)", re.I)),
    ("WIRELESS",   re.compile(r"(wireless|wifi|wi-?fi|bt|bluetooth|lte|5g)", re.I)),
    ("OS",         re.compile(r"(operating_system|bsp|os|linux|windows|yocto|ubuntu|rtos)", re.I)),
    ("CERT",       re.compile(r"(certifications?|ce|fcc|ul|rohs|reach|emc)", re.I)),
    ("COMMERCIAL", re.compile(r"(price|stock|availability|lead_time|moq)", re.I)),
    ("FORM",       re.compile(r"(form_factor|mini-?itx|atx|micro-?atx|nano-?itx|sodimm)", re.I)),
]

FAMILY_ANCHORS = {
    "CPU":        {"CPU","PROCESSOR","CORE","ARCHITECTURE","TDP","INTEL","AMD","NVIDIA","ARM"},
    "MEMORY":     {"RAM","MEMORY","DRAM","DDR3","DDR4","DDR5","LPDDR4","LPDDR5"},
    "STORAGE":    {"STORAGE","SSD","HDD","NVME","EMMC","FLASH","SATA","M.2"},
    "IO":         {"USB","HDMI","ETHERNET","GPIO","UART","I2C","SPI","PCIE","DISPLAYPORT"},
    "POWER":      {"VOLTAGE","V","WATT","W","POWER","INPUT"},
    "THERMAL":    {"OPERATING","TEMPERATURE","°C","CELSIUS","MIN","MAX"},
    "WIRELESS":   {"WIFI","WI-FI","BLUETOOTH","BT","LTE","5G","WIRELESS"},
    "OS":         {"OS","OPERATING","LINUX","YOCTO","UBUNTU","WINDOWS","BSP"},
    "CERT":       {"CE","FCC","UL","ROHS","REACH","CERTIFIED","CERTIFICATION"},
    "COMMERCIAL": {"PRICE","STOCK","AVAILABILITY","LEAD","TIME"},
    "FORM":       {"FORM","FACTOR","ITX","ATX","SODIMM","COM-EXPRESS"},
}

def _family_for_attr(attr: str) -> Optional[str]:
    for fam, pat in FAMILY_PATTERNS:
        if pat.search(attr):
            return fam
    return None

# --- Tokenization & pattern helpers ------------------------------------------
def _toks_upper(val: str) -> List[str]:
    return re.findall(r"[A-Z0-9]+(?:\.[0-9]+)?", val.upper())

def _num_alts(tok: str) -> List[str]:
    # 32.0 -> ["32.0","32"]
    if re.fullmatch(r"\d+\.\d+", tok):
        return [tok, tok[:-2]]
    return [tok]

UNIT_NORMALIZATION = {
    "G": "GB", "GB": "GB", "GIGABYTE": "GB", "GIGABYTES": "GB",
    "T": "TB", "TB": "TB", "TERABYTE": "TB", "TERABYTES": "TB",
    "MHZ": "MHZ", "GHZ": "GHZ",
    "W": "W", "WATT": "W", "WATTS": "W",
    "V": "V", "VDC": "V",
}

def _norm_unit(tok: str) -> str:
    return UNIT_NORMALIZATION.get(tok.upper(), tok.upper())

def _capacity_or_group(tokens: List[str]) -> Optional[List[str]]:
    for i, tok in enumerate(tokens):
        u = _norm_unit(tok)
        if u in {"GB","TB","MHZ","GHZ","W","V"} and i > 0 and re.fullmatch(r"\d+(?:\.\d+)?", tokens[i-1]):
            num = tokens[i-1]
            alts = set()
            for n in _num_alts(num):
                alts.update({f"*{n}{u}*", f"*{n}*{u}*"})
                if u in {"GB","TB"}:  # permit “G/T” variants
                    short = "G" if u == "GB" else "T"
                    alts.update({f"*{n}{short}*", f"*{n}*{short}*"})
            return list(alts)
    return None

def _slash_or_groups(text: str) -> List[List[str]]:
    groups = []
    U = text.upper()
    for m in re.finditer(r"\b([A-Z]+)(\d+)\s*/\s*(?:\1)?(\d+)\b", U):
        pre, a, b = m.group(1), m.group(2), m.group(3)
        groups.append([f"*{pre}{a}*", f"*{pre}{b}*"])
    return groups

def _fallback_groups(tokens: List[str]) -> List[List[str]]:
    groups: List[List[str]] = []
    for tok in tokens:
        if len(tok) == 1:
            continue
        if _needs_boundary(tok):
            grps = _boundary_or_groups_for_token(tok)
            groups.append(grps)
        else:
            groups.append([f"*{alt}*" for alt in _num_alts(tok)])
    return groups

def _anchor_group_from_family(family: Optional[str]) -> Optional[List[str]]:
    if not family: 
        return None
    return [f"*{a}*" for a in FAMILY_ANCHORS.get(family, set())]


def get_groups_from_val(key: str, value: str):
    fam = _family_for_attr(key)
    tokens = _toks_upper(value)

    groups: List[List[str]] = []

    # quantities like 32GB / 65W / 12V
    cap = _capacity_or_group(tokens)
    if cap:
        groups.append(cap)

    # variants like DDR3/4
    groups.extend(_slash_or_groups(value))

    # family anchors (generic, not per-attribute)
    if cap is not None and len(tokens) <= 2:
        fam_anchors = _anchor_group_from_family(fam)
        if fam_anchors:
            groups.append(fam_anchors)

    # if nothing structured, fall back to tokens
    if not groups:
        groups = _fallback_groups(tokens)
        
    return groups

class QueryBuilder:
    def __init__(self):
        # Cache for parsed values from attribute descriptions
        self._valid_values_cache: Dict[str, Dict[str, Set[Union[int, float]]]] = {}

    def build_weaviate_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        """
        Converts dictionary filters into Weaviate Filter objects with generalized handling.
        """
        if not filters:
            return None

        filter_conditions = []
        description_conditions = []

        for key, value in filters.items():
            if isinstance(value, str):
                if value.startswith(">=") or value.startswith("<="):
                    # Extract unit if present
                    numeric_part, unit = self._split_value_and_unit(value[2:])
                    if numeric_part:
                        # Get possible numeric values based on field examples
                        numeric_values = self._create_numeric_values(key, f"{value[:2]}{numeric_part}")
                        if numeric_values:
                            # Add back the unit to each value if it exists
                            possible_values = [f"{v}{unit}" for v in numeric_values] if unit else numeric_values
                            filter_conditions.append(Filter.by_property(key).contains_any(possible_values))
                else:
                    # Handle string values
                    if key == "description":
                        filter_conditions.append(Filter.by_property(key).like(f"*{value}*"))
                    else:
                        filter_conditions.append(Filter.by_property(key).contains_any([value.upper()]))
                        if key == "form_factor":
                            filter_conditions.append(Filter.by_property("category").contains_any([value.upper()]))
            elif isinstance(value, list):
                # For array fields
                upper_values = [v.upper() for v in value]
                filter_conditions.append(Filter.by_property(key).contains_any(upper_values))
            else:
                # For any other types of values
                filter_conditions.append(Filter.by_property(key).equal(str(value)))
        if description_conditions.__len__() > 0:
            filter_conditions.append(Filter.all_of(description_conditions))

        return Filter.all_of(filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]

    def _split_value_and_unit(self, value: str) -> Tuple[str, str]:
        """Split a value into its numeric part and unit."""
        # Match number (including decimals) followed by any non-numeric characters
        match = re.match(r"^([-+]?\d*\.?\d+)([A-Za-z°℃\s]*)?$", value.strip())
        if match:
            return match.group(1), (match.group(2) or "").strip()
        return value, ""

    def _get_valid_values(self, field: str) -> Dict[str, Set[Union[int, float]]]:
        """
        Extracts and categorizes valid numeric values from attribute descriptions.
        Returns a dict with 'singles' and 'ranges' for the field.
        """
        if field in self._valid_values_cache:
            return self._valid_values_cache[field]

        examples = self._get_example_values(field)
        result = {"singles": set(), "ranges": set()}

        for example in examples:
            numeric_part, _ = self._split_value_and_unit(example)

            # Handle range format (e.g., "1-4")
            if "-" in numeric_part:
                range_nums = self._extract_range_numbers(numeric_part)
                if range_nums:
                    # Add both ends of the range
                    for num in range_nums:
                        if isinstance(num, float) and num.is_integer():
                            result["ranges"].add(int(num))
                        else:
                            result["ranges"].add(num)
            else:
                # Handle single number
                single_num = self._extract_number(numeric_part)
                if single_num is not None:
                    if isinstance(single_num, float) and single_num.is_integer():
                        result["singles"].add(int(single_num))
                    else:
                        result["singles"].add(single_num)

        self._valid_values_cache[field] = result
        return result

    def _create_numeric_values(self, field: str, value: str) -> List[str]:
        """Creates list of possible numeric values based on comparison operator and field type."""
        return FeatureValues.get_valid_values(field, value)

    def _get_example_values(self, field: str) -> List[str]:
        """Extract example values from attribute descriptions."""
        from weaviate_interface.models.product import attribute_descriptions

        desc = attribute_descriptions.get(field, "")
        if not desc or "e.g.," not in desc:
            return []

        # Extract examples between parentheses
        match = re.search(r"\((.*?)\)", desc)
        if not match:
            return []

        # Split examples and clean them
        examples = [ex.strip() for ex in match.group(1).split(",")]
        return [ex for ex in examples if ex and not ex.startswith("e.g")]

    def _extract_number(self, text: str) -> Optional[Union[int, float]]:
        """Extract the first number from a text string."""
        match = re.search(r"([-+]?\d*\.?\d+)", text)
        if match:
            try:
                value = float(match.group(1))
                return int(value) if value.is_integer() else value
            except ValueError:
                return None
        return None

    def _extract_range_numbers(self, text: str) -> Optional[Tuple[Union[int, float], Union[int, float]]]:
        """Extract two numbers from a range format."""
        # First split by any non-numeric characters that might separate the range
        numeric_part, _ = self._split_value_and_unit(text)
        numbers = re.findall(r"([-+]?\d*\.?\d+)", numeric_part)
        if len(numbers) >= 2:
            try:
                values = []
                for num in numbers[:2]:
                    val = float(num)
                    values.append(int(val) if val.is_integer() else val)
                return tuple(values)  # type: ignore
            except ValueError:
                pass
        return None
