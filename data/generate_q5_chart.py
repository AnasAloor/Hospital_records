import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/Hospital_records')

BLUE  = '#2E86AB'
RED   = '#E84855'
DARK  = '#1A1A2E'
LIGHT = '#F7F9FC'
ACCENT= '#F4A261'
GREEN = '#2A9D8F'
GRAY  = '#6C757D'
GOLD  = '#E9C46A'

# ── Fetch data ─────────────────────────────────────────────
with engine.connect() as conn:

    # i — avg age by gender
    rows = conn.execute(text("""
        SELECT CASE sex WHEN 'M' THEN 'Male' WHEN 'F' THEN 'Female' END,
               ROUND(AVG(age)::numeric,1), COUNT(DISTINCT patient_id)
        FROM demographics WHERE age IS NOT NULL GROUP BY sex ORDER BY sex
    """)).fetchall()
    gender_labels = [r[0] for r in rows]
    gender_ages   = [float(r[1]) for r in rows]
    gender_counts = [int(r[2]) for r in rows]

    # ii — members at clinic 4057
    members_4057 = conn.execute(text(
        "SELECT COUNT(DISTINCT patient_id) FROM treatment_info WHERE facility_id=4057"
    )).scalar()

    # iii — max/min treatments 2018
    r3 = conn.execute(text("""
        SELECT MAX(total_tx), MIN(total_tx), ROUND(AVG(total_tx)::numeric,1)
        FROM treatment_info WHERE EXTRACT(YEAR FROM month)=2018
    """)).fetchone()
    tx_max, tx_min, tx_avg = int(r3[0]), int(r3[1]), float(r3[2])

    # iv — missing labs
    missing_labs = conn.execute(text("""
        SELECT COUNT(*) FROM labs
        WHERE albumin IS NULL OR hemoglobin IS NULL OR hematocrit IS NULL OR ktv IS NULL
    """)).scalar()
    total_mm = conn.execute(text("SELECT COUNT(*) FROM labs")).scalar()
    pct_missing = round(missing_labs / total_mm * 100, 1)

    # iv — per-lab breakdown
    lab_rows = conn.execute(text("""
        SELECT
            SUM(CASE WHEN albumin   IS NULL THEN 1 ELSE 0 END) AS alb_null,
            SUM(CASE WHEN hemoglobin IS NULL THEN 1 ELSE 0 END) AS hgb_null,
            SUM(CASE WHEN hematocrit IS NULL THEN 1 ELSE 0 END) AS hct_null,
            SUM(CASE WHEN ktv        IS NULL THEN 1 ELSE 0 END) AS ktv_null
        FROM labs
    """)).fetchone()
    lab_missing = {
        'Albumin': int(lab_rows[0]),
        'Hemoglobin': int(lab_rows[1]),
        'Hematocrit': int(lab_rows[2]),
        'KTV': int(lab_rows[3])
    }

    # v — admits by clinic Dec 2017
    v_rows = conn.execute(text("""
        SELECT ti.facility_id, fi.state,
               CASE fi.region_id WHEN 'A' THEN 'Washington' ELSE 'Alabama' END,
               SUM(ai.inpatient_admits)
        FROM admit_info ai
        JOIN treatment_info ti ON ai.patient_id=ti.patient_id AND ai.month=ti.month
        JOIN facility_info fi  ON ti.facility_id=fi.facility_id
        WHERE ai.month='2017-12-31'
        GROUP BY ti.facility_id, fi.state, fi.region_id
        ORDER BY SUM(ai.inpatient_admits) DESC
    """)).fetchall()
    fac_ids     = [str(r[0]) for r in v_rows]
    fac_admits  = [int(r[3]) for r in v_rows]
    fac_regions = [r[2] for r in v_rows]
    fac_colors  = [BLUE if r=='Washington' else RED for r in fac_regions]

# ── Build Figure ───────────────────────────────────────────
fig = plt.figure(figsize=(20, 14), facecolor=DARK)
fig.patch.set_facecolor(DARK)

# Title
fig.text(0.5, 0.97, 'SQL Case Study — Interview Questions 5i–5v',
         ha='center', va='top', fontsize=22, fontweight='bold',
         color='white', fontfamily='monospace')
fig.text(0.5, 0.935, 'DaVita Dialysis | Dataset: Jul 2017 – Jun 2018 | 1,311 Patients | 9 Facilities',
         ha='center', va='top', fontsize=11, color='#AAAAAA')

# Grid: 2 rows × 3 cols  (last row: 2 wide + 1)
gs = fig.add_gridspec(2, 3,
                      left=0.06, right=0.97,
                      top=0.90, bottom=0.07,
                      hspace=0.42, wspace=0.32)

