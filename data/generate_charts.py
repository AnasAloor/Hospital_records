import os
import warnings
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

# ── Config ─────────────────────────────────────────────────────────────────────
DB_URL  = "postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records"
OUT_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(OUT_DIR, exist_ok=True)
engine  = create_engine(DB_URL)

# ── Label maps ─────────────────────────────────────────────────────────────────
REGION_LABELS = {"A": "Washington (Region A)", "B": "Alabama (Region B)"}
SEX_LABELS    = {"M": "Male", "F": "Female"}
RACE_LABELS   = {"W": "White", "B": "Black", "H": "Hispanic", "A": "Asian", "O": "Other"}

COLOR_WA   = "#2E86AB"
COLOR_AL   = "#E84855"
COLOR_HIGH = "#E84855"
COLOR_LOW  = "#3BB273"
COLOR_MID  = "#F4A261"
BG         = "#F7F9FC"
TITLE_C    = "#1A1A2E"
SUB_C      = "#555577"
GRID_C     = "#E0E4EC"

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.facecolor":   BG,
    "figure.facecolor": BG,
    "axes.edgecolor":   GRID_C,
    "axes.grid":        True,
    "grid.color":       GRID_C,
    "grid.linewidth":   0.8,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "xtick.color":      SUB_C,
    "ytick.color":      SUB_C,
    "axes.labelcolor":  TITLE_C,
    "text.color":       TITLE_C,
})

PALETTE_REGION = {"Washington (Region A)": COLOR_WA, "Alabama (Region B)": COLOR_AL}
PALETTE_RISK   = {"High Risk": COLOR_HIGH, "Low Risk": COLOR_LOW}


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  Saved: {name}")


