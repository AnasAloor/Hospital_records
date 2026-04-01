from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')
with engine.connect() as conn:
    rows = conn.execute(text("SELECT DISTINCT month FROM admit_info ORDER BY month")).fetchall()
    print("All distinct months in admit_info:")
    for r in rows:
        print(f"  {r[0]}")
