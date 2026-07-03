import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
from copy import deepcopy

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FTE Calculator — KCP",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PTDH Brand Colors
ORANGE  = "#E8500A"
DARK    = "#1C1C1C"
SURFACE = "#F8F8F8"
GREEN   = "#22C55E"
RED     = "#EF4444"
BLUE    = "#3B82F6"

st.markdown(f"""
<style>
  /* Global */
  html, body, [class*="css"] {{ font-family: 'Segoe UI', sans-serif; }}
  
  /* Header strip */
  .ptdh-header {{
    background: {DARK};
    color: white;
    padding: 16px 24px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-left: 6px solid {ORANGE};
  }}
  .ptdh-header .eyebrow {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {ORANGE};
    margin-bottom: 2px;
  }}
  .ptdh-header .title {{
    font-size: 22px;
    font-weight: 800;
    margin: 0;
  }}

  /* KPI Cards */
  .kpi-card {{
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #E5E7EB;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .kpi-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 6px;
  }}
  .kpi-value {{
    font-size: 36px;
    font-weight: 800;
    color: {DARK};
    line-height: 1;
  }}
  .kpi-sub {{
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
  }}
  .kpi-orange {{ border-top: 3px solid {ORANGE}; }}
  .kpi-green  {{ border-top: 3px solid {GREEN}; }}
  .kpi-blue   {{ border-top: 3px solid {BLUE}; }}
  .kpi-red    {{ border-top: 3px solid {RED}; }}

  /* Section header */
  .sec-hdr {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {ORANGE};
    border-bottom: 2px solid {ORANGE};
    padding-bottom: 6px;
    margin-bottom: 14px;
    margin-top: 24px;
  }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
    background: {DARK} !important;
  }}
  [data-testid="stSidebar"] * {{ color: white !important; }}
  [data-testid="stSidebar"] .stNumberInput input,
  [data-testid="stSidebar"] .stTextInput input,
  [data-testid="stSidebar"] .stSelectbox select {{
    background: #2D2D2D !important;
    color: white !important;
    border: 1px solid #444 !important;
  }}

  /* Table styling */
  .stDataFrame {{ border-radius: 8px; overflow: hidden; }}
  
  /* Streamlit button override */
  .stButton > button {{
    background-color: {ORANGE} !important;
    color: white !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
  }}
  
  div[data-testid='stMetricValue'] {{
    font-size: 28px !important;
    font-weight: 800 !important;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DEFAULT DATA
# ─────────────────────────────────────────────
ROLE_PROP = {
    "Digger":           {"mech": 0.68, "elec": 0.19, "weld": 0.13},
    "Hauler":           {"mech": 0.71, "elec": 0.18, "weld": 0.11},
    "Auxilary Track":   {"mech": 0.69, "elec": 0.18, "weld": 0.13},
    "Auxilary Wheel":   {"mech": 0.71, "elec": 0.18, "weld": 0.11},
    "Support&Facility": {"mech": 0.46, "elec": 0.36, "weld": 0.18},
}

LOAD_FACTOR = {
    "Big Exca":     {"mech": 2.0, "elec": 0.5, "weld": 0.4, "group": "Digger"},
    "Medium Exca":  {"mech": 1.5, "elec": 0.4, "weld": 0.3, "group": "Digger"},
    "Small Exca":   {"mech": 1.0, "elec": 0.3, "weld": 0.2, "group": "Digger"},
    "Big Hauler":   {"mech": 1.6, "elec": 0.4, "weld": 0.2, "group": "Hauler"},
    "Medium Hauler":{"mech": 1.3, "elec": 0.3, "weld": 0.2, "group": "Hauler"},
    "Hauler Small": {"mech": 1.1, "elec": 0.3, "weld": 0.2, "group": "Hauler"},
    "Dozzer":       {"mech": 1.1, "elec": 0.3, "weld": 0.2, "group": "Auxilary Track"},
    "Grader":       {"mech": 0.9, "elec": 0.2, "weld": 0.2, "group": "Auxilary Wheel"},
    "Wheel Loader": {"mech": 0.9, "elec": 0.2, "weld": 0.2, "group": "Auxilary Wheel"},
    "Compactor":    {"mech": 1.0, "elec": 0.2, "weld": 0.1, "group": "Auxilary Wheel"},
    "Light Vehicel":{"mech": 0.3, "elec": 0.2, "weld": 0.1, "group": "Support&Facility"},
    "Light Truck":  {"mech": 0.3, "elec": 0.3, "weld": 0.1, "group": "Support&Facility"},
    "Service Truck":{"mech": 0.3, "elec": 0.3, "weld": 0.1, "group": "Support&Facility"},
    "Water Truck":  {"mech": 0.3, "elec": 0.3, "weld": 0.1, "group": "Support&Facility"},
    "Genset":       {"mech": 0.3, "elec": 0.3, "weld": 0.1, "group": "Support&Facility"},
    "Pump":         {"mech": 0.3, "elec": 0.3, "weld": 0.1, "group": "Support&Facility"},
    "Light Tower":  {"mech": 0.1, "elec": 0.1, "weld": 0.0, "group": "Support&Facility"},
}

DEFAULT_EQUIPMENT = [
    # sub_cat,         unit_type,        pop, pa,   lost_time_obs
    ("Digger",    "Big Exca",     "R9200",       3,  0.85, 3.6),
    ("Digger",    "Medium Exca",  "SY750H",     11,  0.87, 3.1),
    ("Digger",    "Small Exca",   "SY500H",     28,  0.85, 3.6),
    ("Digger",    "Small Exca",   "XC8-C2570",   1,  0.90, 2.4),
    ("Digger",    "Small Exca",   "SY215H",     10,  0.84, 3.8),
    ("Digger",    "Small Exca",   "SY365H",      1,  0.85, 3.6),
    ("Hauler",    "Big Hauler",   "HD785-7",    16,  0.85, 3.6),
    ("Hauler",    "Big Hauler",   "RTH100",     18,  0.92, 1.9),
    ("Hauler",    "Medium Hauler","HD465-7R",   10,  0.82, 4.3),
    ("Hauler",    "Medium Hauler","SKT80S_HB",   3,  0.80, 4.8),
    ("Hauler",    "Medium Hauler","ZT115G",     50,  0.90, 2.4),
    ("Hauler",    "Medium Hauler","HD465_WT",    1,  0.80, 4.8),
    ("Hauler",    "Hauler Small", "P360_CO",     8,  0.80, 4.8),
    ("Hauler",    "Hauler Small", "P360",       40,  0.80, 4.8),
    ("Hauler",    "Hauler Small", "SYZ334C_CO", 13,  0.90, 2.4),
    ("Hauler",    "Hauler Small", "SYZ334C",    13,  0.90, 2.4),
    ("Auxiliary", "Dozzer",       "D155A",       9,  0.82, 4.3),
    ("Auxiliary", "Dozzer",       "PR754",       6,  0.80, 4.8),
    ("Auxiliary", "Dozzer",       "LB230C",      7,  0.82, 4.3),
    ("Auxiliary", "Dozzer",       "PR776",       1,  0.92, 1.9),
    ("Auxiliary", "Dozzer",       "PR756",       3,  0.92, 1.9),
    ("Auxiliary", "Grader",       "14M",         2,  0.80, 4.8),
    ("Auxiliary", "Grader",       "GR3005",      8,  0.80, 4.8),
    ("Auxiliary", "Grader",       "STG230C",     2,  0.80, 4.8),
    ("Auxiliary", "Grader",       "GR3005T",     5,  0.90, 2.4),
    ("Auxiliary", "Grader",       "16H",         1,  0.80, 4.8),
    ("Auxiliary", "Compactor",    "CS10GC",      3,  0.80, 4.8),
    ("Auxiliary", "Compactor",    "SSR220C",     1,  0.80, 4.8),
    ("LV&Support","Water Truck",  "FM400",       1,  0.80, 4.8),
    ("LV&Support","Water Truck",  "M2528",       6,  0.80, 4.8),
    ("LV&Support","Water Truck",  "CMS50",       2,  0.92, 1.9),
    ("LV&Support","Pump",         "MFMS-16",     1,  0.80, 4.8),
    ("LV&Support","Pump",         "CP150SS",     1,  0.85, 3.6),
    ("LV&Support","Pump",         "HH160",       1,  0.85, 3.6),
    ("LV&Support","Pump",         "FBP300",      1,  0.85, 3.6),
    ("LV&Support","Pump",         "XH250-C32",   3,  0.90, 2.4),
    ("LV&Support","Pump",         "XH250-C27",   6,  0.90, 2.4),
]

# M1/M2/M3 distribution from CSV row1
DIST = {"M1": 0.20, "M2": 0.30, "M3": 0.50}

# ─────────────────────────────────────────────
# CORE FORMULA
# ─────────────────────────────────────────────
def calc_fte(pop, pa, emhd_obs, lf_m, lf_e, lf_w, ratio_shift, comp_factor, std_hours, group):
    """
    Core FTE calculation per equipment row.
    FTE_role = round(pop * lf_role * (emhd_obs/std_hours) * ratio_shift / comp_factor * prop_role)
    Total = FTE_mech + FTE_weld + FTE_elec
    """
    prop = ROLE_PROP.get(group, {"mech": 0.68, "elec": 0.19, "weld": 0.13})
    base = (emhd_obs / std_hours) * ratio_shift / comp_factor

    fte_m = round(pop * lf_m * base * prop["mech"])
    fte_w = round(pop * lf_w * base * prop["weld"])
    fte_e = round(pop * lf_e * base * prop["elec"])
    total = fte_m + fte_w + fte_e

    # M1/M2/M3 split for Mechanic
    m1 = max(1, round(fte_m * DIST["M1"])) if fte_m > 0 else 0
    m2 = max(1, round(fte_m * DIST["M2"])) if fte_m > 0 else 0
    m3 = fte_m - m1 - m2 if fte_m > 0 else 0

    # Welder split
    w1 = round(fte_w * 0.43) if fte_w > 0 else 0
    w2 = fte_w - w1 if fte_w > 0 else 0

    # Elec split
    e1 = round(fte_e * 0.43) if fte_e > 0 else 0
    e2 = fte_e - e1 if fte_e > 0 else 0

    return {
        "total": total,
        "fte_mech": fte_m, "fte_weld": fte_w, "fte_elec": fte_e,
        "m1": m1, "m2": m2, "m3": m3,
        "w1": w1, "w2": w2,
        "e1": e1, "e2": e2,
    }

# ─────────────────────────────────────────────
# SIDEBAR — GLOBAL PARAMS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:12px 0 4px 0;'>
      <div style='font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{ORANGE};margin-bottom:4px;'>PT Darma Henwa Tbk</div>
      <div style='font-size:17px;font-weight:800;'>⛏️ FTE Calculator</div>
      <div style='font-size:11px;color:#9CA3AF;margin-top:2px;'>Maintenance Division — KCP Site</div>
    </div>
    <hr style='border-color:#333;margin:12px 0;'>
    """, unsafe_allow_html=True)

    st.markdown("**⚙️ Global Parameters**")

    site = st.text_input("Site", value="Selatan (ACP - KCP)")
    comp_factor = st.slider("Competency Factor (%)", 40, 100, 60, step=5) / 100
    ratio_shift = st.number_input("Ratio Shift", value=1.46, step=0.01, format="%.2f",
                                   help="Dari tabel Ratio Shift per site")
    std_hours = st.number_input("Std Work Hours/Day", value=8.7, step=0.1, format="%.1f")
    jarak_km = st.number_input("Jarak Rata-rata Area Kerja (KM)", value=10, step=1)

    st.markdown("---")
    st.markdown("**📊 Lost Time (dari Observasi)**")
    lost_time_global = st.number_input(
        "Lost Time Global (jam/hari)",
        value=3.04, step=0.01, format="%.2f",
        help="Ambil dari Sheet Resume kolom C1 atau input manual"
    )
    use_per_unit_lt = st.checkbox("Gunakan lost time per unit (dari CSV)", value=True,
                                   help="Jika dicentang, setiap unit pakai lost time observasi masing-masing")

    st.markdown("---")
    st.markdown("**💰 Salary Reference (Rp/bulan)**")
    sal_m1 = st.number_input("Mechanic M1", value=10_000_000, step=500_000)
    sal_m2 = st.number_input("Mechanic M2", value=12_500_000, step=500_000)
    sal_m3 = st.number_input("Mechanic M3", value=16_000_000, step=500_000)
    sal_w  = st.number_input("Welder", value=10_000_000, step=500_000)
    sal_e  = st.number_input("Electrician", value=10_000_000, step=500_000)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="ptdh-header">
  <div>
    <div class="eyebrow">PT Darma Henwa Tbk — Maintenance Division</div>
    <div class="title">⛏️ FTE Calculator — {site}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# EQUIPMENT TABLE (editable)
