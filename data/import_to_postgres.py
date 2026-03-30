import sys
import pandas as pd
from sqlalchemy import create_engine, text

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- Connection ---------------------------------------------------------------
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "Hospital_records"
DB_USER = "postgres"
DB_PASS = "root"

EXCEL_PATH = r"c:/Users/Rtx_5090/Desktop/Hospital_records/data/Gemini Data Set.xlsx"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -- DDL statements -----------------------------------------------------------
DDL = {
    "demographics": """
        CREATE TABLE IF NOT EXISTS demographics (
            month                   DATE,
            patient_id              BIGINT,
            age                     INTEGER,
            sex                     VARCHAR(10),
            race                    VARCHAR(50),
            fdode                   DATE
        );
    """,
    "treatment_info": """
        CREATE TABLE IF NOT EXISTS treatment_info (
            month                               DATE,
            patient_id                          BIGINT,
            access_type                         VARCHAR(50),
            facility_id                         INTEGER,
            assigned_facility_flag              SMALLINT,
            total_tx                            INTEGER,
            total_mtx                           FLOAT,
            total_scheduled_tx                  FLOAT,
            tx_percent_excessive_fluid_gain     FLOAT,
            frequent_excessive_fluid_gain_flag  SMALLINT,
            tx_percent_pw_above_tw              FLOAT,
            frequent_pw_above_tw_flag           SMALLINT
        );
    """,
    "labs": """
        CREATE TABLE IF NOT EXISTS labs (
            month       DATE,
            patient_id  BIGINT,
            albumin     FLOAT,
            hemoglobin  FLOAT,
            hematocrit  FLOAT,
            ktv_type    VARCHAR(20),
            ktv         FLOAT
        );
    """,
    "admit_info": """
        CREATE TABLE IF NOT EXISTS admit_info (
            month               DATE,
            patient_id          BIGINT,
            inpatient_admits    FLOAT,
            bsi_event           FLOAT
        );
    """,
    "facility_info": """
        CREATE TABLE IF NOT EXISTS facility_info (
            facility_id  INTEGER PRIMARY KEY,
            state        VARCHAR(10),
            region_id    VARCHAR(10),
            date_open    DATE,
            monday       SMALLINT,
            tuesday      SMALLINT,
            wednesday    SMALLINT,
            thursday     SMALLINT,
            friday       SMALLINT,
            saturday     SMALLINT,
            sunday       SMALLINT
        );
    """,
}

# -- Sheet -> table config ----------------------------------------------------
SHEET_MAP = {
    "Demographics":   "demographics",
    "Treatment Info": "treatment_info",
    "Labs":           "labs",
    "Admit Info":     "admit_info",
    "Facility Info":  "facility_info",
}


def clean_columns(df):
    """Lowercase column names and replace spaces/special chars with underscores."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def create_tables(conn):
    for table, ddl in DDL.items():
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
        conn.execute(text(ddl))
        print(f"  [DDL] Table '{table}' created.")
    conn.commit()


def import_sheet(sheet_name, table_name):
    df = pd.ExcelFile(EXCEL_PATH).parse(sheet_name)
    df = clean_columns(df)

    # Convert datetime columns to plain date objects
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        df[col] = pd.to_datetime(df[col]).dt.date

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )
    print(f"  [IMPORT] '{sheet_name}' -> '{table_name}': {len(df):,} rows inserted.")
    return len(df)


def verify_counts(conn):
    print("\n-- Row count verification --")
    for table in DDL:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
        count = result.scalar()
        print(f"  {table:<25} {count:>8,} rows")


def main():
    print("Connecting to PostgreSQL ...")

    with engine.connect() as conn:
        print("\n-- Creating tables --")
        create_tables(conn)

    print("\n-- Importing sheets --")
    for sheet_name, table_name in SHEET_MAP.items():
        import_sheet(sheet_name, table_name)

    with engine.connect() as conn:
        verify_counts(conn)

    print("\nDone.")


if __name__ == "__main__":
    main()
