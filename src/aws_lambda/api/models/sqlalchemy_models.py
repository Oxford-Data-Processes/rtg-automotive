from typing import Dict, List

import sqlalchemy

Base = sqlalchemy.orm.declarative_base()


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
        elif field_type == "bigint":
            columns[field_name] = sqlalchemy.Column(sqlalchemy.BigInteger)  # type: ignore
    return columns


def create_model_class(table_name: str, schema: Dict[str, Dict[str, str]]):
    primary_keys = schema["primary_keys"]
    columns = create_columns(schema["columns"])
    columns["__tablename__"] = table_name
    columns["__table_args__"] = (sqlalchemy.PrimaryKeyConstraint(*primary_keys),)
    return type(table_name, (Base,), columns)
