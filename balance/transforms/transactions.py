import pandas as pd


def clean_raw_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    clean_df = raw_df[["Data", "Valor", "Categoria", "Descrição"]].copy()
    clean_df["Data"] = pd.to_datetime(clean_df["Data"], format="%d/%m/%Y")
    clean_df["Valor"] = clean_df["Valor"].astype(str).str.replace(",", ".")
    clean_df["Valor"] = clean_df["Valor"].astype(float)
    clean_df["Ano"] = clean_df["Data"].dt.year
    clean_df["Mês"] = clean_df["Data"].dt.month
    clean_df["Dia"] = clean_df["Data"].dt.day
    return clean_df


def get_categoria_por_mes(cat: str, temp: pd.DataFrame) -> pd.DataFrame:
    agg_df = temp.copy()
    agg_df = agg_df[agg_df["Categoria"] == cat]
    agg_df["Ano"] = agg_df["Data"].dt.year
    agg_df["Mês"] = agg_df["Data"].dt.month
    agg_df["Dia"] = agg_df["Data"].dt.day
    return (
        agg_df.groupby(["Ano", "Mês", "Dia", "Categoria"])
        .sum(numeric_only=True)
        .reset_index()
    )


def get_total_in_month(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Month"] = df["Data"].dt.to_period("M")
    gasto_total = df.copy()
    gasto_total["Month_str"] = gasto_total["Month"].astype(str)
    gasto_total = (
        gasto_total.groupby(["Categoria", "Month", "Month_str"])
        .sum(numeric_only=True)
        .reset_index()
    )
    gasto_total = gasto_total[~gasto_total["Categoria"].isin(["Entrada", "Investimento"])]
    return gasto_total.sort_values(by="Month")

