from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')
with engine.connect() as conn:
    for tbl in ['labs', 'treatment_info']:
        rows = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tbl}' ORDER BY ordinal_position")).fetchall()
        print(f"{tbl}: {[r[0] for r in rows]}")
