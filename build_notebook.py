"""Build the BCBS TN Pharmacy Analytics workshop notebook by loading the
original Actuaries notebook and rewriting markdown cells while keeping the
same dataset and code structure (with light reframing for pharmacy context).
"""
import json
import copy
from pathlib import Path

SRC = Path("/Users/sunmin.lee/bcbs-tn-pharmacy-workshop/original_actuaries.ipynb")
DST = Path("/Users/sunmin.lee/bcbs-tn-pharmacy-workshop/DBX_Workshop_BCBS_TN_Pharmacy_Analytics.ipynb")


def md(text):
    """Helper: build a markdown cell."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True) if text else [],
    }


def code(src):
    """Helper: build a code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src.splitlines(keepends=True) if src else [],
    }


nb = json.loads(SRC.read_text())

# Keep the same overall ordering and replace cell contents in place.
# We will REUSE all code cells (they operate on the same dataset & schema)
# and REWRITE markdown cells for the pharmacy audience. A few markdown cells
# are augmented with extra SAS-vs-Databricks reference content.

new_cells = []

# Cell 0: updated date
new_cells.append(md("_Updated date: November 7, 2025_  \n_Tailored for BCBS Tennessee – Pharmacy Analytics team_\n"))

# Cell 1: Welcome
new_cells.append(md("""# Databricks for Pharmacy Analytics: A Hands-On Workshop
**For the BCBS Tennessee Pharmacy Analytics team — a guide for SAS users moving to Databricks**

---

## Welcome, Pharmacy Analytics team!

This workshop is built for the **BCBS Tennessee Pharmacy Analytics team**. Your day-to-day work centers on making sure pharmacy data is **accurate, governed, and decision-ready**, then turning that data into insights that drive pharmacy operations, financial performance, and strategic initiatives across **Commercial, Medicare, and Exchange** lines of business.

Most of you already do this in **SAS**: joining and merging tables, building macros, applying conditional logic, transposing/appending, formatting outputs, and designing reports. The good news — almost everything you do in SAS has a clean, often simpler, equivalent in Databricks.

## Workshop Objectives

By the end of this workshop, you will be able to:

1. Map your existing SAS workflows (PROC SQL, DATA steps, macros, formats, LIBNAMEs) onto Databricks.
2. Load and query pharmacy claims data using **SQL and PySpark**.
3. Build the pharmacy analytics deliverables your team owns:
   - Pharmacy **Cost, Utilization, and Membership Trends** by LOB, Group, Channel, and Drug
   - **PMPM** trending (drug spend, plan paid, claim counts)
   - **Utilization Management** (volume by decision status)
   - **Program Savings** & **Impact Analyses** (legislation, market changes, strategic goals)
4. Run pharmacy data-quality checks suitable for vendor-feed oversight and anomaly detection.
5. Use Databricks AI Assistant + AI/BI to accelerate ad-hoc analyses and stakeholder requests.

---

### Dataset Overview

We are using a **healthcare claims dataset** that mirrors what your team already works with. For this workshop, treat the tables as your pharmacy domain:

| Table       | What it represents in our pharmacy context                                  |
|-------------|------------------------------------------------------------------------------|
| `members`   | Health plan enrollees (member, plan, effective date)                         |
| `claims`    | Pharmacy claim header — drug spend, decision status, fill date, member, pharmacy |
| `providers` | **Pharmacies** — `specialty` represents the **channel** (Retail / Mail Order / Specialty) |
| `procedures`| Drug-level line items — `procedure_code` ≈ **NDC / GPI**, `procedure_desc` ≈ **Drug name**, `amount` ≈ drug cost |
| `diagnosis` | Diagnosis on the claim — useful for therapy-class analyses                   |

> **Mapping reminder:** Claims = pharmacy claim records, Providers = pharmacies, Procedures = drug-level line items, Specialty = channel.

---
"""))

# Cell 2: Sample data model
new_cells.append(md("""## Sample Data Model

For the BCBS TN Pharmacy book of business, we will work with these tables:

- **Members** — enrollees in a health plan (LOB derived from `plan_id`)
- **Claims** — pharmacy claim records (decision status, fill date, total drug spend)
- **Providers** — pharmacies (channel via `specialty`: Retail / Mail Order / Specialty)
- **Procedures** — drug-level line items (NDC / GPI proxy, drug name, drug cost)
- **Diagnosis** — diagnosis codes from claims (used for therapy-class roll-ups)

Each table has at least 50 rows so you can run every example end-to-end.

<img src="https://user-gen-media-assets.s3.amazonaws.com/gpt4o_images/bdd54dc0-f3c7-4975-80a3-0017ebdb121c.png" alt="Managed Tables" width="400" height="300">
"""))

# Cell 3: Introduction + SAS comparison
new_cells.append(md("""# Introduction for Pharmacy Analytics

## Why Databricks for Pharmacy Analytics?

If you currently work in **SAS**, you might be thinking: "Why learn another tool?"

### Here's why this matters for *our* team:
- **Vendor-feed scale**: Pharmacy data (PBM extracts, eligibility feeds, NDC tables) keeps growing. Databricks handles billions of rows in seconds — no more overnight `PROC SQL` runs to refresh PMPM.
- **Recurring + ad-hoc together**: Schedule the recurring dashboards *and* answer ad-hoc questions in the same environment, with the same governed data.
- **Trusted-advisor work**: Faster turnaround on stakeholder requests means more time for the consultative analysis that distinguishes our team.
- **Your SAS knowledge transfers**: ~90% of `PROC SQL` syntax works as-is. The DATA step has direct equivalents in SQL and PySpark.

---

## SAS → Databricks: Quick Reference

| What you do in SAS | How you do it in Databricks | Difficulty |
|---|---|---|
| `PROC SQL` | SQL queries (almost identical) | Easy |
| `PROC MEANS` / `PROC SUMMARY` | `GROUP BY` + aggregate functions | Easy |
| `PROC FREQ` | `GROUP BY` + `COUNT()` | Easy |
| `DATA` step (filter / derive) | SQL `SELECT` with `CASE WHEN`, or PySpark `withColumn` | Easy |
| `IF-THEN / ELSE` | `CASE WHEN ... THEN ... ELSE ... END` | Easy |
| `LIBNAME` | Unity Catalog: `catalog.schema.table` | Easy |
| `PROC IMPORT` / `PROC EXPORT` (Excel/text) | `COPY INTO`, `spark.read.csv`, `df.write.csv` | Easy |
| Macros (`%LET`, `%MACRO`) | Notebook widgets, Python variables, parameterized SQL | Moderate |
| Macro date functions (`%SYSFUNC(today())`) | `CURRENT_DATE()`, `DATE_ADD()`, `ADD_MONTHS()` | Easy |
| `PROC TRANSPOSE` | SQL `PIVOT` / PySpark `groupBy().pivot()` | Moderate |
| `SET` (append) | SQL `UNION ALL` / PySpark `unionByName` | Easy |
| `MERGE` | SQL `JOIN` (`LEFT`, `INNER`, `FULL OUTER`) | Easy |
| `PROC FORMAT` (custom formats) | `CASE WHEN` or lookup join | Easy |
| Temporary datasets (`work.foo`) | Temp views: `df.createOrReplaceTempView("foo")` | Easy |
| `PROC EXPAND` (trending) | Window functions (`LAG`, `LEAD`, moving avg) | Moderate |
| `PROC UNIVARIATE` (percentiles) | `PERCENTILE_CONT` | Easy |
| `PROC REPORT` / ODS | Built-in `display()`, dashboards, AI/BI | Easy |

**Bottom line:** every item in your team's SAS skill list — joins/merges, temp tables, derived variables, macros (date + function), Excel I/O, conditional logic, transpose/append, formats, libnames, report outputs — has a clean Databricks equivalent. We will hit each of these in this workshop.

---
"""))

