import json
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    BigInteger,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List, Dict

Base = declarative_base()


def create_columns(schema: List[Dict[str, str]]) -> Dict[str, Column]:
    columns = {}
    for field in schema:
        field_name = field["name"]
        field_type = field["type"]
        if field_type == "string":
            columns[field_name] = Column(String)  # type: ignore
        elif field_type == "double":
            columns[field_name] = Column(Float)  # type: ignore
        elif field_type == "integer":
            columns[field_name] = Column(Integer)  # type: ignore
        elif field_type == "bigint":
            columns[field_name] = Column(BigInteger)  # type: ignore
    return columns


with open("src/aws_lambda/api/models/table_schemas.json") as f:
    table_schemas = json.load(f)

# Create the SupplierStock model programmatically
supplier_stock_schema = table_schemas["rtg_automotive_supplier_stock"]["columns"]
columns = create_columns(supplier_stock_schema)
columns["__tablename__"] = "supplier_stock"
columns["__table_args__"] = (PrimaryKeyConstraint("custom_label"),)
SupplierStock = type("SupplierStock", (Base,), columns)


engine = create_engine(
    "mysql+mysqlconnector://admin:password@rtg-automotive-mysql.c14oos6givty.eu-west-2.rds.amazonaws.com/rtg_automotive"
)
Session = sessionmaker(bind=engine)
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