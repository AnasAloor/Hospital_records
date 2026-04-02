"""
Compare Python chart values vs Tableau values to find discrepancies.
Tableau uses: treatment_info as base, LEFT JOINs to all other tables.
Python uses: admit_info as base, INNER JOINs — this causes the mismatch.
"""
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    print("=" * 65)
    print("  DISCREPANCY ANALYSIS: Python (INNER JOIN) vs Tableau (LEFT JOIN)")
    print("=" * 65)

    # ── KPI: Total Member-Months ──────────────────────────────────────
    # Python uses: COUNT(*) FROM admit_info  → only rows in admit_info
    # Tableau uses: COUNT(*) FROM treatment_info (base) → all rows
    py_mm   = conn.execute(text("SELECT COUNT(*) FROM admit_info")).scalar()
    tab_mm  = conn.execute(text("SELECT COUNT(*) FROM treatment_info")).scalar()
    print(f"\n[KPI] Total Member-Months")
    print(f"  Python  (admit_info base)      : {py_mm:,}")
    print(f"  Tableau (treatment_info base)  : {tab_mm:,}")
    print(f"  Tableau shows: 9,106 → matches treatment_info")

    # ── KPI: Total Admits ─────────────────────────────────────────────
    py_admits  = conn.execute(text("SELECT SUM(inpatient_admits) FROM admit_info")).scalar()
    tab_admits = conn.execute(text("SELECT SUM(inpatient_admits) FROM admit_info")).scalar()
    print(f"\n[KPI] Total Admits")
    print(f"  Python  : {int(py_admits):,}")
    print(f"  Tableau : 1,264 (from screenshot)")
    print(f"  Raw DB  : {int(tab_admits):,}")

    # ── KPI: BSI Events ───────────────────────────────────────────────
    bsi = conn.execute(text("SELECT SUM(bsi_event) FROM admit_info")).scalar()
    print(f"\n[KPI] BSI Events")
    print(f"  Python  : {int(bsi)}")
    print(f"  Tableau : 29 (from screenshot)")

    # ── KPI: MM with Missing Lab ──────────────────────────────────────
    py_miss = conn.execute(text("""
        SELECT COUNT(*) FROM labs
        WHERE albumin IS NULL OR hemoglobin IS NULL OR hematocrit IS NULL OR ktv IS NULL
    """)).scalar()
    tab_miss = conn.execute(text("""
        SELECT COUNT(*) FROM treatment_info ti
        LEFT JOIN labs l ON ti.patient_id=l.patient_id AND ti.month=l.month
        WHERE l.albumin IS NULL OR l.hemoglobin IS NULL OR l.hematocrit IS NULL OR l.ktv IS NULL
    """)).scalar()
    print(f"\n[KPI] MM with Missing Lab")
    print(f"  Python  (labs base)            : {py_miss:,}")
    print(f"  Tableau (treatment_info + LEFT): {tab_miss:,}")
    print(f"  Tableau shows: 326")

    # ── KPI: MM at 100% Completion ────────────────────────────────────
    py_comp = conn.execute(text("""
        SELECT COUNT(*) FROM treatment_info
        WHERE total_scheduled_tx>0 AND total_tx>=total_scheduled_tx
    """)).scalar()
    print(f"\n[KPI] MM at 100% Completion")
    print(f"  Python  : {py_comp:,}")
    print(f"  Tableau : 5,356 (from screenshot)")

    # ── Q2: Hosp Rate by Region ───────────────────────────────────────
    print(f"\n[Q2] Hospitalization Rate by Region")
    # Python method: admit_info base, INNER JOIN
    py_rates = conn.execute(text("""
        SELECT fi.region_id,
               COUNT(ai.patient_id) AS mm,
               SUM(ai.inpatient_admits) AS admits,
               ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ai.patient_id))::numeric,3) AS rate
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)).fetchall()
    # Tableau method: treatment_info base, LEFT JOIN
    tab_rates = conn.execute(text("""
        SELECT fi.region_id,
               COUNT(ti.patient_id) AS mm,
               SUM(ai.inpatient_admits) AS admits,
               ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ti.patient_id))::numeric,3) AS rate
        FROM treatment_info ti
        LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
        JOIN facility_info fi   ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)).fetchall()
    region_map = {"A": "Washington", "B": "Alabama"}
    print(f"  {'Region':<12} {'Python MM':>10} {'Python Rate':>12} {'Tableau MM':>10} {'Tableau Rate':>12}")
    for py, tab in zip(py_rates, tab_rates):
        print(f"  {region_map[py[0]]:<12} {py[1]:>10,} {float(py[3]):>12.3f} {tab[1]:>10,} {float(tab[3]):>12.3f}")
    print(f"  Tableau screenshot shows: Alabama=17.226, Washington=14.987")

    # ── Q2 Root Cause: CVC%, Inadequate KTV%, Avg Missed Tx ──────────
    print(f"\n[Q2 Root Cause] CVC%, Inadequate KTV%, Avg Missed Tx by Region")
    # Python: joins labs + treatment_info, filters WHERE ktv IS NOT NULL
    py_rc = conn.execute(text("""
        SELECT fi.region_id,
               ROUND((SUM(CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,2) AS cvc_pct,
               ROUND((SUM(CASE WHEN l.ktv<1.2 THEN 1 ELSE 0 END)*100.0/COUNT(l.ktv))::numeric,2) AS bad_ktv_pct,
               ROUND(AVG(ti.total_mtx)::numeric,2) AS avg_missed
        FROM treatment_info ti
        JOIN labs l           ON ti.patient_id=l.patient_id AND ti.month=l.month
        JOIN facility_info fi ON ti.facility_id=fi.facility_id
        WHERE l.ktv IS NOT NULL
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)).fetchall()
    # Tableau: LEFT JOIN labs
    tab_rc = conn.execute(text("""
        SELECT fi.region_id,
               ROUND((SUM(CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,2) AS cvc_pct,
               ROUND((SUM(CASE WHEN l.ktv<1.2 THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(l.ktv),0))::numeric,2) AS bad_ktv_pct,
               ROUND(AVG(ti.total_mtx)::numeric,2) AS avg_missed
        FROM treatment_info ti
        LEFT JOIN labs l      ON ti.patient_id=l.patient_id AND ti.month=l.month
        JOIN facility_info fi ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)).fetchall()
    print(f"  {'Region':<12} {'Py CVC%':>8} {'Tab CVC%':>9} {'Py KTV%':>8} {'Tab KTV%':>9} {'Py MissedTx':>12} {'Tab MissedTx':>13}")
    for py, tab in zip(py_rc, tab_rc):
        print(f"  {region_map[py[0]]:<12} {float(py[1]):>8.2f} {float(tab[1]):>9.2f} {float(py[2]):>8.2f} {float(tab[2]):>9.2f} {float(py[3]):>12.2f} {float(tab[3]):>13.2f}")
    print(f"  Tableau screenshot: AL CVC=17.62, WA CVC=19.81 | AL MissedTx=2.56, WA=2.67")

    print("\n" + "=" * 65)
    print("  ROOT CAUSE: Python uses INNER JOINs (excludes non-admit rows)")
    print("  FIX: Use treatment_info as base with LEFT JOINs — match Tableau")
    print("=" * 65)