# Cell 4: Lakehouse
new_cells.append(md("""## What is a Lakehouse? (Plain English)

For the Pharmacy Analytics team, think of the lakehouse as a **super-powered SAS library** that:
- Holds all your pharmacy data in one governed place — PBM claims, eligibility, NDC reference, UM decisions, program-savings tracking.
- Lets you analyze it with SQL (just like `PROC SQL`).
- Handles billions of rows in seconds.
- Tracks every change for audit (great for regulator-facing analyses on legislation impact).
- Lets the whole team work at once — no `*.sas7bdat` lock conflicts.

**Practical benefit for our team:** PMPM trending across **all** LOBs (Commercial, Medicare, Exchange) for a multi-year window can run in seconds, not hours.

<img src="https://www.databricks.com/wp-content/uploads/2020/01/data-lakehouse-new.png" alt="Lakehouse" width="500" height="350">

---
"""))

# Cell 5: Unity Catalog
new_cells.append(md("""## Unity Catalog (Data Organization — like SAS LIBNAMEs)

Unity Catalog is the BCBS TN equivalent of your SAS library structure, with stronger governance:

```
In SAS:                                    In Databricks:
LIBNAME.DATASET                            CATALOG.SCHEMA.TABLE
  |                                          |
  v                                          v
work.pharmacy_claims              ->       my_catalog.pharmacy_bronze.claims_raw
pbm.utilization_mgmt              ->       my_catalog.pharmacy_silver.um_decisions
gold.pmpm_summary                 ->       my_catalog.pharmacy_gold.pmpm_trend
```

**What this gives us:**
- One source of truth (no more "which copy of the eligibility extract did you use?").
- Built-in governance — control who can see PHI/PII at the column level.
- Full lineage and audit trail (essential for regulator-facing impact analyses).
- Searchable catalog so the rest of BCBS TN can self-serve without bothering us for ad-hocs.

<img src="https://www.databricks.com/sites/default/files/2025-05/header-unity-catalog.png?v=1748513086" alt="Unity Catalog" width="500" height="300">

---
"""))

# Cell 6: Medallion architecture
new_cells.append(md("""## Medallion Architecture (Bronze → Silver → Gold)

Maps cleanly onto how your team already thinks about pharmacy data work:

### Bronze (Raw vendor feeds)
- **Like:** Raw PBM extracts, eligibility files, NDC reference loads — exactly as you receive them.
- **Use:** Vendor-feed alignment, anomaly identification at ingest, audit trail for upstream change monitoring.

### Silver (Cleaned, deduplicated, typed)
- **Like:** Your standardized SAS datasets after `PROC SORT NODUPKEY`, type casts, and trims.
- **Use:** Governed, analysis-ready tables for claims, members, pharmacies, drugs.

### Gold (Business-ready analytics tables)
- **Like:** Your final analysis datasets feeding scheduled reports and dashboards.
- **Use:** PMPM trend, UM volume by decision status, program savings, channel mix, impact analyses.

This is where the team will spend most time — and where Databricks gives the biggest lift over SAS.

<img src="https://www.databricks.com/sites/default/files/inline-images/building-data-pipelines-with-delta-lake-120823.png?v=1702318922" alt="Medallion Architecture" width="500" height="350">
"""))

# Cell 7: SETUP heading - keep
new_cells.append(md("# SETUP\nJust run the next couple of cells for setup.\n"))

# Cells 8, 9, 10 — keep code as-is from original
new_cells.append(copy.deepcopy(nb['cells'][8]))
new_cells.append(copy.deepcopy(nb['cells'][9]))
new_cells.append(copy.deepcopy(nb['cells'][10]))

# Cell 11: Roadmap
new_cells.append(md("""# Let's Build Your First Pharmacy Data Pipeline

---

## Workshop Roadmap

```
Bronze Layer    ->    Silver Layer    ->    Gold Layer    ->    Analytics
(Raw vendor      (Cleaned, governed     (Pharmacy-ready    (PMPM trends, UM
 feeds as-is)     pharmacy tables)       analytics tables)  volume, savings)
```

We will follow the **Medallion Architecture** end-to-end:

1. **Bronze**: Ingest raw CSVs (think: PBM extracts) into Delta tables.
2. **Silver**: Clean, deduplicate, and type — what your team already does in SAS DATA steps.
3. **Gold**: Build the pharmacy analytics tables you deliver every month.
4. **Analytics**: Generate insights, charts, and AI/BI dashboards stakeholders can self-serve.

Let's go.
"""))

# Cell 12: Bronze intro
new_cells.append(md("""# Bronze Layer — Ingest Raw Pharmacy Data

---

## What is the Bronze Layer?

Bronze is the landing zone for raw pharmacy data — your PBM extracts, eligibility feeds, and reference files exactly as received. Here we:
- Load source files as-is (CSV, JSON, Parquet).
- Store in **Delta Lake** for ACID transactions (no half-loaded refreshes).
- Apply minimal transformation — schema inference only.
- Keep history for **vendor-feed audit** and reprocessing.

> **Best practice:** Use `COPY INTO` for incremental, idempotent loads. It automatically skips files already loaded — perfect for daily PBM drops.

---
"""))

# Cell 13: Step 1
new_cells.append(md("## Step 1: Verify Source Files\n\nLet's confirm the pharmacy source files are available in our volume:\n"))

# Cell 14: %sql LIST - keep
new_cells.append(copy.deepcopy(nb['cells'][14]))

# Cell 15: COPY INTO understanding
new_cells.append(md("""## Step 2: Load Data with COPY INTO

### What `COPY INTO` does (and why pharmacy teams love it)

`COPY INTO` is the recommended command for loading from cloud storage into Delta tables.

**Why it fits our recurring workflow:**
- **Idempotent**: Re-run safely without duplicating PBM claims.
- **Incremental**: Only loads *new* files — your daily/weekly feed just works.
- **Schema evolution**: Handles new columns (e.g., a new PBM adds a flag) via `mergeSchema`.
- **Atomic**: Either fully succeeds or fully rolls back — no partial loads from a corrupted file.

**Syntax:**
```sql
COPY INTO <table_name>
FROM '<source_path>'
FILEFORMAT = CSV
FORMAT_OPTIONS('header' = 'true', 'inferSchema' = 'true')
COPY_OPTIONS('mergeSchema' = 'true')
```

**SAS analogue:** `PROC IMPORT` for CSVs / `PROC APPEND` for incremental loads — but without manually tracking which files you already loaded.

Docs:
- [COPY INTO Documentation](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/delta-copy-into)
- [COPY INTO Examples](https://learn.microsoft.com/en-us/azure/databricks/ingestion/cloud-object-storage/copy-into/)
"""))

