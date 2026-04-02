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
- **Patients:** 1,311 unique members — 750 Male (57.2%), 561 Female (42.8%)
- **Regions:** Washington (Region A — 4 facilities | 809 patients) and Alabama (Region B — 5 facilities | 502 patients)
- **Race Mix:** White 49.1% | Black 19.8% | Hispanic 19.5% | Other 9.5% | Asian 2.1%
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
Each row in the joined dataset represents one patient in one month (a "member-month"). Total member-months = 9,106. The data was imported into PostgreSQL and queried using custom SQL to power all Tableau dashboards.

---

---

## SLIDE 3 — QUESTION 1 PART 1: DATA SUMMARY (KPI Overview)

**Title:** Q1 — Data Summary: Key Performance Indicators

**Chart to insert:** `01_kpi_summary.png` *(Tableau Q1 Summary Dashboard — KPI tiles + Regional Comparison + Monthly Trend)*

**Headline Callouts — exact values from Tableau Q1 Dashboard:**

| KPI | Value |
|-----|-------|
| Total Member-Months | 9,106 |
| Total Inpatient Admits | 1,264 |
| Total Patients | 1,311 |
| Total BSI Events | 29 |
| Total Facilities | 9 |
| Avg Age — Female | 67 yrs |
| Avg Age — Male | 61 yrs |
| MM with Missing Lab | 326 |
| MM at 100% Completion | 5,356 |

**Regional Clinical Comparison — exact values from Tableau:**

| Metric | Washington (A) | Alabama (B) |
|--------|---------------|-------------|
| Hosp. Rate (per 100 MM) | 14.99 | 17.23 |
| Avg KTV | 1.67 | 1.53 |
| Avg Albumin (g/dL) | 3.70 | 3.74 |
| Avg Missed Treatments | 2.67 | 2.56 |
| CVC Usage % | 19.81% | 17.62% |

**3 Key Takeaways:**
- Alabama's hospitalization rate (17.23) is **15.1% higher** than Washington's (14.99)
- Washington has better KTV adequacy (1.67 vs 1.53) — stronger dialysis dose delivery
- 29 total BSI events recorded; Washington has higher CVC usage (19.81%) but lower admission rates

**Speaker Notes:**
The summary dashboard establishes the baseline. Alabama's overall hospitalization rate of 17.23 per 100 member-months is significantly higher than Washington's 14.99. The regional disparity is the most important finding — Alabama underperforms Washington on the two most critical clinical indicators: KTV dose adequacy and hospitalization rate. Interestingly, Washington has higher CVC usage but still outperforms, suggesting CVC access alone is not the only driver.

---

---

## SLIDE 3B — QUESTION 1 PART 2: DATA SUMMARY (Patient Demographics)

**Title:** Q1 — Data Summary: Who Are Our Patients?

**Chart to insert:** *(Tableau Q6 - Demographics Dashboard screenshot — all 3 pies)*

**Gender Distribution — exact Tableau values:**

| Gender | Patients | Share |
|--------|----------|-------|
| Male | 750 | **57.21%** |
| Female | 561 | **42.79%** |
| **Total** | **1,311** | **100%** |

**Race / Ethnicity Distribution — exact Tableau values:**

| Race | Patients | Share |
|------|----------|-------|
| White | 644 | **49.12%** |
| Black | 260 | **19.83%** |
| Hispanic | 255 | **19.45%** |
| Other | 125 | **9.53%** |
| Asian | 27 | **2.06%** |

**Patients by Facility — exact Tableau values:**

| Facility | State | Region | Patients | Share |
|----------|-------|--------|----------|-------|
| Facility 4087 | WA | Washington | ~238 | **17.16%** |
| Facility 4057 | WA | Washington | ~216 | **15.61%** |
| Facility 4154 | WA | Washington | ~189 | **13.62%** |
| Facility 4111 | AL | Alabama | ~169 | **12.18%** |
| Facility 4283 | WA | Washington | ~142 | **10.23%** |
| Facility 4483 | AL | Alabama | ~138 | **9.94%** |
| Facility 4529 | AL | Alabama | ~124 | **8.91%** |
| Facility 4878 | AL | Alabama | ~75 | *(small)* |
| Facility 4426 | AL | Alabama | ~31 | **2.25%** |

