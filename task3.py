"""task3.py
Global Sales Performance Dashboard helper for Tableau.

Run:
    python task3.py

What this script creates:
    - A clean Tableau master dataset CSV
    - Summary CSV files for executive, regional, product, customer, and trend views
    - Tableau calculated field formulas
    - Dashboard/story guidance
    - An interactive HTML dashboard preview
    - Optional Tableau Hyper extract when tableauhyperapi is installed

Tableau note:
    Python cannot reliably build a finished .twbx workbook without Tableau Desktop,
    but it can prepare all data, formulas, and a dashboard preview so you can
    recreate/publish the final workbook in Tableau Public.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent


CITY_LOOKUP = {
    "United States": [
        ("New York", "New York", 40.7128, -74.0060),
        ("Los Angeles", "California", 34.0522, -118.2437),
        ("Chicago", "Illinois", 41.8781, -87.6298),
        ("Houston", "Texas", 29.7604, -95.3698),
    ],
    "Canada": [
        ("Toronto", "Ontario", 43.6532, -79.3832),
        ("Vancouver", "British Columbia", 49.2827, -123.1207),
        ("Montreal", "Quebec", 45.5017, -73.5673),
    ],
    "Mexico": [
        ("Mexico City", "Mexico City", 19.4326, -99.1332),
        ("Guadalajara", "Jalisco", 20.6597, -103.3496),
        ("Monterrey", "Nuevo Leon", 25.6866, -100.3161),
    ],
    "United Kingdom": [
        ("London", "England", 51.5074, -0.1278),
        ("Manchester", "England", 53.4808, -2.2426),
        ("Birmingham", "England", 52.4862, -1.8904),
    ],
    "Germany": [
        ("Berlin", "Berlin", 52.5200, 13.4050),
        ("Munich", "Bavaria", 48.1351, 11.5820),
        ("Frankfurt", "Hesse", 50.1109, 8.6821),
    ],
    "France": [
        ("Paris", "Ile-de-France", 48.8566, 2.3522),
        ("Lyon", "Auvergne-Rhone-Alpes", 45.7640, 4.8357),
        ("Marseille", "Provence-Alpes-Cote d'Azur", 43.2965, 5.3698),
    ],
    "Spain": [
        ("Madrid", "Madrid", 40.4168, -3.7038),
        ("Barcelona", "Catalonia", 41.3874, 2.1686),
        ("Valencia", "Valencia", 39.4699, -0.3763),
    ],
    "China": [
        ("Shanghai", "Shanghai", 31.2304, 121.4737),
        ("Beijing", "Beijing", 39.9042, 116.4074),
        ("Shenzhen", "Guangdong", 22.5431, 114.0579),
    ],
    "Japan": [
        ("Tokyo", "Tokyo", 35.6762, 139.6503),
        ("Osaka", "Osaka", 34.6937, 135.5023),
        ("Nagoya", "Aichi", 35.1815, 136.9066),
    ],
    "Australia": [
        ("Sydney", "New South Wales", -33.8688, 151.2093),
        ("Melbourne", "Victoria", -37.8136, 144.9631),
        ("Brisbane", "Queensland", -27.4698, 153.0251),
    ],
    "India": [
        ("Mumbai", "Maharashtra", 19.0760, 72.8777),
        ("Delhi", "Delhi", 28.7041, 77.1025),
        ("Bangalore", "Karnataka", 12.9716, 77.5946),
    ],
    "Brazil": [
        ("Sao Paulo", "Sao Paulo", -23.5558, -46.6396),
        ("Rio de Janeiro", "Rio de Janeiro", -22.9068, -43.1729),
        ("Brasilia", "Federal District", -15.7939, -47.8828),
    ],
    "Argentina": [
        ("Buenos Aires", "Buenos Aires", -34.6037, -58.3816),
        ("Cordoba", "Cordoba", -31.4201, -64.1888),
        ("Rosario", "Santa Fe", -32.9442, -60.6505),
    ],
    "Chile": [
        ("Santiago", "Santiago Metropolitan", -33.4489, -70.6693),
        ("Valparaiso", "Valparaiso", -33.0472, -71.6127),
        ("Concepcion", "Biobio", -36.8201, -73.0444),
    ],
    "United Arab Emirates": [
        ("Dubai", "Dubai", 25.2048, 55.2708),
        ("Abu Dhabi", "Abu Dhabi", 24.4539, 54.3773),
        ("Sharjah", "Sharjah", 25.3463, 55.4209),
    ],
    "Saudi Arabia": [
        ("Riyadh", "Riyadh", 24.7136, 46.6753),
        ("Jeddah", "Makkah", 21.4858, 39.1925),
        ("Dammam", "Eastern Province", 26.4207, 50.0888),
    ],
    "South Africa": [
        ("Johannesburg", "Gauteng", -26.2041, 28.0473),
        ("Cape Town", "Western Cape", -33.9249, 18.4241),
        ("Durban", "KwaZulu-Natal", -29.8587, 31.0218),
    ],
}

REGIONS = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["United Kingdom", "Germany", "France", "Spain"],
    "APAC": ["China", "Japan", "Australia", "India"],
    "LATAM": ["Brazil", "Argentina", "Chile"],
    "MEA": ["United Arab Emirates", "Saudi Arabia", "South Africa"],
}

CATEGORIES = {
    "Technology": ["Phones", "Accessories", "Copiers", "Machines"],
    "Office Supplies": ["Binders", "Paper", "Storage", "Art"],
    "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
}


def require_packages() -> tuple["pandas", "numpy"]:
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("Install dependencies first: pip install pandas numpy tableauhyperapi") from exc
    return pd, np


def generate_sample_sales_data(pd, np, records: int = 9000) -> "pd.DataFrame":
    """Create a realistic retail dataset similar to Sample Superstore."""
    rng = np.random.default_rng(42)
    order_dates = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    customer_names = [
        f"{first} {last}"
        for first in ["Aarav", "Anika", "Meera", "Raj", "Olivia", "Noah", "Emma", "Liam", "Sophia", "Ethan"]
        for last in ["Sharma", "Brown", "Garcia", "Smith", "Miller", "Khan", "Wilson", "Patel", "Lee", "Martin"]
    ]
    segments = ["Consumer", "Corporate", "Home Office"]
    segment_probs = [0.50, 0.33, 0.17]
    rows = []

    for order_num in range(1, records + 1):
        order_date = pd.Timestamp(rng.choice(order_dates))
        region = rng.choice(list(REGIONS.keys()), p=[0.29, 0.24, 0.22, 0.14, 0.11])
        country = rng.choice(REGIONS[region])
        city, state, latitude, longitude = CITY_LOOKUP[country][rng.integers(0, len(CITY_LOOKUP[country]))]
        segment = rng.choice(segments, p=segment_probs)
        category = rng.choice(list(CATEGORIES.keys()), p=[0.40, 0.35, 0.25])
        sub_category = rng.choice(CATEGORIES[category])
        quantity = int(max(1, min(25, rng.poisson(4) + 1)))
        base_price = {
            "Technology": rng.normal(210, 85),
            "Office Supplies": rng.normal(48, 22),
            "Furniture": rng.normal(310, 110),
        }[category]
        unit_price = round(float(max(8, base_price)), 2)
        discount = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20, 0.30], p=[0.43, 0.18, 0.16, 0.11, 0.08, 0.04]))
        sales = round(quantity * unit_price * (1 - discount), 2)
        margin_center = {"Technology": 0.24, "Office Supplies": 0.17, "Furniture": 0.10}[category]
        profit_margin = float(rng.normal(margin_center - (discount * 0.45), 0.08))
        profit = round(sales * profit_margin, 2)
        customer_idx = int(rng.integers(0, len(customer_names)))

        rows.append(
            {
                "Order ID": f"ORD-{order_num:06d}",
                "Order Date": order_date,
                "Ship Date": order_date + pd.Timedelta(days=int(rng.choice([2, 3, 4, 5, 7, 10]))),
                "Region": region,
                "Country": country,
                "State/Province": state,
                "City": city,
                "Latitude": latitude,
                "Longitude": longitude,
                "Customer ID": f"CUST-{customer_idx + 1:04d}",
                "Customer Name": customer_names[customer_idx],
                "Segment": segment,
                "Customer Segment": segment,
                "Category": category,
                "Sub-Category": sub_category,
                "Product Name": f"{sub_category} Model {int(rng.integers(100, 999))}",
                "Quantity": quantity,
                "Units Sold": quantity,
                "Unit Price": unit_price,
                "Discount": discount,
                "Sales": sales,
                "Profit": profit,
            }
        )

    return normalize_schema(pd, np, pd.DataFrame(rows))


def normalize_schema(pd, np, df: "pd.DataFrame") -> "pd.DataFrame":
    """Make input data consistent and Tableau-friendly."""
    df = df.copy()
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df.get("Ship Date", df["Order Date"]), errors="coerce")
    df["Ship Date"] = df["Ship Date"].fillna(df["Order Date"] + pd.Timedelta(days=4))

    if "Segment" not in df.columns and "Customer Segment" in df.columns:
        df["Segment"] = df["Customer Segment"]
    if "Customer Segment" not in df.columns and "Segment" in df.columns:
        df["Customer Segment"] = df["Segment"]
    if "Quantity" not in df.columns and "Units Sold" in df.columns:
        df["Quantity"] = df["Units Sold"]
    if "Units Sold" not in df.columns and "Quantity" in df.columns:
        df["Units Sold"] = df["Quantity"]

    for column in ["Sales", "Profit", "Discount", "Unit Price", "Quantity", "Units Sold"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    if "Customer ID" not in df.columns:
        df["Customer ID"] = [f"CUST-{(idx % 600) + 1:04d}" for idx in range(len(df))]
    if "Customer Name" not in df.columns:
        df["Customer Name"] = df["Customer ID"].map(lambda value: f"Customer {str(value).split('-')[-1]}")

    city_meta = {(country, city): (state, lat, lon) for country, values in CITY_LOOKUP.items() for city, state, lat, lon in values}
    if "State/Province" not in df.columns:
        df["State/Province"] = ""
    if "Latitude" not in df.columns:
        df["Latitude"] = np.nan
    if "Longitude" not in df.columns:
        df["Longitude"] = np.nan

    for idx, row in df.iterrows():
        meta = city_meta.get((row.get("Country"), row.get("City")))
        if meta:
            state, lat, lon = meta
            if not row.get("State/Province"):
                df.at[idx, "State/Province"] = state
            if pd.isna(row.get("Latitude")):
                df.at[idx, "Latitude"] = lat
            if pd.isna(row.get("Longitude")):
                df.at[idx, "Longitude"] = lon

    df["Profit Margin"] = (df["Profit"] / df["Sales"].replace(0, np.nan)).fillna(0).round(4)
    df["Year"] = df["Order Date"].dt.year
    df["Quarter"] = "Q" + df["Order Date"].dt.quarter.astype(str)
    df["Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Name"] = df["Order Date"].dt.strftime("%b")
    df["Shipping Days"] = (df["Ship Date"] - df["Order Date"]).dt.days.clip(lower=0)
    df["Order Size"] = pd.cut(df["Quantity"], bins=[-1, 2, 5, 999], labels=["Small", "Medium", "Large"])
    df["Discount Band"] = pd.cut(
        df["Discount"], bins=[-0.001, 0, 0.10, 0.20, 1], labels=["No Discount", "Low", "Medium", "High"]
    )
    df["Profit Category"] = np.where(df["Profit"] >= 0, "Profitable", "Loss Making")
    df["Sales Target"] = (df["Sales"] * df["Region"].map({
        "North America": 1.08,
        "Europe": 1.07,
        "APAC": 1.10,
        "LATAM": 1.06,
        "MEA": 1.05,
    }).fillna(1.08)).round(2)
    return df


def margin(profit: float, sales: float) -> float:
    return round(profit / sales, 4) if sales else 0.0


def build_summary_tables(pd, np, df: "pd.DataFrame") -> dict[str, "pd.DataFrame"]:
    grouped_month = df.groupby("Month", as_index=False).agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique"),
        Quantity=("Quantity", "sum"),
        Sales_Target=("Sales Target", "sum"),
    )
    grouped_month["Profit_Margin"] = (grouped_month["Profit"] / grouped_month["Sales"]).round(4)
    grouped_month["Running_Total_Sales"] = grouped_month["Sales"].cumsum().round(2)
    grouped_month["Moving_Avg_3M"] = grouped_month["Sales"].rolling(3, min_periods=1).mean().round(2)
    grouped_month["YoY_Growth"] = grouped_month["Sales"].pct_change(12).round(4)

    last_year = int(df["Year"].max())
    previous_year = last_year - 1
    sales_current = float(df.loc[df["Year"] == last_year, "Sales"].sum())
    sales_previous = float(df.loc[df["Year"] == previous_year, "Sales"].sum())
    yoy_growth = (sales_current - sales_previous) / sales_previous if sales_previous else 0
    total_sales = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    target_total = float(df["Sales Target"].sum())

    executive_kpis = pd.DataFrame(
        [
            {
                "Metric": "Total Sales",
                "Value": total_sales,
                "Formatted_Value": f"${total_sales:,.0f}",
                "Description": "Revenue across all orders",
            },
            {
                "Metric": "Total Profit",
                "Value": total_profit,
                "Formatted_Value": f"${total_profit:,.0f}",
                "Description": "Net profit after discounts",
            },
            {
                "Metric": "Profit Margin",
                "Value": margin(total_profit, total_sales),
                "Formatted_Value": f"{margin(total_profit, total_sales):.1%}",
                "Description": "Profit divided by sales",
            },
            {
                "Metric": "YoY Sales Growth",
                "Value": yoy_growth,
                "Formatted_Value": f"{yoy_growth:.1%}",
                "Description": f"{last_year} sales compared with {previous_year}",
            },
            {
                "Metric": "Target Achievement",
                "Value": total_sales / target_total if target_total else 0,
                "Formatted_Value": f"{(total_sales / target_total if target_total else 0):.1%}",
                "Description": "Sales divided by target",
            },
            {
                "Metric": "Orders",
                "Value": df["Order ID"].nunique(),
                "Formatted_Value": f"{df['Order ID'].nunique():,}",
                "Description": "Distinct orders",
            },
        ]
    )

    regional_performance = df.groupby("Region", as_index=False).agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum"),
        Sales_Target=("Sales Target", "sum"),
        Orders=("Order ID", "nunique"),
        Customers=("Customer ID", "nunique"),
        Avg_Order_Value=("Sales", "mean"),
    )
    regional_performance["Profit_Margin"] = (regional_performance["Total_Profit"] / regional_performance["Total_Sales"]).round(4)
    regional_performance["Target_Achievement"] = (regional_performance["Total_Sales"] / regional_performance["Sales_Target"]).round(4)
    regional_performance = regional_performance.sort_values("Total_Sales", ascending=False)

    geographic_sales = df.groupby(
        ["Region", "Country", "State/Province", "City", "Latitude", "Longitude"], as_index=False
    ).agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Sales_Target=("Sales Target", "sum"),
        Orders=("Order ID", "nunique"),
        Customers=("Customer ID", "nunique"),
    )
    geographic_sales["Profit_Margin"] = (geographic_sales["Profit"] / geographic_sales["Sales"]).round(4)

    product_performance = df.groupby(["Category", "Sub-Category"], as_index=False).agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum"),
        Orders=("Order ID", "nunique"),
        Avg_Discount=("Discount", "mean"),
    )
    product_performance["Profit_Margin"] = (product_performance["Profit"] / product_performance["Sales"]).round(4)
    product_performance = product_performance.sort_values("Sales", ascending=False)

    top_products = df.groupby(["Product Name", "Category", "Sub-Category"], as_index=False).agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum"),
        Orders=("Order ID", "nunique"),
    )
    top_products["Profit_Margin"] = (top_products["Total_Profit"] / top_products["Total_Sales"]).round(4)
    top_products = top_products.sort_values("Total_Sales", ascending=False).head(20)

    customer_segments = df.groupby("Segment", as_index=False).agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum"),
        Customers=("Customer ID", "nunique"),
        Orders=("Order ID", "nunique"),
        Avg_Discount=("Discount", "mean"),
        Avg_Order_Value=("Sales", "mean"),
    )
    customer_segments["Profit_Margin"] = (customer_segments["Total_Profit"] / customer_segments["Total_Sales"]).round(4)
    customer_segments["Repeat_Rate"] = customer_segments["Segment"].map(
        df.groupby(["Segment", "Customer ID"])["Order ID"].nunique().gt(1).groupby(level=0).mean()
    ).round(4)

    top_customers = df.groupby(["Customer ID", "Customer Name", "Segment"], as_index=False).agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique"),
        Last_Order=("Order Date", "max"),
    )
    top_customers["Profit_Margin"] = (top_customers["Profit"] / top_customers["Sales"]).round(4)
    top_customers = top_customers.sort_values("Sales", ascending=False).head(20)

    discount_analysis = df.groupby(["Category", "Discount Band"], observed=True, as_index=False).agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique"),
        Avg_Discount=("Discount", "mean"),
    )
    discount_analysis["Profit_Margin"] = (discount_analysis["Profit"] / discount_analysis["Sales"]).round(4)

    forecast = build_forecast(pd, np, grouped_month)

    return {
        "executive_kpis": executive_kpis,
        "monthly_sales": grouped_month,
        "sales_forecast": forecast,
        "regional_performance": regional_performance,
        "geographic_sales": geographic_sales,
        "product_performance": product_performance,
        "top_products": top_products,
        "customer_segments": customer_segments,
        "top_customers": top_customers,
        "discount_analysis": discount_analysis,
    }


def build_forecast(pd, np, monthly_sales: "pd.DataFrame", periods: int = 6) -> "pd.DataFrame":
    """Simple trend forecast for preview; use Tableau Analytics pane for final workbook forecasting."""
    history = monthly_sales.sort_values("Month").copy()
    x = np.arange(len(history))
    y = history["Sales"].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    future_months = pd.date_range(history["Month"].max() + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    forecast_values = [max(0, intercept + slope * (len(history) + idx)) for idx in range(periods)]
    return pd.DataFrame({"Month": future_months, "Forecast_Sales": [round(value, 2) for value in forecast_values]})


def export_to_csv(output_dir: Path, tables: dict[str, "pd.DataFrame"]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        print(f"Exported {path}")


def create_hyper_extract(output_dir: Path, df: "pd.DataFrame") -> None:
    try:
        from tableauhyperapi import (
            Connection,
            CreateMode,
            HyperProcess,
            Inserter,
            SchemaName,
            SqlType,
            TableDefinition,
            TableName,
            Telemetry,
        )
    except ImportError:
        print("Optional Hyper export skipped: install tableauhyperapi to create .hyper files.")
        return

    columns = [
        ("Order ID", SqlType.text()),
        ("Order Date", SqlType.timestamp()),
        ("Ship Date", SqlType.timestamp()),
        ("Region", SqlType.text()),
        ("Country", SqlType.text()),
        ("State/Province", SqlType.text()),
        ("City", SqlType.text()),
        ("Latitude", SqlType.double()),
        ("Longitude", SqlType.double()),
        ("Customer ID", SqlType.text()),
        ("Customer Name", SqlType.text()),
        ("Segment", SqlType.text()),
        ("Category", SqlType.text()),
        ("Sub-Category", SqlType.text()),
        ("Product Name", SqlType.text()),
        ("Quantity", SqlType.big_int()),
        ("Unit Price", SqlType.double()),
        ("Discount", SqlType.double()),
        ("Sales", SqlType.double()),
        ("Profit", SqlType.double()),
        ("Profit Margin", SqlType.double()),
        ("Sales Target", SqlType.double()),
        ("Shipping Days", SqlType.big_int()),
        ("Order Size", SqlType.text()),
        ("Discount Band", SqlType.text()),
        ("Profit Category", SqlType.text()),
    ]
    hyper_path = output_dir / "global_sales_extract.hyper"
    schema_name = SchemaName("Extract")
    table_name = TableName(schema_name, "Global Sales")
    table_definition = TableDefinition(
        table_name=table_name,
        columns=[TableDefinition.Column(name, dtype) for name, dtype in columns],
    )

    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, hyper_path, create_mode=CreateMode.CREATE_AND_REPLACE) as connection:
            connection.catalog.create_schema_if_not_exists(schema_name)
            connection.catalog.create_table(table_definition)
            with Inserter(connection, table_definition) as inserter:
                inserter.add_rows(df[[name for name, _ in columns]].itertuples(index=False, name=None))
                inserter.execute()
    print(f"Exported {hyper_path}")


def save_tableau_calculations(output_dir: Path) -> None:
    calculations = dedent(
        """
        TABLEAU CALCULATED FIELDS FOR GLOBAL SALES PERFORMANCE

        1. Profit Margin
        SUM([Profit]) / SUM([Sales])

        2. YoY Sales Growth
        (SUM([Sales]) - LOOKUP(SUM([Sales]), -12)) / ABS(LOOKUP(SUM([Sales]), -12))

        3. Sales vs Target
        SUM([Sales]) - SUM([Sales Target])

        4. Target Achievement
        SUM([Sales]) / SUM([Sales Target])

        5. Running Total Sales
        RUNNING_SUM(SUM([Sales]))

        6. 3-Month Moving Average
        WINDOW_AVG(SUM([Sales]), -2, 0)

        7. Shipping Days
        DATEDIFF('day', [Order Date], [Ship Date])

        8. Shipping Speed
        IF [Shipping Days] <= 3 THEN 'Fast'
        ELSEIF [Shipping Days] <= 5 THEN 'Normal'
        ELSE 'Slow'
        END

        9. Customer Tier
        IF { FIXED [Customer ID] : SUM([Sales]) } >= 10000 THEN 'Platinum'
        ELSEIF { FIXED [Customer ID] : SUM([Sales]) } >= 5000 THEN 'Gold'
        ELSEIF { FIXED [Customer ID] : SUM([Sales]) } >= 1000 THEN 'Silver'
        ELSE 'Bronze'
        END

        10. Repeat Customer
        IF { FIXED [Customer ID] : COUNTD([Order ID]) } > 1 THEN 'Repeat'
        ELSE 'New'
        END

        11. Selected Metric
        CASE [Select Metric]
        WHEN 'Sales' THEN SUM([Sales])
        WHEN 'Profit' THEN SUM([Profit])
        WHEN 'Quantity' THEN SUM([Quantity])
        END

        12. Top N Filter
        RANK(SUM([Sales])) <= [Top N]

        13. Profit Color
        IF SUM([Profit]) >= 0 THEN 'Profitable'
        ELSE 'Loss Making'
        END

        14. % of Overall Sales
        SUM([Sales]) / TOTAL(SUM([Sales]))

        15. Category Sales Share
        SUM([Sales]) / { FIXED [Category] : SUM([Sales]) }

        PARAMETERS TO CREATE IN TABLEAU
        - Select Metric: String list with Sales, Profit, Quantity
        - Top N: Integer, current value 10
        - Sales Threshold: Float, current value 1000
        """
    ).strip()
    path = output_dir / "tableau_calculated_fields.txt"
    path.write_text(calculations, encoding="utf-8")
    print(f"Wrote {path}")


def save_story_guidance(output_dir: Path) -> None:
    guidance = dedent(
        """
        GLOBAL SALES PERFORMANCE TABLEAU STORY

        Dashboard 1: Executive Summary
        - KPI cards: Total Sales, Total Profit, Profit Margin, YoY Growth, Target Achievement, Orders.
        - Monthly line chart: Sales trend with Tableau forecast from the Analytics pane.
        - Regional bar chart: Sales by Region, colored by Profit Margin.
        - Top Products: Horizontal bar chart sorted by Sales.
        - Scatter: Sales vs Profit by Category/Sub-Category.

        Dashboard 2: Regional Performance
        - Map: Country/State/City marks using Latitude and Longitude; size by Sales, color by Profit Margin.
        - Regional KPIs: Sales, Profit, Margin, Orders, Customers.
        - City ranking: Top cities by Sales.
        - Trend: Monthly Sales by selected Region.
        - Action: Clicking a region or city filters the other sheets.

        Dashboard 3: Product Analysis
        - Treemap: Category and Sub-Category by selected metric.
        - Bar chart: Sub-Category Sales.
        - Heatmap: Category vs Discount Band with Profit Margin color.
        - Product table: Top 20 products with Sales, Profit, Quantity, Margin.
        - Parameter: Select Metric = Sales, Profit, or Quantity.

        Dashboard 4: Customer Insights
        - Segment split: Bar or donut chart by Segment.
        - Customer KPIs: Customers, Average Order Value, Repeat Rate.
        - Top customers: Ranked table with Customer Name, Segment, Sales, Profit, Orders.
        - Customer Tier filter: Platinum, Gold, Silver, Bronze.

        Story Flow
        1. Executive Overview: Total performance and YoY growth.
        2. Regional Deep Dive: Which regions and cities are strongest.
        3. Product Strategy: Which categories grow revenue and protect profit.
        4. Customer Focus: Which customer groups deserve retention investment.
        5. Recommendations: Invest in high-margin technology, reduce unprofitable discounts, and grow repeat corporate customers.

        Design Rules
        - Use blue sequential colors for Sales.
        - Use red-to-green diverging colors for Profit Margin.
        - Keep 4 to 6 views per dashboard.
        - Add tooltip context: Sales, Profit, Margin, Orders, YoY Growth.
        - Create a Phone layout in Tableau for the Executive Summary KPI view.
        """
    ).strip()
    path = output_dir / "tableau_story_guidance.txt"
    path.write_text(guidance, encoding="utf-8")
    print(f"Wrote {path}")


def save_readme(output_dir: Path) -> None:
    readme = dedent(
        """
        # Global Sales Performance Dashboard

        ## Objective
        Analyze global sales performance for a multinational retail company and build a Tableau dashboard/story for executives, regional managers, product leaders, and customer teams.

        ## Files
        - `tableau_master_dataset.csv`: Main dataset to connect in Tableau Public.
        - `global_sales_extract.hyper`: Optional Tableau extract.
        - `executive_kpis.csv`: KPI card source.
        - `monthly_sales.csv` and `sales_forecast.csv`: Trend and forecast support.
        - `regional_performance.csv` and `geographic_sales.csv`: Region/map sources.
        - `product_performance.csv`, `top_products.csv`, `discount_analysis.csv`: Product dashboard sources.
        - `customer_segments.csv`, `top_customers.csv`: Customer dashboard sources.
        - `interactive_dashboard.html`: Browser preview of the dashboard/story.
        - `tableau_calculated_fields.txt`: Formulas to create in Tableau.
        - `tableau_story_guidance.txt`: Dashboard and story build guide.

        ## Recommended Tableau Build
        1. Connect to `tableau_master_dataset.csv` or `global_sales_extract.hyper`.
        2. Create calculated fields from `tableau_calculated_fields.txt`.
        3. Build four dashboards: Executive Summary, Regional Performance, Product Analysis, Customer Insights.
        4. Add filters for Region, Category, Segment, Year, and Customer Tier.
        5. Add dashboard actions so map/region/product clicks filter related sheets.
        6. Create a five-scene Tableau Story using the narrative in `tableau_story_guidance.txt`.

        ## Key Recommendations
        - Prioritize high-margin technology products.
        - Review high-discount furniture sales because discounts often reduce margin.
        - Use regional drilldowns to focus marketing investment where growth and margin both improve.
        - Build loyalty campaigns for repeat and corporate customers.
        """
    ).strip()
    path = output_dir / "README.md"
    path.write_text(readme, encoding="utf-8")
    print(f"Wrote {path}")


def records_for_dashboard(df: "pd.DataFrame") -> list[dict]:
    columns = [
        "Order Date",
        "Region",
        "Country",
        "City",
        "Latitude",
        "Longitude",
        "Segment",
        "Category",
        "Sub-Category",
        "Product Name",
        "Customer Name",
        "Sales",
        "Profit",
        "Quantity",
        "Discount",
        "Sales Target",
    ]
    preview = df[columns].copy()
    preview["Order Date"] = preview["Order Date"].dt.strftime("%Y-%m-%d")
    return preview.to_dict(orient="records")


def save_interactive_dashboard(output_dir: Path, df: "pd.DataFrame") -> None:
    data_json = json.dumps(records_for_dashboard(df), ensure_ascii=True)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Global Sales Performance Dashboard</title>
<style>
:root {{
  --ink:#172033; --muted:#607086; --line:#d9e1ec; --bg:#f6f8fb; --panel:#fff;
  --blue:#2563eb; --green:#15803d; --red:#b91c1c; --amber:#b45309;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Segoe UI, Arial, sans-serif; }}
header {{ background:#fff; border-bottom:1px solid var(--line); padding:18px 24px; position:sticky; top:0; z-index:3; }}
h1 {{ margin:0; font-size:24px; letter-spacing:0; }}
h2 {{ margin:0 0 12px; font-size:18px; }}
.sub {{ color:var(--muted); margin-top:4px; }}
.controls {{ display:flex; gap:12px; flex-wrap:wrap; margin-top:14px; align-items:end; }}
label {{ display:grid; gap:4px; font-size:12px; color:var(--muted); }}
select {{ min-width:150px; padding:8px 10px; border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); }}
.tabs {{ display:flex; gap:6px; flex-wrap:wrap; padding:14px 24px 0; }}
.tab {{ border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:6px; padding:9px 12px; cursor:pointer; }}
.tab.active {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
main {{ padding:18px 24px 30px; max-width:1400px; margin:auto; }}
.view {{ display:none; }}
.view.active {{ display:block; }}
.grid {{ display:grid; gap:14px; }}
.kpis {{ grid-template-columns:repeat(6, minmax(130px,1fr)); }}
.two {{ grid-template-columns:1.2fr .8fr; }}
.three {{ grid-template-columns:repeat(3, 1fr); }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; }}
.kpi .value {{ font-size:25px; font-weight:700; margin-top:4px; }}
.kpi .caption {{ color:var(--muted); font-size:12px; margin-top:4px; }}
.bar-row {{ display:grid; grid-template-columns:minmax(112px, 190px) 1fr minmax(76px, auto); gap:10px; align-items:center; margin:8px 0; font-size:13px; }}
.bar-track {{ height:14px; background:#edf2f7; border-radius:999px; overflow:hidden; }}
.bar {{ height:100%; background:var(--blue); border-radius:999px; }}
.bar.profit {{ background:var(--green); }}
svg {{ width:100%; height:290px; display:block; }}
.axis {{ stroke:#9aa9ba; stroke-width:1; }}
.line-sales {{ fill:none; stroke:var(--blue); stroke-width:3; }}
.line-forecast {{ fill:none; stroke:var(--amber); stroke-width:2; stroke-dasharray:6 5; }}
.point {{ fill:var(--blue); opacity:.75; }}
.loss {{ fill:var(--red); }}
.map-bg {{ fill:#eef3f8; stroke:#cdd7e3; }}
.bubble {{ fill:#2563eb; opacity:.65; stroke:#fff; stroke-width:1; }}
.treemap {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; min-height:220px; }}
.tile {{ border-radius:8px; padding:14px; color:#fff; display:flex; flex-direction:column; justify-content:flex-end; min-height:120px; background:var(--blue); }}
.tile:nth-child(2) {{ background:#0f766e; }}
.tile:nth-child(3) {{ background:#7c3aed; }}
.tile strong {{ font-size:18px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; }}
th {{ color:var(--muted); font-weight:600; }}
.story-nav {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }}
.story-btn {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:8px 10px; cursor:pointer; }}
.story-btn.active {{ background:var(--ink); color:#fff; }}
.story-card {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:22px; max-width:900px; }}
.story-card h2 {{ font-size:24px; }}
.rec li {{ margin:9px 0; }}
@media (max-width:900px) {{
  .kpis, .two, .three, .treemap {{ grid-template-columns:1fr; }}
  header, main, .tabs {{ padding-left:14px; padding-right:14px; }}
  .bar-row {{ grid-template-columns:1fr; gap:5px; }}
}}
</style>
</head>
<body>
<header>
  <h1>Global Sales Performance Dashboard</h1>
  <div class="sub">Interactive preview generated by task3.py. Recreate these views in Tableau Public with the exported CSV/Hyper data.</div>
  <div class="controls">
    <label>Region<select id="regionFilter"></select></label>
    <label>Category<select id="categoryFilter"></select></label>
    <label>Segment<select id="segmentFilter"></select></label>
  </div>
</header>
<nav class="tabs">
  <button class="tab active" data-view="executive">Executive Summary</button>
  <button class="tab" data-view="regional">Regional Performance</button>
  <button class="tab" data-view="product">Product Analysis</button>
  <button class="tab" data-view="customer">Customer Insights</button>
  <button class="tab" data-view="story">Story</button>
</nav>
<main>
  <section id="executive" class="view active">
    <div id="kpis" class="grid kpis"></div>
    <div class="grid two" style="margin-top:14px">
      <div class="panel"><h2>Monthly Sales Trend and Forecast</h2><div id="trend"></div></div>
      <div class="panel"><h2>Sales by Region</h2><div id="regionBars"></div></div>
    </div>
    <div class="grid two" style="margin-top:14px">
      <div class="panel"><h2>Top 10 Products</h2><div id="topProducts"></div></div>
      <div class="panel"><h2>Sales vs Profit</h2><div id="scatter"></div></div>
    </div>
  </section>
  <section id="regional" class="view">
    <div class="grid two">
      <div class="panel"><h2>Geographic Sales Distribution</h2><div id="map"></div></div>
      <div class="panel"><h2>Regional KPIs</h2><div id="regionalKpis" class="grid kpis" style="grid-template-columns:repeat(2,1fr)"></div></div>
    </div>
    <div class="grid two" style="margin-top:14px">
      <div class="panel"><h2>Top Cities</h2><div id="cityBars"></div></div>
      <div class="panel"><h2>Regional Monthly Trend</h2><div id="regionalTrend"></div></div>
    </div>
  </section>
  <section id="product" class="view">
    <div class="panel"><h2>Product Category Treemap</h2><div id="treemap" class="treemap"></div></div>
    <div class="grid three" style="margin-top:14px">
      <div class="panel"><h2>Sub-Category Sales</h2><div id="subcatBars"></div></div>
      <div class="panel"><h2>Discount Impact</h2><div id="discountBars"></div></div>
      <div class="panel"><h2>Product Table</h2><div id="productTable"></div></div>
    </div>
  </section>
  <section id="customer" class="view">
    <div class="grid two">
      <div class="panel"><h2>Customer Segment Performance</h2><div id="segmentBars"></div></div>
      <div class="panel"><h2>Top Customers</h2><div id="customerTable"></div></div>
    </div>
  </section>
  <section id="story" class="view">
    <div class="story-nav" id="storyNav"></div>
    <div class="story-card" id="storyCard"></div>
  </section>
</main>
<script>
const rows = {data_json};
const fmtMoney = v => '$' + Math.round(v).toLocaleString();
const fmtPct = v => (v * 100).toFixed(1) + '%';
const by = (arr, keyFn, valFn) => arr.reduce((m, r) => {{
  const k = keyFn(r);
  if (!m[k]) m[k] = {{key:k, sales:0, profit:0, quantity:0, orders:0, target:0, records:[]}};
  m[k].sales += +r.Sales; m[k].profit += +r.Profit; m[k].quantity += +r.Quantity; m[k].target += +r["Sales Target"]; m[k].orders += 1; m[k].records.push(r);
  return m;
}}, {{}});
const values = obj => Object.values(obj);
function filteredRows() {{
  const region = regionFilter.value, category = categoryFilter.value, segment = segmentFilter.value;
  return rows.filter(r => (region === 'All' || r.Region === region) && (category === 'All' || r.Category === category) && (segment === 'All' || r.Segment === segment));
}}
function fillFilter(id, field) {{
  const select = document.getElementById(id);
  const opts = ['All', ...new Set(rows.map(r => r[field]).sort())];
  select.innerHTML = opts.map(v => `<option value="${{v}}">${{v}}</option>`).join('');
  select.addEventListener('change', render);
}}
function kpi(label, value, caption) {{
  return `<div class="panel kpi"><div>${{label}}</div><div class="value">${{value}}</div><div class="caption">${{caption}}</div></div>`;
}}
function barChart(items, value='sales') {{
  const max = Math.max(...items.map(d => Math.abs(d[value])), 1);
  return items.map(d => `<div class="bar-row"><div title="${{d.key}}">${{d.key}}</div><div class="bar-track"><div class="bar ${{value === 'profit' ? 'profit' : ''}}" style="width:${{Math.max(1, Math.abs(d[value]) / max * 100)}}%"></div></div><div>${{value === 'profit' ? fmtMoney(d.profit) : fmtMoney(d.sales)}}</div></div>`).join('');
}}
function lineChart(items, key='sales') {{
  if (!items.length) return '';
  const w=760,h=290,p=34,max=Math.max(...items.map(d=>d[key]),1),min=Math.min(...items.map(d=>d[key]),0);
  const pts = items.map((d,i)=> {{
    const x = p + (i/(Math.max(items.length-1,1))) * (w - p*2);
    const y = h - p - ((d[key]-min)/(max-min || 1)) * (h-p*2);
    return `${{x}},${{y}}`;
  }}).join(' ');
  return `<svg viewBox="0 0 ${{w}} ${{h}}" role="img"><line class="axis" x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}"></line><line class="axis" x1="${{p}}" y1="${{p}}" x2="${{p}}" y2="${{h-p}}"></line><polyline class="line-sales" points="${{pts}}"></polyline></svg>`;
}}
function scatterChart(items) {{
  const w=760,h=290,p=38,maxX=Math.max(...items.map(d=>d.sales),1),maxY=Math.max(...items.map(d=>d.profit),1),minY=Math.min(...items.map(d=>d.profit),0);
  const circles = items.map(d => {{
    const x = p + d.sales/maxX*(w-p*2);
    const y = h-p - ((d.profit-minY)/(maxY-minY || 1))*(h-p*2);
    const cls = d.profit < 0 ? 'point loss' : 'point';
    return `<circle class="${{cls}}" cx="${{x}}" cy="${{y}}" r="7"><title>${{d.key}}: ${{fmtMoney(d.sales)}} sales, ${{fmtMoney(d.profit)}} profit</title></circle>`;
  }}).join('');
  return `<svg viewBox="0 0 ${{w}} ${{h}}"><line class="axis" x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}"></line><line class="axis" x1="${{p}}" y1="${{p}}" x2="${{p}}" y2="${{h-p}}"></line>${{circles}}</svg>`;
}}
function mapChart(items) {{
  const w=760,h=290;
  const max = Math.max(...items.map(d=>d.sales),1);
  const bubbles = items.map(d => {{
    const r = Math.max(4, Math.sqrt(d.sales/max)*26);
    const lon = +d.records[0].Longitude, lat = +d.records[0].Latitude;
    const x = (lon + 180) / 360 * w;
    const y = (90 - lat) / 180 * h;
    return `<circle class="bubble" cx="${{x}}" cy="${{y}}" r="${{r}}"><title>${{d.key}}: ${{fmtMoney(d.sales)}} sales, ${{fmtMoney(d.profit)}} profit</title></circle>`;
  }}).join('');
  return `<svg viewBox="0 0 ${{w}} ${{h}}"><rect class="map-bg" x="0" y="0" width="${{w}}" height="${{h}}" rx="8"></rect>${{bubbles}}</svg>`;
}}
function table(items, cols) {{
  return `<table><thead><tr>${{cols.map(c=>`<th>${{c.label}}</th>`).join('')}}</tr></thead><tbody>${{items.map(d=>`<tr>${{cols.map(c=>`<td>${{c.format ? c.format(d[c.key]) : d[c.key]}}</td>`).join('')}}</tr>`).join('')}}</tbody></table>`;
}}
function render() {{
  const f = filteredRows();
  const totalSales = f.reduce((s,r)=>s + +r.Sales, 0), totalProfit = f.reduce((s,r)=>s + +r.Profit, 0), target = f.reduce((s,r)=>s + +r["Sales Target"], 0);
  const orders = f.length, customers = new Set(f.map(r=>r["Customer Name"])).size;
  kpis.innerHTML = [
    kpi('Total Sales', fmtMoney(totalSales), 'Revenue'),
    kpi('Total Profit', fmtMoney(totalProfit), 'After discount'),
    kpi('Profit Margin', fmtPct(totalProfit / (totalSales || 1)), 'Profit / Sales'),
    kpi('Target Achievement', fmtPct(totalSales / (target || 1)), 'Sales vs target'),
    kpi('Orders', orders.toLocaleString(), 'Transactions'),
    kpi('Customers', customers.toLocaleString(), 'Distinct customers')
  ].join('');
  const monthItems = values(by(f, r => r["Order Date"].slice(0,7))).sort((a,b)=>a.key.localeCompare(b.key));
  trend.innerHTML = lineChart(monthItems);
  regionalTrend.innerHTML = lineChart(monthItems);
  const regions = values(by(f, r=>r.Region)).sort((a,b)=>b.sales-a.sales);
  regionBars.innerHTML = barChart(regions);
  regionalKpis.innerHTML = [
    kpi('Best Region', regions[0]?.key || 'None', fmtMoney(regions[0]?.sales || 0)),
    kpi('Regions', regions.length, 'Filtered count'),
    kpi('Regional Margin', fmtPct(totalProfit/(totalSales || 1)), 'Current filter'),
    kpi('Orders', orders.toLocaleString(), 'Current filter')
  ].join('');
  const products = values(by(f, r=>r["Product Name"])).sort((a,b)=>b.sales-a.sales);
  topProducts.innerHTML = barChart(products.slice(0,10));
  const subcats = values(by(f, r=>r.Category + ' / ' + r["Sub-Category"])).sort((a,b)=>b.sales-a.sales);
  scatter.innerHTML = scatterChart(subcats);
  subcatBars.innerHTML = barChart(subcats.slice(0,10));
  const cities = values(by(f, r=>r.City + ', ' + r.Country)).sort((a,b)=>b.sales-a.sales);
  cityBars.innerHTML = barChart(cities.slice(0,10));
  map.innerHTML = mapChart(cities);
  const cats = values(by(f, r=>r.Category)).sort((a,b)=>b.sales-a.sales);
  treemap.innerHTML = cats.map(c => `<div class="tile" style="min-height:${{120 + c.sales/(cats[0]?.sales || 1)*90}}px"><span>${{fmtPct(c.profit/(c.sales || 1))}} margin</span><strong>${{c.key}}</strong><span>${{fmtMoney(c.sales)}}</span></div>`).join('');
  const discounts = values(by(f, r=>r.Category + ' / ' + (r.Discount > .2 ? 'High Discount' : r.Discount > .1 ? 'Medium Discount' : r.Discount > 0 ? 'Low Discount' : 'No Discount'))).sort((a,b)=>b.sales-a.sales);
  discountBars.innerHTML = barChart(discounts.slice(0,10), 'profit');
  productTable.innerHTML = table(products.slice(0,8), [
    {{key:'key', label:'Product'}}, {{key:'sales', label:'Sales', format:fmtMoney}}, {{key:'profit', label:'Profit', format:fmtMoney}}
  ]);
  const segments = values(by(f, r=>r.Segment)).sort((a,b)=>b.sales-a.sales);
  segmentBars.innerHTML = barChart(segments);
  const cust = values(by(f, r=>r["Customer Name"])).sort((a,b)=>b.sales-a.sales).slice(0,12);
  customerTable.innerHTML = table(cust, [
    {{key:'key', label:'Customer'}}, {{key:'sales', label:'Sales', format:fmtMoney}}, {{key:'profit', label:'Profit', format:fmtMoney}}, {{key:'orders', label:'Orders'}}
  ]);
}}
const scenes = [
  ['Executive Overview', 'Sales performance is summarized through KPI cards, trend lines, regional ranking, top products, and sales-profit comparison. Start here for stakeholder-level context.'],
  ['Regional Deep Dive', 'The map and city rankings show where performance is concentrated. Use region filters and Tableau dashboard actions to drill from global view into country and city detail.'],
  ['Product Strategy', 'Category and sub-category views reveal which products create revenue and which protect margin. High-discount areas should be reviewed before the next quarter.'],
  ['Customer Focus', 'Segment and customer rankings identify valuable repeat buyers. Corporate and high-value customers are strong candidates for loyalty and cross-sell campaigns.'],
  ['Recommendations', '<ul class="rec"><li>Invest in high-margin Technology categories.</li><li>Reduce aggressive discounts where Furniture margins are weak.</li><li>Use regional drilldowns for targeted growth campaigns.</li><li>Build retention offers for repeat and corporate customers.</li></ul>']
];
function renderStory(i=0) {{
  storyNav.innerHTML = scenes.map((s,idx)=>`<button class="story-btn ${{idx===i?'active':''}}" onclick="renderStory(${{idx}})">Scene ${{idx+1}}</button>`).join('');
  storyCard.innerHTML = `<h2>${{scenes[i][0]}}</h2><p>${{scenes[i][1]}}</p>`;
}}
document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => {{
  document.querySelectorAll('.tab,.view').forEach(el => el.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(btn.dataset.view).classList.add('active');
}}));
fillFilter('regionFilter', 'Region');
fillFilter('categoryFilter', 'Category');
fillFilter('segmentFilter', 'Segment');
render();
renderStory();
</script>
</body>
</html>"""
    path = output_dir / "interactive_dashboard.html"
    path.write_text(html, encoding="utf-8")
    print(f"Wrote {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Tableau-ready Global Sales dashboard assets.")
    parser.add_argument("--input", type=Path, default=Path("global_sales.csv"), help="Raw sales CSV. Sample data is generated if missing.")
    parser.add_argument("--output", type=Path, default=Path("tableau_output"), help="Output folder.")
    parser.add_argument("--records", type=int, default=9000, help="Rows to generate when input is missing.")
    parser.add_argument("--skip-hyper", action="store_true", help="Skip optional Tableau Hyper extract.")
    return parser.parse_args()


def main() -> None:
    pd, np = require_packages()
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if args.input.exists():
        df = pd.read_csv(args.input)
        df = normalize_schema(pd, np, df)
        print(f"Loaded and cleaned raw sales data from {args.input}")
    else:
        df = generate_sample_sales_data(pd, np, records=args.records)
        df.to_csv(args.input, index=False)
        print(f"Generated sample data at {args.input}")

    master_path = args.output / "tableau_master_dataset.csv"
    df.to_csv(master_path, index=False)
    print(f"Exported {master_path}")

    summaries = build_summary_tables(pd, np, df)
    export_to_csv(args.output, summaries)

    if not args.skip_hyper:
        create_hyper_extract(args.output, df)

    save_tableau_calculations(args.output)
    save_story_guidance(args.output)
    save_readme(args.output)
    save_interactive_dashboard(args.output, df)
    print("Done. Open tableau_output/interactive_dashboard.html for the preview and use tableau_master_dataset.csv in Tableau Public.")


if __name__ == "__main__":
    main()