# ─────────────────────────────────────────────
st.markdown('<div class="sec-hdr">📋 Data Equipment (Editable)</div>', unsafe_allow_html=True)
st.caption("Klik cell untuk mengedit. Data default dari KCP. Bisa tambah/hapus baris.")

# Build initial dataframe
if "eq_df" not in st.session_state:
    rows = []
    for cat, sub_cat, unit, pop, pa, lt in DEFAULT_EQUIPMENT:
        lf = LOAD_FACTOR.get(sub_cat, {"mech":1.0,"elec":0.3,"weld":0.2,"group":"Support&Facility"})
        rows.append({
            "Category": cat,
            "Sub Category": sub_cat,
            "Unit / Model": unit,
            "Population": pop,
            "Target PA (%)": int(pa * 100),
            "Lost Time Obs (jam)": lt,
            "LF Mechanic": lf["mech"],
            "LF Electrician": lf["elec"],
            "LF Welder": lf["weld"],
        })
    st.session_state.eq_df = pd.DataFrame(rows)

col_add, col_reset, _ = st.columns([1,1,6])
with col_add:
    if st.button("➕ Tambah Baris"):
        new_row = {
            "Category": "Hauler",
            "Sub Category": "Big Hauler",
            "Unit / Model": "New Unit",
            "Population": 1,
            "Target PA (%)": 85,
            "Lost Time Obs (jam)": 3.04,
            "LF Mechanic": 1.6,
            "LF Electrician": 0.4,
            "LF Welder": 0.2,
        }
        st.session_state.eq_df = pd.concat(
            [st.session_state.eq_df, pd.DataFrame([new_row])],
            ignore_index=True
        )
