import sqlalchemy
from typing import List, Dict, Any
from sqlalchemy.ext import declarative

Base = declarative.declarative_base(metadata=sqlalchemy.MetaData())


def create_columns(schema: List[Dict[str, str]]) -> Dict[str, sqlalchemy.Column]:
    columns = {}
    for field in schema:
        field_name = field["name"]
        field_type = field["type"]
        if field_type == "string":
            columns[field_name] = sqlalchemy.Column(sqlalchemy.String)  # type: ignore
        elif field_type == "double":
            columns[field_name] = sqlalchemy.Column(sqlalchemy.Float)  # type: ignore
        elif field_type == "integer":
            columns[field_name] = sqlalchemy.Column(sqlalchemy.Integer)  # type: ignore
    return columns
