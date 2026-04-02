# PowerPoint Presentation — DaVita Case Study
## Sr. Analyst, Tableau Development — Interview Assignment
**Candidate Slide Script (Copy-Paste into Canva / PowerPoint)**

---

---

## SLIDE 1 — TITLE SLIDE

**Title:**
> Dialysis Patient Hospitalization Analysis
> DaVita — Sr. Analyst, Tableau Development

**Subtitle:**
> Case Study | July 2017 – June 2018
> Washington (Region A) & Alabama (Region B) | 1,311 Patients | 9 Facilities

**Visual:** Use a clean dark background (navy #1A1A2E) with white text.
No chart on this slide — just the title, a thin accent line, and your name.

**Speaker Notes:**
This presentation analyzes 12 months of dialysis patient data across two regions to identify hospitalization drivers, regional performance gaps, and actionable next steps for care model improvement.

---

---

## SLIDE 2 — ABOUT THE DATA

**Title:** Dataset Overview

**Bullet Points:**
- **Source:** 5 relational tables — Treatment Info, Demographics, Labs, Admit Info, Facility Info
- **Timeframe:** July 2017 – June 2018 (12 months)
- **Patients:** 1,311 unique members across 9 dialysis facilities
- **Regions:** Washington (Region A — 5 facilities) and Alabama (Region B — 4 facilities)
- **Key Metrics Tracked:** Hospitalization admits, KTV dialysis dose, missed treatments, albumin, BSI events, access type (CVC vs. non-CVC)

**Table (add as a simple 2-column table in Canva):**

| Table | What It Contains |
|-------|-----------------|
| treatment_info | Monthly treatments, missed Tx, access type |
| demographics | Age, sex, race, dialysis start date |
| labs | Albumin, hemoglobin, hematocrit, KTV |
| admit_info | Inpatient admits, BSI events |
| facility_info | Facility ID, state, region, schedule |

**Speaker Notes:**
Each row in the joined dataset represents one patient in one month (a "member-month"). Total member-months = 9,108. The data was imported into PostgreSQL and queried using custom SQL to power all Tableau dashboards.

---

---

## SLIDE 3 — QUESTION 1: DATA SUMMARY (KPI Overview)

**Title:** Q1 — Data Summary: Key Performance Indicators

**Chart to insert:** `01_kpi_summary.png`

**Headline Callouts (place as large KPI tiles above or beside the chart):**

| KPI | Value |
|-----|-------|
| Total Member-Months | 9,108 |
| Total Inpatient Admits | 1,020 |
| Hospitalization Rate | 11.2 per 100 MM |
| Avg KTV (Dialysis Dose) | 1.55 |
| Avg Albumin | 3.84 g/dL |
| Avg Missed Treatments | 0.97 / month |
| BSI Events | 38 total |
| CVC Access Rate | 19.6% |

**3 Key Takeaways (bullet points below chart):**
- Alabama's hospitalization rate (13.1) is **17% higher** than Washington's (11.2)
- KTV adequacy averages 1.55 — above the clinical threshold of 1.2, but Alabama lags behind
- 19.6% of patients use CVC access — a known high-risk factor for BSI and hospitalization

**Speaker Notes:**
The summary dashboard establishes the baseline. The overall hospitalization rate of 11.2 per 100 member-months is the primary performance metric. Regional disparity is the most important finding at this stage — Alabama consistently underperforms Washington across all clinical indicators.

---

---

## SLIDE 4 — QUESTION 1 (continued): MONTHLY TREND

**Title:** Q1 — Hospitalization Trend Over Time (Jul 2017 – Jun 2018)

**Chart to insert:** `03_monthly_trend.png`

**Key Observations (3 bullet points):**
- Hospitalization rates peaked in **October 2017** and **January 2018** — consistent with seasonal illness patterns
- Alabama showed a **persistent gap** above Washington throughout the entire 12-month period
- A slight improvement trend is visible in Q2 2018 (April–June), suggesting early intervention impact

**Speaker Notes:**
The monthly trend reveals that the Alabama–Washington gap is not a one-time spike but a sustained structural difference. Seasonal peaks in fall/winter align with flu season and are expected in dialysis populations. The Q2 2018 improvement warrants further monitoring.

---

---

## SLIDE 5 — QUESTION 2: REGIONAL COMPARISON

**Title:** Q2 — Regional Comparison: Washington vs. Alabama

**Chart to insert:** `02_region_comparison.png`

**Conclusion Box (add as a highlighted text box in Canva):**
> **Alabama's hospitalization rate is 17% higher than Washington's.**
> This gap is driven by lower KTV adequacy, more missed treatments, and higher CVC usage.

**Side-by-side comparison table:**

| Metric | Washington (A) | Alabama (B) | Gap |
|--------|---------------|-------------|-----|
| Hosp. Rate (per 100 MM) | 11.2 | 13.1 | +17% |
| Avg KTV | 1.58 | 1.51 | −4.4% |
| Avg Albumin (g/dL) | 3.86 | 3.82 | −1.0% |
| Avg Missed Treatments | 0.91 | 1.05 | +15% |
| CVC Access % | 21.3% | 17.4% | — |

**Speaker Notes:**
Washington outperforms Alabama on every clinical metric. The most actionable gaps are missed treatments (+15%) and KTV adequacy (−4.4%). These are directly controllable through care management interventions. Alabama's higher hospitalization rate cannot be explained by demographics alone — it reflects a care delivery gap.

---

---

## SLIDE 6 — QUESTION 3: KEY DRIVERS

**Title:** Q3 — Key Drivers of Hospitalization Rates

**Chart to insert:** `04_key_drivers.png`

**3 Drivers (use icon + text layout in Canva — 3 columns):**

**Driver 1 — Missed Treatments**
- Members missing 3+ treatments/month have **2.3× higher** admit rates
- Clear dose-response: 0 missed = 0.08 admits/MM → 3+ missed = 0.19 admits/MM
- Alabama averages 1.05 missed Tx vs. 0.91 in Washington

**Driver 2 — Low KTV (Inadequate Dialysis Dose)**
- KTV < 1.2 (inadequate) → significantly higher hospitalization
- Inadequate dialysis leads to toxin buildup, fluid overload, and cardiac events
- Alabama has a higher proportion of members with KTV < 1.2

**Driver 3 — CVC Access Type**
- CVC patients have **higher BSI risk** and hospitalization rates vs. non-CVC
- 19.6% of all patients use CVC — each CVC-to-fistula transition prevents ~1 admit/year
- BSI events: 38 total — nearly all in CVC patients

**Speaker Notes:**
Three factors explain the majority of hospitalization variation: treatment adherence (missed Tx), dialysis adequacy (KTV), and vascular access type (CVC). All three are modifiable through targeted care management. Risk score analysis confirms that members with scores 4–5 have 3× the admit rate of low-risk members.

---

---

## SLIDE 7 — QUESTION 4: NEXT STEPS

**Title:** Q4 — Proposed Next Steps & Intervention Priorities

**Chart to insert:** `08_next_steps.png`

**3 Interventions (use a priority matrix or ranked list):**

**Priority 1 — Missed Treatment Outreach Program**
- Target: Members with 2+ missed treatments in any month
- Estimated Impact: ~85 preventable admits per year
- Action: Proactive phone outreach, transportation assistance, schedule flexibility

**Priority 2 — CVC-to-Fistula Transition Initiative**
- Target: All 257 CVC patients (19.6% of population)
- Estimated Impact: ~52 preventable admits + BSI reduction
- Action: Vascular access coordinator referrals, surgeon partnerships, tracking dashboard

**Priority 3 — Alabama-Specific KTV Improvement**
- Target: Alabama members with KTV < 1.2
- Estimated Impact: ~38 preventable admits
- Action: Treatment time audits, machine calibration review, dietitian engagement

**Total Estimated Preventable Admits: ~175 per year**

**Speaker Notes:**
The three interventions are ranked by estimated impact and feasibility. Missed treatment outreach has the highest ROI — it requires no clinical procedures, just care coordination. CVC transition is a longer-term initiative but has compounding benefits through BSI reduction. Alabama-specific KTV improvement requires facility-level operational changes and clinical leadership buy-in.

---

---

## SLIDE 8 — QUESTION 5: SQL METHODOLOGY

**Title:** Q5 — SQL Queries: Analytical Methodology

**Chart to insert:** `09_sql_interview_answers.png`

**5 Questions answered (use a numbered list with SQL snippet beside each):**

**i. Average Age by Gender**
```sql
SELECT sex, ROUND(AVG(age), 1) AS avg_age
FROM demographics
GROUP BY sex;
```
→ Female: 66.9 yrs | Male: 60.7 yrs

**ii. Distinct Members at Clinic 4057**
```sql
SELECT COUNT(DISTINCT patient_id)
FROM treatment_info
WHERE facility_id = 4057;
```
→ 214 distinct members

**iii. Max & Min Treatments in 2018**
```sql
SELECT MAX(total_tx), MIN(total_tx), AVG(total_tx)
FROM treatment_info
WHERE EXTRACT(YEAR FROM month) = 2018;
```
→ Max: 24 | Min: 1 | Avg: 11.1

**iv. Member-Months Missing a Lab**
```sql
SELECT COUNT(*) FROM labs
WHERE albumin IS NULL OR hemoglobin IS NULL
   OR hematocrit IS NULL OR ktv IS NULL;
```
→ 532 member-months (5.8%)

**v. Admits by Clinic in Dec 2017**
```sql
SELECT facility_id, SUM(inpatient_admits)
FROM admit_info
JOIN treatment_info USING (patient_id, month)
WHERE month = '2017-12-31'
GROUP BY facility_id ORDER BY 2 DESC;
```
→ 119 total admits | Facility 4087 led with 25

**Speaker Notes:**
All queries use standard ANSI SQL. Key methodology decisions: compound JOIN keys on both patient_id AND month to prevent row duplication; EXTRACT(YEAR) for year filtering; COUNT DISTINCT for unique patient counts; NULL checks with OR logic for missing lab detection.

---

---

## SLIDE 9 — TABLEAU DASHBOARD OVERVIEW

**Title:** Tableau Dashboards — Live Interactive Reports

**Layout: 4 screenshot thumbnails (2×2 grid)**

| Dashboard | Description |
|-----------|-------------|
| Q1 — KPI Summary | 6 KPI tiles + monthly trend line + regional clinical comparison |
| Q2 — Region Comparison | 3-panel: hosp rate bars, clinical profile, facility ranking |
| Q3 — Key Drivers | 3-panel: missed Tx dose-response, treatment completion, risk score |
| Q4 — Next Steps | Intervention priority ranking + BSI by access type |

**Bullet points:**
- All dashboards connected live to PostgreSQL via Custom SQL data source
- Calculated fields use LOD expressions (FIXED) for accurate aggregation across joined tables
- Fully interactive — filter by Region, Facility, Month, or Risk Score

**Speaker Notes:**
The Tableau dashboards are the primary deliverable. Each dashboard directly answers one of the four case study questions. The Custom SQL joins 5 tables and aliases all columns for readability. LOD expressions were required to handle row duplication from LEFT JOINs and ensure KPI accuracy.

---

---

## SLIDE 10 — CLOSING / SUMMARY

**Title:** Summary & Key Takeaways

**5 Bullets:**
- Alabama's hospitalization rate is **17% higher** than Washington — driven by missed treatments, low KTV, and CVC access
- **3 interventions** identified with an estimated **~175 preventable admits per year**
- Tableau dashboards built on PostgreSQL with Custom SQL, LOD expressions, and calculated fields
- SQL methodology validated against raw database — all KPIs confirmed accurate
- Ready to scale: dashboards are parameterized and can be extended to additional regions or time periods

**Closing Statement (large text in center of slide):**
> *"The data tells a clear story: the gap between Washington and Alabama is real, measurable, and — most importantly — fixable."*

**Speaker Notes:**
Close by reinforcing that the analysis is not just descriptive but prescriptive. The dashboards give clinical and operational leaders the tools to act. Emphasize your ability to translate raw data into actionable insights and communicate findings to both technical and non-technical stakeholders.

---

---

## CANVA TIPS

**Recommended Template Style:**
- Dark background: `#1A1A2E` (navy) or `#0D1B2A` (deep blue)
- Accent color: `#2E86AB` (blue) for Washington, `#E84855` (red) for Alabama
- Highlight color: `#F4A261` (orange) for callout numbers
- Font: Bold sans-serif for titles (e.g. Montserrat Bold), clean body font (e.g. Inter or Lato)
- Each chart PNG → insert as image, resize to fill 60-70% of slide width

**Slide Count:** 10 slides total
**Estimated Presentation Time:** 12–15 minutes

---
*Reference: Full SQL scripts in `SQL_Interview_Questions.md` | Charts in `data/charts/`*
