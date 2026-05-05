# BCBS Tennessee — Pharmacy Analytics Databricks Workshop

Workshop materials tailored for the BCBS Tennessee **Pharmacy Analytics** team — SAS users transitioning to Databricks.

## Contents
- `DBX_Workshop_BCBS_TN_Pharmacy_Analytics.ipynb` — hands-on Databricks notebook (Bronze → Silver → Gold, with 7 pharmacy use cases)
- `BCBS_TN_Pharmacy_Workshop_Slides.pdf` — companion slide deck (15 slides, PDF export)
- [Editable Google Slides version](https://docs.google.com/presentation/d/1SjYEayZECMWUNhaUyVAV8xBaPgH8vDUf70inrxyO6Ec/edit)
- `build_notebook.py` — script that produced the notebook by reframing [bigdatavik/databricksfirststeps](https://github.com/bigdatavik/databricksfirststeps) for the pharmacy domain

## Source
Built on top of Vik's Actuaries workshop notebook from [bigdatavik/databricksfirststeps](https://github.com/bigdatavik/databricksfirststeps/blob/main/past%20labs/DBX%20Workshop_Actuaries_11072025_answer.ipynb). Same dataset; narrative and Gold-layer use cases rewritten for BCBS TN Pharmacy Analytics.

## Schema reframing for the pharmacy context
| Table       | Pharmacy mapping                                                |
|-------------|-----------------------------------------------------------------|
| `claims`    | Pharmacy claim header (drug spend, decision status, fill date) |
| `providers` | Pharmacies — `specialty` = channel (Retail / Mail Order / Specialty) |
| `procedures`| Drug-level line items — `procedure_code` ≈ NDC/GPI            |
| `members`   | Plan enrollees — `plan_id` maps to LOB                        |

## Gold-layer use cases
1. Drug spend & utilization by channel
2. PMPM trending (drug spend, plan paid, claim count)
3. Utilization Management — volume by decision status
4. High-cost / polypharmacy member identification
5. Drug type mix (Brand / Generic / Specialty proxy)
6. Pharmacy data-quality checks
7. Program savings & impact analysis (legislation, market changes)