# Cell 16
new_cells.append(md("### Loading Data with SQL\n"))

# Cell 17: COPY INTO code - keep
new_cells.append(copy.deepcopy(nb['cells'][17]))

# Cell 18: PySpark alternative
new_cells.append(md("""### Alternative: Loading Data with PySpark

SQL is great for batch loading. PySpark gives you more programmatic control — useful when you need conditional ingest logic (e.g., only load files newer than the last successful refresh).

**SAS analogue:** Using a `%MACRO` to wrap `PROC IMPORT` calls. PySpark is the same idea — code that decides what/when to load.
"""))

# Cell 19: PySpark code - keep
new_cells.append(copy.deepcopy(nb['cells'][19]))

# Cell 20: Silver intro
new_cells.append(md("""# Silver Layer — Clean, Standardize, Join

---

## What is the Silver Layer?

Silver is where raw pharmacy data becomes **governed, analysis-ready** datasets. This is your `DATA` step / `PROC SORT NODUPKEY` work, but expressed as SQL or PySpark:

- **Clean**: Remove nulls, trim whitespace, fix obvious data-quality issues.
- **Transform**: Cast types (numeric drug spend, date casting for fill dates).
- **Deduplicate**: Drop duplicate fills using business keys (claim_id, NDC).
- **Validate**: Apply pharmacy business rules (e.g., positive drug spend, fill date present).
- **Enrich**: Join eligibility, drug reference, channel.

> **Best practice:** Silver tables should be the **single source of truth** that every recurring report and ad-hoc analysis pulls from. No more `work.claims_v3_final_FINAL.sas7bdat`.

"""))

# Cell 21
new_cells.append(md("""## Step 1: Transform Bronze to Silver (SQL)

We'll clean and transform our Bronze tables. First in **SQL** — closest to your existing `PROC SQL` workflow — then in **PySpark** for cases where business logic is more complex.
"""))

# Cell 22: Silver SQL - keep (schema is the same)
new_cells.append(copy.deepcopy(nb['cells'][22]))

# Cell 23
new_cells.append(md("""## Step 2: Transform with PySpark

Now the same idea in PySpark. Use this pattern when transformations are easier as code than as SQL — e.g., dynamic column lists, complex conditional drug categorization, or reusable functions.

### Example: Clean drug-level line items (procedures table)

We will:
- Strip non-numeric characters from `amount` (sometimes PBMs send `"$123.45"`).
- Drop duplicates on `(claim_id, procedure_code)` — same NDC reported twice on the same claim.
- Add a **drug cost tier** using `CASE WHEN` logic (your `IF-THEN` equivalent).

### SAS analogue
```sas
DATA pharmacy_silver.procedures;
    SET pharmacy_bronze.procedures_raw;
    amount_clean = INPUT(COMPRESS(amount, , 'kd.'), BEST12.);
    IF amount_clean < 100        THEN cost_tier = 'Low';
    ELSE IF amount_clean < 500   THEN cost_tier = 'Medium';
    ELSE IF amount_clean < 1000  THEN cost_tier = 'High';
    ELSE                              cost_tier = 'Very High';
RUN;
PROC SORT DATA=pharmacy_silver.procedures NODUPKEY; BY claim_id procedure_code; RUN;
```
"""))

# Cell 24: PySpark transform code - keep
new_cells.append(copy.deepcopy(nb['cells'][24]))

# NEW: SAS reference cell — Macros, Transpose, Format, Append patterns
new_cells.append(md("""## SAS → Databricks Reference: Macros, Transpose, Append, Formats

Before we move to the Gold layer, here are direct equivalents for the SAS patterns your team uses every week.

### 1. Macro variables (dates and parameters)

**SAS:**
```sas
%LET as_of = %SYSFUNC(today(), yymmddn8.);
%LET lob   = Commercial;

PROC SQL;
    CREATE TABLE rx_recent AS
    SELECT * FROM pbm.claims
    WHERE claim_date <= "&as_of"d AND lob = "&lob";
QUIT;
```

**Databricks (notebook widgets — see the SETUP cell):**
```sql
-- Widgets behave like SAS macro variables, picked up via :paramName syntax
SELECT * FROM payer_silver.claims
WHERE claim_date <= CURRENT_DATE()
  AND member_id IN (
    SELECT member_id FROM payer_silver.members
    WHERE plan_id = :plan_id
  );
```

### 2. Macro date functions

| SAS                                | Databricks SQL                       |
|-----------------------------------|--------------------------------------|
| `%SYSFUNC(today())`               | `CURRENT_DATE()`                     |
| `INTNX('MONTH', today(), -1)`     | `ADD_MONTHS(CURRENT_DATE(), -1)`     |
| `INTNX('YEAR', today(), -1)`      | `ADD_MONTHS(CURRENT_DATE(), -12)`    |
| `INTCK('MONTH', d1, d2)`          | `MONTHS_BETWEEN(d2, d1)`             |
| `MDY(m, d, y)`                    | `MAKE_DATE(y, m, d)`                 |

### 3. PROC TRANSPOSE → SQL `PIVOT`

**SAS:**
```sas
PROC TRANSPOSE DATA=pmpm OUT=pmpm_wide;
    BY claim_month;
    ID lob;
    VAR pmpm;
RUN;
```

**Databricks SQL:**
```sql
SELECT *
FROM (
  SELECT claim_month, lob, pmpm FROM payer_gold.pmpm_by_lob
)
PIVOT (
  SUM(pmpm) FOR lob IN ('Commercial', 'Medicare', 'Exchange')
);
```

### 4. PROC APPEND / SET → `UNION ALL`

**SAS:**
```sas
DATA all_claims;
    SET pbm.claims_2024 pbm.claims_2025;
RUN;
```

**Databricks SQL:**
```sql
SELECT * FROM payer_silver.claims_2024
UNION ALL
SELECT * FROM payer_silver.claims_2025;
```

### 5. PROC FORMAT → `CASE WHEN` or lookup join

**SAS:**
```sas
PROC FORMAT;
    VALUE $channel 'R' = 'Retail'  'M' = 'Mail Order'  'S' = 'Specialty';
RUN;
```

**Databricks SQL:**
```sql
SELECT
  pharmacy_id,
  CASE channel_code
    WHEN 'R' THEN 'Retail'
    WHEN 'M' THEN 'Mail Order'
    WHEN 'S' THEN 'Specialty'
    ELSE 'Unknown'
  END AS channel
FROM payer_silver.pharmacies;
```

### 6. Temporary datasets (`work.foo`) → temp views

**SAS:** `DATA work.recent; SET pbm.claims; WHERE claim_date >= '01JAN2025'd; RUN;`

**Databricks:**
```python
recent = spark.table("payer_silver.claims").filter("claim_date >= '2025-01-01'")
recent.createOrReplaceTempView("recent_claims")  # session-scoped, like work.
```
"""))

# Cell 25: AI Assistant intro
new_cells.append(md("""# Using Databricks AI Assistant

---

Databricks AI Assistant can help you write SQL/PySpark, understand pharmacy data, and troubleshoot issues — useful for the consultative, ad-hoc work the team handles every day.

### How to use it
1. Click the AI Assistant icon.
2. Ask in plain English (e.g., "Convert this SAS PROC SQL to Databricks SQL").
3. Use the suggestions as a starting point — review, adapt, validate against expected pharmacy results.

### Best Practices
- **Be specific**: "Top 10 pharmacies by total drug spend in Q3 2025 for Commercial LOB."
- **Provide table context**: Mention `payer_silver.claims`, `payer_silver.providers`, etc.
- **Iterate**: Refine prompts to fix errors or add filters (e.g., "only Specialty channel").
- **Verify**: Always sanity-check totals against your existing SAS reports during transition.
"""))

