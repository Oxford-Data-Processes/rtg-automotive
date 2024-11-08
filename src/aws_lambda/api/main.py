import logging
import os

from aws_utils import iam  # type: ignore
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum

iam.get_aws_credentials(os.environ)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


app = FastAPI()


@app.get("/items/")
async def read_items(
    table_name: str,
    limit: int = 5,
) -> JSONResponse:
    results = {"key": table_name, "limit": limit}

    logger.info(f"results: {results}")

    return JSONResponse(content=results)


lambda_handler = Mangum(app)
