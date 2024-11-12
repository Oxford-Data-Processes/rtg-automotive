import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, create_model

PROJECT = "rtg-automotive"


def load_schemas() -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    table_schemas_path = os.path.join(current_dir, "table_schemas.json")

    with open(table_schemas_path) as f:
        return json.load(f)


def map_schema(schema: List[Dict[str, str]]) -> Dict[str, Any]:
    type_mapping = {
        "integer": int,
        "string": str,
        "double": float,
        "boolean": bool,
    }
    mapped_schema = {}
    for item in schema:
        name = item["name"]
        mapped_schema[name] = (type_mapping[item["type"]], ...)
    return mapped_schema


schemas = load_schemas()

RtgAutomotiveSupplierStockModel = create_model(
    "RtgAutomotiveSupplierStockModel",
    **map_schema(schemas["rtg_automotive_supplier_stock"]),
)
RtgAutomotiveStoreModel = create_model(
    "RtgAutomotiveStoreModel", **map_schema(schemas["rtg_automotive_store"])
)
