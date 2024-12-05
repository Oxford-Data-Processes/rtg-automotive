import os

from aws_utils import events, iam

iam.get_aws_credentials(os.environ)

events_handler = events.EventsHandler()


def trigger_create_parquet_lambda(table_name: str, rds_identifier: str) -> None:
    events_handler.publish_event(
        "rtg-automotive-create-parquet-lambda-event-bus",
        "com.oxforddataprocesses",
        "RtgAutomotiveCreateParquet",
        {
            "event_type": "RtgAutomotiveCreateParquet",
            "table_name": table_name,
            "rds_identifier": rds_identifier,
        },
    )


def trigger_run_sql_query_lambda(query: str, rds_identifier: str) -> None:
    events_handler.publish_event(
        "rtg-automotive-run-sql-query-lambda-event-bus",
        "com.oxforddataprocesses",
        "RtgAutomotiveRunSQLQuery",
        {
            "event_type": "RtgAutomotiveRunSQLQuery",
            "rds_identifier": rds_identifier,
            "query": query,
        },
    )


# trigger_create_parquet_lambda("store", "rtg-automotive-db")
# trigger_create_parquet_lambda("supplier_stock", "rtg-automotive-db")

# Updated file path to match the correct location of the SQL files
with open("src/sql/store_filtered.sql", "r") as file:
    query = file.read()
    print(query)
    trigger_run_sql_query_lambda(query, "rtg-automotive-db")

with open("src/sql/supplier_stock_ranked.sql", "r") as file:
    query = file.read()
    print(query)
    trigger_run_sql_query_lambda(query, "rtg-automotive-db")
