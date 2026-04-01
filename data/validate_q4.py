from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

with engine.connect() as conn:
    print("=" * 60)
    print("  Q4 VALIDATION — INTERVENTION PRIORITY & BSI")
    print("=" * 60)

    # CVC vs Non-CVC rates
    cvc = conn.execute(text("""
        SELECT ti.access_type,
               COUNT(ai.patient_id) AS mm,
               SUM(ai.inpatient_admits) AS admits,
               ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ai.patient_id))::numeric,2) AS rate
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        GROUP BY ti.access_type
    """)).fetchall()
    print("\n--- CVC vs Non-CVC Rates ---")
    for r in cvc:
        print(f"  {r[0]:<10} MM={r[1]:,}  Admits={int(r[2]):,}  Rate={r[3]}")

    cvc_mm   = int([r for r in cvc if r[0]=='CVC'][0][1])
    cvc_rate = float([r for r in cvc if r[0]=='CVC'][0][3])
    noncvc_rate = float([r for r in cvc if r[0]=='Non-CVC'][0][3])
    cvc_saves = round((cvc_rate - noncvc_rate) / 100 * cvc_mm)
    print(f"\n  CVC Transition saves: ~{cvc_saves} admits")

    # Missed Tx
    mtx = conn.execute(text("""
        SELECT CASE WHEN ti.total_mtx > 0 THEN 'Has Missed Tx' ELSE 'No Missed Tx' END AS grp,
               COUNT(*) AS mm,
               ROUND(AVG(ai.inpatient_admits)::numeric,3) AS avg_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        GROUP BY grp
    """)).fetchall()
    print("\n--- Missed Tx Impact ---")
    for r in mtx:
        print(f"  {r[0]:<15} MM={r[1]:,}  Avg={r[2]}")
    mtx_mm   = int([r for r in mtx if r[0]=='Has Missed Tx'][0][1])
    mtx_high = float([r for r in mtx if r[0]=='Has Missed Tx'][0][2])
    mtx_low  = float([r for r in mtx if r[0]=='No Missed Tx'][0][2])
    mtx_saves = round((mtx_high - mtx_low) * mtx_mm)
    print(f"\n  Missed Tx Outreach saves: ~{mtx_saves} admits")

    # KTV
    ktv = conn.execute(text("""
        SELECT CASE WHEN l.ktv < 1.2 THEN 'Inadequate' ELSE 'Adequate' END AS grp,
               COUNT(*) AS mm,
               ROUND(AVG(ai.inpatient_admits)::numeric,3) AS avg_admits
        FROM admit_info ai
        JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
        WHERE l.ktv IS NOT NULL
        GROUP BY grp
    """)).fetchall()
    print("\n--- KTV Impact ---")
    for r in ktv:
        print(f"  {r[0]:<12} MM={r[1]:,}  Avg={r[2]}")
    ktv_mm   = int([r for r in ktv if r[0]=='Inadequate'][0][1])
    ktv_high = float([r for r in ktv if r[0]=='Inadequate'][0][2])
    ktv_low  = float([r for r in ktv if r[0]=='Adequate'][0][2])
    ktv_saves = round((ktv_high - ktv_low) * ktv_mm)
    print(f"\n  KTV Monitoring saves: ~{ktv_saves} admits")

    # Albumin
    alb = conn.execute(text("""
        SELECT CASE WHEN l.albumin < 3.5 THEN 'Low' ELSE 'Normal' END AS grp,
               COUNT(*) AS mm,
               ROUND(AVG(ai.inpatient_admits)::numeric,3) AS avg_admits
        FROM admit_info ai
        JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
        WHERE l.albumin IS NOT NULL
        GROUP BY grp
    """)).fetchall()
    print("\n--- Albumin Impact ---")
    for r in alb:
        print(f"  {r[0]:<8} MM={r[1]:,}  Avg={r[2]}")
    alb_mm   = int([r for r in alb if r[0]=='Low'][0][1])
    alb_high = float([r for r in alb if r[0]=='Low'][0][2])
    alb_low  = float([r for r in alb if r[0]=='Normal'][0][2])
    alb_saves = round((alb_high - alb_low) * alb_mm)
    print(f"\n  Nutrition Intervention saves: ~{alb_saves} admits")

    # BSI by access type
    bsi = conn.execute(text("""
        SELECT ti.access_type,
               SUM(ai.bsi_event) AS bsi_events,
               COUNT(*) AS mm
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        WHERE ai.bsi_event IS NOT NULL
        GROUP BY ti.access_type
    """)).fetchall()
    print("\n--- BSI Events by Access Type ---")
    for r in bsi:
        rate = round(float(r[1])/r[2]*1000, 1)
        print(f"  {r[0]:<10} BSI={int(r[1])}  MM={r[2]:,}  Rate={rate} per 1000 MM")

    print("\n--- INTERVENTION SUMMARY (for Tableau) ---")
    print(f"  1. CVC Transition      : ~{cvc_saves:,} admits preventable")
    print(f"  2. Missed Tx Outreach  : ~{mtx_saves:,} admits preventable")
    print(f"  3. KTV Monitoring      : ~{ktv_saves:,} admits preventable")
    print(f"  4. Nutrition/Albumin   : ~{alb_saves:,} admits preventable")
    print("=" * 60)
