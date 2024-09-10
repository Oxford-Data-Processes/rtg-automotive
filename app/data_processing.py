import pandas as pd
from typing import List, Tuple
from sqlalchemy.engine.base import Engine
from config import CONFIG
from database import read_from_mysql, append_mysql_table


def prepare_stock_data(engine: Engine) -> pd.DataFrame:
    """
    Prepare stock data by reading from the database and performing initial processing.

    Args:
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        pd.DataFrame: Processed stock data.
    """
    df = read_from_mysql("supplier_stock_history", engine)
    df = df.drop_duplicates(subset=["custom_label", "updated_date"], keep="first")
    df = df.sort_values(["custom_label", "updated_date"], ascending=[True, False])
    df_grouped = df.groupby("custom_label").head(2)
    return df_grouped


def process_stock_data(engine: Engine) -> pd.DataFrame:
    """
    Process stock data to calculate quantity deltas.

    Args:
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        pd.DataFrame: Processed stock data with quantity deltas.
    """
    df_grouped = prepare_stock_data(engine)
    df_delta = (
        df_grouped.groupby("custom_label")
        .agg(
            {
                "quantity": lambda x: (
                    x.iloc[0] - x.iloc[1] if len(x) > 1 else x.iloc[0]
                ),
                "updated_date": "first",
            }
        )
        .reset_index()
    )

    df_delta = df_delta.rename(columns={"quantity": "quantity_delta"})
    df_delta["Quantity"] = df_grouped.groupby("custom_label")["quantity"].first().values
    df_delta = df_delta[
        (df_delta["quantity_delta"] != 0) & (df_delta["quantity_delta"].notnull())
    ]

    return df_delta


def process_dataframe(
    config_key: str, file: pd.ExcelFile, processed_date: str
) -> pd.DataFrame:
    """
    Process an Excel file based on the configuration for a specific supplier.

    Args:
        config_key (str): Key for the supplier configuration.
        file (pd.ExcelFile): Excel file to process.
        processed_date (str): Date of processing.

    Returns:
        pd.DataFrame: Processed dataframe.
    """
    df = pd.read_excel(file)

    config_data = CONFIG[config_key]
    code_column = df.iloc[:, config_data["code_column_number"] - 1]
    stock_column = df.iloc[:, config_data["stock_column_number"] - 1]

    df_output = pd.DataFrame(
        {
            "part_number": code_column,
            "supplier": config_key,
            "quantity": stock_column.apply(config_data["process_func"]),
            "last_updated": processed_date,
        }
    )

    return df_output


def merge_stock_with_product_and_store(
    stock_df: pd.DataFrame, engine: Engine
) -> pd.DataFrame:
    """
    Merge stock data with product and store information.

    Args:
        stock_df (pd.DataFrame): Stock dataframe.
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        pd.DataFrame: Merged dataframe with stock, product, and store information.
    """
    store_df = read_from_mysql("store", engine)

    ebay_df = pd.merge(
        stock_df,
        store_df[["custom_label", "item_id", "store"]],
        on="custom_label",
        how="inner",
    )

    return ebay_df[["item_id", "Quantity", "custom_label", "store"]]


def create_ebay_dataframe(stock_df: pd.DataFrame, engine: Engine) -> pd.DataFrame:
    """
    Create an eBay-compatible dataframe from stock data.

    Args:
        stock_df (pd.DataFrame): Stock dataframe.
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        pd.DataFrame: eBay-compatible dataframe.
    """
    ebay_df = merge_stock_with_product_and_store(stock_df, engine)
    ebay_df = ebay_df.rename(
        columns={
            "custom_label": "CustomLabel",
            "item_id": "ItemID",
            "store": "Store",
        }
    )
    ebay_df["Action"] = "Revise"
    ebay_df["SiteID"] = "UK"
    ebay_df["Currency"] = "GBP"
    ebay_df = ebay_df[
        [
            "Action",
            "ItemID",
            "SiteID",
            "Currency",
            "Quantity",
            "Store",
        ]
    ]
    ebay_df["Quantity"] = ebay_df["Quantity"].astype(int)
    ebay_df["ItemID"] = ebay_df["ItemID"].astype(int)
    return ebay_df


def process_stock_history_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process stock history data.

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        pd.DataFrame: Processed stock history dataframe.
    """
    df_copy = df.copy()[
        ["custom_label", "part_number", "supplier", "quantity", "last_updated"]
    ]
    df_copy["updated_date"] = df_copy["last_updated"]
    df_copy.drop(columns=["last_updated"], inplace=True)
    return df_copy


def process_and_upload_files(
    uploaded_folder: List[pd.ExcelFile], processed_date: str, engine: Engine
) -> List[Tuple[pd.DataFrame, str]]:
    """
    Process and upload files to the database.

    Args:
        uploaded_folder (List[pd.ExcelFile]): List of uploaded Excel files.
        processed_date (str): Date of processing.
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        List[Tuple[pd.DataFrame, str]]: List of processed dataframes and their corresponding supplier names.
    """
    processed_dataframes = []
    for file in uploaded_folder:
        supplier = file.name.split()[0]
        if supplier in CONFIG:

            df_supplier_stock = process_dataframe(supplier, file, processed_date)

            product_df = pd.read_sql_table("product", engine)

            df_supplier_stock = pd.merge(
                df_supplier_stock,
                product_df,
                how="left",
                left_on=["supplier", "part_number"],
                right_on=["supplier", "part_number"],
            )

            append_mysql_table(df_supplier_stock, "supplier_stock", engine)
            append_mysql_table(
                process_stock_history_data(df_supplier_stock),
                "supplier_stock_history",
                engine,
            )

            processed_dataframes.append((df_supplier_stock, supplier))
        else:
            print(f"No configuration found for {supplier}. Skipping this file.")
    return processed_dataframes