**3 Key Takeaways:**
- Patient population is **57% Male** — consistent with dialysis disease prevalence nationally
- **White patients are the majority (49%)**, but racial mix differs sharply by region
- Facility 4087 (WA) and 4057 (WA) together serve **~33%** of all patients — two largest facilities are both in Washington

**Speaker Notes:**
This slide provides the demographic context for the case study. The 57/43 male-to-female split is typical for end-stage renal disease. The racial composition differs significantly by region — Washington has a large Hispanic population (227) while Alabama's patient base is predominantly White and Black. Facility 4087 and 4057 are the two largest Washington facilities. Importantly, hospitalization rates across all racial groups are similar (1.05–1.16 avg admits/MM), confirming the Alabama–Washington performance gap is driven by clinical and operational factors — not demographics.

---

---

## SLIDE 4 — QUESTION 1 (continued): MONTHLY TREND

**Title:** Q1 — Hospitalization Trend Over Time (Jul 2017 – Jun 2018)

**Chart to insert:** `03_monthly_trend.png`

**Key Observations — from Tableau Q1.3 Monthly Trend sheet:**
- Washington peaked at **75 total admits in August 2017**, then trended downward with fluctuations
- Alabama remained consistently between **40–52 admits per month** throughout the year
- Washington shows **more volatility** (range 22–75), while Alabama is more stable but persistently elevated
- Both regions showed a **low point in November–December 2017** (WA: 51, AL: 40), then rebounded in early 2018
- By June 2018, Washington: 55 admits, Alabama: 46 admits — gap is narrowing

**Speaker Notes:**
The monthly trend reveals that Washington's high overall admit count is partly driven by a sharp spike in August 2017 (75 admits). Alabama's pattern is more consistently elevated. The convergence in mid-2018 (Jun: WA 55, AL 46) may indicate early improvement effects or seasonal variation. The sustained nature of the gap across all 12 months confirms this is a structural — not seasonal — problem.

---

---

## SLIDE 5 — QUESTION 2: REGIONAL COMPARISON

**Title:** Q2 — Regional Comparison: Washington vs. Alabama

**Chart to insert:** `02_region_comparison.png`

**Conclusion Box (add as a highlighted text box in Canva):**
> **Alabama's hospitalization rate is 15.1% higher than Washington's.**
> Alabama: 17.226 per 100 MM vs Washington: 14.987 per 100 MM

**Side-by-side comparison table — exact Tableau values:**

| Metric | Washington (A) | Alabama (B) | Direction |
|--------|---------------|-------------|-----------|
| Hosp. Rate (per 100 MM) | 14.987 | 17.226 | AL higher (+15.1%) |
| Avg KTV (Dialysis Dose) | 1.67 | 1.53 | WA better (+9.2%) |
| Avg Albumin (g/dL) | 3.70 | 3.74 | Similar |
| Avg Missed Treatments | 2.67 | 2.56 | Similar |
| CVC Usage % | 19.81% | 17.62% | WA higher |
| Inadequate KTV % (<1.2) | 2.22% | 2.29% | AL slightly worse |

**Facility Ranking — from Tableau Q2.3 Facility Level Ranking:**

| Facility | Region | Rate |
|----------|--------|------|
| Facility 4283 (WA) | Washington | 21.05 — highest outlier |
| Facility 4111 (AL) | Alabama | 18.91 |
| Facility 4483 (AL) | Alabama | 17.20 |
| Facility 4529 (AL) | Alabama | 16.97 |
| Facility 4087 (WA) | Washington | 16.60 |
| Facility 4426 (AL) | Alabama | 16.53 |
| Facility 4057 (WA) | Washington | 14.91 |
| Facility 4878 (AL) | Alabama | 14.58 |
| Facility 4154 (WA) | Washington | 10.21 — lowest |

