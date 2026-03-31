from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

tables = ['treatment_info', 'demographics', 'labs', 'admit_info', 'facility_info']

with engine.connect() as conn:
    for table in tables:
        q = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}' ORDER BY ordinal_position"
        cols = conn.execute(text(q)).fetchall()
        print(f"\n=== {table} ===")
        for col in cols:
            print(f"  {col[0]:<45} {col[1]}")
