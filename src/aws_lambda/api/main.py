import logging
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum
from src.aws_lambda.api.models.sqlalchemy_models import create_model_class
from aws_utils import iam  # type: ignore


def get_table_schemas_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    table_schemas_path = os.path.join(current_dir, "models", "table_schemas.json")
    return table_schemas_path


table_schemas_path = get_table_schemas_path()


def load_schemas(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


schemas = load_schemas(table_schemas_path)

iam.get_aws_credentials(os.environ)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

engine = create_engine(
    "mysql+mysqlconnector://admin:password@rtg-automotive-mysql.c14oos6givty.eu-west-2.rds.amazonaws.com/rtg_automotive"
)
Session = sessionmaker(bind=engine)

app = FastAPI()


@app.get("/items/")
async def read_items(
    table_name: str,
    filters: str,
    limit: int = 5,
) -> JSONResponse:
    session = Session()
    model = None

    model = create_model_class(
        table_name, schemas[f"rtg_automotive_{table_name}"], "custom_label"
    )

    if model is None:
        return JSONResponse(content={"error": "Invalid table name"}, status_code=400)

    query = session.query(model)

    # Parse the filters string as a dictionary
    try:
        print(f"filters: {filters}")
        filters_dict = json.loads(filters)
    except json.JSONDecodeError:
        return JSONResponse(
            content={"error": "Invalid filters format"}, status_code=400
        )

    for column_name, filter_value in filters_dict.items():
        query = query.filter(getattr(model, column_name) == filter_value)

    items = query.limit(limit).all()

    if not items:
        return JSONResponse(content={"error": "No items found"}, status_code=404)

    results = [
        {column.name: getattr(item, column.name) for column in model.__table__.columns}
        for item in items
    ]

    logger.info(f"results: {results}")

    return JSONResponse(content=results)


lambda_handler = Mangum(app)
