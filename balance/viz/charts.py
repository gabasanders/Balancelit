import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from balance.config.colors import COLOR_MAP


def get_months_cat(test_df: pd.DataFrame):
    test_df = test_df.copy()
    test_df["Data"] = pd.to_datetime(
        test_df["Ano"].astype(str)
        + "-"
        + test_df["Mês"].astype(str).str.zfill(2)
        + "-"
        + test_df["Dia"].astype(str).str.zfill(2)
    )
    test_df["Weekday"] = test_df["Data"].dt.weekday

    unique_comb = test_df[["Ano", "Mês"]].drop_duplicates().reset_index(drop=True)
    n = len(unique_comb)
    ncols = math.ceil(math.sqrt(n))
    nrows = math.ceil(n / ncols)

    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        subplot_titles=[
            f"{int(r.Ano)}–{int(r.Mês):02d}" for _, r in unique_comb.iterrows()
        ],
    )

    for idx, row in unique_comb.iterrows():
        year, month = row.Ano, row.Mês
        df = test_df[
            (test_df["Ano"] == year)
            & (test_df["Mês"] == month)
            & (~test_df["Categoria"].isin(["Entrada", "Investimento"]))
        ]

        colors = df["Weekday"].apply(lambda wd: "red" if wd >= 5 else "blue")
        r = idx // ncols + 1
        c = idx % ncols + 1

        fig.add_trace(
            go.Scatter(
                x=df["Dia"],
                y=df["Valor"],
                mode="markers",
                marker=dict(color=colors, size=8),
                showlegend=False,
            ),
            row=r,
            col=c,
        )

        count_val = len(df)
        sum_val = df["Valor"].sum()
        mean_val = df["Valor"].mean()

        fig.add_annotation(
            text=f"Count: {count_val}<br>Sum: {sum_val:.2f}<br>Mean: {mean_val:.2f}",
            x=0.02,
            y=0.95,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            font=dict(size=10),
            row=r,
            col=c,
        )

    fig.update_layout(
        height=300 * nrows,
        width=350 * ncols,
        title_text="Valores diários por Mês/Ano (pontos de fim de semana em vermelho)",
    )
    return fig


def get_general_graph(df: pd.DataFrame):
    gasto_total = df.copy()
    gasto_total = gasto_total[~gasto_total["Categoria"].isin(["Entrada", "Investimento"])]
    return px.bar(
        gasto_total,
        x="Data",
        y="Valor",
        color="Categoria",
        hover_data="Descrição",
        color_discrete_map=COLOR_MAP,
    )

