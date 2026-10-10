"""Analyze supermarket sales data and export KPIs and charts.

Run from the repository root:
    python src/analyze_sales.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "raw" / "supermarket_sales.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
CHART_DIR = ROOT / "outputs" / "charts"
REPORT_DIR = ROOT / "outputs" / "reports"

# Canonical field -> accepted source column names (normalized before matching).
ALIASES = {
    "product": ["product", "product name", "item", "item name", "product line", "product category item"],
    "category": ["category", "product category", "product line", "department"],
    "branch": ["branch", "branch name", "store", "store branch"],
    "city": ["city", "location", "town"],
    "customer_type": ["customer type", "customer_type", "customer", "membership", "member type"],
    "quantity": ["quantity", "qty", "units sold", "units"],
    "unit_price": ["unit price", "unit_price", "price per unit", "price", "unit cost"],
    "sales": ["sales", "total sales", "revenue", "total", "total amount", "amount"],
    "payment": ["payment", "payment method", "payment type", "pay method"],
    "rating": ["rating", "customer rating", "customer ratings", "review score"],
}

sns.set_theme(style="whitegrid", context="talk")


def normalize_name(value: object) -> str:
    """Normalize a column name for alias matching."""
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def find_column(columns: list[str], canonical: str) -> Optional[str]:
    normalized = {normalize_name(col): col for col in columns}
    for alias in ALIASES[canonical]:
        if normalize_name(alias) in normalized:
            return normalized[normalize_name(alias)]
    return None


def money(value: object) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def configure_console_encoding() -> None:
    """Ensure UTF-8 output on Windows terminals that default to a legacy code page."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def save_bar_chart(series: pd.Series, title: str, xlabel: str, ylabel: str, filename: str,
                   horizontal: bool = True, top_n: int = 12) -> None:
    if series.empty:
        return
    data = series.sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(12, max(6, len(data) * 0.55)))
    if horizontal:
        sns.barplot(x=data.values, y=data.index.astype(str), ax=ax, color="#5B5F97")
    else:
        sns.barplot(x=data.index.astype(str), y=data.values, ax=ax, color="#5B5F97")
        ax.tick_params(axis="x", rotation=30)
    ax.set_title(title, pad=18, weight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    fig.savefig(CHART_DIR / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_console_encoding()

    for directory in (PROCESSED_DIR, CHART_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_CSV}\n"
            "Export the provided Google Sheet as CSV and save it to data/raw/supermarket_sales.csv."
        )

    raw = pd.read_csv(INPUT_CSV)
    if raw.empty:
        raise ValueError("The CSV is empty. Check the downloaded dataset.")
    original_columns = list(raw.columns)

    mapping = {key: find_column(original_columns, key) for key in ALIASES}
    # Product line is ambiguous in some datasets. If it was used as product, also
    # use it as category only when no separate category field exists.
    if mapping["category"] is None and mapping["product"] is not None:
        possible = normalize_name(mapping["product"])
        if possible in {"product line", "category", "product category"}:
            mapping["category"] = mapping["product"]

    required_missing = [name for name in ("quantity", "unit_price")
                        if mapping[name] is None and mapping["sales"] is None]
    if required_missing:
        raise ValueError(
            "Could not identify required columns to calculate sales. "
            f"Detected columns: {original_columns}. "
            "Please update ALIASES in src/analyze_sales.py."
        )
    if mapping["sales"] is None and (mapping["quantity"] is None or mapping["unit_price"] is None):
        raise ValueError("Need either a Sales column or both Quantity and Unit Price columns.")

    df = raw.copy()
    duplicate_count = int(df.duplicated().sum())
    missing_before = {str(k): int(v) for k, v in df.isna().sum().items()}
    df = df.drop_duplicates().copy()

    # Create canonical columns while retaining source columns.
    for canonical, source in mapping.items():
        if source is not None:
            df[canonical] = df[source]

    for col in ("quantity", "unit_price", "sales", "rating"):
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[₹,$,\s]", "", regex=True),
                errors="coerce"
            )

    calculated_sales = None
    if "quantity" in df.columns and "unit_price" in df.columns:
        calculated_sales = df["quantity"] * df["unit_price"]
    if "sales" not in df.columns:
        df["sales"] = calculated_sales
        sales_source = "calculated from quantity × unit price"
        sales_mismatch_count = 0
    elif calculated_sales is not None:
        valid = df["sales"].notna() & calculated_sales.notna()
        sales_mismatch_count = int(
            (~np.isclose(df.loc[valid, "sales"], calculated_sales.loc[valid], rtol=0.01, atol=0.02)).sum()
        )
        # Keep the provided Sales field as the reported metric; expose calculated
        # sales separately for auditability.
        df["calculated_sales"] = calculated_sales
        sales_source = "provided Sales column (compared with quantity × unit price)"
    else:
        sales_mismatch_count = 0
        sales_source = "provided Sales column"

    # Keep records with a usable sales value for analysis.
    invalid_sales_count = int(df["sales"].isna().sum())
    df = df[df["sales"].notna()].copy()
    if df.empty:
        raise ValueError("No rows with valid sales values remain after numeric conversion.")

    # Standardize text fields without changing the original source columns.
    for col in ("product", "category", "branch", "city", "customer_type", "payment"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
            df[col] = df[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    df.to_csv(PROCESSED_DIR / "cleaned_sales.csv", index=False)

    def total_by(field: str) -> pd.Series:
        if field not in df.columns:
            return pd.Series(dtype=float)
        return df.dropna(subset=[field]).groupby(field)["sales"].sum().sort_values(ascending=False)

    product_sales = total_by("product")
    category_sales = total_by("category")
    branch_sales = total_by("branch")
    city_sales = total_by("city")
    payment_counts = df["payment"].value_counts() if "payment" in df.columns else pd.Series(dtype=int)
    customer_average = (
        df.dropna(subset=["customer_type"]).groupby("customer_type")["sales"].mean().sort_values(ascending=False)
        if "customer_type" in df.columns else pd.Series(dtype=float)
    )
    average_rating = float(df["rating"].mean()) if "rating" in df.columns and df["rating"].notna().any() else None

    save_bar_chart(product_sales, "Top Products by Sales", "Sales (₹)", "Product", "top_products_by_sales.png")
    save_bar_chart(category_sales, "Sales by Category", "Sales (₹)", "Category", "sales_by_category.png")
    save_bar_chart(branch_sales, "Sales by Branch", "Sales (₹)", "Branch", "sales_by_branch.png")
    save_bar_chart(payment_counts, "Transactions by Payment Method", "Transactions", "Payment Method",
                    "payment_method_counts.png")
    save_bar_chart(customer_average, "Average Transaction Sales by Customer Type", "Average sales (₹)",
                    "Customer Type", "average_sales_by_customer_type.png")

    if "rating" in df.columns and df["rating"].notna().any():
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(df["rating"].dropna(), bins=10, kde=True, ax=ax, color="#3C8DAD")
        ax.set_title("Distribution of Customer Ratings", pad=18, weight="bold")
        ax.set_xlabel("Customer rating")
        ax.set_ylabel("Number of transactions")
        fig.tight_layout()
        fig.savefig(CHART_DIR / "customer_rating_distribution.png", dpi=180, bbox_inches="tight")
        plt.close(fig)

    def top_item(series: pd.Series) -> Optional[dict]:
        if series.empty:
            return None
        return {"name": str(series.index[0]), "sales": round(float(series.iloc[0]), 2)}

    kpis = {
        "source_file": str(INPUT_CSV.relative_to(ROOT)),
        "rows_loaded": int(len(raw)),
        "rows_analyzed": int(len(df)),
        "duplicate_rows_removed": duplicate_count,
        "invalid_sales_rows_excluded": invalid_sales_count,
        "missing_values_before_cleaning": missing_before,
        "sales_metric_source": sales_source,
        "sales_mismatch_count_tolerance_1_percent_or_2_currency_units": sales_mismatch_count,
        "total_sales": round(float(df["sales"].sum()), 2),
        "transaction_count": int(len(df)),
        "average_transaction_sales": round(float(df["sales"].mean()), 2),
        "median_transaction_sales": round(float(df["sales"].median()), 2),
        "average_customer_rating": round(average_rating, 2) if average_rating is not None else None,
        "top_product_by_sales": top_item(product_sales),
        "top_category_by_sales": top_item(category_sales),
        "top_branch_by_sales": top_item(branch_sales),
        "top_city_by_sales": top_item(city_sales),
        "most_used_payment_method": (
            {"name": str(payment_counts.index[0]), "transactions": int(payment_counts.iloc[0])}
            if not payment_counts.empty else None
        ),
        "average_sales_by_customer_type": {
            str(k): round(float(v), 2) for k, v in customer_average.items()
        },
        "column_mapping": {k: v for k, v in mapping.items() if v is not None},
    }

    with (REPORT_DIR / "kpi_summary.json").open("w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=2, ensure_ascii=False)

    lines = [
        "SUPERMARKET SALES ANALYSIS — GENERATED SUMMARY",
        "=" * 48,
        f"Rows loaded: {len(raw)}",
        f"Rows analyzed: {len(df)}",
        f"Duplicate rows removed: {duplicate_count}",
        f"Invalid sales rows excluded: {invalid_sales_count}",
        f"Sales source: {sales_source}",
        f"Sales mismatches: {sales_mismatch_count}",
        f"Total sales: {money(kpis['total_sales'])}",
        f"Average transaction sales: {money(kpis['average_transaction_sales'])}",
        f"Median transaction sales: {money(kpis['median_transaction_sales'])}",
        f"Average customer rating: {average_rating:.2f}/5" if average_rating is not None else "Average customer rating: N/A",
        "",
        "Top product by sales: " + (f"{kpis['top_product_by_sales']['name']} ({money(kpis['top_product_by_sales']['sales'])})" if kpis["top_product_by_sales"] else "N/A"),
        "Top category by sales: " + (f"{kpis['top_category_by_sales']['name']} ({money(kpis['top_category_by_sales']['sales'])})" if kpis["top_category_by_sales"] else "N/A"),
        "Top branch by sales: " + (f"{kpis['top_branch_by_sales']['name']} ({money(kpis['top_branch_by_sales']['sales'])})" if kpis["top_branch_by_sales"] else "N/A"),
        "Top city by sales: " + (f"{kpis['top_city_by_sales']['name']} ({money(kpis['top_city_by_sales']['sales'])})" if kpis["top_city_by_sales"] else "N/A"),
        "Most-used payment method: " + (f"{kpis['most_used_payment_method']['name']} ({kpis['most_used_payment_method']['transactions']} transactions)" if kpis["most_used_payment_method"] else "N/A"),
        "",
        "Average sales by customer type:",
    ]
    lines.extend([f"  - {key}: {money(value)}" for key, value in kpis["average_sales_by_customer_type"].items()])
    lines += [
        "",
        "Interpretation: use high-revenue products/categories to inform stock planning,",
        "investigate branch differences before reallocating resources, and use payment",
        "and rating patterns to guide customer experience improvements.",
    ]
    (REPORT_DIR / "analysis_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nCharts saved to: {CHART_DIR}")
    print(f"Reports saved to: {REPORT_DIR}")


if __name__ == "__main__":
    main()
