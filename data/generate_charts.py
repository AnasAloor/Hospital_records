import os
import warnings
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
DB_URL = "postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records"
OUT_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(OUT_DIR, exist_ok=True)

engine = create_engine(DB_URL)

# ── Global style ──────────────────────────────────────────────────────────────
PALETTE_REGION = {"A": "#2E86AB", "B": "#E84855"}
PALETTE_RISK   = {"High Risk": "#E84855", "Low Risk": "#3BB273"}
BG             = "#F7F9FC"
TITLE_COLOR    = "#1A1A2E"
SUBTITLE_COLOR = "#555577"
GRID_COLOR     = "#E0E4EC"
FONT_FAMILY    = "DejaVu Sans"

plt.rcParams.update({
    "font.family":        FONT_FAMILY,
    "axes.facecolor":     BG,
    "figure.facecolor":   BG,
    "axes.edgecolor":     GRID_COLOR,
    "axes.grid":          True,
    "grid.color":         GRID_COLOR,
    "grid.linewidth":     0.8,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "xtick.color":        SUBTITLE_COLOR,
    "ytick.color":        SUBTITLE_COLOR,
    "axes.labelcolor":    TITLE_COLOR,
    "text.color":         TITLE_COLOR,
})


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  Saved: {name}")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — KPI Summary Dashboard
# ─────────────────────────────────────────────────────────────────────────────
def chart_kpi_summary():
    with engine.connect() as conn:
        patients   = conn.execute(text("SELECT COUNT(DISTINCT patient_id) FROM demographics")).scalar()
        admits     = conn.execute(text("SELECT SUM(inpatient_admits) FROM admit_info")).scalar()
        bsi        = conn.execute(text("SELECT SUM(bsi_event) FROM admit_info")).scalar()
        mm         = conn.execute(text("SELECT COUNT(*) FROM admit_info")).scalar()
        miss_labs  = conn.execute(text(
            "SELECT COUNT(*) FROM labs WHERE albumin IS NULL OR hemoglobin IS NULL OR hematocrit IS NULL OR ktv IS NULL"
        )).scalar()
        facilities = conn.execute(text("SELECT COUNT(*) FROM facility_info")).scalar()
        cvc_pct    = conn.execute(text(
            "SELECT ROUND((SUM(CASE WHEN access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,1) FROM treatment_info"
        )).scalar()
        avg_age    = conn.execute(text("SELECT ROUND(AVG(age)::numeric,1) FROM demographics WHERE age BETWEEN 0 AND 120")).scalar()

    kpis = [
        ("Distinct Patients",          f"{patients:,}",       "#2E86AB"),
        ("Total Inpatient Admits",      f"{int(admits):,}",    "#E84855"),
        ("Member-Months",               f"{mm:,}",             "#3BB273"),
        ("BSI Events",                  f"{int(bsi)}",         "#F4A261"),
        ("Facilities",                  f"{facilities}",       "#7B2D8B"),
        ("CVC Access %",                f"{cvc_pct}%",         "#E84855"),
        ("Avg Patient Age",             f"{avg_age} yrs",      "#2E86AB"),
        ("Member-Months Missing Lab",   f"{miss_labs:,}",      "#888899"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle("DaVita Dialysis Patient Data — Summary Dashboard\nJuly 2017 – June 2018",
                 fontsize=17, fontweight="bold", color=TITLE_COLOR, y=1.02)

    for ax, (label, value, color) in zip(axes.flat, kpis):
        ax.set_facecolor("white")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        # colored top bar
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.05, 0.82), 0.9, 0.12,
            boxstyle="round,pad=0.02", linewidth=0,
            facecolor=color, alpha=0.85
        ))
        ax.text(0.5, 0.88, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
        ax.text(0.5, 0.45, value, ha="center", va="center",
                fontsize=26, fontweight="bold", color=color)
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.tight_layout(pad=1.5)
    save(fig, "01_kpi_summary.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Region A vs B Hospitalization Rate
# ─────────────────────────────────────────────────────────────────────────────
def chart_region_comparison():
    q = """
        SELECT fi.region_id,
               COUNT(ai.patient_id) as member_months,
               SUM(ai.inpatient_admits) as total_admits,
               (SUM(ai.inpatient_admits) * 100.0 / COUNT(ai.patient_id)) as rate
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        JOIN facility_info fi ON ti.facility_id = fi.facility_id
        GROUP BY fi.region_id
        ORDER BY fi.region_id
    """
    df = pd.read_sql(q, engine)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Hospitalization Rate: Region A vs Region B",
                 fontsize=16, fontweight="bold", color=TITLE_COLOR, y=1.01)

    # Left — admits per 100 MM
    ax = axes[0]
    colors = [PALETTE_REGION[r] for r in df["region_id"]]
    bars = ax.bar(df["region_id"], df["rate"], color=colors, width=0.45,
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, df["rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"{val:.2f}", ha="center", va="bottom", fontsize=13, fontweight="bold",
                color=TITLE_COLOR)
    diff = ((df.loc[df.region_id == "B", "rate"].values[0] /
             df.loc[df.region_id == "A", "rate"].values[0]) - 1) * 100
    ax.set_title(f"Admits per 100 Member-Months\n(Region B is {diff:.1f}% higher)",
                 fontsize=12, color=SUBTITLE_COLOR)
    ax.set_xlabel("Region", fontsize=11)
    ax.set_ylabel("Admits per 100 Member-Months", fontsize=11)
    ax.set_ylim(0, df["rate"].max() * 1.25)
    ax.set_facecolor(BG)

    # Right — absolute admits + member-months
    ax2 = axes[1]
    x = range(len(df))
    w = 0.35
    b1 = ax2.bar([i - w/2 for i in x], df["total_admits"], w,
                 label="Total Admits", color=[PALETTE_REGION[r] for r in df["region_id"]],
                 alpha=0.9, edgecolor="white")
    b2 = ax2.bar([i + w/2 for i in x], df["member_months"] / 100, w,
                 label="Member-Months / 100", color=[PALETTE_REGION[r] for r in df["region_id"]],
                 alpha=0.4, edgecolor="white")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(df["region_id"])
    ax2.set_title("Total Admits vs Member-Months (÷100)", fontsize=12, color=SUBTITLE_COLOR)
    ax2.set_xlabel("Region", fontsize=11)
    ax2.legend(fontsize=10)
    ax2.set_facecolor(BG)

    plt.tight_layout()
    save(fig, "02_region_comparison.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 3 — Monthly Hospitalization Trend by Region
# ─────────────────────────────────────────────────────────────────────────────
def chart_monthly_trend():
    q = """
        SELECT ai.month,
               fi.region_id,
               SUM(ai.inpatient_admits) as total_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        JOIN facility_info fi ON ti.facility_id = fi.facility_id
        GROUP BY ai.month, fi.region_id
        ORDER BY ai.month
    """
    df = pd.read_sql(q, engine)
    df["month"] = pd.to_datetime(df["month"])

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle("Monthly Inpatient Hospitalization Trend by Region",
                 fontsize=16, fontweight="bold", color=TITLE_COLOR)

    for region, grp in df.groupby("region_id"):
        color = PALETTE_REGION[region]
        ax.plot(grp["month"], grp["total_admits"], marker="o", linewidth=2.5,
                markersize=7, color=color, label=f"Region {region}")
        ax.fill_between(grp["month"], grp["total_admits"], alpha=0.08, color=color)
        for _, row in grp.iterrows():
            ax.annotate(f"{int(row['total_admits'])}",
                        (row["month"], row["total_admits"]),
                        textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8, color=color)

    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Total Inpatient Admits", fontsize=12)
    ax.legend(fontsize=12, framealpha=0.9)
    ax.set_facecolor(BG)
    plt.xticks(rotation=30)
    plt.tight_layout()
    save(fig, "03_monthly_trend.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 4 — Key Drivers of Hospitalization
# ─────────────────────────────────────────────────────────────────────────────
def chart_key_drivers():
    with engine.connect() as conn:
        # CVC
        r = conn.execute(text("""
            SELECT ti.access_type,
                   AVG(ai.inpatient_admits) as avg_admits
            FROM admit_info ai
            JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
            GROUP BY ti.access_type
        """)).fetchall()
        cvc_data = {row[0]: float(row[1]) for row in r}

        # Missed Tx
        r = conn.execute(text("""
            SELECT CASE WHEN ti.total_mtx > 0 THEN 'Has Missed Tx' ELSE 'No Missed Tx' END as grp,
                   AVG(ai.inpatient_admits) as avg_admits
            FROM admit_info ai
            JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
            GROUP BY grp
        """)).fetchall()
        mtx_data = {row[0]: float(row[1]) for row in r}

        # Albumin
        r = conn.execute(text("""
            SELECT CASE WHEN l.albumin < 3.5 THEN 'Low Albumin' ELSE 'Normal Albumin' END as grp,
                   AVG(ai.inpatient_admits) as avg_admits
            FROM admit_info ai JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
            WHERE l.albumin IS NOT NULL
            GROUP BY grp
        """)).fetchall()
        alb_data = {row[0]: float(row[1]) for row in r}

        # KTV
        r = conn.execute(text("""
            SELECT CASE WHEN l.ktv < 1.2 THEN 'KTV < 1.2' ELSE 'KTV >= 1.2' END as grp,
                   AVG(ai.inpatient_admits) as avg_admits
            FROM admit_info ai JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
            WHERE l.ktv IS NOT NULL
            GROUP BY grp
        """)).fetchall()
        ktv_data = {row[0]: float(row[1]) for row in r}

        # Fluid gain
        r = conn.execute(text("""
            SELECT CASE WHEN ti.frequent_excessive_fluid_gain_flag=1 THEN 'Freq Fluid Gain' ELSE 'No Fluid Gain' END as grp,
                   AVG(ai.inpatient_admits) as avg_admits
            FROM admit_info ai
            JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
            GROUP BY grp
        """)).fetchall()
        fluid_data = {row[0]: float(row[1]) for row in r}

    rows = [
        ("CVC Access",       "CVC",             cvc_data.get("CVC", 0),            "High Risk"),
        ("CVC Access",       "Non-CVC",         cvc_data.get("Non-CVC", 0),        "Low Risk"),
        ("Missed Tx",        "Has Missed Tx",   mtx_data.get("Has Missed Tx", 0),  "High Risk"),
        ("Missed Tx",        "No Missed Tx",    mtx_data.get("No Missed Tx", 0),   "Low Risk"),
        ("Albumin Level",    "Low Albumin",     alb_data.get("Low Albumin", 0),    "High Risk"),
        ("Albumin Level",    "Normal Albumin",  alb_data.get("Normal Albumin", 0), "Low Risk"),
        ("KTV Adequacy",     "KTV < 1.2",       ktv_data.get("KTV < 1.2", 0),      "High Risk"),
        ("KTV Adequacy",     "KTV >= 1.2",      ktv_data.get("KTV >= 1.2", 0),     "Low Risk"),
        ("Fluid Gain Flag",  "Freq Fluid Gain", fluid_data.get("Freq Fluid Gain", 0), "High Risk"),
        ("Fluid Gain Flag",  "No Fluid Gain",   fluid_data.get("No Fluid Gain", 0),   "Low Risk"),
    ]
    df = pd.DataFrame(rows, columns=["Category", "Group", "Avg Admits", "Risk"])
    df = df.sort_values("Avg Admits", ascending=True)

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.suptitle("Key Drivers of Hospitalization Rate\n(Avg Inpatient Admits per Member-Month)",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    colors = [PALETTE_RISK[r] for r in df["Risk"]]
    bars = ax.barh(df["Group"], df["Avg Admits"], color=colors,
                   edgecolor="white", linewidth=1, height=0.6)

    for bar, val in zip(bars, df["Avg Admits"]):
        ax.text(val + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=10, fontweight="bold",
                color=TITLE_COLOR)

    # Category separators
    categories = df["Category"].tolist()
    for i in range(1, len(categories)):
        if categories[i] != categories[i - 1]:
            ax.axhline(i - 0.5, color=GRID_COLOR, linewidth=1.5, linestyle="--")

    high_patch = mpatches.Patch(color=PALETTE_RISK["High Risk"], label="High Risk Group")
    low_patch  = mpatches.Patch(color=PALETTE_RISK["Low Risk"],  label="Low Risk Group")
    ax.legend(handles=[high_patch, low_patch], fontsize=11, loc="lower right")
    ax.set_xlabel("Avg Inpatient Admits per Member-Month", fontsize=11)
    ax.set_facecolor(BG)
    plt.tight_layout()
    save(fig, "04_key_drivers.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 5 — Admits by Facility (Dec 2017)
# ─────────────────────────────────────────────────────────────────────────────
def chart_admits_by_facility():
    q = """
        SELECT ti.facility_id,
               fi.region_id,
               SUM(ai.inpatient_admits) as total_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi ON ti.facility_id=fi.facility_id
        WHERE ai.month = '2017-12-31'
        GROUP BY ti.facility_id, fi.region_id
        ORDER BY fi.region_id, ti.facility_id
    """
    df = pd.read_sql(q, engine)
    df["facility_id"] = df["facility_id"].astype(str)
    df["total_admits"] = df["total_admits"].fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle("Inpatient Admits by Facility — December 2017",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    colors = [PALETTE_REGION[r] for r in df["region_id"]]
    bars = ax.bar(df["facility_id"], df["total_admits"], color=colors,
                  edgecolor="white", linewidth=1.5, width=0.55)

    for bar, val, region in zip(bars, df["total_admits"], df["region_id"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{int(val)}", ha="center", va="bottom", fontsize=12,
                fontweight="bold", color=TITLE_COLOR)
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                f"Reg {region}", ha="center", va="center", fontsize=9,
                color="white", fontweight="bold")

    patch_a = mpatches.Patch(color=PALETTE_REGION["A"], label="Region A (WA)")
    patch_b = mpatches.Patch(color=PALETTE_REGION["B"], label="Region B (AL)")
    ax.legend(handles=[patch_a, patch_b], fontsize=11)
    ax.set_xlabel("Facility ID", fontsize=12)
    ax.set_ylabel("Total Inpatient Admits", fontsize=12)
    ax.set_facecolor(BG)
    plt.tight_layout()
    save(fig, "05_admits_by_facility.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 6 — Patient Demographics
# ─────────────────────────────────────────────────────────────────────────────
def chart_demographics():
    with engine.connect() as conn:
        sex_df  = pd.read_sql("SELECT sex, COUNT(*) as cnt FROM demographics GROUP BY sex", conn)
        race_df = pd.read_sql("SELECT race, COUNT(*) as cnt FROM demographics GROUP BY race", conn)

    race_labels = {"W": "White", "B": "Black", "H": "Hispanic", "A": "Asian", "O": "Other"}
    race_df["race"] = race_df["race"].map(race_labels).fillna(race_df["race"])

    sex_colors  = ["#2E86AB", "#E84855"]
    race_colors = ["#2E86AB", "#E84855", "#3BB273", "#F4A261", "#7B2D8B"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.suptitle("Patient Demographics — DaVita Dialysis Dataset",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    # Sex donut
    ax = axes[0]
    wedges, texts, autotexts = ax.pie(
        sex_df["cnt"], labels=sex_df["sex"],
        autopct="%1.1f%%", startangle=90,
        colors=sex_colors, pctdistance=0.75,
        wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2}
    )
    for t in texts:
        t.set_fontsize(13)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Sex Distribution", fontsize=13, color=SUBTITLE_COLOR, pad=15)
    ax.set_facecolor(BG)

    # Race donut
    ax2 = axes[1]
    wedges2, texts2, autotexts2 = ax2.pie(
        race_df["cnt"], labels=race_df["race"],
        autopct="%1.1f%%", startangle=90,
        colors=race_colors, pctdistance=0.75,
        wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2}
    )
    for t in texts2:
        t.set_fontsize(11)
        t.set_fontweight("bold")
    for at in autotexts2:
        at.set_fontsize(10)
        at.set_color("white")
        at.set_fontweight("bold")
    ax2.set_title("Race Distribution", fontsize=13, color=SUBTITLE_COLOR, pad=15)
    ax2.set_facecolor(BG)

    plt.tight_layout()
    save(fig, "06_demographics.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 7 — CVC vs Non-CVC Hospitalization Rate
# ─────────────────────────────────────────────────────────────────────────────
def chart_cvc_comparison():
    q = """
        SELECT ti.access_type,
               COUNT(ai.patient_id) as member_months,
               SUM(ai.inpatient_admits) as total_admits,
               (SUM(ai.inpatient_admits) * 100.0 / COUNT(ai.patient_id)) as rate_per_100mm
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        GROUP BY ti.access_type
        ORDER BY ti.access_type
    """
    df = pd.read_sql(q, engine)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.suptitle("CVC vs Non-CVC Access Type — Hospitalization Impact",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    cvc_colors = {"CVC": "#E84855", "Non-CVC": "#3BB273"}
    colors = [cvc_colors.get(a, "#888") for a in df["access_type"]]

    # Left — rate per 100 MM
    ax = axes[0]
    bars = ax.bar(df["access_type"], df["rate_per_100mm"], color=colors,
                  width=0.4, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, df["rate_per_100mm"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.2f}", ha="center", va="bottom", fontsize=14,
                fontweight="bold", color=TITLE_COLOR)
    ratio = df.loc[df.access_type == "CVC", "rate_per_100mm"].values[0] / \
            df.loc[df.access_type == "Non-CVC", "rate_per_100mm"].values[0]
    ax.set_title(f"Admits per 100 Member-Months\n(CVC is {ratio:.1f}x higher)",
                 fontsize=12, color=SUBTITLE_COLOR)
    ax.set_ylabel("Admits per 100 Member-Months", fontsize=11)
    ax.set_facecolor(BG)

    # Right — member-months distribution
    ax2 = axes[1]
    wedges, texts, autotexts = ax2.pie(
        df["member_months"],
        labels=df["access_type"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for t in texts:
        t.set_fontsize(12)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")
    ax2.set_title("Member-Month Distribution\nby Access Type", fontsize=12, color=SUBTITLE_COLOR)
    ax2.set_facecolor(BG)

    plt.tight_layout()
    save(fig, "07_cvc_comparison.png")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Output directory: {OUT_DIR}\n")
    print("Generating charts...")
    chart_kpi_summary()
    chart_region_comparison()
    chart_monthly_trend()
    chart_key_drivers()
    chart_admits_by_facility()
    chart_demographics()
    chart_cvc_comparison()
    print(f"\nAll 7 charts saved to: {OUT_DIR}")