# Cell 26: YOUR TURN
new_cells.append(md("""## YOUR TURN (3 mins)
Ask Databricks Assistant: **"How do I calculate total drug spend by pharmacy in SQL?"**

Hint: Join `payer_silver.claims` to `payer_silver.providers` (which represents pharmacies in our data model).
"""))

# Cell 27: Replacement code (drug spend by pharmacy)
new_cells.append(code("""%sql
-- Total drug spend by pharmacy
-- Provider in our schema = pharmacy; specialty = channel (Retail / Mail Order / Specialty)
SELECT
  p.provider_id        AS pharmacy_id,
  p.provider_name      AS pharmacy_name,
  p.specialty          AS channel,
  COUNT(*)             AS claim_count,
  ROUND(SUM(c.total_charge), 2) AS total_drug_spend
FROM
  payer_silver.claims c
  LEFT JOIN payer_silver.providers p
    ON c.provider_id = p.provider_id
GROUP BY p.provider_id, p.provider_name, p.specialty
ORDER BY total_drug_spend DESC;
"""))

# Cell 28: Gold intro - Pharmacy edition
new_cells.append(md("""# Gold Layer — Pharmacy Analytics (the deliverables)

---

## What is the Gold Layer? (For Pharmacy Analytics)

This is where you spend most of your time. Gold tables are your **monthly deliverables** — the analyses stakeholders rely on for pharmacy operations, finance, and strategy.

### What we'll build (mapped to your team's deliverables)

| # | Use case                                              | Maps to team deliverable                  |
|---|-------------------------------------------------------|-------------------------------------------|
| 1 | Drug Spend / Utilization by **LOB and Channel**       | Pharmacy Cost & Utilization Trends        |
| 2 | **PMPM Trending** (drug spend, plan paid, claim count)| Pharmacy Cost & Membership Trends         |
| 3 | **Utilization Management** (volume by decision status)| Utilization Management reporting          |
| 4 | **High-Cost / Polypharmacy Member Identification**    | Risk segmentation & care management input |
| 5 | **Brand vs Generic / Specialty Mix** by demographic   | Drug Type analysis (Brand/Generic/Specialty) |
| 6 | **Pharmacy Data Quality Checks**                       | Vendor-feed oversight, anomaly detection  |
| 7 | **Program Savings & Impact Analysis**                  | Program savings, legislation/market impact|

---

## How this compares to SAS

| Your SAS workflow                       | In Databricks Gold layer                    |
|-----------------------------------------|----------------------------------------------|
| Build final analysis dataset            | `CREATE OR REPLACE TABLE payer_gold.foo`     |
| `PROC SQL` with aggregations            | SQL `SELECT` with `GROUP BY`                 |
| `PROC MEANS` for summary stats          | Aggregate functions (`AVG`, `SUM`, …)        |
| Multiple DATA steps for derivations     | One SQL statement with CTEs                  |
| `%MACRO` for repeated calcs             | Parameterized queries / widgets / Python     |
| Export to Excel for chart               | Built-in `display()` charts + AI/BI dashboards |

---

## Your Pharmacy Analytics Toolbox

Common pharmacy analyses translate cleanly to Databricks:

- **PMPM**: `SUM(plan_paid) / SUM(member_months)`
- **Channel mix**: `GROUP BY` channel + share-of-total via window functions
- **Trending**: `LAG`, `LEAD`, moving averages (your `PROC EXPAND` replacement)
- **Polypharmacy**: `COUNT(DISTINCT drug)` per member
- **Decision-status mix**: `CASE WHEN` + `GROUP BY`
- **Program savings**: pre/post comparison with conditional aggregation

Ready? Let's build.

---
"""))

# Cell 29: Example 1 — Drug Spend / Utilization by LOB and Channel
new_cells.append(md("""## Pharmacy Example 1: Drug Spend & Utilization by Channel

### Business question
**"What is our drug spend and utilization by pharmacy channel and state?"**

This is a **core monthly deliverable** — stakeholders want to see where members are filling (Retail / Mail Order / Specialty) and how spend is distributed. In our data model `providers.specialty` represents **channel**.

### SAS version
```sas
PROC SQL;
    CREATE TABLE channel_summary AS
    SELECT
        p.specialty          AS channel,
        p.state,
        COUNT(*)             AS claim_count,
        SUM(c.total_charge)  AS total_drug_spend,
        ROUND(SUM(c.total_charge) / COUNT(*), 2) AS avg_spend_per_claim
    FROM pbm.claims AS c
    LEFT JOIN pbm.pharmacies AS p
        ON c.provider_id = p.provider_id
    GROUP BY p.specialty, p.state;
QUIT;
```

### Databricks version
Almost identical SQL — just a different LIBNAME (catalog.schema). Let's build it.
"""))

# Cell 30: Example 1 SQL
new_cells.append(code("""%sql
-- PHARMACY ANALYSIS: Drug Spend & Utilization by Channel and State
-- providers.specialty represents channel (Retail / Mail Order / Specialty)

CREATE OR REPLACE TABLE payer_gold.channel_summary AS
SELECT
    p.specialty                                                  AS channel,
    p.state,
    COUNT(*)                                                     AS claim_count,
    ROUND(SUM(c.total_charge), 2)                                AS total_drug_spend,
    ROUND(SUM(c.total_charge) / COUNT(*), 2)                     AS avg_spend_per_claim
FROM payer_silver.claims c
LEFT JOIN payer_silver.providers p
    ON c.provider_id = p.provider_id
GROUP BY p.specialty, p.state;

-- Display results
SELECT
    channel,
    state,
    claim_count,
    total_drug_spend,
    avg_spend_per_claim
FROM payer_gold.channel_summary
ORDER BY total_drug_spend DESC;
"""))

# Cell 31: YOUR TURN with SAS
new_cells.append(md("""## YOUR TURN (3 mins)
Use the SAS script below and ask the Databricks Assistant: **"Convert this SAS script into Databricks SQL and PySpark."**

```sas
PROC SQL;
    CREATE TABLE channel_summary_ranked AS
    SELECT
        channel,
        state,
        SUM(claim_count)        AS claim_count,
        SUM(total_drug_spend)   AS total_drug_spend,
        AVG(avg_spend_per_claim) AS avg_spend_per_claim
    FROM payer_gold.channel_summary
    GROUP BY channel, state
    ORDER BY total_drug_spend DESC;
QUIT;
```
"""))

# Cell 32: PySpark conversion
new_cells.append(code("""from pyspark.sql import functions as F

df = spark.table("payer_gold.channel_summary")

channel_summary_ranked = (
    df.groupBy("channel", "state")
      .agg(
          F.sum("claim_count").alias("claim_count"),
          F.sum("total_drug_spend").alias("total_drug_spend"),
          F.avg("avg_spend_per_claim").alias("avg_spend_per_claim"),
      )
      .orderBy(F.col("total_drug_spend").desc())
)

display(channel_summary_ranked)
"""))

