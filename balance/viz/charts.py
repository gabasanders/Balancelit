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

def plot_recurring_waterfall(df_recurring: pd.DataFrame) -> go.Figure:
    if df_recurring is None or df_recurring.empty:
        fig = go.Figure()
        fig.update_layout(title="No recurring items")
        return fig

    # Ensure value is numeric
    df_recurring["value"] = pd.to_numeric(df_recurring["value"], errors="coerce").fillna(0)

    df_income = df_recurring[df_recurring["type"] == "income"]
    total_income = df_income["value"].sum()
    
    df_expense = df_recurring[df_recurring["type"] == "expense"]
    
    # First bar: Total Income
    x = ["Income"]
    y = [total_income]
    measure = ["relative"]
    
    income_items_str = "<br>".join([f"{row['name']}: {row['value']:,.2f}" + (f" ({(row['value']/total_income*100):.1f}%)" if total_income > 0 else "") for _, row in df_income.iterrows()])
    custom_data = [[income_items_str]]
    
    # Following bars: Categories
    if not df_expense.empty:
        for cat, group in df_expense.groupby("category"):
            cat_total = group["value"].sum()
            x.append(cat)
            y.append(-cat_total)
            measure.append("relative")
            
            items_str = "<br>".join([f"{row['name']}: {row['value']:,.2f}" + (f" ({(row['value']/total_income*100):.1f}%)" if total_income > 0 else "") for _, row in group.iterrows()])
            custom_data.append([items_str])

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measure,
        x=x,
        textposition="outside",
        text=[f"{val:,.2f}" for val in y],
        y=y,
        customdata=custom_data,
        decreasing={"marker": {"color": "red"}},
        increasing={"marker": {"color": "green"}},
        totals={"marker": {"color": "blue"}},
        hovertemplate="<b>%{x}</b><br>Amount: %{y:,.2f}<br><br><b>Items:</b><br>%{customdata[0]}<extra></extra>"
    ))
    
    fig.update_layout(title="Recurring Income and Expenses", waterfallgap=0.3)
    return fig

