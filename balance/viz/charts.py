from __future__ import annotations

from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from balance.config.colors import COLOR_MAP


def plot_expenses_stacked_bar(
    df: pd.DataFrame,
    view_type: Literal["Yearly", "Monthly"],
) -> go.Figure:
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(title="No expenses in range")
        return fig
    title = "Expenses by month" if view_type == "Yearly" else "Expenses by day"
    cats = df["category"].unique()
    cmap = {c: COLOR_MAP.get(c, "#888888") for c in cats}
    fig = px.bar(
        df,
        x="period",
        y="value",
        color="category",
        title=title,
        color_discrete_map=cmap,
    )
    fig.update_layout(barmode="stack", xaxis_title=None, yaxis_title="Amount")
    return fig
