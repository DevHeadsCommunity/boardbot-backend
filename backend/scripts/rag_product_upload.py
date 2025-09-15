#!/usr/bin/env python3
import os
import sys
import math
import time
import json
import logging
from typing import Dict, Any, Iterable, List

# --- dotenv: load .env early, before reading env vars ---
try:
    from dotenv import load_dotenv, find_dotenv
    _env_path = find_dotenv(usecwd=True)  # finds .env, .env.local, etc.
    load_dotenv(_env_path, override=False)
    _loaded_env = bool(_env_path)
except Exception:
    _loaded_env = False

import requests
import mysql.connector

# ---------------------------
# Config
# ---------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("batch_raw_sender")
if _loaded_env:
    log.info("Loaded environment from: %s", _env_path)
else:
    log.info("No .env file found; using process environment only.")

# API
BASE_API_URL = os.environ.get("BASE_API_URL", "http://localhost:8000")
BATCH_ENDPOINT = os.environ.get("BATCH_ENDPOINT_PATH", "/api/products/batch/raw")
API_URL = f"{BASE_API_URL.rstrip('/')}{BATCH_ENDPOINT}"

# Auth (optional)
API_AUTH_HEADER = os.environ.get("API_AUTH_HEADER_NAME", "Authorization")
API_AUTH_VALUE = os.environ.get("API_AUTH_HEADER_VALUE")  # e.g., "Bearer abc123"

# Controls (payload knobs)
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "5"))
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.7"))
MAX_MISSING_FEATURE_ATTEMPTS = int(os.environ.get("MAX_MISSING_FEATURE_ATTEMPTS", "0"))
MAX_LOW_CONFIDENCE_ATTEMPTS = int(os.environ.get("MAX_LOW_CONFIDENCE_ATTEMPTS", "0"))
MAX_NO_PROGRESS_ATTEMPTS = int(os.environ.get("MAX_NO_PROGRESS_ATTEMPTS", "0"))

# Chunking for API calls: send 50 products per HTTP POST
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "50"))

# MySQL
DB_HOST = os.environ.get("DATABASE_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DATABASE_PORT", "3306"))
DB_USER = os.environ.get("DATABASE_USER", "root")
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
DB_NAME = os.environ.get("DATABASE_NAME", "products_db")

SQL = """
SELECT
    id AS product_id,
    name,
    manufacturer,
    category,
    sub_category,
    description,
    image_url,
    permalink
FROM products LIMIT 10
"""

# ---------------------------
# Helpers
# ---------------------------
def chunked(items: List[Dict[str, Any]], n: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), n):
        yield items[i : i + n]

def nv(v: Any) -> str:
    """Normalize None/empty to 'Not available' string, else str()."""
    if v is None:
        return "Not available"
    s = str(v).strip()
    return s if s else "Not available"

def build_raw_data(row: Dict[str, Any]) -> str:
    """
    Compose a single text blob that includes:
    - manufacturer, category, sub_category, permalink, image_url
    - description (verbatim if present)
    """
    parts = [
        f"Manufacturer: {nv(row.get('manufacturer'))}",
        f"Category: {nv(row.get('category'))}",
        f"Sub-Category: {nv(row.get('sub_category'))}",
        f"Permalink: {nv(row.get('permalink'))}",
        f"Image URL: {nv(row.get('image_url'))}",
        "----- DESCRIPTION START -----",
        nv(row.get("description")),
        "----- DESCRIPTION END -----",
    ]
    return "\n".join(parts)

def fetch_rows() -> List[Dict[str, Any]]:
    db = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        port=DB_PORT,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(SQL)
        rows = list(cursor.fetchall())
        log.info("Fetched %d products from SQL", len(rows))
        return rows
    finally:
        try:
            db.close()
        except Exception:
            pass

def send_chunk(chunk_rows: List[Dict[str, Any]]) -> requests.Response:
    # Build the request payload
    products_payload = []
    for r in chunk_rows:
        products_payload.append(
            {
                "product_id": str(r["product_id"]),
                "raw_data": build_raw_data(r),
            }
        )

    payload = {
        "products": products_payload,
        "batch_size": BATCH_SIZE,
        "max_missing_feature_attempts": MAX_MISSING_FEATURE_ATTEMPTS,
        "max_low_confidence_attempts": MAX_LOW_CONFIDENCE_ATTEMPTS,
        "max_no_progress_attempts": MAX_NO_PROGRESS_ATTEMPTS,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
    }

    headers = {"Content-Type": "application/json"}
    if API_AUTH_VALUE:
        headers[API_AUTH_HEADER] = API_AUTH_VALUE

    resp = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=120)
    return resp

# ---------------------------
# Main
# ---------------------------
def main():
    rows = fetch_rows()
    if not rows:
        log.warning("No products found. Exiting.")
        return

    total = len(rows)
    num_chunks = math.ceil(total / CHUNK_SIZE)
    log.info(
        "Sending %d products in %d chunk(s) of %d each to %s",
        total, num_chunks, CHUNK_SIZE, API_URL
    )

    sent = 0
    failures = 0

    for idx, chunk_rows in enumerate(chunked(rows, CHUNK_SIZE), start=1):
        try:
            resp = send_chunk(chunk_rows)
            ok = 200 <= resp.status_code < 300
            msg = resp.text[:500].replace("\n", " ")
            if ok:
                sent += len(chunk_rows)
                log.info("Chunk %d/%d OK (%d items). Response: %s", idx, num_chunks, len(chunk_rows), msg)
            else:
                failures += len(chunk_rows)
                log.error(
                    "Chunk %d/%d FAILED (%d items). HTTP %s. Response: %s",
                    idx, num_chunks, len(chunk_rows), resp.status_code, msg
                )
        except requests.RequestException as e:
            failures += len(chunk_rows)
            log.exception(
                "Chunk %d/%d EXCEPTION (%d items): %s",
                idx, num_chunks, len(chunk_rows), e
            )

        time.sleep(float(os.environ.get("INTER_CHUNK_SLEEP_SEC", "0.2")))

    log.info("Done. Sent=%d, Failures=%d", sent, failures)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Interrupted.")
        sys.exit(130)
