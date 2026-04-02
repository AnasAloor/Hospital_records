from sqlalchemy import create_engine, text
e = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')
with e.connect() as conn:
    print("--- Gender ---")
    for r in conn.execute(text("SELECT sex, COUNT(DISTINCT patient_id) FROM demographics GROUP BY sex ORDER BY sex")).fetchall():
        print(f"  {r[0]}: {r[1]:,}")

    print("\n--- Race ---")
    for r in conn.execute(text("SELECT race, COUNT(DISTINCT patient_id) FROM demographics GROUP BY race ORDER BY race")).fetchall():
        print(f"  {r[0]}: {r[1]:,}")

    print("\n--- Gender + Region ---")
    for r in conn.execute(text("""
        SELECT fi.region_id,
               CASE d.sex WHEN 'M' THEN 'Male' WHEN 'F' THEN 'Female' END AS gender,
               COUNT(DISTINCT d.patient_id) AS cnt
        FROM demographics d
        JOIN treatment_info ti ON d.patient_id=ti.patient_id AND d.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id, d.sex ORDER BY fi.region_id, d.sex
    """)).fetchall():
        print(f"  Region {r[0]} | {r[1]}: {r[2]:,}")

    print("\n--- Race + Region ---")
    for r in conn.execute(text("""
        SELECT fi.region_id,
               CASE d.race WHEN 'W' THEN 'White' WHEN 'B' THEN 'Black'
                           WHEN 'H' THEN 'Hispanic' WHEN 'A' THEN 'Asian' ELSE 'Other' END AS race,
               COUNT(DISTINCT d.patient_id) AS cnt
        FROM demographics d
        JOIN treatment_info ti ON d.patient_id=ti.patient_id AND d.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id, d.race ORDER BY fi.region_id, d.race
    """)).fetchall():
        print(f"  Region {r[0]} | {r[1]}: {r[2]:,}")

    print("\n--- Avg Hosp Rate by Race ---")
    for r in conn.execute(text("""
        SELECT CASE d.race WHEN 'W' THEN 'White' WHEN 'B' THEN 'Black'
                           WHEN 'H' THEN 'Hispanic' WHEN 'A' THEN 'Asian' ELSE 'Other' END AS race,
               COUNT(ti.patient_id) AS mm,
               ROUND(AVG(ai.inpatient_admits)::numeric,3) AS avg_admits
        FROM treatment_info ti
        LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
        LEFT JOIN demographics d ON ti.patient_id=d.patient_id AND ti.month=d.month
        GROUP BY d.race ORDER BY avg_admits DESC
    """)).fetchall():
        print(f"  {r[0]}: MM={r[1]:,}  AvgAdmits={r[2]}")
