import json
import logging
import os
import sys
from typing import List, Optional

from aws_utils import iam, rds
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.sqlalchemy_models import Base, create_model_class  # type: ignore


def create_database_session() -> sessionmaker:
    rds_handler = rds.RDSHandler()
    rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
    rds_endpoint = rds_instance["Endpoint"]
    engine = create_engine(
        f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
    )
    return sessionmaker(bind=engine)


# Load table schemas from JSON file
def get_table_schemas() -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    table_schemas_path = os.path.join(current_dir, "models", "table_schemas.json")
    with open(table_schemas_path) as f:
        return json.load(f)


iam.get_aws_credentials(os.environ)

# Initialize FastAPI app
app = FastAPI()
Session = create_database_session()
schemas = get_table_schemas()


# Parse filters from string to dictionary
def parse_filters(filters: str) -> Optional[dict]:
    try:
        filters = json.loads(filters)
        if isinstance(filters, dict):
            for key, value in filters.items():
                if not isinstance(value, list) or not all(
                    isinstance(v, str) for v in value
                ):
                    return None
            return filters
        return None
    except json.JSONDecodeError:
        return None


# Apply filters to the query
def apply_filters(query, model, filters_dict: dict):
    for column_name, filter_value in filters_dict.items():
        query = query.filter(getattr(model, column_name).in_(filter_value))
    return query


# Format results into a list of dictionaries for specified columns
def format_results(items, model, columns: List[str]) -> list:
    return [
        {column: getattr(item, column) for column in columns if hasattr(item, column)}
        for item in items
    ]


# Handle item retrieval
async def handle_read_items(
    session,
    model,
    filters: Optional[str],
    limit: int,
    columns: Optional[str],
) -> JSONResponse:
    query = session.query(model)
    Base.metadata.clear()

    print(filters)
    print(type(filters))

    if filters:
        filters_dict = parse_filters(filters)
        if filters_dict is None:
            return JSONResponse(
                content={"error": "Invalid filters format"}, status_code=400
            )
        query = apply_filters(query, model, filters_dict)

    limited_query = query.limit(limit)
    items = limited_query.all()

    if not items:
        return JSONResponse(content={"error": "No items found"}, status_code=404)

    selected_columns = (
        columns.split(",")
        if columns
        else [column.name for column in model.__table__.columns]
    )
    results = format_results(items, model, selected_columns)
    return JSONResponse(content=results)


async def handle_edit_items(
    session, model, payload: dict, operation_type: str
) -> JSONResponse:
    items_data = payload.get("items", [])
    Base.metadata.clear()
    if not items_data:
        return JSONResponse(content={"error": "No items provided"}, status_code=400)

    try:
        if operation_type == "append":
            for item in items_data:
                new_item = model(**item)
                session.add(new_item)
        elif operation_type == "update":
            for item in items_data:
                item_id = item.get("id")
                if item_id is None:
                    continue  # Skip if no ID is provided
                existing_item = session.query(model).filter_by(id=item_id).first()
                Base.metadata.clear()
                if existing_item:
                    for key, value in item.items():
                        setattr(existing_item, key, value)
                else:
                    return JSONResponse(
                        content={"error": f"Item with id {item_id} not found"},
                        status_code=404,
                    )
        elif operation_type == "delete":
            for item in items_data:
                item_id = item.get("id")
                if item_id is None:
                    continue
                existing_item = session.query(model).filter_by(id=item_id).first()
                Base.metadata.clear()
                if existing_item:
                    session.delete(existing_item)
                else:
                    return JSONResponse(
                        content={"error": f"Item with id {item_id} not found"},
                        status_code=404,
                    )

        session.commit()
        Base.metadata.clear()
        return JSONResponse(
            content={
                "message": f"{operation_type.capitalize()} operation on items completed successfully"
            },
            status_code=200,
        )
    except Exception as e:
        session.rollback()
        Base.metadata.clear()
        logger.error(f"Error during {operation_type} items: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to {operation_type} items: {str(e)}"},
            status_code=500,
        )


@app.get("/items/")
async def read_items(
    table_name: str,
    columns: Optional[str] = None,
    filters: Optional[str] = None,
    limit: int = 5,
) -> JSONResponse:
    session = Session()
    model = create_model_class(table_name, schemas.get(f"rtg_automotive_{table_name}"))

    if model is None:
        return JSONResponse(content={"error": "Invalid table name"}, status_code=400)

    return await handle_read_items(session, model, filters, limit, columns)


@app.post("/items/")
async def edit_items(
    table_name: str,
    type: str,
    payload: dict,
) -> JSONResponse:
    session = Session()
    model = create_model_class(table_name, schemas.get(f"rtg_automotive_{table_name}"))

    if model is None:
        return JSONResponse(
            content={"error": f"Invalid table name: {table_name}"}, status_code=400
        )

    return await handle_edit_items(session, model, payload, type)


lambda_handler = Mangum(app)