with col_reset:
    if st.button("🔄 Reset Default"):
        del st.session_state.eq_df
        st.rerun()

edited_df = st.data_editor(
    st.session_state.eq_df,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Category": st.column_config.SelectboxColumn(
            options=["Digger","Hauler","Auxiliary","LV&Support"], required=True
        ),
        "Sub Category": st.column_config.SelectboxColumn(
            options=list(LOAD_FACTOR.keys()), required=True
        ),
        "Target PA (%)": st.column_config.NumberColumn(min_value=50, max_value=100, step=1, format="%d%%"),
        "Lost Time Obs (jam)": st.column_config.NumberColumn(min_value=0.0, max_value=12.0, step=0.1, format="%.1f"),
        "LF Mechanic": st.column_config.NumberColumn(min_value=0.0, max_value=5.0, step=0.1, format="%.1f"),
        "LF Electrician": st.column_config.NumberColumn(min_value=0.0, max_value=5.0, step=0.1, format="%.1f"),
        "LF Welder": st.column_config.NumberColumn(min_value=0.0, max_value=5.0, step=0.1, format="%.1f"),
        "Population": st.column_config.NumberColumn(min_value=0, step=1),
    },
    hide_index=True,
    key="equipment_editor"
)
st.session_state.eq_df = edited_df

