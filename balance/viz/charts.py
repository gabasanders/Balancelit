from __future__ import annotations

from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_expenses_stacked_bar(
    df: pd.DataFrame,
    view_type: Literal["Monthly", "Yearly"],
    category_colors: dict[str, str] | None = None,
) -> go.Figure:
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(title="No expenses in range")
        return fig
    title = "Expenses by month" if view_type == "Yearly" else "Expenses by day"
    cmap_src = category_colors or {}
    cats = df["category"].unique()
    cmap = {c: cmap_src.get(c, "#888888") for c in cats}
    fig = px.bar(
        df,
        x="period",
        y="value",
        color="category",
        title=title,
        color_discrete_map=cmap,
        custom_data=["items"],
    )
    fig.update_layout(barmode="stack", xaxis_title=None, yaxis_title="Amount")
    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "%{x}<br>"
            "Total: %{y:,.2f}<br><br>"
            "%{customdata[0]}"
            "<extra></extra>"
        ),
    )
    return fig
