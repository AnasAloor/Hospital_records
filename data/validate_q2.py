from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    def q(sql): return conn.execute(text(sql)).fetchall()

    print("=" * 60)
    print("  Q2 VALIDATION REPORT")
    print("=" * 60)

    # Panel 1 - Hosp Rate by Region
    rows = q("""
        SELECT CASE fi.region_id WHEN 'A' THEN 'Washington (Region A)'
                                 ELSE 'Alabama (Region B)' END AS region,
               COUNT(DISTINCT ai.patient_id) AS patients,
               COUNT(ai.patient_id) AS mm,
               SUM(ai.inpatient_admits) AS admits,
               ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ai.patient_id))::numeric,3) AS rate
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)
    print("\n--- PANEL 1: Hospitalization Rate by Region ---")
    for r in rows:
        print(f"  {r[0]}")
        print(f"    Member-Months : {r[2]:,}")
        print(f"    Total Admits  : {int(r[3]):,}")
        print(f"    Rate /100 MM  : {r[4]}")
    diff = float(rows[1][4]) / float(rows[0][4]) * 100 - 100
    print(f"\n  Alabama is {diff:.1f}% HIGHER than Washington")

    # Panel 2 - Root Cause Clinical Profile
    rows2 = q("""
        SELECT CASE fi.region_id WHEN 'A' THEN 'Washington (Region A)'
                                 ELSE 'Alabama (Region B)' END AS region,
               ROUND((SUM(CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,2) AS cvc_pct,
               ROUND((SUM(CASE WHEN l.ktv < 1.2 THEN 1 ELSE 0 END)*100.0/COUNT(l.ktv))::numeric,2) AS inadequate_ktv_pct,
               ROUND(AVG(ti.total_mtx)::numeric,2) AS avg_missed_tx
        FROM treatment_info ti
        JOIN labs l            ON ti.patient_id=l.patient_id AND ti.month=l.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        WHERE l.ktv IS NOT NULL
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)
    print("\n--- PANEL 2: Root Cause Clinical Profile ---")
    for r in rows2:
        print(f"  {r[0]}")
        print(f"    CVC Usage %        : {r[1]}%")
        print(f"    Inadequate KTV %   : {r[2]}%")
        print(f"    Avg Missed Tx/Mo   : {r[3]}")

    # Panel 3 - Facility Level Ranking
    rows3 = q("""
        SELECT ti.facility_id,
               fi.state,
               CASE fi.region_id WHEN 'A' THEN 'Washington' ELSE 'Alabama' END AS region,
               COUNT(DISTINCT ai.patient_id) AS patients,
               COUNT(ai.patient_id) AS mm,
               SUM(ai.inpatient_admits) AS admits,
               ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ai.patient_id))::numeric,2) AS rate
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY ti.facility_id, fi.state, fi.region_id
        ORDER BY rate DESC
    """)
    print("\n--- PANEL 3: Facility-Level Ranking ---")
    print(f"  {'Facility':<15} {'State':<6} {'Region':<12} {'Rate':>8}")
    print(f"  {'-'*15} {'-'*6} {'-'*12} {'-'*8}")
    for r in rows3:
        print(f"  Facility {r[0]:<6} {r[1]:<6} {r[2]:<12} {float(r[6]):>8.2f}")

    print("\n" + "=" * 60)
    print("  VALIDATION COMPLETE")
    print("=" * 60)
