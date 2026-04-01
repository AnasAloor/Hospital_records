# SQL Interview Questions — DaVita Case Study

**Candidate Reference Document**
**Dataset:** July 2017 – June 2018 | 1,311 Patients | 9 Facilities | Washington & Alabama

---

## Question i — Average Age of Members by Gender

**Business Question:** What is the average age of members by gender?

```sql
SELECT
    CASE sex
        WHEN 'M' THEN 'Male'
        WHEN 'F' THEN 'Female'
        ELSE sex
    END                              AS gender,
    ROUND(AVG(age)::numeric, 1)      AS avg_age,
    COUNT(DISTINCT patient_id)       AS total_members
FROM demographics
WHERE age IS NOT NULL
GROUP BY sex
ORDER BY sex;
```

**Answer:**


| Gender | Avg Age | Members |
| ------ | ------- | ------- |
| Female | 66.9    | 561     |
| Male   | 60.7    | 750     |


**Methodology:** Aggregate AVG on the `age` column from the `demographics` table, grouped by `sex`. CASE statement converts M/F codes to readable labels. NULL ages excluded via WHERE clause.

---

## Question ii — Distinct Members Treated at Clinic 4057

**Business Question:** How many distinct members were treated at clinic 4057 in the dataset timeframe?

```sql
SELECT
    COUNT(DISTINCT patient_id) AS distinct_members
FROM treatment_info
WHERE facility_id = 4057;
```

**Answer:** **214 distinct members**

**Methodology:** COUNT DISTINCT on `patient_id` in `treatment_info` filtered by `facility_id = 4057`. DISTINCT ensures each patient is counted once even if they had multiple monthly visits.

---

## Question iii — Maximum and Minimum Treatments in 2018

**Business Question:** What is the maximum and minimum number of treatments a member had in 2018?

```sql
SELECT
    MAX(total_tx)                        AS max_treatments,
    MIN(total_tx)                        AS min_treatments,
    ROUND(AVG(total_tx)::numeric, 1)     AS avg_treatments
FROM treatment_info
WHERE EXTRACT(YEAR FROM month) = 2018;
```

**Answer:**


| Metric             | Value |
| ------------------ | ----- |
| Maximum Treatments | 24    |
| Minimum Treatments | 1     |
| Average Treatments | 11.1  |


**Methodology:** MAX and MIN aggregate functions on `total_tx` (total treatments per member per month) from `treatment_info`. Filtered to 2018 using EXTRACT(YEAR FROM month). Each row represents one member's treatments in one month.

---

## Question iv — Member-Months Missing At Least 1 Lab Value

**Business Question:** How many member-months were missing at least 1 lab value?

```sql
SELECT
    COUNT(*)                                    AS missing_lab_mm,
    (SELECT COUNT(*) FROM labs)                 AS total_mm,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM labs)::numeric, 1
    )                                           AS pct_missing
FROM labs
WHERE albumin    IS NULL
   OR hemoglobin IS NULL
   OR hematocrit IS NULL
   OR ktv        IS NULL;
```

**Answer:**


| Metric                         | Value |
| ------------------------------ | ----- |
| Member-Months with Missing Lab | 532   |
| Total Member-Months            | 9,108 |
| Percentage Missing             | 5.8%  |


**Methodology:** COUNT rows from `labs` table where ANY of the 4 key lab values (albumin, hemoglobin, hematocrit, KTV) is NULL. OR logic captures rows missing at least one value. Subquery calculates total for percentage.

---

## Question v — Admits by Clinic in December 2017

**Business Question:** How many admits were there for members by clinic in December 2017?

```sql
SELECT
    ti.facility_id,
    fi.state,
    CASE fi.region_id
        WHEN 'A' THEN 'Washington (Region A)'
        WHEN 'B' THEN 'Alabama (Region B)'
    END                              AS region,
    COUNT(DISTINCT ai.patient_id)    AS distinct_members,
    SUM(ai.inpatient_admits)         AS total_admits
FROM admit_info ai
JOIN treatment_info ti
    ON ai.patient_id = ti.patient_id
    AND ai.month     = ti.month
JOIN facility_info fi
    ON ti.facility_id = fi.facility_id
WHERE ai.month = '2017-12-31'
GROUP BY ti.facility_id, fi.state, fi.region_id
ORDER BY total_admits DESC;
```

**Answer:**


| Facility  | State | Region     | Members | Admits  |
| --------- | ----- | ---------- | ------- | ------- |
| 4087      | WA    | Washington | 135     | 25      |
| 4057      | WA    | Washington | 134     | 19      |
| 4283      | WA    | Washington | 71      | 17      |
| 4111      | AL    | Alabama    | 106     | 15      |
| 4529      | AL    | Alabama    | 64      | 14      |
| 4154      | WA    | Washington | 123     | 10      |
| 4483      | AL    | Alabama    | 67      | 8       |
| 4426      | AL    | Alabama    | 21      | 6       |
| 4878      | AL    | Alabama    | 54      | 5       |
| **Total** |       |            |         | **119** |


**Methodology:** Three-table JOIN — `admit_info` (admits) → `treatment_info` (facility assignment) → `facility_info` (state/region). Compound JOIN key on both `patient_id` AND `month` ensures correct month-level matching. Filtered to December 2017 (stored as 2017-12-31, end-of-month format).

---

## Notes on Methodology

1. **Compound JOIN keys:** All joins between patient-level tables use BOTH `patient_id` AND `month` to ensure month-level accuracy and avoid row duplication.
2. **Date format:** Months are stored as end-of-month dates (e.g. `2017-12-31`). Use `EXTRACT(YEAR FROM month)` or exact date match accordingly.
3. **DISTINCT vs COUNT:** Use `COUNT(DISTINCT patient_id)` when counting unique patients; use `COUNT(*)` for member-months (one row per patient per month).
4. **NULL handling:** Always filter or account for NULLs in lab values — 532 member-months (5.8%) have at least one missing lab.
5. **Code mappings:** Region A = Washington, Region B = Alabama; Sex M = Male, F = Female.

