# Tableau Custom SQL Query — Documentation

**Project:** DaVita Dialysis Patient Analytics — Case Study  
**Database:** `Hospital_records` (PostgreSQL, localhost:5432)  
**Used In:** Tableau Desktop → Data Source → New Custom SQL

---

## The Query

```sql
SELECT
    ti.month,
    ti.patient_id,
    ti.access_type,
    ti.facility_id,
    ti.assigned_facility_flag,
    ti.total_tx,
    ti.total_mtx,
    ti.total_scheduled_tx,
    ti.tx_percent_excessive_fluid_gain,
    ti.frequent_excessive_fluid_gain_flag,
    ti.tx_percent_pw_above_tw,
    ti.frequent_pw_above_tw_flag,

    d.age,
    d.sex,
    d.race,
    d.fdode,

    l.albumin,
    l.hemoglobin,
    l.hematocrit,
    l.ktv_type,
    l.ktv,

    ai.inpatient_admits,
    ai.bsi_event,

    fi.state,
    fi.region_id,
    fi.date_open,
    fi.monday,
    fi.tuesday,
    fi.wednesday,
    fi.thursday,
    fi.friday,
    fi.saturday,
    fi.sunday

FROM treatment_info ti
LEFT JOIN demographics  d  ON ti.patient_id = d.patient_id  AND ti.month = d.month
LEFT JOIN labs          l  ON ti.patient_id = l.patient_id  AND ti.month = l.month
LEFT JOIN admit_info    ai ON ti.patient_id = ai.patient_id AND ti.month = ai.month
LEFT JOIN facility_info fi ON ti.facility_id = fi.facility_id
```

---

## Purpose

This query creates a single unified analytical dataset by joining all 5 database tables together. Instead of querying each table separately, it produces one flat table with every patient's treatment, lab, admission, and facility data in a single row per patient per month — ready for Tableau to visualize directly.

---

## Table Roles

| Table | Role | Rows |
|---|---|---|
| `treatment_info` | **Primary/Driving table** — every patient-month record lives here | 9,526 |
| `demographics` | Patient attributes — age, sex, race, first dialysis date | 9,106 |
| `labs` | Monthly lab results — albumin, hemoglobin, KTV | 9,108 |
| `admit_info` | Hospitalization events — inpatient admits, BSI events | 9,106 |
| `facility_info` | Clinic reference data — state, region, operating days | 9 |

---

## Join Logic Explained

### Why `treatment_info` is the Driving Table

`treatment_info` is the most complete table — it has a record for every patient in every month, and it contains both `patient_id` and `facility_id`, making it the natural bridge to all other tables. All other tables are joined to it as dependents.

### Why LEFT JOIN (not INNER JOIN)

A LEFT JOIN keeps all rows from `treatment_info` even if a matching row does not exist in the other table. This is critical because:

- Some patients have a treatment record but no lab result that month (532 member-months have missing labs)
- Some patients have no hospitalization that month — `NULL` inpatient_admits is valid and means zero admits
- Using INNER JOIN would silently drop those rows and produce biased hospitalization rate calculations

### Why Join on Both `patient_id` AND `month`

```sql
LEFT JOIN demographics d ON ti.patient_id = d.patient_id AND ti.month = d.month
```

The dataset is longitudinal — the same patient appears across 12 months (July 2017 – June 2018). Joining on `patient_id` alone would create a many-to-many explosion, matching each treatment row to all 12 demographic rows for that patient. Adding `month` ensures a precise one-to-one match per patient per month.

### Why `facility_info` Uses a Single-Field Join

```sql
LEFT JOIN facility_info fi ON ti.facility_id = fi.facility_id
```

`facility_info` is a reference/lookup table with one row per clinic (only 9 rows total). There is no month dimension here, so a single field join is correct. Every treatment row gets the clinic's region, state, and operating schedule appended automatically.

---

## Column Selection Strategy

- Columns are prefixed by table alias (`ti.`, `d.`, `l.`, `ai.`, `fi.`) to make the source of each column explicit and avoid ambiguity — both `treatment_info` and `demographics` have `patient_id` and `month`, so the prefix removes any confusion.
- Only analytically relevant columns are selected. Duplicate keys already represented in `treatment_info` (e.g., `facility_id`) are not re-selected from `facility_info`.

---

## Output

| Property | Value |
|---|---|
| Total rows | 9,526 (one per patient per month) |
| Total columns | 30+ |
| Grain | Patient × Month |
| Date range | July 2017 – June 2018 (12 months) |
| Distinct patients | 1,311 |
| Facilities covered | 9 (4 in Region A / WA, 5 in Region B / AL) |

---

## Interview Q&A

**Q: Why did you use a LEFT JOIN?**

> I used LEFT JOINs to preserve all treatment records as the base. Some patients have missing lab values or no hospitalizations in a given month — that is clinically meaningful data. An INNER JOIN would silently exclude those patients and bias the hospitalization rate calculations.

**Q: Why is `treatment_info` the driving table?**

> `treatment_info` is the most granular and complete table — it captures every patient-month combination and contains the `facility_id` needed to link to clinic-level data. It is the natural hub that connects patient demographics, lab results, and admission events.

**Q: Why join on both `patient_id` AND `month`?**

> The dataset is longitudinal — the same patient appears across 12 months. Joining on `patient_id` alone would create a many-to-many explosion, matching each treatment row to all 12 demographic rows for that patient. The compound key ensures a precise one-to-one match per patient per month.

**Q: What does this query produce?**

> It produces one row per patient per month — a fully denormalized analytical table with 9,526 rows and 30+ columns covering treatment compliance, lab values, hospitalization events, and facility attributes. This is the foundation for all visualizations and metrics in the analysis.
