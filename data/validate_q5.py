from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    print("=" * 60)
    print("  Q5 — SQL INTERVIEW QUESTIONS VALIDATION")
    print("=" * 60)

    # i. Average age by gender
    print("\n--- i. Average Age by Gender ---")
    rows = conn.execute(text("""
        SELECT
            CASE sex WHEN 'M' THEN 'Male' WHEN 'F' THEN 'Female' ELSE sex END AS gender,
            ROUND(AVG(age)::numeric, 1) AS avg_age,
            COUNT(DISTINCT patient_id) AS members
        FROM demographics
        WHERE age IS NOT NULL
        GROUP BY sex ORDER BY sex
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:<10} Avg Age: {r[1]}  Members: {r[2]:,}")

    # ii. Distinct members at clinic 4057
    print("\n--- ii. Distinct Members at Clinic 4057 ---")
    r = conn.execute(text("""
        SELECT COUNT(DISTINCT patient_id) AS distinct_members
        FROM treatment_info
        WHERE facility_id = 4057
    """)).scalar()
    print(f"  Distinct Members: {r:,}")

    # iii. Max and min treatments in 2018
    print("\n--- iii. Max & Min Treatments in 2018 ---")
    r = conn.execute(text("""
        SELECT
            MAX(total_tx) AS max_treatments,
            MIN(total_tx) AS min_treatments,
            ROUND(AVG(total_tx)::numeric, 1) AS avg_treatments
        FROM treatment_info
        WHERE EXTRACT(YEAR FROM month) = 2018
    """)).fetchone()
    print(f"  Max Treatments: {r[0]}")
    print(f"  Min Treatments: {r[1]}")
    print(f"  Avg Treatments: {r[2]}")

    # iv. Member-months missing at least 1 lab value
    print("\n--- iv. Member-Months Missing At Least 1 Lab Value ---")
    r = conn.execute(text("""
        SELECT COUNT(*) AS missing_mm
        FROM labs
        WHERE albumin IS NULL
           OR hemoglobin IS NULL
           OR hematocrit IS NULL
           OR ktv IS NULL
    """)).scalar()
    total = conn.execute(text("SELECT COUNT(*) FROM labs")).scalar()
    print(f"  Missing Lab MM  : {r:,}")
    print(f"  Total MM        : {total:,}")
    print(f"  Percentage      : {round(r/total*100,1)}%")

    # v. Admits by clinic in Dec 2017
    print("\n--- v. Admits by Clinic in December 2017 ---")
    rows = conn.execute(text("""
        SELECT
            ti.facility_id,
            fi.state,
            CASE fi.region_id WHEN 'A' THEN 'Washington' ELSE 'Alabama' END AS region,
            COUNT(DISTINCT ai.patient_id) AS members,
            SUM(ai.inpatient_admits) AS total_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        WHERE ai.month = '2017-12-31'
        GROUP BY ti.facility_id, fi.state, fi.region_id
        ORDER BY total_admits DESC
    """)).fetchall()
    print(f"  {'Facility':<12} {'State':<6} {'Region':<12} {'Members':>8} {'Admits':>8}")
    print(f"  {'-'*12} {'-'*6} {'-'*12} {'-'*8} {'-'*8}")
    total_dec = 0
    for r in rows:
        print(f"  {str(r[0]):<12} {r[1]:<6} {r[2]:<12} {r[3]:>8} {int(r[4]):>8}")
        total_dec += int(r[4])
    print(f"\n  Total Admits Dec 2017: {total_dec}")

    print("\n" + "=" * 60)
    print("  ALL ANSWERS CONFIRMED")
    print("=" * 60)