# ─────────────────────────────────────────────
# CALCULATE
# ─────────────────────────────────────────────
results = []
for _, row in edited_df.iterrows():
    sub_cat = row["Sub Category"]
    lf_info = LOAD_FACTOR.get(sub_cat, {"mech":1.0,"elec":0.3,"weld":0.2,"group":"Support&Facility"})
    group   = lf_info["group"]

    emhd = row["Lost Time Obs (jam)"] if use_per_unit_lt else lost_time_global
    pa   = row["Target PA (%)"] / 100

    res = calc_fte(
        pop        = int(row["Population"]),
        pa         = pa,
        emhd_obs   = emhd,
        lf_m       = row["LF Mechanic"],
        lf_e       = row["LF Electrician"],
        lf_w       = row["LF Welder"],
        ratio_shift= ratio_shift,
        comp_factor= comp_factor,
        std_hours  = std_hours,
        group      = group
    )
    results.append({
        "Category":    row["Category"],
        "Sub Category":sub_cat,
        "Unit":        row["Unit / Model"],
        "Pop":         int(row["Population"]),
        "PA":          f'{row["Target PA (%)"]}%',
        "LT (jam)":    emhd,
        "FTE Mech":    res["fte_mech"],
        "FTE Weld":    res["fte_weld"],
        "FTE Elec":    res["fte_elec"],
        "Total FTE":   res["total"],
        "M1":res["m1"],"M2":res["m2"],"M3":res["m3"],
        "W1":res["w1"],"W2":res["w2"],
        "E1":res["e1"],"E2":res["e2"],
    })