# Cell 33: Example 2 - PMPM Trending
new_cells.append(md("""## Pharmacy Example 2: PMPM Trending (Drug Spend & Utilization)

### Business question
**"How are drug spend, plan paid, and claim counts trending month-over-month and year-over-year?"**

PMPM trending is one of your **scheduled monthly deliverables**. It feeds:
- **Trend factors** for the rate development team
- **Budgeting / forecasting** for finance
- **Anomaly identification** (a sudden spike usually means a vendor-feed change or a clinical event)

### What we'll calculate
```
Month-over-Month (MoM) growth = (this month - last month) / last month
Year-over-Year (YoY)  growth = (this month - same month last year) / same month last year
3-month moving average        = smoothing for noisy months
```

### SAS equivalent
You'd typically use **PROC EXPAND** or `LAG` in a DATA step. In Databricks, we use **window functions** — `LAG()` and `LEAD()` over an ordered partition.

> Don't know window functions yet? Ask the AI Assistant: *"Explain `LAG()` in Databricks SQL with a pharmacy example."*
"""))

# Cell 34: PMPM trending code
new_cells.append(code("""%sql
-- PHARMACY ANALYSIS: Monthly Drug Spend Trending
-- Window functions for MoM and YoY calculations

CREATE OR REPLACE TABLE payer_gold.pharmacy_trend AS
WITH monthly_pharmacy AS (
    -- Step 1: Aggregate pharmacy claims by month
    SELECT
        DATE_TRUNC('MONTH', claim_date)               AS claim_month,
        YEAR(claim_date)                              AS claim_year,
        MONTH(claim_date)                             AS claim_month_num,
        COUNT(*)                                      AS claim_count,
        ROUND(SUM(total_charge), 2)                   AS total_drug_spend,
        ROUND(AVG(total_charge), 2)                   AS avg_spend_per_claim
    FROM payer_silver.claims
    GROUP BY claim_month, claim_year, claim_month_num
)
SELECT
    claim_month,
    claim_count,
    total_drug_spend,
    avg_spend_per_claim,

    -- Month-over-Month
    LAG(total_drug_spend, 1) OVER (ORDER BY claim_month) AS prior_month_spend,
    ROUND(
        (total_drug_spend - LAG(total_drug_spend, 1) OVER (ORDER BY claim_month)) /
        LAG(total_drug_spend, 1) OVER (ORDER BY claim_month) * 100,
        2
    ) AS mom_growth_pct,

    -- Year-over-Year (12 months ago)
    LAG(total_drug_spend, 12) OVER (ORDER BY claim_month) AS prior_year_spend,
    ROUND(
        (total_drug_spend - LAG(total_drug_spend, 12) OVER (ORDER BY claim_month)) /
        LAG(total_drug_spend, 12) OVER (ORDER BY claim_month) * 100,
        2
    ) AS yoy_growth_pct,

    -- 3-month moving average for smoothing
    ROUND(
        AVG(total_drug_spend) OVER (
            ORDER BY claim_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS moving_avg_3mo

FROM monthly_pharmacy
ORDER BY claim_month;

-- Display the trend
SELECT * FROM payer_gold.pharmacy_trend;
"""))

# Cell 35: Example 3 - Utilization Management
new_cells.append(md("""## Pharmacy Example 3: Utilization Management — Volume by Decision Status

### Business question
**"What is our UM claim volume by decision status, and how is it trending?"**

This is a **scheduled deliverable** for the UM team and a frequent ad-hoc request from operations. We use the `claim_status` field on `payer_silver.claims` to represent the **UM decision status** (Approved / Denied / Pending in our model).

### What we'll calculate
- Volume by decision status (Approved / Denied / Pending) by month
- Approval rate (Approved / Total)
- Decision-status mix shifts month-over-month

> **Note on turnaround time**: Real UM turnaround uses the time between **submission** and **decision** dates. Our schema doesn't carry a separate submission date, so the example below shows the *pattern* using `claim_date` minus `member.effective_date` as a placeholder. When you point this at production PBM/UM data, swap in the real `submitted_date` and `decision_date`.

### SAS equivalent
```sas
PROC SQL;
    CREATE TABLE um_volume AS
    SELECT
        INTNX('MONTH', claim_date, 0, 'B') AS claim_month FORMAT=monyy7.,
        UPCASE(claim_status)               AS decision_status,
        COUNT(*)                           AS claim_count
    FROM pbm.claims
    GROUP BY 1, 2;
QUIT;
```
"""))

# Cell 36: UM code (NEW)
new_cells.append(code("""%sql
-- PHARMACY ANALYSIS: Utilization Management — Volume by Decision Status
-- claim_status represents the UM decision status in our model
-- (Production: replace with PBM/UM-system decision codes.)

CREATE OR REPLACE TABLE payer_gold.um_volume AS
WITH base AS (
    SELECT
        DATE_TRUNC('MONTH', c.claim_date)                AS claim_month,
        UPPER(c.claim_status)                             AS decision_status,
        c.claim_id,
        c.total_charge,
        -- Placeholder turnaround proxy: days between member effective and fill date.
        -- Replace with DATEDIFF(DAY, submitted_date, decision_date) in production.
        DATEDIFF(DAY, m.effective_date, c.claim_date)    AS turnaround_days_proxy
    FROM payer_silver.claims c
    INNER JOIN payer_silver.members m
        ON c.member_id = m.member_id
)
SELECT
    claim_month,
    decision_status,
    COUNT(*)                                              AS claim_count,
    ROUND(SUM(total_charge), 2)                           AS total_drug_spend,
    ROUND(AVG(turnaround_days_proxy), 1)                  AS avg_turnaround_days_proxy,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (PARTITION BY claim_month),
        2
    ) AS pct_of_month
FROM base
GROUP BY claim_month, decision_status
ORDER BY claim_month, decision_status;

-- Approval rate roll-up
WITH monthly_status AS (
  SELECT claim_month, decision_status, claim_count
  FROM payer_gold.um_volume
)
SELECT
    claim_month,
    SUM(CASE WHEN decision_status = 'APPROVED' THEN claim_count ELSE 0 END) AS approved,
    SUM(CASE WHEN decision_status = 'DENIED'   THEN claim_count ELSE 0 END) AS denied,
    SUM(CASE WHEN decision_status = 'PENDING'  THEN claim_count ELSE 0 END) AS pending,
    SUM(claim_count)                                                        AS total_claims,
    ROUND(
        SUM(CASE WHEN decision_status = 'APPROVED' THEN claim_count ELSE 0 END) * 100.0 /
        NULLIF(SUM(claim_count), 0),
        2
    ) AS approval_rate_pct
FROM monthly_status
GROUP BY claim_month
ORDER BY claim_month;
"""))

# Cell 37: YOUR TURN
new_cells.append(md("""## YOUR TURN (5 mins)
Work with the Databricks Assistant to extend the UM analysis:

**"For each LOB (`plan_id`), show the monthly approval rate and the average turnaround_days_proxy. Order by claim_month, plan_id."**

Hint: join `claims` to `members` on `member_id`, then `GROUP BY` `DATE_TRUNC('MONTH', claim_date)` and `plan_id`.
"""))

