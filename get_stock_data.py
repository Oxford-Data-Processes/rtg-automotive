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
    df_stock["last_updated"] = pd.Timestamp.now().strftime("%Y-%m-%d")
    df_stock.drop_duplicates(
        subset=["part_number", "supplier"], keep="first", inplace=True
    )

    df_product = df_stock.copy()[["custom_label", "part_number", "supplier"]]
    df_product.to_csv("data/tables/product.csv", index=False)

    df_stock.to_csv("data/tables/supplier_stock.csv", index=False)


if __name__ == "__main__":
    main()
