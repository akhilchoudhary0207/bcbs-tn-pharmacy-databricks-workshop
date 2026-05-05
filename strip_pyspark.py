"""Remove all PySpark content from the workshop notebook so it is SQL-only.

Changes:
- Drop "Alternative: Loading Data with PySpark" (markdown + code)
- Drop "Step 2: Transform with PySpark" (markdown + code), but keep the
  procedures cleanup logic by adding a SQL equivalent into the existing
  Silver SQL cell.
- Drop the YOUR TURN PySpark answer cell after Example 1, and rewrite
  the YOUR TURN markdown to ask for SAS -> SQL only.
- Strip PySpark mentions in welcome / intro / AI Assistant / summary.
"""
import json
from pathlib import Path

NB = Path("/Users/sunmin.lee/bcbs-tn-pharmacy-workshop/DBX_Workshop_BCBS_TN_Pharmacy_Analytics.ipynb")

nb = json.loads(NB.read_text())

def get_src(cell):
    s = cell.get("source", [])
    return "".join(s) if isinstance(s, list) else s

def set_src(cell, text):
    cell["source"] = text.splitlines(keepends=True)

# 1) Append a SQL `procedures` cleanup to the existing Silver SQL cell
#    (the PySpark cell at index 24 used to do this work).
sql_silver = get_src(nb["cells"][22])
sql_silver += """

-- Procedures (drug-level line items): cast amount, dedupe on (claim_id, NDC proxy),
-- and add a drug cost tier. This was previously a PySpark example;
-- doing it in SQL keeps the workshop SQL-only.
CREATE OR REPLACE TABLE payer_silver.procedures AS
WITH cleaned AS (
    SELECT
        claim_id,
        UPPER(TRIM(procedure_code)) AS procedure_code,
        TRIM(procedure_desc)        AS procedure_desc,
        ROUND(
            CAST(REGEXP_REPLACE(CAST(amount AS STRING), '[^0-9.]', '') AS DOUBLE),
            2
        ) AS amount
    FROM payer_bronze.procedures_raw
    WHERE claim_id IS NOT NULL
)
SELECT
    claim_id,
    procedure_code,
    procedure_desc,
    amount,
    CASE
        WHEN amount <  100  THEN 'Low'
        WHEN amount <  500  THEN 'Medium'
        WHEN amount < 1000  THEN 'High'
        ELSE                     'Very High'
    END AS cost_category
FROM (
    SELECT
        c.*,
        ROW_NUMBER() OVER (
            PARTITION BY claim_id, procedure_code
            ORDER BY amount DESC
        ) AS rn
    FROM cleaned c
    WHERE amount > 0
) dedup
WHERE rn = 1;

-- Quick distribution check
SELECT cost_category, COUNT(*) AS line_count
FROM payer_silver.procedures
GROUP BY cost_category
ORDER BY cost_category;
"""
set_src(nb["cells"][22], sql_silver)

# 2) Rewrite cell 21 markdown ("Step 1") to drop the SQL+PySpark phrasing.
set_src(nb["cells"][21], """## Step 1: Transform Bronze to Silver (SQL)

We'll clean and transform our Bronze tables in SQL — closest to your existing `PROC SQL` workflow. The same SQL cell below also covers the drug-level line-item cleanup (procedures), so we end up with all four Silver tables: members, claims, providers, and procedures.
""")

# 3) Rewrite the YOUR TURN markdown after Example 1 to ask for SAS -> SQL only.
set_src(nb["cells"][32], """## YOUR TURN (3 mins)
Use the SAS script below and ask the Databricks Assistant: **"Convert this SAS script into Databricks SQL."**

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
""")

# 4) Replace the PySpark answer code (cell 33) with a SQL answer.
set_src(nb["cells"][33], """%sql
-- Databricks SQL equivalent of the SAS PROC SQL above
SELECT
    channel,
    state,
    SUM(claim_count)         AS claim_count,
    SUM(total_drug_spend)    AS total_drug_spend,
    AVG(avg_spend_per_claim) AS avg_spend_per_claim
FROM payer_gold.channel_summary
GROUP BY channel, state
ORDER BY total_drug_spend DESC;
""")
# Make sure the cell type is `code` (it was already, but be defensive).
nb["cells"][33]["cell_type"] = "code"
nb["cells"][33].setdefault("metadata", {})
nb["cells"][33].setdefault("execution_count", None)
nb["cells"][33].setdefault("outputs", [])

# 5) Strip PySpark from cell 1 (welcome objectives).
welcome = get_src(nb["cells"][1])
welcome = welcome.replace(
    "Load and query pharmacy claims data using **SQL and PySpark**.",
    "Load and query pharmacy claims data using **SQL**.",
)
set_src(nb["cells"][1], welcome)

# 6) Strip PySpark row from the SAS comparison table in cell 3.
intro = get_src(nb["cells"][3])
intro = intro.replace(
    "| `DATA` step (filter / derive) | SQL `SELECT` with `CASE WHEN`, or PySpark `withColumn` | Easy |",
    "| `DATA` step (filter / derive) | SQL `SELECT` with `CASE WHEN` | Easy |",
)
set_src(nb["cells"][3], intro)

# 7) Strip PySpark mentions in the AI Assistant intro (cell 26).
ai = get_src(nb["cells"][26])
ai = ai.replace(
    "Databricks AI Assistant can help you write SQL/PySpark, understand pharmacy data,",
    "Databricks AI Assistant can help you write SQL, understand pharmacy data,",
)
ai = ai.replace(
    '2. Ask in plain English (e.g., "Convert this SAS PROC SQL to Databricks SQL").',
    '2. Ask in plain English (e.g., "Convert this SAS PROC SQL to Databricks SQL").',
)
set_src(nb["cells"][26], ai)

# 8) Strip PySpark mentions in the Workshop Summary (last cell).
summary = get_src(nb["cells"][-1])
summary = summary.replace(
    "### 2. Start with SQL\nMost pharmacy analyses can be done in pure SQL. PySpark is there when you need programmatic control (dynamic columns, complex business logic, reuse).",
    "### 2. SQL is enough for most pharmacy work\nEvery example in this workshop is SQL — `PROC SQL` translates almost directly. Reach for Python only when you need orchestration or non-SQL libraries.",
)
set_src(nb["cells"][-1], summary)

# 9) Now drop the four PySpark-only cells. Drop in reverse order so indices stay valid.
#    18 = "Alternative: Loading Data with PySpark" markdown
#    19 = PySpark loading code
#    23 = "Step 2: Transform with PySpark" markdown
#    24 = PySpark procedures transform code
to_drop = sorted([18, 19, 23, 24], reverse=True)
for idx in to_drop:
    del nb["cells"][idx]

print(f"Final cell count: {len(nb['cells'])}")
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print(f"Wrote: {NB}")