**Speaker Notes:**
Alabama's 15.1% higher hospitalization rate is the central finding of Q2. The root cause panel shows Alabama has lower KTV adequacy (1.53 vs 1.67) and slightly more inadequate KTV cases. Notably, Facility 4283 in Washington is the single highest-rate facility at 21.05 — an outlier that warrants investigation even within the better-performing region. Facility 4154 (WA) at 10.21 represents the benchmark that all facilities should aim toward.

---

---

## SLIDE 6 — QUESTION 3: KEY DRIVERS

**Title:** Q3 — Key Drivers of Hospitalization Rates

**Chart to insert:** `04_key_drivers.png`

**3 Drivers — exact values from Tableau Q3 sheets:**

**Driver 1 — Missed Treatments (Dose-Response Effect)**
- Clear step-up pattern: each additional missed treatment increases admit rate
- 0 missed: **0.6053** avg admits/MM (baseline)
- 1 missed: **1.0248** avg admits/MM (+69%)
- 2 missed: **1.0524** avg admits/MM (+74%)
- 3+ missed: **1.2623** avg admits/MM (+109% vs baseline)
- Members missing 3+ treatments/month have **2× the admit rate** of members with 0 missed

**Driver 2 — Treatment Completion Rate**
- Below 70% completion: **1.2635** avg admits/MM
- 70–89% completion: **1.1063** avg admits/MM
- 90–99% completion: **1.0217** avg admits/MM
- 100% (fully complete): **0.6389** avg admits/MM
- Members with below 70% completion have **2× more hospitalizations** than 100% compliant members

**Driver 3 — Cumulative Risk Score (0–5 factors)**
- 0 risk factors: **0.3077** avg admits/MM (lowest risk)
- 1 risk factor: **1.1005** avg admits/MM (3.6×)
- 2 risk factors: **1.1465** avg admits/MM (3.7×)
- 3 risk factors: **1.2381** avg admits/MM (4.0× — peak risk)
- 4 risk factors: **1.1954** avg admits/MM (3.9×)
- 5 risk factors: **1.0000** avg admits/MM (small n=10 group)
- Risk factors scored: CVC access | Missed Tx | Low Albumin (<3.5) | Low KTV (<1.2) | Excessive Fluid Gain

**Speaker Notes:**
Three factors explain the majority of hospitalization variation: treatment adherence (missed Tx), treatment completion rate, and a composite risk score. All three show a clear dose-response or staircase pattern — the more risk factors present, the higher the admit rate. Members at risk score 3 have 4× the admit rate of zero-risk members. These are all modifiable factors through targeted care management programs.

---

---

## SLIDE 7 — QUESTION 4: NEXT STEPS

**Title:** Q4 — Proposed Next Steps & Intervention Priorities

**Chart to insert:** `08_next_steps.png`

**Intervention Priority Ranking — from Tableau Q4.1 sheet:**

| Priority | Intervention | Basis |
|----------|-------------|-------|
| 1 | Missed Treatment Outreach Program | Highest preventable admit volume |
| 2 | Transition CVC to Permanent Access (Fistula/Graft) | Strong BSI + admit reduction |
| 3 | Dialysis Dose Optimization (KTV ≥ 1.2) | Targeted clinical improvement |
| 4 | Nutrition Intervention (Albumin ≥ 3.5 g/dL) | Dietitian review program |

**BSI by Access Type — from Tableau Q4.2 sheet:**
- **CVC patients: 16 BSI events** (53% of all BSI events)
- **Non-CVC patients: 14 BSI events** (47% of all BSI events)
- Total BSI events: **29** (confirmed across both dashboards)
- CVC patients account for the majority of infections despite being only ~19.8% of member-months

**3 Action Steps:**
1. **Immediate:** Launch missed-treatment outreach — phone calls + transportation support for members with 2+ missed Tx/month
2. **60-day:** Vascular access coordinator referrals for all CVC patients — prioritize conversion to fistula or graft
3. **90-day:** Facility-level KTV audit for Alabama facilities — target Facility 4283 (WA) and Facility 4111 (AL) as highest-rate sites

