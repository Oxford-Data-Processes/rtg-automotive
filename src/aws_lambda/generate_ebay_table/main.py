import json
import logging
import os

from aws_utils import iam
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_database_session() -> sessionmaker:
    engine = create_engine(
        "mysql+mysqlconnector://admin:password@rtg-automotive-mysql.c14oos6givty.eu-west-2.rds.amazonaws.com/rtg_automotive"
    )
    return sessionmaker(bind=engine)


iam.get_aws_credentials(os.environ)


def lambda_handler(event, context):
    session = create_database_session()()
    current_directory = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_directory, "generate_ebay_table.sql"), "r") as file:
        queries = file.read().split(
            ";"
        )  # Split the SQL file into individual statements

    logger.info(f"Queries: {queries}")

    try:
        for query in queries:
            if query.strip():  # Check if the query is not empty
                session.execute(text(query))  # Execute each query separately

        session.commit()  # Commit the transaction after executing all queries

        logger.info("All queries executed successfully.")
    except Exception as e:
        logger.error(f"Error executing queries: {str(e)}")
        session.rollback()  # Rollback in case of error
        raise e
    finally:
        session.close()

    return {"statusCode": 200, "body": json.dumps("Queries executed successfully!")}