# Cell 38: UM follow-up - aggregate query
new_cells.append(code("""%sql
-- UM volume + approval rate by LOB (plan_id) and month
WITH base AS (
    SELECT
        DATE_TRUNC('MONTH', c.claim_date) AS claim_month,
        m.plan_id                          AS lob,
        UPPER(c.claim_status)              AS decision_status,
        DATEDIFF(DAY, m.effective_date, c.claim_date) AS turnaround_days_proxy,
        c.claim_id
    FROM payer_silver.claims c
    INNER JOIN payer_silver.members m
        ON c.member_id = m.member_id
)
SELECT
    claim_month,
    lob,
    COUNT(*)                                                              AS total_claims,
    SUM(CASE WHEN decision_status = 'APPROVED' THEN 1 ELSE 0 END)         AS approved,
    SUM(CASE WHEN decision_status = 'DENIED'   THEN 1 ELSE 0 END)         AS denied,
    ROUND(
        SUM(CASE WHEN decision_status = 'APPROVED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS approval_rate_pct,
    ROUND(AVG(turnaround_days_proxy), 1)                                  AS avg_turnaround_days_proxy
FROM base
GROUP BY claim_month, lob
ORDER BY claim_month, lob;
"""))

# Cell 39: Example 4 - High-Cost / Polypharmacy Members
new_cells.append(md("""## Pharmacy Example 4: High-Cost & Polypharmacy Member Identification

### Business question
**"Which members are driving our pharmacy cost? Who is on the most distinct medications? Who should clinical programs target first?"**

This analysis supports:
- **Care management & specialty programs** — identify members who would benefit from outreach
- **Trend investigations** — explain a sudden PMPM spike (often a few high-cost specialty members)
- **Program savings analysis** — measure the intervention impact on top-tier members
- **Polypharmacy review** — members on many distinct drugs are clinical-program candidates

### What we'll calculate
- **95th, 90th, 75th percentile** of total drug spend per member
- **Polypharmacy count**: distinct NDCs/drugs per member (using `procedures.procedure_code`)
- **Risk tier classification** for outreach prioritization

### SAS equivalent
```sas
PROC UNIVARIATE DATA=member_summary;
    VAR total_drug_spend;
    OUTPUT OUT=pctiles PCTLPTS=75 90 95 PCTLPRE=p_;
RUN;
```
In Databricks, `PERCENTILE_CONT` does this in a single CTE.
"""))

# Cell 40: high cost / polypharmacy code
new_cells.append(code("""%sql
-- PHARMACY ANALYSIS: High-Cost & Polypharmacy Member Identification

CREATE OR REPLACE TABLE payer_gold.high_cost_members AS
WITH member_summary AS (
    -- Step 1: Aggregate pharmacy claims by member
    SELECT
        c.member_id,
        COUNT(c.claim_id)                       AS claim_count,
        ROUND(SUM(c.total_charge), 2)           AS total_drug_spend,
        ROUND(AVG(c.total_charge), 2)           AS avg_spend_per_claim,
        MIN(c.claim_date)                       AS first_fill_date,
        MAX(c.claim_date)                       AS last_fill_date,
        COUNT(DISTINCT YEAR(c.claim_date))      AS years_with_fills
    FROM payer_silver.claims c
    GROUP BY c.member_id
),
polypharmacy AS (
    -- Step 2: Distinct drugs per member (NDC proxy)
    SELECT
        c.member_id,
        COUNT(DISTINCT pr.procedure_code)       AS distinct_drugs
    FROM payer_silver.claims c
    INNER JOIN payer_silver.procedures pr
        ON c.claim_id = pr.claim_id
    GROUP BY c.member_id
),
risk_threshold AS (
    -- Step 3: Spend percentiles
    SELECT
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_drug_spend) AS p95_threshold,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_drug_spend) AS p90_threshold,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_drug_spend) AS p75_threshold
    FROM member_summary
),
classified AS (
    -- Step 4: Classify members by spend tier and polypharmacy
    SELECT
        ms.*,
        COALESCE(pp.distinct_drugs, 0) AS distinct_drugs,
        CASE
            WHEN ms.total_drug_spend >= rt.p95_threshold THEN 'Tier 1 — Critical (95th+ pct)'
            WHEN ms.total_drug_spend >= rt.p90_threshold THEN 'Tier 2 — High (90th-95th pct)'
            WHEN ms.total_drug_spend >= rt.p75_threshold THEN 'Tier 3 — Moderate (75th-90th pct)'
            ELSE 'Tier 4 — Standard'
        END AS spend_tier,
        CASE
            WHEN COALESCE(pp.distinct_drugs, 0) >= 10 THEN 'Polypharmacy — Refer to clinical review'
            WHEN COALESCE(pp.distinct_drugs, 0) >= 5  THEN 'Watch list'
            ELSE 'Standard'
        END AS polypharmacy_flag,
        rt.p95_threshold,
        rt.p90_threshold,
        rt.p75_threshold
    FROM member_summary ms
    LEFT JOIN polypharmacy pp ON ms.member_id = pp.member_id
    CROSS JOIN risk_threshold rt
)
SELECT
    cl.*,
    m.first_name,
    m.last_name,
    m.gender,
    m.birth_date,
    YEAR(CURRENT_DATE()) - YEAR(m.birth_date) AS age,
    m.plan_id                                  AS lob,
    DATEDIFF(DAY, cl.last_fill_date, CURRENT_DATE()) AS days_since_last_fill
FROM classified cl
INNER JOIN payer_silver.members m
    ON cl.member_id = m.member_id
WHERE cl.total_drug_spend >= cl.p75_threshold  -- focus on moderate-and-above
ORDER BY cl.total_drug_spend DESC;

-- Top 20 members for outreach prioritization
SELECT * FROM payer_gold.high_cost_members LIMIT 20;
"""))

# Cell 41: Example 5 - Brand vs Generic / Specialty mix by demographics
new_cells.append(md("""## Pharmacy Example 5: Drug Type Mix (Brand / Generic / Specialty) by Demographic

### Business question
**"How does our brand / generic / specialty drug mix vary by age and gender? Where can clinical programs steer toward generics?"**

This drives:
- **Channel strategy** (mail-order generics save money)
- **Formulary review** (where is brand utilization highest?)
- **Stakeholder narratives** for trend investigations
- **Program-savings input** (specialty drug spend is the biggest lever)

### How we model "drug type" with the workshop dataset
The workshop dataset doesn't have an explicit brand/generic flag. We will derive a **proxy drug type** from `procedures.amount`:

| Proxy drug type  | Cost band       |
|------------------|-----------------|
| Generic (proxy)  | < $100          |
| Brand   (proxy)  | $100 – $999     |
| Specialty (proxy)| ≥ $1,000        |

> Real production: replace this with your formulary join on NDC/GPI to get the actual brand/generic/specialty flag.

### SAS equivalent
```sas
PROC SQL;
    CREATE TABLE drug_mix AS
    SELECT
        age_band,
        gender,
        drug_type,
        COUNT(*)            AS claim_count,
        SUM(amount)         AS total_drug_spend
    FROM derived_drug_claims
    GROUP BY age_band, gender, drug_type;
QUIT;
```
"""))