res_df = pd.DataFrame(results)

# Totals
tot_mech = int(res_df["FTE Mech"].sum())
tot_weld = int(res_df["FTE Weld"].sum())
tot_elec = int(res_df["FTE Elec"].sum())
tot_all  = int(res_df["Total FTE"].sum())
tot_m1   = int(res_df["M1"].sum())
tot_m2   = int(res_df["M2"].sum())
tot_m3   = int(res_df["M3"].sum())
tot_w1   = int(res_df["W1"].sum())
tot_w2   = int(res_df["W2"].sum())
tot_e1   = int(res_df["E1"].sum())
tot_e2   = int(res_df["E2"].sum())

# Cost calculation
cost_mech_mo = (tot_m1*sal_m1 + tot_m2*sal_m2 + tot_m3*sal_m3)
cost_weld_mo = (tot_w1+tot_w2) * sal_w
cost_elec_mo = (tot_e1+tot_e2) * sal_e
cost_total_mo = cost_mech_mo + cost_weld_mo + cost_elec_mo
cost_total_yr = cost_total_mo * 12

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
st.markdown('<div class="sec-hdr">📊 Summary FTE</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card kpi-orange">
      <div class="kpi-label">Total FTE</div>
      <div class="kpi-value">{tot_all}</div>
      <div class="kpi-sub">Semua peran</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card kpi-blue">
      <div class="kpi-label">Mechanic</div>
      <div class="kpi-value">{tot_mech}</div>
      <div class="kpi-sub">M1:{tot_m1} · M2:{tot_m2} · M3:{tot_m3}</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card kpi-green">
      <div class="kpi-label">Welder</div>
      <div class="kpi-value">{tot_weld}</div>
      <div class="kpi-sub">W1:{tot_w1} · W2:{tot_w2}</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card kpi-red">
      <div class="kpi-label">Electrician</div>
      <div class="kpi-value">{tot_elec}</div>
      <div class="kpi-sub">E1:{tot_e1} · E2:{tot_e2}</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #8B5CF6;">
      <div class="kpi-label">Est. Cost/Bulan</div>
      <div class="kpi-value" style="font-size:22px;color:#8B5CF6;">Rp {cost_total_mo/1e9:.2f}B</div>
      <div class="kpi-sub">Per tahun: Rp {cost_total_yr/1e9:.1f}B</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    # FTE by Category
    cat_sum = res_df.groupby("Category")[["FTE Mech","FTE Weld","FTE Elec"]].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Mechanic", x=cat_sum["Category"], y=cat_sum["FTE Mech"],
                         marker_color=ORANGE))
    fig.add_trace(go.Bar(name="Welder",   x=cat_sum["Category"], y=cat_sum["FTE Weld"],
                         marker_color=BLUE))
    fig.add_trace(go.Bar(name="Electrician", x=cat_sum["Category"], y=cat_sum["FTE Elec"],
                         marker_color=GREEN))
    fig.update_layout(
        title="FTE by Category & Role",
        barmode="stack",
        height=320,
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=20, l=20, r=20),
        font=dict(size=12)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#F3F4F6")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    # Role composition donut
    labels = ["Mechanic", "Welder", "Electrician"]
    values = [tot_mech, tot_weld, tot_elec]
    colors = [ORANGE, BLUE, GREEN]
    fig2 = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent+value",
        textfont_size=12,
    ))
    fig2.update_layout(
        title="Komposisi Role",
        height=320,
        paper_bgcolor="white",
        showlegend=False,
        margin=dict(t=50, b=20, l=20, r=20),
        annotations=[dict(text=f"<b>{tot_all}</b><br>Total", x=0.5, y=0.5,
                          font_size=16, showarrow=False)]
    )
    st.plotly_chart(fig2, use_container_width=True)

