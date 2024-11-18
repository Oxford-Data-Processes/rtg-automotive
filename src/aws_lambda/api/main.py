import json
import logging
import os
import sys
from typing import List, Optional

from aws_utils import iam  # type: ignore
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


# Parse filters from string to dictionary
def parse_filters(filters: str) -> Optional[dict]:
    try:
        return json.loads(filters)
    except json.JSONDecodeError:
        return None


# Apply filters to the query
def apply_filters(query, model, filters_dict: dict):
    for column_name, filter_value in filters_dict.items():
        query = query.filter(getattr(model, column_name) == filter_value)
    return query


# Format results into a list of dictionaries for specified columns
def format_results(items, model, columns: List[str]) -> list:
    return [
        {column: getattr(item, column) for column in columns if hasattr(item, column)}
        for item in items
    ]


# Database engine and session setup
def create_database_session() -> sessionmaker:
    engine = create_engine(
        "mysql+mysqlconnector://admin:password@rtg-automotive-mysql.c14oos6givty.eu-west-2.rds.amazonaws.com/rtg_automotive"
    )
    return sessionmaker(bind=engine)


# Load table schemas from JSON file
def get_table_schemas() -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    table_schemas_path = os.path.join(current_dir, "models", "table_schemas.json")
    with open(table_schemas_path) as f:
        return json.load(f)


# Initialize IAM credentials
def initialize_iam():
    iam.get_aws_credentials(os.environ)


# Initialize FastAPI app
app = FastAPI()
Session = create_database_session()
schemas = get_table_schemas()
initialize_iam()


# Read items from the database
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

    query = session.query(model)
    if filters:
        filters_dict = parse_filters(filters)
        if filters_dict is None:
            return JSONResponse(
                content={"error": "Invalid filters format"}, status_code=400
            )
        query = apply_filters(query, model, filters_dict)

    items = query.limit(limit).all()
    if not items:
        return JSONResponse(content={"error": "No items found"}, status_code=404)

    selected_columns = (
        columns.split(",")
        if columns
        else [column.name for column in model.__table__.columns]
    )
    results = format_results(items, model, selected_columns)
    logger.info(f"results: {results}")
    Base.metadata.clear()
    return JSONResponse(content=results)


@app.post("/items/")
async def put_items(
    table_name: str,
    payload: dict,
) -> JSONResponse:
    session = Session()
    model = create_model_class(table_name, schemas.get(f"rtg_automotive_{table_name}"))

    print(f"Schema for model {table_name}: {model.__table__.columns.keys()}")

    if model is None:
        return JSONResponse(content={"error": "Invalid table name"}, status_code=400)

    items_data = payload.get("items", [])
    if not items_data:
        return JSONResponse(content={"error": "No items provided"}, status_code=400)

    try:
        for item in items_data:
            new_item = model(**item)
            session.add(new_item)
        session.commit()
        Base.metadata.clear()
        return JSONResponse(
            content={"message": "Items added successfully"}, status_code=201
        )
    except Exception as e:
        session.rollback()
        Base.metadata.clear()
        logger.error(f"Error adding items: {str(e)}")
        return JSONResponse(content={"error": "Failed to add items"}, status_code=500)


lambda_handler = Mangum(app)