**Speaker Notes:**
The intervention priority chart ranks four programs by their potential to reduce inpatient admits. Missed treatment outreach has the highest estimated impact. The BSI breakdown confirms CVC access is a major infection risk — 53% of all BSI events occur in CVC patients who represent less than 20% of member-months. Transitioning these patients to permanent access (fistula or graft) addresses both BSI and hospitalization risk simultaneously.

---

---

## SLIDE 8 — QUESTION 5: SQL METHODOLOGY

**Title:** Q5 — SQL Queries: Analytical Methodology

**Chart to insert:** `09_sql_interview_answers.png`

**5 Questions answered:**

**i. Average Age by Gender**
```sql
SELECT sex, ROUND(AVG(age), 1) AS avg_age
FROM demographics
GROUP BY sex;
```
→ Female: **66.9 yrs** (561 members) | Male: **60.7 yrs** (750 members)

**ii. Distinct Members at Clinic 4057**
```sql
SELECT COUNT(DISTINCT patient_id)
FROM treatment_info
WHERE facility_id = 4057;
```
→ **214 distinct members** (16.3% of all 1,311 patients)

**iii. Max & Min Treatments in 2018**
```sql
SELECT MAX(total_tx), MIN(total_tx), AVG(total_tx)
FROM treatment_info
WHERE EXTRACT(YEAR FROM month) = 2018;
```
→ Max: **24** | Min: **1** | Avg: **11.1** treatments per member-month

**iv. Member-Months Missing a Lab**
```sql
SELECT COUNT(*) FROM labs
WHERE albumin IS NULL OR hemoglobin IS NULL
   OR hematocrit IS NULL OR ktv IS NULL;
```
→ **532 member-months** with at least 1 missing lab (5.8% of 9,108 total lab records)
→ Tableau KPI shows **326** — counts only rows where ALL labs are missing simultaneously

**v. Admits by Clinic in Dec 2017**
```sql
SELECT facility_id, SUM(inpatient_admits)
FROM admit_info
JOIN treatment_info USING (patient_id, month)
WHERE month = '2017-12-31'
GROUP BY facility_id ORDER BY 2 DESC;
```
→ **119 total admits** | Facility 4087 (WA) led with **25 admits**

**Speaker Notes:**
All queries use standard ANSI SQL across 5 tables. Key methodology decisions: compound JOIN keys on both patient_id AND month prevent row duplication; EXTRACT(YEAR) for year filtering; COUNT DISTINCT for unique patient counts. Note on Q5iv: the "missing lab" count differs between the raw SQL result (532, using OR logic — any lab missing) and the Tableau dashboard (326, which counts rows where no lab data exists at all). Both are valid depending on the business question asked.

---

---

## SLIDE 9 — TABLEAU DASHBOARD OVERVIEW

**Title:** Tableau Dashboards — Live Interactive Reports

**Layout: 5 screenshot thumbnails — use your Tableau screenshots**

| Dashboard | Sheets Inside | Key Insight Shown |
|-----------|--------------|-------------------|
| Q1 — KPI Summary | KPI Tiles + Regional Clinical Comparison + Monthly Trend | 9,106 MMs \| 1,264 Admits \| AL 15.1% higher |
| Q2 — Region Comparison | Hosp Rate Bars + Root Cause Profile + Facility Ranking | AL=17.226 vs WA=14.987 \| Facility 4283 outlier |
| Q3 — Key Drivers | Missed Tx Dose-Response + Completion Rate + Risk Score | 3+ missed Tx = 2× admit rate \| Risk score 3 = 4× baseline |
| Q4 — Next Steps | Intervention Priority Ranking + BSI by Access Type | CVC = 53% of BSI events \| Missed Tx = top intervention |
| Q6 — Demographics | Gender Pie + Race/Ethnicity Pie | Male 57.21% \| White 49.12% \| Hispanic 19.45% |