panel_kw = dict(facecolor='#16213E')

def style_panel(ax):
    for spine in ax.spines.values():
        spine.set_edgecolor('#2E86AB')
        spine.set_linewidth(1.2)

# ── Panel i — Avg Age by Gender ────────────────────────────
ax1 = fig.add_subplot(gs[0, 0], **panel_kw)
style_panel(ax1)
colors_g = [BLUE, RED]
bars = ax1.bar(gender_labels, gender_ages, color=colors_g, width=0.45,
               edgecolor='white', linewidth=0.8, zorder=3)
ax1.set_ylim(0, 80)
ax1.set_facecolor('#16213E')
ax1.tick_params(colors='white', labelsize=11)
for spine in ax1.spines.values():
    spine.set_edgecolor('#444466')
ax1.yaxis.label.set_color('white')
ax1.set_ylabel('Average Age (yrs)', color='#AAAAAA', fontsize=10)
ax1.set_title('i.  Average Age by Gender', color=ACCENT, fontsize=12,
              fontweight='bold', pad=10)
ax1.yaxis.grid(True, color='#2A2A4A', linewidth=0.6, zorder=0)
ax1.set_axisbelow(True)
for bar, age, cnt in zip(bars, gender_ages, gender_counts):
    ax1.text(bar.get_x() + bar.get_width()/2, age + 1.5,
             f'{age} yrs\n({cnt:,} members)', ha='center', va='bottom',
             color='white', fontsize=10, fontweight='bold')
# SQL caption
ax1.text(0.5, -0.22,
         "SQL: SELECT sex, ROUND(AVG(age),1) FROM demographics\nGROUP BY sex",
         transform=ax1.transAxes, ha='center', fontsize=7.5,
         color='#88AACC', style='italic')

# ── Panel ii — Clinic 4057 ─────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1], **panel_kw)
style_panel(ax2)
ax2.axis('off')
ax2.set_title('ii.  Distinct Members — Clinic 4057', color=ACCENT,
              fontsize=12, fontweight='bold', pad=10)

# Big number display
ax2.text(0.5, 0.65, str(f'{members_4057:,}'), transform=ax2.transAxes,
         ha='center', va='center', fontsize=72, fontweight='bold',
         color=BLUE)
ax2.text(0.5, 0.38, 'Distinct Members', transform=ax2.transAxes,
         ha='center', va='center', fontsize=15, color='white')
ax2.text(0.5, 0.28, 'treated at Facility 4057\n(Jul 2017 – Jun 2018)',
         transform=ax2.transAxes, ha='center', va='center',
         fontsize=10, color='#AAAAAA')

# Percent of total
total_patients = 1311
pct_4057 = round(members_4057 / total_patients * 100, 1)
ax2.text(0.5, 0.10, f'{pct_4057}% of all 1,311 members',
         transform=ax2.transAxes, ha='center', va='center',
         fontsize=10, color=GREEN, fontweight='bold')
ax2.text(0.5, -0.06,
         "SQL: SELECT COUNT(DISTINCT patient_id)\nFROM treatment_info WHERE facility_id = 4057",
         transform=ax2.transAxes, ha='center', fontsize=7.5,
         color='#88AACC', style='italic')

# ── Panel iii — Max/Min Treatments 2018 ───────────────────
ax3 = fig.add_subplot(gs[0, 2], **panel_kw)
style_panel(ax3)
ax3.axis('off')
ax3.set_title('iii.  Max & Min Treatments — 2018', color=ACCENT,
              fontsize=12, fontweight='bold', pad=10)

metrics_3  = ['Minimum', 'Average', 'Maximum']
values_3   = [tx_min, tx_avg, tx_max]
colors_3   = [GREEN, GOLD, RED]
y_pos = [0.72, 0.48, 0.24]

for label, val, col, y in zip(metrics_3, values_3, colors_3, y_pos):
    ax3.text(0.18, y, f'{label}:', transform=ax3.transAxes,
             ha='left', va='center', fontsize=12, color='#AAAAAA')
    ax3.text(0.72, y, f'{val}', transform=ax3.transAxes,
             ha='center', va='center', fontsize=26, fontweight='bold',
             color=col)
    ax3.text(0.92, y, 'tx', transform=ax3.transAxes,
             ha='left', va='center', fontsize=11, color='#AAAAAA')

ax3.text(0.5, 0.08, 'treatments per member-month',
         transform=ax3.transAxes, ha='center', va='center',
         fontsize=9, color='#777799')
