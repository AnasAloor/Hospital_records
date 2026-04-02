from sqlalchemy import create_engine, text
e = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')
with e.connect() as conn:
    rows = conn.execute(text("SELECT region_id, COUNT(*) FROM facility_info GROUP BY region_id ORDER BY region_id")).fetchall()
    for r in rows:
        print(f"Region {r[0]}: {r[1]} facilities")
