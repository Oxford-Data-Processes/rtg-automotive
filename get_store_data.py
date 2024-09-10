import pandas as pd
from pathlib import Path


def process_dataframe(df, store):
    df = df.iloc[:, :3]
    df.columns = ["item_id", "brand", "custom_label"]
    df["store"] = store
    return df


def read_excel_files(directory):
    dfs = {}
    for file in directory.glob("*.xlsx"):
        dfs[file.stem.split(" ")[0]] = pd.read_excel(file)
    return dfs


def main():
    data_dir = Path("data/store_database")
    dfs = read_excel_files(data_dir)

    processed_dfs = [process_dataframe(df, store) for store, df in dfs.items()]
    df_store = pd.concat(processed_dfs)

    df_store.drop_duplicates(subset=["item_id", "custom_label", "store"], inplace=True)
    df_store.to_csv("data/tables/store.csv", index=False)


if __name__ == "__main__":
    main()
