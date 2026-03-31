from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    # Q5i
    r = conn.execute(text('SELECT sex, ROUND(AVG(age),1) FROM demographics GROUP BY sex')).fetchall()
    print('Q5i avg age by gender:', r)

    # Q5ii
    r = conn.execute(text('SELECT COUNT(DISTINCT patient_id) FROM treatment_info WHERE facility_id = 4057')).fetchone()
    print('Q5ii distinct members clinic 4057:', r)

    # Q5iii
    r = conn.execute(text('SELECT MAX(total_tx), MIN(total_tx) FROM treatment_info WHERE EXTRACT(YEAR FROM month) = 2018')).fetchone()
    print('Q5iii max/min tx in 2018:', r)

    # Q5iv
    r = conn.execute(text('SELECT COUNT(*) FROM labs WHERE albumin IS NULL OR hemoglobin IS NULL OR hematocrit IS NULL OR ktv IS NULL')).fetchone()
    print('Q5iv member months missing >= 1 lab:', r)

    # Q5v
    q = """
        SELECT ti.facility_id, SUM(ai.inpatient_admits) as total_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        WHERE ai.month = '2017-12-31'
        GROUP BY ti.facility_id
        ORDER BY ti.facility_id
    """
    r = conn.execute(text(q)).fetchall()
    print('Q5v admits by clinic Dec 2017:', r)

    # Age outliers
    r = conn.execute(text('SELECT COUNT(*) FROM demographics WHERE age < 0 OR age > 120')).fetchone()
    print('Age outliers (outside 0-120):', r)

    # PW above TW flag vs admits
    q2 = """
        SELECT ti.frequent_pw_above_tw_flag,
               AVG(ai.inpatient_admits) as avg_admits,
               COUNT(*) as cnt
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        GROUP BY ti.frequent_pw_above_tw_flag
    """
    r = conn.execute(text(q2)).fetchall()
    print('PW above TW flag vs admits:', r)

    # Distinct patients per region
    q3 = """
        SELECT fi.region_id, COUNT(DISTINCT d.patient_id)
        FROM demographics d
        JOIN treatment_info ti ON d.patient_id = ti.patient_id AND d.month = ti.month
        JOIN facility_info fi ON ti.facility_id = fi.facility_id
        GROUP BY fi.region_id
    """
    r = conn.execute(text(q3)).fetchall()
    print('Distinct patients per region:', r)

    # Hospitalization rate by region (admits per 100 member-months)
    q4 = """
        SELECT fi.region_id,
               COUNT(ai.patient_id) as member_months,
               SUM(ai.inpatient_admits) as total_admits,
               ROUND((SUM(ai.inpatient_admits) * 100.0 / COUNT(ai.patient_id))::numeric, 2) as admits_per_100mm
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        JOIN facility_info fi ON ti.facility_id = fi.facility_id
        GROUP BY fi.region_id
    """
    r = conn.execute(text(q4)).fetchall()
    print('Hospitalization rate per 100 member-months by region:', r)

    # Missed tx vs hospitalization
    q5 = """
        SELECT
            CASE WHEN ti.total_mtx > 0 THEN 'Has Missed Tx' ELSE 'No Missed Tx' END as missed_tx,
            AVG(ai.inpatient_admits) as avg_admits,
            COUNT(*) as cnt
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        GROUP BY missed_tx
    """
    r = conn.execute(text(q5)).fetchall()
    print('Missed tx vs admits:', r)

    # CVC vs Non-CVC admits
    q6 = """
        SELECT ti.access_type,
               SUM(ai.inpatient_admits) as total_admits,
               COUNT(ai.patient_id) as member_months,
               ROUND((SUM(ai.inpatient_admits) * 100.0 / COUNT(ai.patient_id))::numeric, 2) as admits_per_100mm
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        GROUP BY ti.access_type
    """
    r = conn.execute(text(q6)).fetchall()
    print('CVC vs Non-CVC admits:', r)

    # Fluid gain flag vs admits
    q7 = """
        SELECT ti.frequent_excessive_fluid_gain_flag,
               ROUND(AVG(ai.inpatient_admits)::numeric, 4) as avg_admits,
               COUNT(*) as cnt
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        GROUP BY ti.frequent_excessive_fluid_gain_flag
    """
    r = conn.execute(text(q7)).fetchall()
    print('Fluid gain flag vs admits:', r)

    # KTV below 1.2 (inadequate dialysis) vs admits
    q8 = """
        SELECT
            CASE WHEN l.ktv < 1.2 THEN 'KTV < 1.2 (inadequate)' ELSE 'KTV >= 1.2 (adequate)' END as ktv_group,
            ROUND(AVG(ai.inpatient_admits)::numeric, 4) as avg_admits,
            COUNT(*) as cnt
        FROM admit_info ai
        JOIN labs l ON ai.patient_id = l.patient_id AND ai.month = l.month
        WHERE l.ktv IS NOT NULL
        GROUP BY ktv_group
    """
    r = conn.execute(text(q8)).fetchall()
    print('KTV adequacy vs admits:', r)

    # Albumin low (<3.5) vs admits
    q9 = """
        SELECT
            CASE WHEN l.albumin < 3.5 THEN 'Low Albumin (<3.5)' ELSE 'Normal Albumin (>=3.5)' END as alb_group,
            ROUND(AVG(ai.inpatient_admits)::numeric, 4) as avg_admits,
            COUNT(*) as cnt
        FROM admit_info ai
        JOIN labs l ON ai.patient_id = l.patient_id AND ai.month = l.month
        WHERE l.albumin IS NOT NULL
        GROUP BY alb_group
    """
    r = conn.execute(text(q9)).fetchall()
    print('Albumin vs admits:', r)