# Cell 42: Example 5 code
new_cells.append(code("""%sql
-- PHARMACY ANALYSIS: Drug Type Mix by Demographic
-- Brand/Generic/Specialty proxy derived from procedure (line-item) amount

CREATE OR REPLACE TABLE payer_gold.drug_type_mix AS
WITH drug_lines AS (
    SELECT
        c.claim_id,
        c.member_id,
        pr.procedure_code                        AS ndc_proxy,
        pr.procedure_desc                        AS drug_name,
        pr.amount                                AS drug_cost,
        m.gender,
        m.plan_id                                AS lob,
        YEAR(CURRENT_DATE()) - YEAR(m.birth_date) AS age,
        CASE
            WHEN YEAR(CURRENT_DATE()) - YEAR(m.birth_date) < 18 THEN '0-17'
            WHEN YEAR(CURRENT_DATE()) - YEAR(m.birth_date) < 35 THEN '18-34'
            WHEN YEAR(CURRENT_DATE()) - YEAR(m.birth_date) < 50 THEN '35-49'
            WHEN YEAR(CURRENT_DATE()) - YEAR(m.birth_date) < 65 THEN '50-64'
            ELSE '65+'
        END AS age_band,
        CASE
            WHEN pr.amount <  100  THEN 'Generic (proxy)'
            WHEN pr.amount < 1000  THEN 'Brand (proxy)'
            ELSE 'Specialty (proxy)'
        END AS drug_type
    FROM payer_silver.claims c
    INNER JOIN payer_silver.procedures pr ON c.claim_id   = pr.claim_id
    INNER JOIN payer_silver.members m     ON c.member_id  = m.member_id
),
mix AS (
    SELECT
        age_band,
        gender,
        lob,
        drug_type,
        COUNT(*)                               AS line_count,
        COUNT(DISTINCT member_id)              AS member_count,
        ROUND(SUM(drug_cost), 2)               AS total_drug_spend,
        ROUND(AVG(drug_cost), 2)               AS avg_drug_cost
    FROM drug_lines
    GROUP BY age_band, gender, lob, drug_type
)
SELECT
    *,
    -- Share of spend within demographic cell (age_band x gender x lob)
    ROUND(
        total_drug_spend * 100.0 /
        SUM(total_drug_spend) OVER (PARTITION BY age_band, gender, lob),
        2
    ) AS pct_of_cell_spend,
    -- Credibility tag
    CASE
        WHEN line_count >= 1000 THEN 'Full credibility'
        WHEN line_count >=  500 THEN 'Partial credibility'
        WHEN line_count >=  100 THEN 'Limited credibility'
        ELSE 'Low credibility'
    END AS credibility_indicator
FROM mix
ORDER BY age_band, gender, lob, drug_type;

SELECT * FROM payer_gold.drug_type_mix;
"""))

# Cell 43: Example 6 - Pharmacy Data Quality
new_cells.append(md("""## Pharmacy Example 6: Pharmacy Data-Quality Checks

**Objective:** Catch data-quality issues before they distort PMPM, UM, and savings reports.

This is the **vendor-feed oversight** part of our team's charter — anomaly identification, upstream change monitoring, and stakeholder protection from misinterpreted data.

### Common pharmacy DQ issues
1. **Completeness** — missing claim_id, member_id, fill date, drug spend
2. **Accuracy** — negative drug spend, future fill dates, zero-dollar claims (sometimes a vendor mapping error)
3. **Consistency** — duplicate claim_id rows, conflicting member info across feeds
4. **Timeliness** — recent months underreport (PBM lag) — never trend on incomplete months

### Why this matters for our deliverables
- Bad spend totals propagate into **PMPM trend** and **trend factors**
- Bad UM data inflates or deflates **approval rates**
- Bad NDC mappings undercount **specialty drug spend**
- Regulators and stakeholders question our analyses if DQ caveats aren't documented

### Quick checks
**Completeness**
```sql
SELECT 'Missing claim_id' AS issue, COUNT(*) AS record_count
FROM payer_silver.claims WHERE claim_id IS NULL
UNION ALL
SELECT 'Missing total_charge', COUNT(*) FROM payer_silver.claims WHERE total_charge IS NULL
UNION ALL
SELECT 'Missing member_id',    COUNT(*) FROM payer_silver.claims WHERE member_id   IS NULL;
```

**Accuracy**
```sql
SELECT 'Negative drug spend' AS issue, COUNT(*) AS record_count
FROM payer_silver.claims WHERE total_charge < 0
UNION ALL
SELECT 'Future fill dates',   COUNT(*) FROM payer_silver.claims WHERE claim_date > CURRENT_DATE()
UNION ALL
SELECT 'Zero-dollar claims',  COUNT(*) FROM payer_silver.claims WHERE total_charge = 0;
```

**Duplicates**
```sql
SELECT claim_id, COUNT(*) AS dup_count
FROM payer_silver.claims
GROUP BY claim_id
HAVING COUNT(*) > 1
ORDER BY dup_count DESC;
```

> **Best practice:** Make DQ checks part of the monthly close. Surface anomalies to PBM partners before stakeholders see surprise numbers in their dashboards.

---
"""))

# Cell 44: Quality exercise
new_cells.append(md("""## Exercise: Pharmacy Data-Quality Report

Here is a complete DQ report combining completeness, accuracy, and consistency checks — the kind you'd run at month-end.
"""))

# Cell 45: Quality SQL - keep
new_cells.append(copy.deepcopy(nb['cells'][45]))

# Cell 46: Quality % code - keep
new_cells.append(copy.deepcopy(nb['cells'][46]))

