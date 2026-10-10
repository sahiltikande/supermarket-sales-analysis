# Supermarket Sales Analysis

A reproducible data analytics project that explores supermarket transactions to identify sales trends across products, categories, branches, customer types, payment methods, and customer ratings.

## Project objectives

- Inspect and clean the transaction dataset.
- Validate sales using `Quantity × Unit Price` where the required columns are available.
- Summarize revenue, transaction volume, average transaction value, product/category performance, branch performance, payment preferences, and customer ratings.
- Generate presentation-ready charts and a machine-readable KPI report.
- Translate findings into practical business recommendations.

## Dataset

The source spreadsheet supplied for this project is:
[Supermarket Sales Dataset (Google Sheets)](https://docs.google.com/spreadsheets/d/1QIX__4VObHFMEXnRM2xJyXmB5JAB2peHrJcQ41_U9TE/edit?usp=sharing)

Download/export the sheet as CSV and save it as:

`data/raw/supermarket_sales.csv`

Use **File → Download → Comma-separated values (.csv)** in Google Sheets. Do not commit sensitive or licensed data unless you have permission to publish it.

The project expects columns corresponding to product/item, branch, city, category, customer type, quantity, unit price, payment method, rating, and optionally sales. Column names are normalized and common alternatives are supported. If your spreadsheet uses different column names, update the aliases in `src/analyze_sales.py`.

## Repository structure

```text
supermarket-sales-analysis/
├── data/
│   ├── raw/                 # Place the source CSV here (not committed by default)
│   └── processed/           # Cleaned data output (not committed by default)
├── outputs/
│   ├── charts/              # Generated PNG charts
│   └── reports/             # Generated KPI JSON and text summary
├── src/
│   └── analyze_sales.py     # Data validation, analysis, charts, and KPI export
├── .gitignore
├── requirements.txt
└── README.md
```

## Tech stack

- Python 3.10+
- Pandas — data cleaning and aggregation
- Matplotlib and Seaborn — visualizations
- NumPy — numerical operations

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/supermarket-sales-analysis.git
cd supermarket-sales-analysis
```

### 2. Create and activate a virtual environment (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add the dataset

Export the Google Sheet as CSV and save it to `data/raw/supermarket_sales.csv`.

### 5. Run the analysis

From the repository root:

```bash
python src/analyze_sales.py
```

The script writes:
- `data/processed/cleaned_sales.csv`
- `outputs/reports/kpi_summary.json`
- `outputs/reports/analysis_summary.txt`
- PNG charts in `outputs/charts/`

## Questions explored

1. Which product generates the highest sales?
2. Which branch and city generate the highest sales?
3. Which category generates the highest sales?
4. Which payment method is used most often?
5. Do Members have a higher average transaction value than Normal customers?
6. What is the average customer rating?
7. How much revenue and how many transactions are represented in the dataset?

## Business interpretation

Use the output to consider inventory planning for high-revenue products/categories, investigate what drives strong branch performance, maintain convenient payment options, and identify customer-experience improvements. Membership offers should be based on verified customer behavior rather than assumptions.

## Data-quality and metric notes

- If a `Sales` column exists, the script compares it with `Quantity × Unit Price` when both input columns are available.
- If `Sales` is missing but quantity and unit price exist, sales is calculated from those fields.
- The script reports missing values and duplicate rows before cleaning.
- Product/category/branch rankings use summed sales; payment popularity uses transaction counts; customer-type spending compares average transaction sales.
- Currency formatting is shown as ₹ for this project. Confirm the source data's currency before publishing results.
- The project does not hard-code previously reported findings. All final figures are calculated from the CSV at runtime.

## Current reported findings to verify

The initial project brief reported Cheese as the highest-sales product (₹27,906.30), Branch C / Mumbai as the highest-sales branch (₹72,469.45), Beverages as the highest-sales category (₹56,108.24), UPI as the most-used payment method (127 transactions), average Member transaction sales of ₹483.14 versus ₹497.07 for Normal customers, and an average rating of 3.99/5.

These are **provisional figures from the brief**, not independently verified results. Re-run the analysis against the actual CSV before using them in a portfolio, report, or interview.

## Suggested resume bullet

**Supermarket Sales Analysis | Python, Pandas, Matplotlib, Seaborn**
- Cleaned and analyzed supermarket transaction data to evaluate product/category revenue, branch performance, payment preferences, customer spending patterns, and customer ratings.
- Automated KPI summaries and visual reports to turn transaction-level data into actionable inventory and customer-experience recommendations.

Only claim the exact number of records, results, or business impact after running and validating the supplied dataset.

## License

Add a license only after deciding what permissions apply to your code and dataset. The dataset is not bundled with this repository.
