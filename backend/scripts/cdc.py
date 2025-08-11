#!/usr/bin/env python3
import asyncio
import logging
import os, sys
from urllib.parse import urlparse

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    WriteRowsEvent,
    UpdateRowsEvent,
    DeleteRowsEvent,
)
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))
from services.weaviate_service import WeaviateService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cdc_sync")

async def run_cdc():
    # 1) Connect to Weaviate
    svc = WeaviateService(
        openai_key=os.environ["OPENAI_API_KEY"],
        weaviate_url=os.environ["WEAVIATE_URL"],
        product_data_preprocessor=None,
    )
    await svc.connect()

    conn_settings = {
        "host":   os.environ["DATABASE_HOST"],
        "port":   int(os.environ["DATABASE_PORT"]),
        "user":   os.environ["DATABASE_USER"],
        "passwd": os.environ["DATABASE_PASSWORD"],
    }
    schema_name = os.environ["DATABASE_NAME"]

    # 3) Start tailing the binlog
    stream = BinLogStreamReader(
        connection_settings=conn_settings,
        server_id=123,                    # any unique integer
        only_events=[WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent],
        blocking=True,
        resume_stream=True,               # remember file/pos in .binlog_position
        only_schemas=[schema_name],
        only_tables=["products"],
    )

    logger.info("CDC: listening for product changes…")
    for event in stream:
        for row in event.rows:
            if isinstance(event, WriteRowsEvent):
                data, action = row["values"], "insert"
            elif isinstance(event, UpdateRowsEvent):
                data, action = row["after_values"], "update"
            elif isinstance(event, DeleteRowsEvent):
                data, action = row["values"], "delete"
            else:
                continue

            obj = {
                "product_id":   str(data["id"]),
                "name":         data.get("name"),
                "manufacturer": data.get("manufacturer"),
                "category":     data.get("category"),
                "subcategory":  data.get("subcategory"),
                "description":  data.get("description"),
                "image_url":    data.get("image_url"),
            }

            try:
                if action in ("insert", "update"):
                    # Upsert by product_id
                    await svc.wi.client.insert_object(
                        collection_name="Product",
                        data=obj,
                        unique_properties=["product_id"],
                    )
                    logger.info(f"{action.upper()}: {obj['product_id']}")
                else:
                    # Delete by UUID == product_id
                    await svc.wi.client.delete_object(
                        collection_name="Product",
                        uuid=str(data["id"])
                    )
                    logger.info(f"DELETE: {obj['product_id']}")
            except Exception as e:
                logger.error(f"Error on {action} {obj['product_id']}: {e}")

    stream.close()
    await svc.close_connection()

if __name__ == "__main__":
    asyncio.run(run_cdc())
