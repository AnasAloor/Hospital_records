from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    def q(sql): return conn.execute(text(sql)).scalar()

    total_patients   = q("SELECT COUNT(DISTINCT patient_id) FROM demographics")
    total_admits     = q("SELECT SUM(inpatient_admits) FROM admit_info")
    total_mm         = q("SELECT COUNT(*) FROM admit_info")
    total_bsi        = q("SELECT SUM(bsi_event) FROM admit_info")
    total_facilities = q("SELECT COUNT(DISTINCT facility_id) FROM facility_info")
    avg_age_male     = q("SELECT ROUND(AVG(age)::numeric,1) FROM demographics WHERE sex='M'")
    avg_age_female   = q("SELECT ROUND(AVG(age)::numeric,1) FROM demographics WHERE sex='F'")
    mm_100pct        = q("""SELECT COUNT(*) FROM treatment_info
                            WHERE total_scheduled_tx > 0
                            AND total_tx >= total_scheduled_tx""")
    mm_missing_lab   = q("""SELECT COUNT(*) FROM admit_info ai
                            LEFT JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
                            WHERE l.albumin IS NULL OR l.ktv IS NULL""")
    hosp_rate        = q("""SELECT ROUND((SUM(inpatient_admits)*100.0/COUNT(*))::numeric,2)
                            FROM admit_info""")

    # Region breakdown
    print("=" * 55)
    print("  KPI VALIDATION REPORT")
    print("=" * 55)
    print(f"  Total Distinct Patients     : {total_patients:,}")
    print(f"  Total Inpatient Admits      : {int(total_admits):,}")
    print(f"  Total Member-Months         : {total_mm:,}")
    print(f"  Total BSI Events            : {int(total_bsi)}")
    print(f"  Total Dialysis Facilities   : {total_facilities}")
    print(f"  Avg Age - Male              : {avg_age_male}")
    print(f"  Avg Age - Female            : {avg_age_female}")
    print(f"  MM at 100% Completion       : {mm_100pct:,}")
    print(f"  MM with Missing Lab         : {mm_missing_lab:,}")
    print(f"  Overall Hosp Rate /100 MM   : {hosp_rate}")
    print()

    # Per-region
    rows = conn.execute(text("""
        SELECT fi.region_id,
               CASE fi.region_id WHEN 'A' THEN 'Washington' ELSE 'Alabama' END AS region,
               COUNT(DISTINCT d.patient_id)  AS patients,
               SUM(ai.inpatient_admits)       AS admits,
               COUNT(ai.patient_id)           AS mm,
               ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ai.patient_id))::numeric,2) AS rate,
               ROUND(AVG(d.age)::numeric,1)   AS avg_age,
               ROUND(AVG(l.ktv)::numeric,2)   AS avg_ktv,
               ROUND(AVG(l.albumin)::numeric,2) AS avg_albumin,
               ROUND(AVG(ti.total_mtx)::numeric,2) AS avg_missed,
               ROUND((SUM(CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,1) AS cvc_pct
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN demographics d    ON ai.patient_id=d.patient_id  AND ai.month=d.month
        JOIN labs l            ON ai.patient_id=l.patient_id  AND ai.month=l.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY fi.region_id ORDER BY fi.region_id
    """)).fetchall()

    print("-" * 55)
    print("  REGIONAL BREAKDOWN")
    print("-" * 55)
    for r in rows:
        print(f"  {r[1]} (Region {r[0]})")
        print(f"    Patients       : {r[2]:,}")
        print(f"    Total Admits   : {int(r[3]):,}")
        print(f"    Member-Months  : {r[4]:,}")
        print(f"    Hosp Rate      : {r[5]} per 100 MM")
        print(f"    Avg Age        : {r[6]}")
        print(f"    Avg KTV        : {r[7]}")
        print(f"    Avg Albumin    : {r[8]}")
        print(f"    Avg Missed Tx  : {r[9]}")
        print(f"    CVC %          : {r[10]}%")
        print()

    # Monthly trend
    monthly = conn.execute(text("""
        SELECT ai.month,
               CASE fi.region_id WHEN 'A' THEN 'Washington' ELSE 'Alabama' END AS region,
               SUM(ai.inpatient_admits) AS admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        GROUP BY ai.month, fi.region_id ORDER BY ai.month, fi.region_id
    """)).fetchall()

    print("-" * 55)
    print("  MONTHLY TREND (Total Admits per Region)")
    print("-" * 55)
    print(f"  {'Month':<12} {'Washington':>12} {'Alabama':>10}")
    print(f"  {'-'*12} {'-'*12} {'-'*10}")
    months = {}
    for r in monthly:
        m = str(r[0])[:7]
        if m not in months:
            months[m] = {}
        months[m][r[1]] = int(r[2])
    for m, v in sorted(months.items()):
        wa = v.get('Washington', 0)
        al = v.get('Alabama', 0)
        print(f"  {m:<12} {wa:>12} {al:>10}")

    print()
    print("=" * 55)
    print("  VALIDATION COMPLETE")
    print("=" * 55)
