from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    print("=" * 60)
    print("  Q3 VALIDATION — ALL PANEL VALUES")
    print("=" * 60)

    # Panel 1 - Missed Tx dose-response
    print("\n--- PANEL 1: Missed Tx Dose-Response ---")
    rows = conn.execute(text("""
        SELECT
            CASE WHEN ti.total_mtx IS NULL OR ti.total_mtx = 0 THEN '0 Missed Treatments'
                 WHEN ti.total_mtx = 1 THEN '1 Missed Treatment'
                 WHEN ti.total_mtx = 2 THEN '2 Missed Treatments'
                 ELSE '3 or More Missed Treatments' END AS grp,
            COUNT(*) AS mm,
            ROUND(AVG(ai.inpatient_admits)::numeric, 3) AS avg_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        GROUP BY grp ORDER BY avg_admits
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:<35} n={r[1]:>5,}  avg_admits={r[2]}")

    # Panel 2 - Treatment completion rate
    print("\n--- PANEL 2: Treatment Completion Rate ---")
    rows2 = conn.execute(text("""
        SELECT
            CASE
                WHEN ti.total_scheduled_tx = 0 OR ti.total_scheduled_tx IS NULL THEN 'No Schedule'
                WHEN (ti.total_tx::float/ti.total_scheduled_tx) < 0.70 THEN 'Below 70% (Critically Low)'
                WHEN (ti.total_tx::float/ti.total_scheduled_tx) < 0.90 THEN '70% to 89% (Low)'
                WHEN (ti.total_tx::float/ti.total_scheduled_tx) < 1.00 THEN '90% to 99% (Near Complete)'
                ELSE '100% (Fully Complete)'
            END AS grp,
            COUNT(*) AS mm,
            ROUND(AVG(ai.inpatient_admits)::numeric, 3) AS avg_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        GROUP BY grp ORDER BY avg_admits DESC
    """)).fetchall()
    for r in rows2:
        print(f"  {r[0]:<35} n={r[1]:>5,}  avg_admits={r[2]}")

    # Panel 3 - Risk score
    print("\n--- PANEL 3: Risk Score Staircase ---")
    rows3 = conn.execute(text("""
        SELECT
            (CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END
           + CASE WHEN ti.total_mtx > 0 THEN 1 ELSE 0 END
           + CASE WHEN l.albumin < 3.5 THEN 1 ELSE 0 END
           + CASE WHEN l.ktv < 1.2 THEN 1 ELSE 0 END
           + CASE WHEN ti.frequent_excessive_fluid_gain_flag = 1 THEN 1 ELSE 0 END
            ) AS risk_score,
            COUNT(*) AS mm,
            ROUND(AVG(ai.inpatient_admits)::numeric, 3) AS avg_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN labs l            ON ai.patient_id=l.patient_id  AND ai.month=l.month
        WHERE l.albumin IS NOT NULL AND l.ktv IS NOT NULL
        GROUP BY risk_score ORDER BY risk_score
    """)).fetchall()
    for r in rows3:
        print(f"  Risk Score {r[0]}  n={r[1]:>5,}  avg_admits={r[2]}")

    print("\n" + "=" * 60)
    print("  CORRECT TABLEAU FORMULAS TO USE")
    print("=" * 60)
    print("""
  Avg Admits per MM (CORRECT formula):
  SUM([Inpatient Admits]) / COUNT([Patient ID])

  BUT this gives row-level calc. Use this instead:
  { FIXED [Missed Tx Groups] : SUM([Inpatient Admits]) / COUNT([Patient ID]) }

  OR simpler - just use AVG([Inpatient Admits]) directly
    """)
