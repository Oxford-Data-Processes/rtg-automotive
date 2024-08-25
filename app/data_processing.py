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
    df = df.drop_duplicates(subset=["product_id", "updated_date"], keep="first")
    df = df.sort_values(["product_id", "updated_date"], ascending=[True, False])
    df_grouped = df.groupby("product_id").head(2)
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
        df_grouped.groupby("product_id")
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
    df_delta["Quantity"] = df_grouped.groupby("product_id")["quantity"].first().values
    df_delta = df_delta[
        (df_delta["quantity_delta"] != 0) & (df_delta["quantity_delta"].notnull())
    ]

    return df_delta

def process_dataframe(config_key: str, file: pd.ExcelFile, processed_date: str) -> pd.DataFrame:
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
            "stock_id": code_column.apply(
                lambda x: f"{processed_date}-{config_key}-{x}"
            ),
            "product_id": code_column.apply(lambda x: f"{config_key}-{x}"),
            "quantity_raw": stock_column,
            "quantity": stock_column.apply(config_data["process_func"]),
            "last_updated": processed_date,
        }
    )

    return df_output

def merge_stock_with_product_and_store(stock_df: pd.DataFrame, engine: Engine) -> pd.DataFrame:
    """
    Merge stock data with product and store information.

    Args:
        stock_df (pd.DataFrame): Stock dataframe.
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        pd.DataFrame: Merged dataframe with stock, product, and store information.
    """
    product_df = read_from_mysql("product", engine)
    store_df = read_from_mysql("store", engine)

    ebay_df = pd.merge(
        stock_df.copy(),
        product_df[["product_id", "custom_label"]],
        on="product_id",
        how="inner",
    )

    ebay_df = pd.merge(
        ebay_df,
        store_df[["custom_label", "item_id", "store"]],
        on="custom_label",
        how="inner",
    )

    return ebay_df[["product_id", "item_id", "Quantity", "custom_label", "store"]]

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
            "product_id": "ProductID",
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
    df_copy = df.copy()[["product_id", "quantity", "last_updated"]]
    df_copy["updated_date"] = df_copy["last_updated"]
    df_copy.drop(columns=["last_updated"], inplace=True)
    return df_copy

def process_and_upload_files(uploaded_folder: List[pd.ExcelFile], processed_date: str, engine: Engine) -> List[Tuple[pd.DataFrame, str]]:
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
            df_output = process_dataframe(supplier, file, processed_date)
            df_stock_history = process_stock_history_data(df_output)

            append_mysql_table(df_output, "supplier_stock", engine)
            append_mysql_table(df_stock_history, "supplier_stock_history", engine)

            processed_dataframes.append((df_output, supplier))
        else:
            print(f"No configuration found for {supplier}. Skipping this file.")
    return processed_dataframes