# Mechanic Level breakdown bar
c3, c4 = st.columns(2)
with c3:
    fig3 = go.Figure(go.Bar(
        x=["M1\n(Junior)", "M2\n(Senior)", "M3\n(Master)"],
        y=[tot_m1, tot_m2, tot_m3],
        marker_color=[ORANGE, "#F97316", DARK],
        text=[tot_m1, tot_m2, tot_m3],
        textposition="outside"
    ))
    fig3.update_layout(
        title="Mechanic Level Distribution",
        height=280,
        paper_bgcolor="white", plot_bgcolor="white",
        showlegend=False,
        margin=dict(t=50, b=20, l=20, r=20),
        yaxis=dict(gridcolor="#F3F4F6"),
        xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    # Lost Time scatter
    fig4 = px.scatter(
        res_df, x="Pop", y="Total FTE",
        size="Total FTE", color="Category",
        hover_data=["Unit", "LT (jam)", "FTE Mech", "FTE Weld", "FTE Elec"],
        title="Population vs Total FTE per Unit",
        color_discrete_sequence=[ORANGE, BLUE, GREEN, "#8B5CF6"]
    )
    fig4.update_layout(
        height=280,
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    )
    fig4.update_xaxes(gridcolor="#F3F4F6")
    fig4.update_yaxes(gridcolor="#F3F4F6")
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────
# DETAIL TABLE
# ─────────────────────────────────────────────
st.markdown('<div class="sec-hdr">📋 Detail FTE per Unit</div>', unsafe_allow_html=True)

# Color coding
def color_fte(val):
    if isinstance(val, (int, float)):
        if val == 0: return "color: #9CA3AF"
        if val >= 20: return f"color: {RED}; font-weight:700"
        if val >= 10: return f"color: {ORANGE}; font-weight:700"
    return ""

display_cols = ["Category","Sub Category","Unit","Pop","PA","LT (jam)",
                "FTE Mech","FTE Weld","FTE Elec","Total FTE",
                "M1","M2","M3","W1","W2","E1","E2"]

styled = res_df[display_cols].style\
    .applymap(color_fte, subset=["FTE Mech","FTE Weld","FTE Elec","Total FTE"])\
    .highlight_max(subset=["Total FTE"], color="#FFF3EE")\
    .format({"LT (jam)": "{:.1f}"})\
    .set_properties(**{"font-size":"13px"})

st.dataframe(styled, use_container_width=True, height=450, hide_index=True)

# Totals row
tot_row = pd.DataFrame([{
    "Category":"TOTAL","Sub Category":"","Unit":"","Pop":int(edited_df["Population"].sum()),
    "PA":"","LT (jam)":"",
    "FTE Mech":tot_mech,"FTE Weld":tot_weld,"FTE Elec":tot_elec,"Total FTE":tot_all,
    "M1":tot_m1,"M2":tot_m2,"M3":tot_m3,"W1":tot_w1,"W2":tot_w2,"E1":tot_e1,"E2":tot_e2
}])

st.markdown(f"""
<div style="background:{DARK};color:white;padding:10px 16px;border-radius:8px;
            display:flex;gap:24px;align-items:center;font-weight:700;font-size:14px;">
  <span>🏁 TOTAL</span>
  <span style="color:{ORANGE};">Mech: {tot_mech}</span>
  <span style="color:{BLUE};">Welder: {tot_weld}</span>
  <span style="color:{GREEN};">Elec: {tot_elec}</span>
  <span>|</span>
  <span>M1:{tot_m1} · M2:{tot_m2} · M3:{tot_m3}</span>
  <span>W1:{tot_w1} · W2:{tot_w2}</span>
  <span>E1:{tot_e1} · E2:{tot_e2}</span>
  <span>|</span>
  <span style="color:{ORANGE};">Grand Total: {tot_all} FTE</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# COST BREAKDOWN
# ─────────────────────────────────────────────
st.markdown('<div class="sec-hdr">💰 Estimasi Biaya</div>', unsafe_allow_html=True)

cc1, cc2, cc3, cc4 = st.columns(4)
with cc1:
    st.metric("Mechanic / Bulan", f"Rp {cost_mech_mo/1e6:.0f}jt",
              help=f"M1×{tot_m1} + M2×{tot_m2} + M3×{tot_m3}")
with cc2:
    st.metric("Welder / Bulan", f"Rp {cost_weld_mo/1e6:.0f}jt")
with cc3:
    st.metric("Electrician / Bulan", f"Rp {cost_elec_mo/1e6:.0f}jt")
with cc4:
    st.metric("Total / Bulan", f"Rp {cost_total_mo/1e9:.3f}B")

st.metric("💵 Total Biaya Per Tahun", f"Rp {cost_total_yr/1e9:.2f} Miliar",
          delta=f"~Rp {cost_total_yr/1e6:.0f}jt / tahun")

# ─────────────────────────────────────────────
# FORMULA INFO
# ─────────────────────────────────────────────
with st.expander("ℹ️ Formula & Metodologi"):
    st.markdown(f"""
    ### Formula FTE (per unit)
    
    ```
    FTE_Mech = round(Population × LF_Mech × (LostTime / StdHours) × RatioShift / CompFactor × PropMech)
    FTE_Weld = round(Population × LF_Weld × (LostTime / StdHours) × RatioShift / CompFactor × PropWeld)
    FTE_Elec = round(Population × LF_Elec × (LostTime / StdHours) × RatioShift / CompFactor × PropElec)
    ```

    ### Parameter Global
    | Parameter | Nilai | Keterangan |
    |---|---|---|
    | Competency Factor | {comp_factor:.0%} | Faktor kompetensi mekanik |
    | Ratio Shift | {ratio_shift} | Faktor kebutuhan per shift (Selatan/KCP) |
    | Std Hours/Day | {std_hours} | Jam kerja standar per shift |
    | Lost Time | Per unit (observasi) | Jam terbuang per hari dari Time & Motion Study |
    
    ### Load Factor (per sub-kategori)
    | Sub Kategori | LF Mechanic | LF Electrician | LF Welder |
    |---|---|---|---|
    | Big Exca | 2.0 | 0.5 | 0.4 |
    | Medium Exca | 1.5 | 0.4 | 0.3 |
    | Small Exca | 1.0 | 0.3 | 0.2 |
    | Big Hauler | 1.6 | 0.4 | 0.2 |
    | Medium Hauler | 1.3 | 0.3 | 0.2 |
    | Hauler Small | 1.1 | 0.3 | 0.2 |
    | Dozzer/Grader | 0.9–1.1 | 0.2–0.3 | 0.2 |
    | Support/LV | 0.1–0.3 | 0.1–0.3 | 0.0–0.1 |
    
    ### Distribusi Level
    - **Mechanic**: M1 (Junior) 20% · M2 (Senior) 30% · M3 (Master) 50%
    - **Welder**: W1 43% · W2 57%
    - **Electrician**: E1 43% · E2 57%
    
    ### Proporsi Role per Grup Equipment
    | Grup | Mechanic | Electrician | Welder |
    |---|---|---|---|
    | Digger | 68% | 19% | 13% |
    | Hauler | 71% | 18% | 11% |
    | Aux Track | 69% | 18% | 13% |
    | Aux Wheel | 71% | 18% | 11% |
    | Support & Facility | 46% | 36% | 18% |
    """)

# Footer
st.markdown(f"""
<hr style="border-color:#E5E7EB;margin-top:32px;">
<div style="text-align:center;color:#9CA3AF;font-size:11px;padding:8px;">
  PT Darma Henwa Tbk · Maintenance Division · FTE Calculator v1.0 · Site: {site}
</div>
""", unsafe_allow_html=True)
