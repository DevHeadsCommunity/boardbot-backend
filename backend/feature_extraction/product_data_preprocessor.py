import re
import ast
import logging
import tiktoken
import pandas as pd
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)


class ProductDataProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            length_function=self.tiktoken_len,
        )

    def tiktoken_len(self, text):
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        return len(tokens)

    def load_and_preprocess_data(self, csv_file_path: str) -> List[Dict[str, Any]]:
        products = pd.read_csv(csv_file_path)
        logger.info(f"Loaded {len(products)} products from CSV.")

        products_data = products.to_dict(orient="records")
        processed_data = []

        for item in products_data:
            processed_item = self.preprocess_item(item)
            processed_data.append(processed_item)

        return processed_data

    def preprocess_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        self._process_list_fields(item)
        self._process_evaluation_or_commercialization(item)
        self._process_processor_core_count(item)
        self._standardize_units(item)
        self._replace_nan_with_none(item)
        return item

    def _process_list_fields(self, item: Dict[str, Any]) -> None:
        list_fields = [
            "operating_system_bsp",
            "certifications",
            "target_applications",
            "duplicate_ids",
            "io_count",
            "wireless",
        ]
        for key in list_fields:
            if isinstance(item.get(key), str):
                try:
                    item[key] = ast.literal_eval(item[key])
                except:
                    item[key] = [item[key]] if item[key] else None
            elif self.is_na(item.get(key)):
                item[key] = None

    def _process_evaluation_or_commercialization(self, item: Dict[str, Any]) -> None:
        if "evaluation_or_commercialization" in item:
            value = item["evaluation_or_commercialization"]
            if isinstance(value, str):
                value = value.strip().lower()
                if value == "true":
                    item["evaluation_or_commercialization"] = "Evaluation"
                elif value == "false":
                    item["evaluation_or_commercialization"] = "Commercial"
                else:
                    item["evaluation_or_commercialization"] = None
            elif isinstance(value, bool):
                item["evaluation_or_commercialization"] = "Evaluation" if value else "Commercial"
            else:
                item["evaluation_or_commercialization"] = None

    def _process_processor_core_count(self, item: Dict[str, Any]) -> None:
        if "processor_core_count" in item:
            value = item["processor_core_count"]
            if not self.is_na(value):
                numeric_value = re.search(r"\d+", str(value))
                if numeric_value:
                    item["processor_core_count"] = str(int(numeric_value.group()))
                else:
                    item["processor_core_count"] = None
            else:
                item["processor_core_count"] = None

    def _standardize_units(self, item: Dict[str, Any]) -> None:
        unit_fields = ["memory", "processor_tdp", "operating_temperature_max", "operating_temperature_min"]
        for key in unit_fields:
            value = item.get(key)
            if not self.is_na(value) and isinstance(value, str):
                item[key] = self.standardize_units(value, key)
            else:
                item[key] = None

    def _replace_nan_with_none(self, item: Dict[str, Any]) -> None:
        for key, value in item.items():
            if self.is_na(value):
                item[key] = None

    def is_na(self, value):
        if pd.api.types.is_scalar(value):
            return pd.isna(value)
        else:
            return pd.isna(value).any()

    def standardize_units(self, value: str, field_name: str) -> str:
        # Implement unit standardization logic based on field_name
        # This is a placeholder implementation
        return value

    def create_chunks(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)