# Cell 47: Example 7 - Program Savings & Impact Analysis (replaces bias detection)
new_cells.append(md("""## Pharmacy Example 7: Program Savings & Impact Analysis

**Objective:** Quantify the impact of pharmacy programs and external events on drug spend, utilization, and PMPM.

This covers two of your team's core deliverables:
- **Program savings** by pharmacy program
- **Impact analyses** based on legislation, market changes, and strategic/operational/financial goals

The pattern is the same: **define a pre-period and a post-period, compare aggregates, attribute the delta**. Below are three reusable templates.

---

### 7A — Program Savings: Pre vs Post Window

**Use case:** Did launching a new mail-order generic-substitution program reduce drug spend?

```sql
-- Compare avg monthly drug spend pre vs post program launch
WITH baseline AS (
    SELECT
        DATE_TRUNC('MONTH', claim_date) AS claim_month,
        SUM(total_charge)               AS monthly_drug_spend
    FROM payer_silver.claims
    WHERE claim_date BETWEEN DATE_SUB(CURRENT_DATE(), 365) AND DATE_SUB(CURRENT_DATE(), 181)
    GROUP BY 1
),
post AS (
    SELECT
        DATE_TRUNC('MONTH', claim_date) AS claim_month,
        SUM(total_charge)               AS monthly_drug_spend
    FROM payer_silver.claims
    WHERE claim_date >= DATE_SUB(CURRENT_DATE(), 180)
    GROUP BY 1
)
SELECT
    'Pre-program (months -12 to -6)'  AS period,
    ROUND(AVG(monthly_drug_spend), 2) AS avg_monthly_spend
FROM baseline
UNION ALL
SELECT
    'Post-program (months -6 to today)',
    ROUND(AVG(monthly_drug_spend), 2)
FROM post;
```

**Interpretation tips for the team's trusted-advisor conversations:**
- Adjust for **member-month exposure** before declaring savings (a drop in spend may just reflect membership decline).
- Always include a **DQ caveat** for the most recent 1–2 months (PBM lag).

---

### 7B — Channel-Mix Shift (Strategic / Operational Goal)

**Use case:** Has the strategic push toward Mail Order succeeded? What share of total spend is each channel capturing this year vs last year?

```sql
SELECT
    YEAR(c.claim_date)                      AS year,
    p.specialty                              AS channel,
    ROUND(SUM(c.total_charge), 2)           AS channel_spend,
    ROUND(
        SUM(c.total_charge) * 100.0 /
        SUM(SUM(c.total_charge)) OVER (PARTITION BY YEAR(c.claim_date)),
        2
    ) AS pct_of_year_spend
FROM payer_silver.claims c
INNER JOIN payer_silver.providers p ON c.provider_id = p.provider_id
GROUP BY YEAR(c.claim_date), p.specialty
ORDER BY year, channel;
```

---

### 7C — Legislative / Market-Change Impact (Cohort Comparison)

**Use case:** A legislative change took effect on date `X`. Did pharmacy spend behavior change for members affected by it?

The pattern: **partition members into affected vs not-affected**, then compare each group's pre/post deltas (a lightweight difference-in-differences). Template:

```sql
-- Define the policy effective date as a parameter (use a widget in production)
WITH params AS (SELECT DATE'2025-01-01' AS effective_date),

-- Tag claims as pre or post the effective date
tagged AS (
    SELECT
        c.member_id,
        c.total_charge,
        CASE WHEN c.claim_date < (SELECT effective_date FROM params)
             THEN 'pre' ELSE 'post' END AS period,
        m.plan_id                                  AS lob
    FROM payer_silver.claims c
    INNER JOIN payer_silver.members m ON c.member_id = m.member_id
),

agg AS (
    SELECT
        lob,
        period,
        ROUND(SUM(total_charge), 2)             AS total_spend,
        COUNT(DISTINCT member_id)               AS members,
        ROUND(SUM(total_charge) /
              NULLIF(COUNT(DISTINCT member_id), 0), 2) AS spend_per_member
    FROM tagged
    GROUP BY lob, period
)

SELECT
    lob,
    MAX(CASE WHEN period = 'pre'  THEN spend_per_member END) AS pre_spend_per_member,
    MAX(CASE WHEN period = 'post' THEN spend_per_member END) AS post_spend_per_member,
    ROUND(
        (MAX(CASE WHEN period = 'post' THEN spend_per_member END) -
         MAX(CASE WHEN period = 'pre'  THEN spend_per_member END)) * 100.0 /
        NULLIF(MAX(CASE WHEN period = 'pre' THEN spend_per_member END), 0),
        2
    ) AS pct_change
FROM agg
GROUP BY lob
ORDER BY lob;
```

---

### Communicating impact analyses to non-technical stakeholders
This is the consultative work your team is known for. A few patterns that translate well:
- Lead with **dollar impact** and **PMPM impact** before going into methodology.
- Always show **DQ caveats** (incomplete months, PBM lag, mapping limitations).
- Be explicit about **what the analysis cannot tell you** (correlation vs causation, confounders).
- Offer a recommended **next step** — that's what makes it consultative, not just descriptive.

---
"""))

# Cell 48: AI/BI - keep
new_cells.append(copy.deepcopy(nb['cells'][48]))

# Cell 49: Genie - keep
new_cells.append(copy.deepcopy(nb['cells'][49]))

# Cell 50: Workshop summary
new_cells.append(md("""# Workshop Summary — You Did It!

## Congratulations, Pharmacy Analytics team!

You've just completed your first Databricks workshop tailored to your charter. Let's review.

---

## What you accomplished today

### 1. Mapped your SAS workflows to Databricks
- Catalog/schema/table = LIBNAME.DATASET
- `PROC SQL` = SQL (almost identical)
- `DATA` step = SQL `SELECT` with `CASE WHEN`, or PySpark
- `%MACRO` = widgets / parameterized SQL / Python
- `PROC TRANSPOSE` = `PIVOT`
- `SET / PROC APPEND` = `UNION ALL`
- `PROC FORMAT` = `CASE WHEN` / lookup join
- `PROC UNIVARIATE` = `PERCENTILE_CONT`
- `PROC EXPAND` = window functions (`LAG`, `LEAD`, moving avg)

### 2. Built the team's deliverables in Databricks
- Drug spend & utilization by **channel and state**
- **PMPM trending** (MoM, YoY, moving average)
- **Utilization Management** volume by decision status + approval rate
- **High-cost / polypharmacy** member identification
- **Drug type mix** (Brand / Generic / Specialty proxy)
- **Pharmacy data-quality** checks for vendor-feed oversight
- **Program savings & impact analysis** templates (pre/post, channel mix, legislative cohort)

### 3. Learned the key SQL techniques
- `GROUP BY` (your `PROC MEANS`)
- `JOIN` (your `MERGE`)
- `CASE WHEN` (your `IF-THEN`)
- `LAG / LEAD` (your trending macros)
- `PERCENTILE_CONT` (your `PROC UNIVARIATE`)
- Window functions (your `PROC EXPAND`)
- CTEs (cleaner than nested temp datasets)

---

## How to use this at work tomorrow

1. **Monthly recurring deliverables** — port your PMPM and channel-mix reports, swap in scheduled refreshes.
2. **Ad-hoc stakeholder requests** — use AI Assistant + Genie to turn around answers same-day.
3. **Vendor-feed oversight** — schedule the Data-Quality checks as part of monthly close.
4. **Program savings tracking** — build the pre/post template once per program, parameterize the dates, and reuse.
5. **Impact analyses** — keep the cohort/diff template handy for legislative and market-change requests.

---

## Key takeaways

### 1. Your SAS knowledge transfers directly
If you know `PROC SQL`, you know ~90% of Databricks SQL. The `DATA` step has direct equivalents.

### 2. Start with SQL
Most pharmacy analyses can be done in pure SQL. PySpark is there when you need programmatic control (dynamic columns, complex business logic, reuse).

### 3. Make Silver the source of truth
Stop emailing `*.sas7bdat` files. Point everything at one governed `payer_silver` schema.

### 4. Lean on AI Assistant + Genie
Faster turnaround on ad-hocs = more time for the consultative analysis that distinguishes the team.

### 5. Document DQ caveats
Especially on recent months (PBM lag), legislative cohorts, and vendor remappings. This is what protects the team's trusted-advisor reputation.

---

## Feedback

We'd love to hear what worked, what didn't, and what you want to learn next.

---

## Thank you, BCBS Tennessee Pharmacy Analytics team!

Ready to translate one of your existing SAS reports into Databricks together?
"""))

# Sanity: original had 51 cells, we should produce 52 (we inserted one new SAS reference cell)
print(f"Original cells: {len(nb['cells'])}")
print(f"New cells:      {len(new_cells)}")

# Replace cells and write
nb['cells'] = new_cells

# Make sure metadata stays minimal & valid
nb.setdefault('metadata', {})
nb['metadata'].setdefault('kernelspec', {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
})
nb['metadata'].setdefault('language_info', {"name": "python"})

DST.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print(f"Wrote: {DST}")
