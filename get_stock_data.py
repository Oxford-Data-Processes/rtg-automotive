import pandas as pd
from pathlib import Path


def read_excel_sheets(file_path, sheet_names):
    excel = pd.ExcelFile(file_path)
    return {sheet: pd.read_excel(excel, sheet_name=sheet) for sheet in sheet_names}


def process_dataframe(df):
    df = df.iloc[:, :4]
    df.columns = ["custom_label", "part_number", "supplier", "quantity"]
    return df


def main():
    excel_file = Path("data/supplier_stock/Stock Feed Master.xlsx")
    sheet_names = ["Direct", "FPS"]

    dfs = read_excel_sheets(excel_file, sheet_names)

    processed_dfs = [process_dataframe(df) for df in dfs.values()]
    df_stock = pd.concat(processed_dfs)
    df_stock["updated_date"] = (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    df_stock.drop_duplicates(
        subset=["part_number", "supplier"], keep="first", inplace=True
    )

    df_stock["custom_label"] = df_stock["custom_label"].str.upper().str.strip()

    # Read the custom labels to remove
    remove_labels = pd.read_csv("data/tables/remove_custom_labels.csv")[
        "custom_label"
    ].tolist()

    # Convert remove_labels to uppercase and strip whitespace for consistency
    remove_labels = [label.upper().strip() for label in remove_labels]

    # Remove the specified custom labels from df_product
    df_stock = df_stock[~df_stock["custom_label"].isin(remove_labels)]
    df_stock.to_csv("data/tables/supplier_stock.csv", index=False)

    df_product = df_stock.copy()[["custom_label", "part_number", "supplier"]]
    df_product.to_csv("data/tables/product.csv", index=False)

    # Create a copy of df_stock with yesterday's date
    df_stock_yesterday = df_stock.copy()
    df_stock_yesterday["updated_date"] = (
        pd.Timestamp.now() - pd.Timedelta(days=2)
    ).strftime("%Y-%m-%d")

    # Append df_stock to df_stock_yesterday
    df_stock_yesterday = pd.concat([df_stock_yesterday, df_stock], ignore_index=True)

    # Sort the combined dataframe by custom_label and updated_date
    df_stock_yesterday.sort_values(
        ["custom_label", "updated_date"], ascending=[True, False], inplace=True
    )

    # Remove duplicates, keeping the first (most recent) occurrence
    df_stock_yesterday.drop_duplicates(
        subset=["custom_label", "updated_date"], keep="first", inplace=True
    )
    # Update the CSV file with the new data
    df_stock_yesterday.to_csv("data/tables/supplier_stock_history.csv", index=False)


if __name__ == "__main__":
    main()