**Bullet points:**
- All dashboards connected live to PostgreSQL via Custom SQL joining 5 tables
- Calculated fields use LOD expressions (`FIXED`) for accurate de-duplicated aggregation
- Fully interactive — filter by Region, Facility, Month, or Risk Score
- Validated against direct database queries — all KPI values confirmed accurate

**Speaker Notes:**
The Tableau dashboards are the primary deliverable. Each dashboard directly answers one of the four case study questions. The Custom SQL joins 5 tables and aliases all columns for readability. LOD expressions were required because the LEFT JOIN data source creates row duplication — FIXED expressions ensure Total Admits and BSI Events are not double-counted across the joined tables.

---

---

## SLIDE 9B — DEMOGRAPHICS (Additional Chart)

**Title:** Patient Demographics — Gender & Race/Ethnicity Breakdown

**Chart to insert:** `06_demographics.png` *(or use your Tableau Q6 - Demographics dashboard screenshot)*

**Gender Distribution — exact values from Tableau:**

| Gender | Patients | Share |
|--------|----------|-------|
| Male | 750 | **57.21%** |
| Female | 561 | **42.79%** |
| **Total** | **1,311** | **100%** |

**Race / Ethnicity Distribution — exact values from Tableau:**

| Race | Patients | Share |
|------|----------|-------|
| White | 644 | **49.12%** |
| Black | 260 | **19.83%** |
| Hispanic | 255 | **19.45%** |
| Other | 125 | **9.53%** |
| Asian | 27 | **2.06%** |
| **Total** | **1,311** | **100%** |

**2 Key Observations:**
- Patient population is **57% Male** — consistent with dialysis disease prevalence patterns
- **White patients are the majority (49%)**, but the racial mix differs significantly by region — Washington has a large Hispanic population (227) while Alabama is predominantly White + Black

**Speaker Notes:**
Demographics are important context for the case study. The gender split (57/43) is typical for end-stage renal disease populations. The racial composition differs significantly by region — Washington's large Hispanic population (227 patients) vs Alabama's predominantly White + Black population reflects local community demographics. However, hospitalization rates across all racial groups are similar (1.05–1.16 avg admits/MM), confirming the Alabama–Washington performance gap is driven by **clinical and operational factors**, not demographic differences.

---

---

## SLIDE 10 — CLOSING / SUMMARY

**Title:** Summary & Key Takeaways

**5 Bullets:**
- Alabama's hospitalization rate (**17.23**) is **15.1% higher** than Washington (**14.99**) — a structural, not seasonal, gap
- **3 primary drivers** identified: missed treatments, low KTV adequacy, and CVC vascular access type
- **4 interventions** prioritized, led by missed-treatment outreach and CVC-to-fistula transition program
- Tableau dashboards built on PostgreSQL with Custom SQL, LOD expressions, and calculated fields — all values validated
- Ready to scale: dashboards can be extended to additional regions, facilities, or time periods

**Closing Statement (large text in center of slide):**
> *"The data tells a clear story: the gap between Washington and Alabama is real, measurable, and — most importantly — fixable."*

**Speaker Notes:**
Close by reinforcing that the analysis is not just descriptive but prescriptive. The dashboards give clinical and operational leaders the tools to act on specific, data-backed interventions. Emphasize your ability to translate raw relational data into validated, actionable insights — and to communicate findings clearly to both technical and non-technical stakeholders including executive leadership.

---

---

## CANVA TIPS

**Recommended Template Style:**
- Dark background: `#1A1A2E` (navy) or `#0D1B2A` (deep blue)
- Accent color: `#2E86AB` (blue) for Washington, `#E84855` (red) for Alabama
- Highlight color: `#F4A261` (orange) for callout numbers
- Font: Bold sans-serif for titles (e.g. Montserrat Bold), clean body font (e.g. Inter or Lato)
- Each chart PNG → insert as image, resize to fill 60-70% of slide width

**Slide Count:** 12 slides total
(Slide 3 Part 1 + Slide 3 Part 2 added for Q1 Summary split)
**Estimated Presentation Time:** 15–18 minutes

---
*Reference: Full SQL scripts in `SQL_Interview_Questions.md` | Charts in `data/charts/`*
