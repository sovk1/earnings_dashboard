import random
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

#######################################
# PAGE SETUP
#######################################

st.set_page_config(page_title="Sales Dashboard", page_icon=":bar_chart:", layout="wide")

st.title("Sales Streamlit Dashboard")
st.markdown("_Prototype v0.4.1_")

with st.sidebar:
    st.header("Configuration")
    uploaded_file = st.file_uploader("Choose a file")
    selected_year = st.selectbox("Select Year", [2023, 2022, 2021], index=0)
    selected_account = st.selectbox("Select Account", ['Sales', 'Profit', 'Expenses'])

if uploaded_file is None:
    st.info(" Upload a file through config", icon="ℹ️")
    st.stop()

#######################################
# DATA LOADING
#######################################

@st.cache_data
def load_data(path: str):
    return pd.read_excel(path)

df = load_data(uploaded_file)
all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

with st.expander("Data Preview"):
    st.dataframe(df)

#######################################
# VISUALIZATION METHODS
#######################################

def plot_metric(label, value, prefix="", suffix="", show_graph=False, color_graph=""):
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            value=value,
            gauge={"axis": {"visible": False}},
            number={
                "prefix": prefix,
                "suffix": suffix,
                "font.size": 28,
            },
            title={"text": label, "font": {"size": 24}},
        )
    )

    if show_graph:
        fig.add_trace(
            go.Scatter(
                y=random.sample(range(0, 101), 30),
                hoverinfo="skip",
                fill="tozeroy",
                fillcolor=color_graph,
                line={"color": color_graph},
            )
        )

    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)
    fig.update_layout(
        margin=dict(t=30, b=0),
        showlegend=False,
        plot_bgcolor="white",
        height=100,
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_gauge(value, color, suffix, title, max_bound):
    fig = go.Figure(
        go.Indicator(
            value=value,
            mode="gauge+number",
            number={"suffix": suffix, "font.size": 26},
            gauge={
                "axis": {"range": [0, max_bound], "tickwidth": 1},
                "bar": {"color": color},
            },
            title={"text": title, "font.size": 28},
        )
    )
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)


def plot_top_right(df, year):
    query = f"""
        SELECT business_unit, Scenario, SUM(sales) as sales
        FROM (
            SELECT * 
            FROM df 
            WHERE Year='{year}' AND Account='Sales'
        )
        GROUP BY Scenario, business_unit
    """
    sales_data = duckdb.sql(query).df()

    fig = px.bar(
        sales_data,
        x="business_unit",
        y="sales",
        color="Scenario",
        barmode="group",
        text_auto=".2s",
        title=f"Sales for Year {year}",
        height=400,
    )
    fig.update_traces(textfont_size=12, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, use_container_width=True)


def plot_bottom_left(df, year):
    query = f"""
        SELECT Scenario, month, sales
        FROM (
            SELECT Scenario, {','.join(all_months)} 
            FROM df 
            WHERE Year='{year}' AND Account='Sales' AND business_unit='Software'
        ) UNPIVOT (SELECT {','.join(all_months)} INTO sales FOR month)
    """
    sales_data = duckdb.sql(query).df()

    fig = px.line(
        sales_data,
        x="month",
        y="sales",
        color="Scenario",
        markers=True,
        text="sales",
        title=f"Monthly Budget vs Forecast {year}",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)


def plot_bottom_right(df):
    query = f"""
        SELECT Account, Year, SUM(sales) as sales
        FROM (
            SELECT Account, Year, {','.join([f'ABS({month}) as {month}' for month in all_months])}
            FROM df 
            WHERE Scenario='Actuals' AND Account!='Sales'
        ) UNPIVOT (SELECT {','.join(all_months)} INTO sales FOR month)
        GROUP BY Account, Year
    """
    sales_data = duckdb.sql(query).df()

    fig = px.bar(
        sales_data,
        x="Year",
        y="sales",
        color="Account",
        title="Actual Yearly Sales Per Account",
    )
    st.plotly_chart(fig, use_container_width=True)


#######################################
# STREAMLIT LAYOUT
#######################################

top_left_column, top_right_column = st.columns((2, 1))
bottom_left_column, bottom_right_column = st.columns(2)

with top_left_column:
    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        plot_metric("Total Accounts Receivable", 6621280, prefix="$", show_graph=True, color_graph="rgba(0, 104, 201, 0.2)")
        plot_gauge(1.86, "#0068C9", "%", "Current Ratio", 3)

    with column_2:
        plot_metric("Total Accounts Payable", 1630270, prefix="$", show_graph=True, color_graph="rgba(255, 43, 43, 0.2)")
        plot_gauge(10, "#FF8700", " days", "In Stock", 31)

    with column_3:
        plot_metric("Equity Ratio", 75.38, suffix=" %")
        plot_gauge(7, "#FF2B2B", " days", "Out Stock", 31)

    with column_4:
        plot_metric("Debt Equity", 1.10, suffix=" %")
        plot_gauge(28, "#29B09D", " days", "Delay", 31)

with top_right_column:
    plot_top_right(df, selected_year)

with bottom_left_column:
    plot_bottom_left(df, selected_year)

with bottom_right_column:
    plot_bottom_right(df)
