# El-Sharnouby Group — BI & AI Dashboard 📊

**Live dashboard:** https://sharnouby-bi.streamlit.app  (English / العربية)

HVIA Task 02 · Business Intelligence & AI Applications Challenge · by **Shahd Ibrahim**

> **السؤال:** مبيعات الشرنوبي بتزيد كل سنة… طب الربح فين؟
> **The question:** sales grow every year — so where is the profit?

---

## The answer in one line
**7 actions could add ~9.8M EGP of gross profit a year (+43%)** — from 23.1M to 32.9M — and every number has its assumption written next to it, so anyone can change it in the dashboard.

## What I found
| Area | Finding |
|---|---|
| Sales | Discounts were **2.8x gross profit**; orders with 32–38% discount earn only 8.6% margin |
| Inventory | **Half the stock is excess** (7.9M of 15.4M EGP) while wholesale stockout days grew **161 → 599** |
| Factory | 83.7% of orders on time; sewing + finishing cause **68%** of delay days |
| Quality | Poor quality costs **31% of gross profit** (20.1M EGP in 3 years) |
| Marketing | Platforms claim **14x** the sales that actually happened; real lift during campaigns ≈ 0% |
| Suppliers | Two suppliers late on **80%+** of orders since 2025 — the factory slips a quarter later |
| Size & fit | **#1** reason in returns (37% of refunds), in support tickets (21%) and in QC defects |

## The 8 apps
1. **Executive Command Center** — KPIs, alerts, and a live profit bridge (waterfall) with what-if sliders
2. **Smart Inventory & Replenishment** — AI demand forecast (19% more accurate than "same as last year"), reorder plan, internal transfers
3. **Customer 360 & Retention** — RFM segments, cohorts, customer lookup, win-back test list (test vs control)
4. **Factory Digital Twin** — what-if per production stage, cost of poor quality, printing machine priority
5. **Marketing Attribution & Growth** — claimed vs real sales, ROAS, budget simulator
6. **Branch Intelligence & Expansion** — channel value and where to open the next store
7. **Procurement & Supplier Risk** — adjustable supplier risk score, material cost trends
8. **Size & Fit Intelligence** *(built without being asked)* — a working Fit Assistant prototype

## Honest by design
- The AI forecast was tested on 3 months it never saw before being used.
- A churn model scored **AUC 0.51** (a coin flip), so it was **rejected** — a control-group test replaces it.
- Cost of poor quality is counted conservatively, with no double counting.

## Tech
Python · pandas · scikit-learn (HistGradientBoosting) · Plotly · Streamlit

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure
```
app.py          menu + language switch
utils.py        data loading + every calculation (one place only)
views/          one file per app
data/           cleaned data (compressed)
```

## Data note
The task uses a **modeled / anonymized training dataset** (20 files, Oct 2023 – Sep 2026), not real customer or supplier records.
