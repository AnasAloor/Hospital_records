import os
import warnings
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
DB_URL = "postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records"
OUT_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(OUT_DIR, exist_ok=True)

engine = create_engine(DB_URL)

# ── Label maps — all codes replaced with full natural names ───────────────────
REGION_LABELS  = {"A": "Washington (Region A)", "B": "Alabama (Region B)"}
SEX_LABELS     = {"M": "Male", "F": "Female"}
RACE_LABELS    = {"W": "White", "B": "Black", "H": "Hispanic", "A": "Asian", "O": "Other"}
KTV_LABELS     = {"sp": "Single-Pool (sp)", "std": "Standard (std)"}

PALETTE_REGION = {"Washington (Region A)": "#2E86AB", "Alabama (Region B)": "#E84855"}
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
        avg_age    = conn.execute(text(
            "SELECT ROUND(AVG(age)::numeric,1) FROM demographics WHERE age BETWEEN 0 AND 120"
        )).scalar()

    kpis = [
        ("Distinct Patients",                    f"{patients:,}",    "#2E86AB"),
        ("Total Inpatient Hospital Admits",       f"{int(admits):,}", "#E84855"),
        ("Total Member-Months",                  f"{mm:,}",          "#3BB273"),
        ("Bloodstream Infection (BSI) Events",   f"{int(bsi)}",      "#F4A261"),
        ("Dialysis Facilities",                  f"{facilities}",    "#7B2D8B"),
        ("Central Venous Catheter (CVC) %",      f"{cvc_pct}%",      "#E84855"),
        ("Average Patient Age",                  f"{avg_age} yrs",   "#2E86AB"),
        ("Member-Months with Missing Lab Value", f"{miss_labs:,}",   "#888899"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(18, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle("DaVita Dialysis Patient Data — Summary Dashboard\nJuly 2017 – June 2018  |  9 Facilities  |  Washington & Alabama",
                 fontsize=16, fontweight="bold", color=TITLE_COLOR, y=1.02)

    for ax, (label, value, color) in zip(axes.flat, kpis):
        ax.set_facecolor("white")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.05, 0.78), 0.9, 0.16,
            boxstyle="round,pad=0.02", linewidth=0,
            facecolor=color, alpha=0.85
        ))
        ax.text(0.5, 0.86, label, ha="center", va="center",
                fontsize=9, fontweight="bold", color="white")
        ax.text(0.5, 0.42, value, ha="center", va="center",
                fontsize=24, fontweight="bold", color=color)
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.tight_layout(pad=1.5)
    save(fig, "01_kpi_summary.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Region Hospitalization Rate Comparison
# ─────────────────────────────────────────────────────────────────────────────
def chart_region_comparison():
    q = """
        SELECT fi.region_id,
               COUNT(ai.patient_id)                                    AS member_months,
               SUM(ai.inpatient_admits)                                AS total_admits,
               (SUM(ai.inpatient_admits) * 100.0 / COUNT(ai.patient_id)) AS rate
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        JOIN facility_info  fi ON ti.facility_id = fi.facility_id
        GROUP BY fi.region_id
        ORDER BY fi.region_id
    """
    df = pd.read_sql(q, engine)
    df["region_label"] = df["region_id"].map(REGION_LABELS)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Inpatient Hospitalization Rate Comparison\nWashington (Region A) vs Alabama (Region B)",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR, y=1.02)

    # Left — admits per 100 member-months
    ax = axes[0]
    colors = [PALETTE_REGION[r] for r in df["region_label"]]
    bars = ax.bar(df["region_label"], df["rate"], color=colors, width=0.45,
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, df["rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"{val:.2f}", ha="center", va="bottom", fontsize=13,
                fontweight="bold", color=TITLE_COLOR)
    diff = ((df.loc[df.region_id == "B", "rate"].values[0] /
             df.loc[df.region_id == "A", "rate"].values[0]) - 1) * 100
    ax.set_title(f"Admits per 100 Member-Months\nAlabama (Region B) is {diff:.1f}% higher than Washington (Region A)",
                 fontsize=11, color=SUBTITLE_COLOR)
    ax.set_xlabel("Region", fontsize=11)
    ax.set_ylabel("Admits per 100 Member-Months", fontsize=11)
    ax.set_ylim(0, df["rate"].max() * 1.3)
    ax.set_facecolor(BG)
    plt.setp(ax.get_xticklabels(), rotation=10, ha="right", fontsize=9)

    # Right — total admits vs member-months side by side
    ax2 = axes[1]
    x = range(len(df))
    w = 0.35
    ax2.bar([i - w/2 for i in x], df["total_admits"], w,
            label="Total Inpatient Admits", color=colors, alpha=0.9, edgecolor="white")
    ax2.bar([i + w/2 for i in x], df["member_months"] / 100, w,
            label="Total Member-Months (divided by 100)", color=colors, alpha=0.35, edgecolor="white")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(df["region_label"], rotation=10, ha="right", fontsize=9)
    ax2.set_title("Total Inpatient Admits vs Total Member-Months\n(Member-Months divided by 100 for scale)",
                  fontsize=11, color=SUBTITLE_COLOR)
    ax2.set_xlabel("Region", fontsize=11)
    ax2.legend(fontsize=9)
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
               SUM(ai.inpatient_admits) AS total_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id = ti.patient_id AND ai.month = ti.month
        JOIN facility_info  fi ON ti.facility_id = fi.facility_id
        GROUP BY ai.month, fi.region_id
        ORDER BY ai.month
    """
    df = pd.read_sql(q, engine)
    df["month"] = pd.to_datetime(df["month"])
    df["region_label"] = df["region_id"].map(REGION_LABELS)

    fig, ax = plt.subplots(figsize=(15, 6))
    fig.suptitle("Monthly Inpatient Hospitalization Trend by Region\nJuly 2017 – June 2018",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    for region_label, grp in df.groupby("region_label"):
        color = PALETTE_REGION[region_label]
        ax.plot(grp["month"], grp["total_admits"], marker="o", linewidth=2.5,
                markersize=7, color=color, label=region_label)
        ax.fill_between(grp["month"], grp["total_admits"], alpha=0.08, color=color)
        for _, row in grp.iterrows():
            ax.annotate(f"{int(row['total_admits'])}",
                        (row["month"], row["total_admits"]),
                        textcoords="offset points", xytext=(0, 9),
                        ha="center", fontsize=8, color=color, fontweight="bold")

    ax.set_xlabel("Reporting Month", fontsize=12)
    ax.set_ylabel("Total Inpatient Hospital Admits", fontsize=12)
    ax.legend(fontsize=12, framealpha=0.9, title="Region")
    ax.set_facecolor(BG)
    plt.xticks(rotation=30)
    plt.tight_layout()
    save(fig, "03_monthly_trend.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 4 — Key Drivers of Hospitalization
# ─────────────────────────────────────────────────────────────────────────────
def chart_key_drivers():
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT ti.access_type, AVG(ai.inpatient_admits) AS avg_admits
            FROM admit_info ai
            JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
            GROUP BY ti.access_type
        """)).fetchall()
        cvc_data = {row[0]: float(row[1]) for row in r}

        r = conn.execute(text("""
            SELECT CASE WHEN ti.total_mtx > 0 THEN 'Has Missed Treatments'
                        ELSE 'No Missed Treatments' END AS grp,
                   AVG(ai.inpatient_admits) AS avg_admits
            FROM admit_info ai
            JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
            GROUP BY grp
        """)).fetchall()
        mtx_data = {row[0]: float(row[1]) for row in r}

        r = conn.execute(text("""
            SELECT CASE WHEN l.albumin < 3.5 THEN 'Low Albumin (< 3.5 g/dL)'
                        ELSE 'Normal Albumin (>= 3.5 g/dL)' END AS grp,
                   AVG(ai.inpatient_admits) AS avg_admits
            FROM admit_info ai
            JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
            WHERE l.albumin IS NOT NULL
            GROUP BY grp
        """)).fetchall()
        alb_data = {row[0]: float(row[1]) for row in r}

        r = conn.execute(text("""
            SELECT CASE WHEN l.ktv < 1.2 THEN 'Inadequate Dialysis Dose (KTV < 1.2)'
                        ELSE 'Adequate Dialysis Dose (KTV >= 1.2)' END AS grp,
                   AVG(ai.inpatient_admits) AS avg_admits
            FROM admit_info ai
            JOIN labs l ON ai.patient_id=l.patient_id AND ai.month=l.month
            WHERE l.ktv IS NOT NULL
            GROUP BY grp
        """)).fetchall()
        ktv_data = {row[0]: float(row[1]) for row in r}

        r = conn.execute(text("""
            SELECT CASE WHEN ti.frequent_excessive_fluid_gain_flag=1
                        THEN 'Frequent Excessive Fluid Gain (> 10% of Treatments)'
                        ELSE 'No Frequent Excessive Fluid Gain' END AS grp,
                   AVG(ai.inpatient_admits) AS avg_admits
            FROM admit_info ai
            JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
            GROUP BY grp
        """)).fetchall()
        fluid_data = {row[0]: float(row[1]) for row in r}

    rows = [
        ("Vascular Access Type",     "Central Venous Catheter (CVC)",          cvc_data.get("CVC", 0),                                      "High Risk"),
        ("Vascular Access Type",     "Non-CVC (Fistula or Graft)",             cvc_data.get("Non-CVC", 0),                                  "Low Risk"),
        ("Treatment Adherence",      "Has Missed Treatments",                  mtx_data.get("Has Missed Treatments", 0),                    "High Risk"),
        ("Treatment Adherence",      "No Missed Treatments",                   mtx_data.get("No Missed Treatments", 0),                     "Low Risk"),
        ("Nutritional Status",       "Low Albumin (< 3.5 g/dL)",              alb_data.get("Low Albumin (< 3.5 g/dL)", 0),                 "High Risk"),
        ("Nutritional Status",       "Normal Albumin (>= 3.5 g/dL)",          alb_data.get("Normal Albumin (>= 3.5 g/dL)", 0),             "Low Risk"),
        ("Dialysis Dose (KTV)",      "Inadequate Dialysis Dose (KTV < 1.2)",  ktv_data.get("Inadequate Dialysis Dose (KTV < 1.2)", 0),     "High Risk"),
        ("Dialysis Dose (KTV)",      "Adequate Dialysis Dose (KTV >= 1.2)",   ktv_data.get("Adequate Dialysis Dose (KTV >= 1.2)", 0),      "Low Risk"),
        ("Fluid Management",         "Frequent Excessive Fluid Gain (> 10% of Treatments)", fluid_data.get("Frequent Excessive Fluid Gain (> 10% of Treatments)", 0), "High Risk"),
        ("Fluid Management",         "No Frequent Excessive Fluid Gain",      fluid_data.get("No Frequent Excessive Fluid Gain", 0),        "Low Risk"),
    ]
    df = pd.DataFrame(rows, columns=["Category", "Group", "Avg Admits", "Risk"])
    df = df.sort_values("Avg Admits", ascending=True)

    fig, ax = plt.subplots(figsize=(15, 8))
    fig.suptitle("Key Clinical Drivers of Inpatient Hospitalization Rate\n(Average Inpatient Admits per Member-Month — Higher = More Hospitalizations)",
                 fontsize=14, fontweight="bold", color=TITLE_COLOR)

    colors = [PALETTE_RISK[r] for r in df["Risk"]]
    bars = ax.barh(df["Group"], df["Avg Admits"], color=colors,
                   edgecolor="white", linewidth=1, height=0.6)

    for bar, val in zip(bars, df["Avg Admits"]):
        ax.text(val + 0.003, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=9, fontweight="bold", color=TITLE_COLOR)

    categories = df["Category"].tolist()
    for i in range(1, len(categories)):
        if categories[i] != categories[i - 1]:
            ax.axhline(i - 0.5, color=GRID_COLOR, linewidth=1.5, linestyle="--")

    high_patch = mpatches.Patch(color=PALETTE_RISK["High Risk"], label="High Risk Group (more hospitalizations)")
    low_patch  = mpatches.Patch(color=PALETTE_RISK["Low Risk"],  label="Low Risk Group (fewer hospitalizations)")
    ax.legend(handles=[high_patch, low_patch], fontsize=10, loc="lower right")
    ax.set_xlabel("Average Inpatient Admits per Member-Month", fontsize=11)
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
               fi.state,
               SUM(ai.inpatient_admits) AS total_admits
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info  fi ON ti.facility_id=fi.facility_id
        WHERE ai.month = '2017-12-31'
        GROUP BY ti.facility_id, fi.region_id, fi.state
        ORDER BY fi.region_id, ti.facility_id
    """
    df = pd.read_sql(q, engine)
    df["total_admits"] = df["total_admits"].fillna(0)
    df["region_label"] = df["region_id"].map(REGION_LABELS)
    df["facility_label"] = "Facility " + df["facility_id"].astype(str) + "\n(" + df["state"] + ")"

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle("Total Inpatient Hospital Admits by Dialysis Facility\nDecember 2017",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    colors = [PALETTE_REGION[r] for r in df["region_label"]]
    bars = ax.bar(df["facility_label"], df["total_admits"], color=colors,
                  edgecolor="white", linewidth=1.5, width=0.55)

    for bar, val, rlabel in zip(bars, df["total_admits"], df["region_label"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{int(val)}", ha="center", va="bottom", fontsize=12,
                fontweight="bold", color=TITLE_COLOR)
        short = "WA" if "Washington" in rlabel else "AL"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                short, ha="center", va="center", fontsize=9,
                color="white", fontweight="bold")

    patch_a = mpatches.Patch(color=PALETTE_REGION["Washington (Region A)"], label="Washington — Region A")
    patch_b = mpatches.Patch(color=PALETTE_REGION["Alabama (Region B)"],    label="Alabama — Region B")
    ax.legend(handles=[patch_a, patch_b], fontsize=11)
    ax.set_xlabel("Dialysis Facility (State)", fontsize=12)
    ax.set_ylabel("Total Inpatient Hospital Admits", fontsize=12)
    ax.set_facecolor(BG)
    plt.tight_layout()
    save(fig, "05_admits_by_facility.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 6 — Patient Demographics
# ─────────────────────────────────────────────────────────────────────────────
def chart_demographics():
    with engine.connect() as conn:
        sex_df  = pd.read_sql("SELECT sex,  COUNT(*) AS cnt FROM demographics GROUP BY sex",  conn)
        race_df = pd.read_sql("SELECT race, COUNT(*) AS cnt FROM demographics GROUP BY race", conn)

    sex_df["sex"]   = sex_df["sex"].map(SEX_LABELS).fillna(sex_df["sex"])
    race_df["race"] = race_df["race"].map(RACE_LABELS).fillna(race_df["race"])

    sex_colors  = ["#2E86AB", "#E84855"]
    race_colors = ["#2E86AB", "#E84855", "#3BB273", "#F4A261", "#7B2D8B"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    fig.suptitle("Patient Demographics — DaVita Dialysis Dataset\n1,311 Distinct Patients  |  July 2017 – June 2018",
                 fontsize=15, fontweight="bold", color=TITLE_COLOR)

    # Gender donut
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
    ax.set_title("Gender Distribution", fontsize=13, color=SUBTITLE_COLOR, pad=15)
    ax.set_facecolor(BG)

    # Race/Ethnicity donut
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
    ax2.set_title("Race / Ethnicity Distribution", fontsize=13, color=SUBTITLE_COLOR, pad=15)
    ax2.set_facecolor(BG)

    plt.tight_layout()
    save(fig, "06_demographics.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 7 — CVC vs Non-CVC Hospitalization Rate
# ─────────────────────────────────────────────────────────────────────────────
def chart_cvc_comparison():
    q = """
        SELECT ti.access_type,
               COUNT(ai.patient_id)                                      AS member_months,
               SUM(ai.inpatient_admits)                                  AS total_admits,
               (SUM(ai.inpatient_admits) * 100.0 / COUNT(ai.patient_id)) AS rate_per_100mm
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        GROUP BY ti.access_type
        ORDER BY ti.access_type
    """
    df = pd.read_sql(q, engine)

    access_labels = {
        "CVC":     "Central Venous Catheter (CVC)\n— Temporary / Higher Risk",
        "Non-CVC": "Non-CVC Access\n(Fistula or Graft — Permanent)"
    }
    df["access_label"] = df["access_type"].map(access_labels).fillna(df["access_type"])

    cvc_colors = {
        "Central Venous Catheter (CVC)\n— Temporary / Higher Risk": "#E84855",
        "Non-CVC Access\n(Fistula or Graft — Permanent)":           "#3BB273"
    }
    colors = [cvc_colors.get(a, "#888") for a in df["access_label"]]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Vascular Access Type Impact on Hospitalization Rate\nCentral Venous Catheter (CVC) vs Non-CVC (Fistula / Graft)",
                 fontsize=14, fontweight="bold", color=TITLE_COLOR)

    # Left — rate per 100 member-months
    ax = axes[0]
    bars = ax.bar(df["access_label"], df["rate_per_100mm"], color=colors,
                  width=0.4, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, df["rate_per_100mm"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.2f}", ha="center", va="bottom", fontsize=13,
                fontweight="bold", color=TITLE_COLOR)
    cvc_rate    = df.loc[df.access_type == "CVC",     "rate_per_100mm"].values[0]
    noncvc_rate = df.loc[df.access_type == "Non-CVC", "rate_per_100mm"].values[0]
    ratio = cvc_rate / noncvc_rate
    ax.set_title(f"Admits per 100 Member-Months\nCVC patients are hospitalized {ratio:.1f}x more than Non-CVC patients",
                 fontsize=11, color=SUBTITLE_COLOR)
    ax.set_ylabel("Admits per 100 Member-Months", fontsize=11)
    ax.set_facecolor(BG)
    plt.setp(ax.get_xticklabels(), fontsize=8)

    # Right — member-months distribution pie
    ax2 = axes[1]
    wedges, texts, autotexts = ax2.pie(
        df["member_months"],
        labels=df["access_label"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for t in texts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")
    ax2.set_title("Share of Total Member-Months\nby Vascular Access Type", fontsize=11, color=SUBTITLE_COLOR)
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
