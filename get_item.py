import json
import os
from typing import Dict, List

import sqlalchemy
from aws_utils import iam, rds

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


with open("src/aws_lambda/api/models/table_schemas.json") as f:
    table_schemas = json.load(f)

# Create the SupplierStock model programmatically
supplier_stock_schema = table_schemas["rtg_automotive_supplier_stock"]["columns"]
columns = create_columns(supplier_stock_schema)
columns["__tablename__"] = "supplier_stock"
columns["__table_args__"] = (sqlalchemy.PrimaryKeyConstraint("custom_label"),)
SupplierStock = type("SupplierStock", (Base,), columns)


iam.get_aws_credentials(os.environ)
rds_handler = rds.RDSHandler()
rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
rds_endpoint = rds_instance["Endpoint"]

engine = sqlalchemy.create_engine(
    f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
)
Session = sqlalchemy.orm.sessionmaker(bind=engine)
session = Session()

item = (
    session.query(SupplierStock)
    .filter(SupplierStock.custom_label == "UKD-APE-ABR101")
    .first()
)

if item is None:
    print("No item found with custom_label 'UKD-APE-ABR101'")
else:
    print(
        {
            column.name: getattr(item, column.name)
            for column in SupplierStock.__table__.columns
        }
    )
