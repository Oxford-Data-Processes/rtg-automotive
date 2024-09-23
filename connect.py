from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Connection string
engine = create_engine(
    "mysql+mysqlconnector://admin:password@rtg-automotive-db.c14oos6givty.eu-west-2.rds.amazonaws.com:3306/rtg_automotive"
)

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM supplier_stock LIMIT 10;")
        )  # Replace with your actual table name
        for row in result:
            print(row)
except SQLAlchemyError as e:
    print(f"Error: {e}")