ax3.text(0.5, -0.06,
         "SQL: SELECT MAX(total_tx), MIN(total_tx), AVG(total_tx)\nFROM treatment_info WHERE EXTRACT(YEAR FROM month)=2018",
         transform=ax3.transAxes, ha='center', fontsize=7.5,
         color='#88AACC', style='italic')

# ── Panel iv — Missing Labs ────────────────────────────────
ax4 = fig.add_subplot(gs[1, 0], **panel_kw)
style_panel(ax4)
lab_names  = list(lab_missing.keys())
lab_vals   = list(lab_missing.values())
lab_colors = [ACCENT, BLUE, GREEN, RED]
bars4 = ax4.barh(lab_names, lab_vals, color=lab_colors,
                 edgecolor='white', linewidth=0.6, height=0.5)
ax4.set_facecolor('#16213E')
ax4.tick_params(colors='white', labelsize=10)
ax4.set_xlabel('Count of NULL rows', color='#AAAAAA', fontsize=9)
ax4.set_title(f'iv.  Missing Lab Values  ({pct_missing}% of MMs)',
              color=ACCENT, fontsize=12, fontweight='bold', pad=10)
ax4.xaxis.grid(True, color='#2A2A4A', linewidth=0.6)
ax4.set_axisbelow(True)
for bar, val in zip(bars4, lab_vals):
    ax4.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
             f'{val:,}', va='center', color='white', fontsize=10, fontweight='bold')
ax4.set_xlim(0, max(lab_vals) * 1.22)

# Big number overlay
ax4.text(0.73, 0.18, f'{missing_labs:,}', transform=ax4.transAxes,
         ha='center', va='center', fontsize=28, fontweight='bold',
         color=RED, alpha=0.85)
ax4.text(0.73, 0.06, 'total MM\nmissing', transform=ax4.transAxes,
         ha='center', va='center', fontsize=8, color='#AAAAAA')
ax4.text(0.5, -0.22,
         "SQL: SELECT COUNT(*) FROM labs\nWHERE albumin IS NULL OR hemoglobin IS NULL OR hematocrit IS NULL OR ktv IS NULL",
         transform=ax4.transAxes, ha='center', fontsize=7.5,
         color='#88AACC', style='italic')

# ── Panel v — Admits by Clinic Dec 2017 ───────────────────
ax5 = fig.add_subplot(gs[1, 1:], **panel_kw)
style_panel(ax5)
y_pos5 = np.arange(len(fac_ids))
bars5 = ax5.barh(y_pos5, fac_admits, color=fac_colors,
                 edgecolor='white', linewidth=0.6, height=0.6)
ax5.set_yticks(y_pos5)
ax5.set_yticklabels([f'Facility {f}' for f in fac_ids],
                    color='white', fontsize=10)
ax5.tick_params(colors='white', labelsize=10)
ax5.set_xlabel('Inpatient Admits', color='#AAAAAA', fontsize=10)
ax5.set_title('v.  Admits by Clinic — December 2017  (Total: 119)',
              color=ACCENT, fontsize=12, fontweight='bold', pad=10)
ax5.xaxis.grid(True, color='#2A2A4A', linewidth=0.6)
ax5.set_axisbelow(True)
ax5.invert_yaxis()
for bar, val, reg in zip(bars5, fac_admits, fac_regions):
    ax5.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
             f'{val}  ({reg})', va='center',
             color='white', fontsize=9.5, fontweight='bold')
ax5.set_xlim(0, max(fac_admits) * 1.55)

legend_patches = [
    mpatches.Patch(color=BLUE, label='Washington (Region A)'),
    mpatches.Patch(color=RED,  label='Alabama (Region B)')
]
ax5.legend(handles=legend_patches, loc='lower right',
           facecolor='#1A1A2E', edgecolor='#2E86AB',
           labelcolor='white', fontsize=9)
ax5.text(0.5, -0.14,
         "SQL: SELECT facility_id, SUM(inpatient_admits) FROM admit_info JOIN treatment_info USING(patient_id,month)\nJOIN facility_info USING(facility_id) WHERE month='2017-12-31' GROUP BY facility_id ORDER BY 2 DESC",
         transform=ax5.transAxes, ha='center', fontsize=7.5,
         color='#88AACC', style='italic')

# ── Footer ─────────────────────────────────────────────────
fig.text(0.5, 0.012,
         "Each SQL snippet uses standard ANSI SQL • Tables: demographics, treatment_info, labs, admit_info, facility_info",
         ha='center', fontsize=9, color='#666688', style='italic')

out = r'c:\Users\Rtx_5090\Desktop\Hospital_records\data\charts\09_sql_interview_answers.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=DARK)
plt.close()
print(f"Saved → {out}")
