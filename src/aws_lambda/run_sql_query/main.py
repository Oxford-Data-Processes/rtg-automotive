import logging
import os

from aws_utils import iam, rds
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam.get_aws_credentials(os.environ)


def create_database_session() -> sessionmaker:
    rds_handler = rds.RDSHandler()
    rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
    rds_endpoint = rds_instance["Endpoint"]
    engine = create_engine(
        f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
    )
    return sessionmaker(bind=engine)


def execute_query(query: str) -> None:
    session = create_database_session()()
    try:
        logger.info(f"Executing query: {query}")
        split_query = query.split(";")
        for statement in split_query:
            session.execute(text(statement))
        session.commit()
        logger.info("Query executed successfully.")
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        session.rollback()
        raise e
    finally:
        session.close()


def lambda_handler(event, context):
    query = event["detail"]["query"]
    execute_query(query)
    return {"statusCode": 200, "body": "Query executed successfully"}