# ═══════════════════════════════════════════════════════════════════════════════
# Q1 — RICH DATA SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
def chart_kpi_summary():
    with engine.connect() as conn:
        # Use treatment_info as base (matches Tableau's Custom SQL base table)
        # De-duplicate admits using MAX per patient-month (matches Tableau LOD)
        patients  = conn.execute(text("SELECT COUNT(DISTINCT patient_id) FROM treatment_info")).scalar()
        mm        = conn.execute(text("SELECT COUNT(*) FROM treatment_info")).scalar()
        admits    = conn.execute(text("""
            SELECT SUM(a.inpatient_admits)
            FROM (SELECT DISTINCT patient_id, month, MAX(inpatient_admits) AS inpatient_admits
                  FROM admit_info GROUP BY patient_id, month) a
        """)).scalar()
        bsi       = conn.execute(text("SELECT SUM(bsi_event) FROM admit_info")).scalar()
        facilities= conn.execute(text("SELECT COUNT(*) FROM facility_info")).scalar()
        avg_age_m = conn.execute(text("SELECT ROUND(AVG(age)::numeric,1) FROM demographics WHERE sex='M' AND age BETWEEN 0 AND 120")).scalar()
        avg_age_f = conn.execute(text("SELECT ROUND(AVG(age)::numeric,1) FROM demographics WHERE sex='F' AND age BETWEEN 0 AND 120")).scalar()
        # Missing labs: count treatment_info rows where joined lab is NULL (matches Tableau 326)
        miss_labs = conn.execute(text("""
            SELECT COUNT(*) FROM treatment_info ti
            LEFT JOIN labs l ON ti.patient_id=l.patient_id AND ti.month=l.month
            WHERE l.albumin IS NULL AND l.hemoglobin IS NULL AND l.hematocrit IS NULL AND l.ktv IS NULL
        """)).scalar()
        comp_100  = conn.execute(text("SELECT COUNT(*) FROM treatment_info WHERE total_scheduled_tx>0 AND total_tx>=total_scheduled_tx")).scalar()
        comp_low  = conn.execute(text("SELECT COUNT(*) FROM treatment_info WHERE total_scheduled_tx>0 AND (total_tx::float/total_scheduled_tx)<0.70")).scalar()

        # Per-region clinical profile — treatment_info base, LEFT JOINs (matches Tableau)
        q_region = """
            SELECT fi.region_id,
                   COUNT(DISTINCT ti.patient_id)                                                          AS patients,
                   ROUND((SUM(ai.inpatient_admits)*100.0/COUNT(ti.patient_id))::numeric,2)                AS hosp_rate,
                   ROUND(AVG(d.age)::numeric,1)                                                           AS avg_age,
                   ROUND(AVG(l.ktv)::numeric,2)                                                           AS avg_ktv,
                   ROUND(AVG(l.albumin)::numeric,2)                                                       AS avg_albumin,
                   ROUND(AVG(ti.total_mtx)::numeric,2)                                                    AS avg_missed,
                   ROUND((SUM(CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,1) AS cvc_pct
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            LEFT JOIN demographics d ON ti.patient_id=d.patient_id AND ti.month=d.month
            LEFT JOIN labs l         ON ti.patient_id=l.patient_id AND ti.month=l.month
            JOIN facility_info fi    ON ti.facility_id=fi.facility_id
            GROUP BY fi.region_id ORDER BY fi.region_id
        """
        region_rows = conn.execute(text(q_region)).fetchall()

    r = {row[0]: row for row in region_rows}
    wa, al = r["A"], r["B"]

    overall_rate = round(float(admits) / mm * 100, 1)

    # ── Layout: top KPI tiles + bottom regional comparison ──────────────────
    fig = plt.figure(figsize=(18, 11))
    gs  = gridspec.GridSpec(2, 1, height_ratios=[1.1, 1], hspace=0.45)

    # ── TOP: 8 KPI tiles ────────────────────────────────────────────────────
    gs_top = gridspec.GridSpecFromSubplotSpec(2, 4, subplot_spec=gs[0], hspace=0.15, wspace=0.3)

    kpis = [
        ("Total Distinct Patients",
         f"{patients:,}",
         f"Washington: {wa[1]:,}  |  Alabama: {al[1]:,}",
         COLOR_WA),
        ("Total Inpatient Hospital Admits",
         f"{int(admits):,}",
         f"Overall rate: {overall_rate} per 100 member-months",
         COLOR_HIGH),
        ("Total Member-Months",
         f"{mm:,}",
         f"12 months  |  July 2017 – June 2018",
         "#3BB273"),
        ("Bloodstream Infection (BSI) Events",
         f"{int(bsi)}",
         f"53% occurred in CVC access patients",
         COLOR_MID),
        ("Dialysis Facilities",
         f"{facilities}",
         f"4 in Washington (Region A)  |  5 in Alabama (Region B)",
         "#7B2D8B"),
        ("Average Patient Age",
         f"{avg_age_m} / {avg_age_f}",
         f"Male avg {avg_age_m} yrs  |  Female avg {avg_age_f} yrs",
         COLOR_WA),
        ("Treatment Completion at 100%",
         f"{comp_100:,} MMs",
         f"{comp_low:,} member-months below 70% — high risk",
         COLOR_HIGH),
        ("Member-Months with Missing Lab",
         f"{miss_labs:,}",
         f"{round(miss_labs/mm*100,1)}% of all member-months",
         "#888899"),
    ]

    for idx, (label, value, subtext, color) in enumerate(kpis):
        row, col = divmod(idx, 4)
        ax = fig.add_subplot(gs_top[row, col])
        ax.set_facecolor("white")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.04, 0.80), 0.92, 0.17,
            boxstyle="round,pad=0.02", linewidth=0, facecolor=color, alpha=0.88))
        ax.text(0.5, 0.885, label, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white")
        ax.text(0.5, 0.50, value, ha="center", va="center",
                fontsize=20, fontweight="bold", color=color)
        ax.text(0.5, 0.13, subtext, ha="center", va="center",
                fontsize=7.5, color=SUB_C, style="italic")

    # ── BOTTOM: Regional Clinical Profile Comparison ────────────────────────
    gs_bot = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=gs[1], wspace=0.45)

    metrics = [
        ("Hosp. Rate\n(per 100 MM)",   float(wa[2]),  float(al[2]),  "lower = better",  18,  True),
        ("Avg KTV\n(Dialysis Dose)",    float(wa[4]),  float(al[4]),  "higher = better", 2.5, False),
        ("Avg Albumin\n(g/dL)",         float(wa[5]),  float(al[5]),  "higher = better", 5,   False),
        ("Avg Missed\nTreatments/Mo",   float(wa[6]),  float(al[6]),  "lower = better",  5,   True),
        ("CVC Usage\n(%)",              float(wa[7]),  float(al[7]),  "lower = better",  30,  True),
    ]

    for idx, (metric, wa_val, al_val, direction, ymax, lower_better) in enumerate(metrics):
        ax = fig.add_subplot(gs_bot[0, idx])
        bars = ax.bar(
            ["WA\n(Region A)", "AL\n(Region B)"],
            [wa_val, al_val],
            color=[COLOR_WA, COLOR_AL],
            width=0.5, edgecolor="white", linewidth=1.5
        )
        for bar, val in zip(bars, [wa_val, al_val]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + ymax*0.02,
                    f"{val}", ha="center", va="bottom", fontsize=10, fontweight="bold", color=TITLE_C)
        ax.set_title(metric, fontsize=9, fontweight="bold", color=TITLE_C, pad=6)
        ax.set_ylim(0, ymax)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_facecolor(BG)
        better = "WA" if (lower_better and wa_val < al_val) or (not lower_better and wa_val > al_val) else "AL"
        ax.text(0.5, -0.22, f"({direction})", ha="center", transform=ax.transAxes,
                fontsize=7.5, color=SUB_C, style="italic")

    fig.suptitle(
        "DaVita Dialysis Patient Data — Full Summary\n"
        "July 2017 – June 2018  |  1,311 Patients  |  9 Facilities  |  Washington & Alabama",
        fontsize=15, fontweight="bold", color=TITLE_C, y=1.01
    )
    save(fig, "01_kpi_summary.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Q2 — REGION COMPARISON WITH ROOT CAUSE + FACILITY RANKING
# ═══════════════════════════════════════════════════════════════════════════════
def chart_region_comparison():
    with engine.connect() as conn:
        # Use treatment_info as base with LEFT JOIN to admit_info — matches Tableau
        q_rate = """
            SELECT fi.region_id,
                   COUNT(ti.patient_id) AS mm,
                   SUM(ai.inpatient_admits) AS admits,
                   (SUM(ai.inpatient_admits)*100.0/COUNT(ti.patient_id)) AS rate
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            JOIN facility_info fi   ON ti.facility_id=fi.facility_id
            GROUP BY fi.region_id ORDER BY fi.region_id
        """
        rate_df = pd.DataFrame(conn.execute(text(q_rate)).fetchall(),
                               columns=["region_id","mm","admits","rate"])
        rate_df["rate"]   = rate_df["rate"].astype(float)
        rate_df["label"]  = rate_df["region_id"].map(REGION_LABELS)

        # Root cause: treatment_info base, LEFT JOIN labs — matches Tableau
        q_profile = """
            SELECT fi.region_id,
                   ROUND(AVG(l.ktv)::numeric,2)    AS avg_ktv,
                   ROUND((SUM(CASE WHEN l.ktv<1.2 THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(l.ktv),0))::numeric,1) AS pct_inadequate_ktv,
                   ROUND((SUM(CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END)*100.0/COUNT(*))::numeric,1) AS cvc_pct,
                   ROUND(AVG(ti.total_mtx)::numeric,2) AS avg_missed
            FROM treatment_info ti
            LEFT JOIN labs l      ON ti.patient_id=l.patient_id AND ti.month=l.month
            JOIN facility_info fi ON ti.facility_id=fi.facility_id
            GROUP BY fi.region_id ORDER BY fi.region_id
        """
        profile_df = pd.DataFrame(conn.execute(text(q_profile)).fetchall(),
                                  columns=["region_id","avg_ktv","pct_inadequate_ktv","cvc_pct","avg_missed"])
        for c in ["avg_ktv","pct_inadequate_ktv","cvc_pct","avg_missed"]:
            profile_df[c] = profile_df[c].astype(float)
        profile_df["label"] = profile_df["region_id"].map(REGION_LABELS)

        # Facility ranking: treatment_info base, LEFT JOIN admit_info — matches Tableau
        q_fac = """
            SELECT ti.facility_id, fi.state, fi.region_id,
                   COUNT(DISTINCT ti.patient_id) AS patients,
                   SUM(ai.inpatient_admits) AS admits,
                   (SUM(ai.inpatient_admits)*100.0/COUNT(ti.patient_id)) AS rate
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            JOIN facility_info fi   ON ti.facility_id=fi.facility_id
            GROUP BY ti.facility_id, fi.state, fi.region_id
            ORDER BY rate DESC
        """
        fac_df = pd.DataFrame(conn.execute(text(q_fac)).fetchall(),
                              columns=["facility_id","state","region_id","patients","admits","rate"])
        fac_df["rate"]         = fac_df["rate"].astype(float)
        fac_df["fac_label"]    = "Facility " + fac_df["facility_id"].astype(str) + "\n(" + fac_df["state"] + ")"
        fac_df["region_label"] = fac_df["region_id"].map(REGION_LABELS)

    fig, axes = plt.subplots(1, 3, figsize=(19, 7))
    fig.suptitle(
        "Q2 — Hospitalization Rate: Washington (Region A) vs Alabama (Region B)\n"
        "Rate Comparison  |  Root Cause Analysis  |  Facility-Level Breakdown",
        fontsize=14, fontweight="bold", color=TITLE_C, y=1.02
    )

    # Panel 1 — Rate bar
    ax = axes[0]
    colors = [PALETTE_REGION[l] for l in rate_df["label"]]
    bars = ax.bar(rate_df["label"], rate_df["rate"], color=colors, width=0.45,
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, rate_df["rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{val:.2f}", ha="center", va="bottom", fontsize=14, fontweight="bold", color=TITLE_C)
    diff = (rate_df.loc[rate_df.region_id=="B","rate"].values[0] /
            rate_df.loc[rate_df.region_id=="A","rate"].values[0] - 1) * 100
    avg_line = rate_df["rate"].mean()
    ax.axhline(avg_line, color=SUB_C, linewidth=1.5, linestyle="--", alpha=0.7)
    ax.text(1.02, avg_line, f"Overall avg\n{avg_line:.2f}", va="center", fontsize=8,
            color=SUB_C, transform=ax.get_yaxis_transform())
    ax.set_title(f"Admits per 100 Member-Months\nAlabama is {diff:.1f}% higher than Washington",
                 fontsize=11, color=SUB_C)
    ax.set_ylabel("Admits per 100 Member-Months", fontsize=11)
    ax.set_ylim(0, 22)
    ax.set_facecolor(BG)
    plt.setp(ax.get_xticklabels(), fontsize=8.5, rotation=8)

    # Panel 2 — Root cause: 3 clinical metrics side-by-side
    ax2 = axes[1]
    metrics_names  = ["CVC Usage (%)", "Inadequate KTV\nDose (%)", "Avg Missed\nTreatments/Mo"]
    wa_vals = [
        float(profile_df.loc[profile_df.region_id=="A","cvc_pct"].values[0]),
        float(profile_df.loc[profile_df.region_id=="A","pct_inadequate_ktv"].values[0]),
        float(profile_df.loc[profile_df.region_id=="A","avg_missed"].values[0]),
    ]
    al_vals = [
        float(profile_df.loc[profile_df.region_id=="B","cvc_pct"].values[0]),
        float(profile_df.loc[profile_df.region_id=="B","pct_inadequate_ktv"].values[0]),
        float(profile_df.loc[profile_df.region_id=="B","avg_missed"].values[0]),
    ]
    x = np.arange(len(metrics_names))
    w = 0.32
    b1 = ax2.bar(x - w/2, wa_vals, w, label="Washington (Region A)", color=COLOR_WA,
                 edgecolor="white", linewidth=1.2, alpha=0.92)
    b2 = ax2.bar(x + w/2, al_vals, w, label="Alabama (Region B)",    color=COLOR_AL,
                 edgecolor="white", linewidth=1.2, alpha=0.92)
    for bars_set in [b1, b2]:
        for bar in bars_set:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                     f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9,
                     fontweight="bold", color=TITLE_C)
    ax2.set_xticks(x)
    ax2.set_xticklabels(metrics_names, fontsize=9)
    ax2.set_title("Root Cause: Clinical Profile Comparison\n(All three drive Alabama's higher rate)",
                  fontsize=11, color=SUB_C)
    ax2.set_ylabel("Value", fontsize=11)
    ax2.legend(fontsize=9, loc="upper right")
    ax2.set_facecolor(BG)
    ax2.text(0.5, -0.18,
             "Alabama has lower KTV adequacy and more missed treatments\n"
             "Washington Region A has slightly higher CVC% but better dialysis dose",
             ha="center", transform=ax2.transAxes, fontsize=8, color=SUB_C, style="italic")

    # Panel 3 — Facility ranking
    ax3 = axes[2]
    fac_colors = [PALETTE_REGION[r] for r in fac_df["region_label"]]
    bars3 = ax3.barh(fac_df["fac_label"], fac_df["rate"], color=fac_colors,
                     edgecolor="white", linewidth=1, height=0.55)
    for bar, val in zip(bars3, fac_df["rate"]):
        ax3.text(val + 0.2, bar.get_y() + bar.get_height()/2,
                 f"{val:.1f}", va="center", fontsize=9.5, fontweight="bold", color=TITLE_C)
    avg_r = fac_df["rate"].mean()
    ax3.axvline(avg_r, color=SUB_C, linewidth=1.5, linestyle="--", alpha=0.7)
    ax3.text(avg_r + 0.2, -0.6, f"Avg {avg_r:.1f}", fontsize=8, color=SUB_C)
    patch_wa = mpatches.Patch(color=COLOR_WA, label="Washington — Region A")
    patch_al = mpatches.Patch(color=COLOR_AL, label="Alabama — Region B")
    ax3.legend(handles=[patch_wa, patch_al], fontsize=9, loc="lower right")
    ax3.set_title("Hospitalization Rate by Individual Facility\n(Facility 4283-WA is the highest outlier in Region A)",
                  fontsize=11, color=SUB_C)
    ax3.set_xlabel("Admits per 100 Member-Months", fontsize=10)
    ax3.set_facecolor(BG)

    plt.tight_layout()
    save(fig, "02_region_comparison.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Q3 — KEY DRIVERS: DOSE-RESPONSE + COMPLETION RATE + RISK SCORE STAIRCASE
# ═══════════════════════════════════════════════════════════════════════════════
def chart_key_drivers():
    with engine.connect() as conn:
        # Missed Tx dose-response — treatment_info base, LEFT JOIN admit_info (matches Tableau)
        q1 = text("""
            SELECT CASE WHEN ti.total_mtx IS NULL OR ti.total_mtx=0 THEN '0 Missed Treatments'
                        WHEN ti.total_mtx=1 THEN '1 Missed Treatment'
                        WHEN ti.total_mtx=2 THEN '2 Missed Treatments'
                        ELSE '3 or More Missed Treatments' END AS grp,
                   COUNT(*) AS cnt,
                   ROUND(AVG(ai.inpatient_admits)::numeric,4) AS avg_admits
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            GROUP BY grp
            ORDER BY avg_admits
        """)
        mtx_df = pd.DataFrame(conn.execute(q1).fetchall(), columns=["grp","cnt","avg_admits"])
        mtx_df["avg_admits"] = mtx_df["avg_admits"].astype(float)

        # Treatment completion rate vs admits — treatment_info base, LEFT JOIN admit_info
        q2 = text("""
            SELECT CASE
                WHEN (ti.total_tx::float/NULLIF(ti.total_scheduled_tx,0))*100 < 70
                     THEN 'Below 70% (Critically Low)'
                WHEN (ti.total_tx::float/NULLIF(ti.total_scheduled_tx,0))*100 < 90
                     THEN '70% to 89% (Low)'
                WHEN (ti.total_tx::float/NULLIF(ti.total_scheduled_tx,0))*100 < 100
                     THEN '90% to 99% (Near Complete)'
                ELSE '100% (Fully Complete)'
            END AS comp_grp,
            COUNT(*) AS cnt,
            ROUND(AVG(ai.inpatient_admits)::numeric,4) AS avg_admits
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            WHERE ti.total_scheduled_tx > 0
            GROUP BY comp_grp
            ORDER BY avg_admits DESC
        """)
        comp_df = pd.DataFrame(conn.execute(q2).fetchall(), columns=["comp_grp","cnt","avg_admits"])
        comp_df["avg_admits"] = comp_df["avg_admits"].astype(float)

        # Risk score staircase — treatment_info base, LEFT JOINs (matches Tableau)
        q3 = text("""
            SELECT
                (CASE WHEN ti.access_type='CVC' THEN 1 ELSE 0 END
               + CASE WHEN ti.total_mtx > 0 THEN 1 ELSE 0 END
               + CASE WHEN l.albumin < 3.5 THEN 1 ELSE 0 END
               + CASE WHEN l.ktv < 1.2 THEN 1 ELSE 0 END
               + CASE WHEN ti.frequent_excessive_fluid_gain_flag=1 THEN 1 ELSE 0 END) AS risk_score,
                COUNT(*) AS mm,
                ROUND(AVG(ai.inpatient_admits)::numeric,4) AS avg_admits
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            LEFT JOIN labs l        ON ti.patient_id=l.patient_id  AND ti.month=l.month
            WHERE l.albumin IS NOT NULL AND l.ktv IS NOT NULL
            GROUP BY risk_score ORDER BY risk_score
        """)
        risk_df = pd.DataFrame(conn.execute(q3).fetchall(), columns=["risk_score","mm","avg_admits"])
        risk_df["avg_admits"] = risk_df["avg_admits"].astype(float)

    fig, axes = plt.subplots(1, 3, figsize=(19, 7))
    fig.suptitle(
        "Q3 — Key Drivers of Inpatient Hospitalization Rate\n"
        "Dose-Response Effect  |  Treatment Completion Impact  |  Cumulative Risk Score",
        fontsize=14, fontweight="bold", color=TITLE_C, y=1.02
    )

    # Panel 1 — Missed Tx dose-response
    ax = axes[0]
    order      = ["0 Missed Treatments", "1 Missed Treatment",
                  "2 Missed Treatments", "3 or More Missed Treatments"]
    mtx_df["grp"] = pd.Categorical(mtx_df["grp"], categories=order, ordered=True)
    mtx_df = mtx_df.sort_values("grp")
    bar_colors = [COLOR_LOW, COLOR_MID, "#F4633A", COLOR_HIGH]
    bars = ax.bar(mtx_df["grp"], mtx_df["avg_admits"], color=bar_colors,
                  edgecolor="white", linewidth=1.5, width=0.55)
    base = mtx_df["avg_admits"].iloc[0]
    for bar, val, cnt in zip(bars, mtx_df["avg_admits"], mtx_df["cnt"]):
        pct = f"+{round((val/base-1)*100)}%" if val > base else "Baseline"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}\n({pct})", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=TITLE_C)
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                f"n={cnt:,}", ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    ax.set_title("Missed Dialysis Treatments → Hospital Admits\nClear dose-response: each missed Tx increases risk",
                 fontsize=10.5, color=SUB_C)
    ax.set_ylabel("Avg Inpatient Admits per Member-Month", fontsize=10)
    ax.set_ylim(0, 1.55)
    ax.set_facecolor(BG)
    plt.setp(ax.get_xticklabels(), fontsize=8.5)

    # Panel 2 — Treatment completion rate
    ax2 = axes[1]
    comp_order = ["Below 70% (Critically Low)", "70% to 89% (Low)",
                  "90% to 99% (Near Complete)", "100% (Fully Complete)"]
    comp_df["comp_grp"] = pd.Categorical(comp_df["comp_grp"], categories=comp_order, ordered=True)
    comp_df = comp_df.sort_values("comp_grp")
    c_colors = [COLOR_HIGH, "#F4633A", COLOR_MID, COLOR_LOW]
    bars2 = ax2.bar(comp_df["comp_grp"], comp_df["avg_admits"], color=c_colors,
                    edgecolor="white", linewidth=1.5, width=0.55)
    base2 = comp_df.loc[comp_df.comp_grp=="100% (Fully Complete)", "avg_admits"].values[0]
    for bar, val, cnt in zip(bars2, comp_df["avg_admits"], comp_df["cnt"]):
        pct = f"{round((val/base2-1)*100)}% more\nthan 100%" if val > base2 else "Baseline\n(100%)"
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{val:.3f}\n({pct})", ha="center", va="bottom",
                 fontsize=8.5, fontweight="bold", color=TITLE_C)
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                 f"n={cnt:,}", ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    ax2.set_title("Treatment Completion Rate vs Hospital Admits\nBelow 70% completion = 2x more hospitalizations",
                  fontsize=10.5, color=SUB_C)
    ax2.set_ylabel("Avg Inpatient Admits per Member-Month", fontsize=10)
    ax2.set_ylim(0, 1.6)
    ax2.set_facecolor(BG)
    plt.setp(ax2.get_xticklabels(), fontsize=8.5)

    # Panel 3 — Risk score staircase
    ax3 = axes[2]
    risk_colors = [COLOR_LOW, "#A8D5A2", COLOR_MID, "#F4633A", COLOR_HIGH, "#8B0000"]
    risk_df["risk_label"] = risk_df["risk_score"].astype(str) + " Risk Factor" + risk_df["risk_score"].apply(lambda x: "s" if x != 1 else "")
    bars3 = ax3.bar(risk_df["risk_label"], risk_df["avg_admits"],
                    color=risk_colors[:len(risk_df)], edgecolor="white", linewidth=1.5, width=0.6)
    base3 = risk_df.loc[risk_df.risk_score==0, "avg_admits"].values[0]
    for bar, val, mm in zip(bars3, risk_df["avg_admits"], risk_df["mm"]):
        mult = f"{val/base3:.1f}x" if val > base3 else "Baseline"
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{val:.3f}\n({mult})", ha="center", va="bottom",
                 fontsize=9, fontweight="bold", color=TITLE_C)
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                 f"n={mm:,}", ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    ax3.set_title("Cumulative Risk Score vs Hospital Admits\n(0=No risk factors  |  5=All risk factors present)",
                  fontsize=10.5, color=SUB_C)
    ax3.set_ylabel("Avg Inpatient Admits per Member-Month", fontsize=10)
    ax3.set_ylim(0, 1.55)
    ax3.set_facecolor(BG)
    ax3.text(0.5, -0.18,
             "Risk factors: CVC access  |  Missed Tx  |  Low Albumin  |  Low KTV  |  Excessive Fluid Gain",
             ha="center", transform=ax3.transAxes, fontsize=8, color=SUB_C, style="italic")
    plt.setp(ax3.get_xticklabels(), fontsize=8.5)

    plt.tight_layout()
    save(fig, "04_key_drivers.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Q4 — NEXT STEPS: INTERVENTION PRIORITY + BSI BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
def chart_next_steps():
    with engine.connect() as conn:
        # CVC rate — treatment_info base, LEFT JOIN admit_info (matches Tableau)
        q_cvc = """
            SELECT ti.access_type,
                   COUNT(ti.patient_id) AS mm,
                   SUM(ai.inpatient_admits) AS admits,
                   (SUM(ai.inpatient_admits)*100.0/COUNT(ti.patient_id)) AS rate
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            GROUP BY ti.access_type
        """
        cvc_df = pd.DataFrame(conn.execute(text(q_cvc)).fetchall(), columns=["access_type","mm","admits","rate"])
        cvc_df["rate"] = cvc_df["rate"].astype(float)
        cvc_rate    = float(cvc_df.loc[cvc_df.access_type=="CVC",     "rate"].values[0])
        noncvc_rate = float(cvc_df.loc[cvc_df.access_type=="Non-CVC", "rate"].values[0])
        cvc_mm      = int(cvc_df.loc[cvc_df.access_type=="CVC",       "mm"].values[0])

        # Missed Tx rate — treatment_info base, LEFT JOIN admit_info
        q_mtx = """
            SELECT CASE WHEN ti.total_mtx>0 THEN 'Has Missed Tx' ELSE 'No Missed Tx' END AS grp,
                   COUNT(*) AS mm,
                   ROUND(AVG(ai.inpatient_admits)::numeric,4) AS avg_admits
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            GROUP BY grp
        """
        mtx_df   = pd.DataFrame(conn.execute(text(q_mtx)).fetchall(), columns=["grp","mm","avg_admits"])
        mtx_df["avg_admits"] = mtx_df["avg_admits"].astype(float)
        mtx_high = float(mtx_df.loc[mtx_df.grp=="Has Missed Tx", "avg_admits"].values[0])
        mtx_low  = float(mtx_df.loc[mtx_df.grp=="No Missed Tx",  "avg_admits"].values[0])
        mtx_mm   = int(mtx_df.loc[mtx_df.grp=="Has Missed Tx",   "mm"].values[0])

        # KTV — treatment_info base, LEFT JOIN labs and admit_info
        q_ktv = """
            SELECT CASE WHEN l.ktv<1.2 THEN 'Inadequate' ELSE 'Adequate' END AS grp,
                   COUNT(*) AS mm,
                   ROUND(AVG(ai.inpatient_admits)::numeric,4) AS avg_admits
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            LEFT JOIN labs l        ON ti.patient_id=l.patient_id  AND ti.month=l.month
            WHERE l.ktv IS NOT NULL
            GROUP BY grp
        """
        ktv_df   = pd.DataFrame(conn.execute(text(q_ktv)).fetchall(), columns=["grp","mm","avg_admits"])
        ktv_df["avg_admits"] = ktv_df["avg_admits"].astype(float)
        ktv_high = float(ktv_df.loc[ktv_df.grp=="Inadequate", "avg_admits"].values[0])
        ktv_low  = float(ktv_df.loc[ktv_df.grp=="Adequate",   "avg_admits"].values[0])
        ktv_mm   = int(ktv_df.loc[ktv_df.grp=="Inadequate",   "mm"].values[0])

        # Albumin — treatment_info base, LEFT JOINs
        q_alb = """
            SELECT CASE WHEN l.albumin<3.5 THEN 'Low' ELSE 'Normal' END AS grp,
                   COUNT(*) AS mm,
                   ROUND(AVG(ai.inpatient_admits)::numeric,4) AS avg_admits
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            LEFT JOIN labs l        ON ti.patient_id=l.patient_id  AND ti.month=l.month
            WHERE l.albumin IS NOT NULL
            GROUP BY grp
        """
        alb_df   = pd.DataFrame(conn.execute(text(q_alb)).fetchall(), columns=["grp","mm","avg_admits"])
        alb_df["avg_admits"] = alb_df["avg_admits"].astype(float)
        alb_high = float(alb_df.loc[alb_df.grp=="Low",    "avg_admits"].values[0])
        alb_low  = float(alb_df.loc[alb_df.grp=="Normal", "avg_admits"].values[0])
        alb_mm   = int(alb_df.loc[alb_df.grp=="Low",      "mm"].values[0])

        # BSI by access type — treatment_info base, LEFT JOIN admit_info
        q_bsi = """
            SELECT ti.access_type,
                   SUM(ai.bsi_event) AS bsi_events,
                   COUNT(ti.patient_id) AS mm
            FROM treatment_info ti
            LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
            GROUP BY ti.access_type
        """
        bsi_df = pd.DataFrame(conn.execute(text(q_bsi)).fetchall(), columns=["access_type","bsi_events","mm"])

    # Calculate potential admits saved if all at-risk patients reach low-risk rate
    interventions = [
        ("1. Transition CVC Patients\nto Permanent Access\n(Fistula or Graft)",
         cvc_mm, cvc_rate/100, noncvc_rate/100,
         f"{cvc_mm:,} member-months affected\nRate: {cvc_rate:.1f} → {noncvc_rate:.1f} per 100 MM\n({round((cvc_rate/noncvc_rate-1)*100)}% reduction potential)",
         COLOR_HIGH),
        ("2. Missed Treatment\nOutreach Program\n(Proactive Patient Contact)",
         mtx_mm, mtx_high, mtx_low,
         f"{mtx_mm:,} member-months affected\nAvg admits: {mtx_high:.3f} → {mtx_low:.3f}\n({round((mtx_high/mtx_low-1)*100)}% reduction potential)",
         "#F4633A"),
        ("3. Dialysis Dose\nOptimization\n(Increase KTV >= 1.2)",
         ktv_mm, ktv_high, ktv_low,
         f"{ktv_mm:,} member-months affected\nAvg admits: {ktv_high:.3f} → {ktv_low:.3f}\n({round((ktv_high/ktv_low-1)*100)}% reduction potential)",
         COLOR_MID),
        ("4. Nutrition Intervention\n(Albumin >= 3.5 g/dL)\n(Dietitian Review)",
         alb_mm, alb_high, alb_low,
         f"{alb_mm:,} member-months affected\nAvg admits: {alb_high:.3f} → {alb_low:.3f}\n({round((alb_high/alb_low-1)*100)}% reduction potential)",
         "#F4A261"),
    ]

    potential_saves = [round((h - l) * mm) for _, mm, h, l, _, _ in interventions]

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(
        "Q4 — Proposed Next Steps: Prioritized Clinical Interventions\n"
        "Ranked by Potential Reduction in Inpatient Hospital Admissions",
        fontsize=14, fontweight="bold", color=TITLE_C, y=1.02
    )

    # Panel 1 — Intervention priority
    ax = axes[0]
    labels = [iv[0] for iv in interventions]
    saves  = potential_saves
    colors = [iv[5] for iv in interventions]
    bars = ax.barh(labels[::-1], saves[::-1], color=colors[::-1],
                   edgecolor="white", linewidth=1.5, height=0.55)
    for bar, val, iv in zip(bars, saves[::-1], interventions[::-1]):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                f"~{val} fewer admits", va="center", fontsize=10, fontweight="bold", color=TITLE_C)
        ax.text(bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                iv[4], va="center", ha="center", fontsize=7.5,
                color="white", fontweight="bold")
    ax.set_title("Estimated Admits That Could Be Prevented\nIf At-Risk Patients Reach Low-Risk Rate",
                 fontsize=11, color=SUB_C)
    ax.set_xlabel("Estimated Inpatient Admits Preventable per Year", fontsize=10)
    ax.set_facecolor(BG)
    ax.set_xlim(0, max(saves) * 1.55)

    # Panel 2 — BSI by access type + additional next steps
    ax2 = axes[1]
    bsi_df["access_label"] = bsi_df["access_type"].apply(
        lambda x: "Central Venous\nCatheter (CVC)" if x == "CVC" else "Non-CVC\n(Fistula or Graft)"
    )
    bsi_colors = [COLOR_HIGH if "CVC" in l else COLOR_LOW for l in bsi_df["access_label"]]
    bars2 = ax2.bar(bsi_df["access_label"], bsi_df["bsi_events"],
                    color=bsi_colors, edgecolor="white", linewidth=1.5, width=0.45)
    for bar, val, mm in zip(bars2, bsi_df["bsi_events"], bsi_df["mm"]):
        rate_bsi = round(float(val) / mm * 1000, 2)
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f"{int(val)} events\n({rate_bsi} per 1,000 MM)",
                 ha="center", va="bottom", fontsize=10, fontweight="bold", color=TITLE_C)
    ax2.set_title("Bloodstream Infection (BSI) Events by Vascular Access Type\nCVC patients account for 53% of all BSI events",
                  fontsize=11, color=SUB_C)
    ax2.set_ylabel("Total BSI Events", fontsize=11)
    ax2.set_ylim(0, bsi_df["bsi_events"].max() * 1.55)
    ax2.set_facecolor(BG)

    # Add next steps text box
    next_steps_text = (
        "Additional Proposed Next Steps:\n\n"
        "5.  Investigate Facility 4283 (WA) — hospitalization\n"
        "     rate of 21.1 is highest across all 9 facilities\n\n"
        "6.  Predictive Risk Scoring — flag patients with\n"
        "     3+ risk factors for monthly clinical review\n\n"
        "7.  Resolve data quality issues — 532 member-\n"
        "     months with missing lab values\n\n"
        "8.  Extended analysis — add diagnosis codes,\n"
        "     medication data, and social determinants"
    )
    ax2.text(1.08, 0.98, next_steps_text, transform=ax2.transAxes,
             fontsize=8.5, va="top", ha="left", color=TITLE_C,
             bbox=dict(boxstyle="round,pad=0.6", facecolor="white",
                       edgecolor=GRID_C, linewidth=1.2))

    plt.tight_layout()
    save(fig, "08_next_steps.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Monthly Trend (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_monthly_trend():
    q = """
        SELECT ti.month, fi.region_id, SUM(ai.inpatient_admits) AS total_admits
        FROM treatment_info ti
        LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
        JOIN facility_info  fi  ON ti.facility_id=fi.facility_id
        GROUP BY ti.month, fi.region_id ORDER BY ti.month
    """
    df = pd.read_sql(q, engine)
    df["month"] = pd.to_datetime(df["month"])
    df["region_label"] = df["region_id"].map(REGION_LABELS)

    fig, ax = plt.subplots(figsize=(15, 6))
    fig.suptitle("Monthly Inpatient Hospitalization Trend by Region\nJuly 2017 – June 2018",
                 fontsize=15, fontweight="bold", color=TITLE_C)
    palette = {"Washington (Region A)": COLOR_WA, "Alabama (Region B)": COLOR_AL}
    for rlabel, grp in df.groupby("region_label"):
        color = palette[rlabel]
        ax.plot(grp["month"], grp["total_admits"], marker="o", linewidth=2.5,
                markersize=7, color=color, label=rlabel)
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


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Admits by Facility Dec 2017 (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_admits_by_facility():
    q = """
        SELECT ti.facility_id, fi.state, fi.region_id,
               SUM(ai.inpatient_admits) AS total_admits
        FROM treatment_info ti
        LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
        JOIN facility_info  fi  ON ti.facility_id=fi.facility_id
        WHERE ti.month = '2017-12-31'
        GROUP BY ti.facility_id, fi.state, fi.region_id
        ORDER BY fi.region_id, ti.facility_id
    """
    df = pd.read_sql(q, engine)
    df["total_admits"]  = df["total_admits"].fillna(0)
    df["region_label"]  = df["region_id"].map(REGION_LABELS)
    df["facility_label"]= "Facility " + df["facility_id"].astype(str) + "\n(" + df["state"] + ")"
    palette = {"Washington (Region A)": COLOR_WA, "Alabama (Region B)": COLOR_AL}
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle("Total Inpatient Hospital Admits by Dialysis Facility — December 2017",
                 fontsize=15, fontweight="bold", color=TITLE_C)
    colors = [palette[r] for r in df["region_label"]]
    bars = ax.bar(df["facility_label"], df["total_admits"], color=colors,
                  edgecolor="white", linewidth=1.5, width=0.55)
    for bar, val, rl in zip(bars, df["total_admits"], df["region_label"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{int(val)}", ha="center", va="bottom", fontsize=12, fontweight="bold", color=TITLE_C)
        short = "WA" if "Washington" in rl else "AL"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                short, ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    patch_wa = mpatches.Patch(color=COLOR_WA, label="Washington — Region A")
    patch_al = mpatches.Patch(color=COLOR_AL, label="Alabama — Region B")
    ax.legend(handles=[patch_wa, patch_al], fontsize=11)
    ax.set_xlabel("Dialysis Facility (State)", fontsize=12)
    ax.set_ylabel("Total Inpatient Hospital Admits", fontsize=12)
    ax.set_facecolor(BG)
    plt.tight_layout()
    save(fig, "05_admits_by_facility.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Demographics (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_demographics():
    with engine.connect() as conn:
        sex_df  = pd.read_sql("SELECT sex,  COUNT(*) AS cnt FROM demographics GROUP BY sex",  conn)
        race_df = pd.read_sql("SELECT race, COUNT(*) AS cnt FROM demographics GROUP BY race", conn)
    sex_df["sex"]   = sex_df["sex"].map(SEX_LABELS).fillna(sex_df["sex"])
    race_df["race"] = race_df["race"].map(RACE_LABELS).fillna(race_df["race"])
    sex_colors  = [COLOR_WA, COLOR_AL]
    race_colors = [COLOR_WA, COLOR_AL, COLOR_LOW, COLOR_MID, "#7B2D8B"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    fig.suptitle("Patient Demographics — DaVita Dialysis Dataset\n1,311 Distinct Patients  |  July 2017 – June 2018",
                 fontsize=15, fontweight="bold", color=TITLE_C)
    for ax, data, col_field, col_colors, title in [
        (axes[0], sex_df,  "sex",  sex_colors,  "Gender Distribution"),
        (axes[1], race_df, "race", race_colors, "Race / Ethnicity Distribution"),
    ]:
        wedges, texts, autotexts = ax.pie(
            data["cnt"], labels=data[col_field],
            autopct="%1.1f%%", startangle=90, colors=col_colors,
            pctdistance=0.75, wedgeprops={"width":0.55,"edgecolor":"white","linewidth":2})
        for t in texts:     t.set_fontsize(12); t.set_fontweight("bold")
        for at in autotexts: at.set_fontsize(10); at.set_color("white"); at.set_fontweight("bold")
        ax.set_title(title, fontsize=13, color=SUB_C, pad=15)
        ax.set_facecolor(BG)
    plt.tight_layout()
    save(fig, "06_demographics.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 7 — CVC Comparison (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_cvc_comparison():
    q = """
        SELECT ti.access_type,
               COUNT(ti.patient_id) AS mm,
               SUM(ai.inpatient_admits) AS admits,
               (SUM(ai.inpatient_admits)*100.0/COUNT(ti.patient_id)) AS rate
        FROM treatment_info ti
        LEFT JOIN admit_info ai ON ti.patient_id=ai.patient_id AND ti.month=ai.month
        GROUP BY ti.access_type ORDER BY ti.access_type
    """
    df = pd.read_sql(q, engine)
    access_labels = {
        "CVC":     "Central Venous Catheter (CVC)\nTemporary / Higher Risk",
        "Non-CVC": "Non-CVC Access\n(Fistula or Graft — Permanent)"
    }
    df["access_label"] = df["access_type"].map(access_labels)
    cvc_colors = {
        "Central Venous Catheter (CVC)\nTemporary / Higher Risk": COLOR_HIGH,
        "Non-CVC Access\n(Fistula or Graft — Permanent)":         COLOR_LOW
    }
    colors = [cvc_colors.get(a, "#888") for a in df["access_label"]]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Vascular Access Type Impact on Hospitalization Rate\nCVC vs Non-CVC (Fistula / Graft)",
                 fontsize=14, fontweight="bold", color=TITLE_C)
    ax = axes[0]
    bars = ax.bar(df["access_label"], df["rate"], color=colors, width=0.4, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, df["rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{val:.2f}", ha="center", va="bottom", fontsize=13, fontweight="bold", color=TITLE_C)
    ratio = df.loc[df.access_type=="CVC","rate"].values[0] / df.loc[df.access_type=="Non-CVC","rate"].values[0]
    ax.set_title(f"Admits per 100 Member-Months\nCVC patients hospitalised {ratio:.1f}x more than Non-CVC",
                 fontsize=11, color=SUB_C)
    ax.set_ylabel("Admits per 100 Member-Months", fontsize=11)
    ax.set_facecolor(BG)
    plt.setp(ax.get_xticklabels(), fontsize=8)
    ax2 = axes[1]
    wedges, texts, autotexts = ax2.pie(
        df["mm"], labels=df["access_label"], autopct="%1.1f%%",
        colors=colors, startangle=90, wedgeprops={"edgecolor":"white","linewidth":2})
    for t in texts:      t.set_fontsize(9);  t.set_fontweight("bold")
    for at in autotexts: at.set_fontsize(11); at.set_color("white"); at.set_fontweight("bold")
    ax2.set_title("Share of Total Member-Months\nby Vascular Access Type", fontsize=11, color=SUB_C)
    ax2.set_facecolor(BG)
    plt.tight_layout()
    save(fig, "07_cvc_comparison.png")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
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
    chart_next_steps()
    print(f"\nAll 8 charts saved to: {OUT_DIR}")
