# app.py - Heat Transfer Analysis with clear inputs & styled UI
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import plotly.graph_objects as go

# ---------- Page Setup ----------
st.set_page_config(page_title="Heat Transfer Analysis", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.main { padding: 0rem 2rem; }
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#0f172a 0%, #0b1220 100%);
  color: #e2e8f0;
}
label, .stSlider label, .stNumberInput label { 
  font-weight: 700 !important; 
  color: #e5e7eb !important; 
}
small.help { color:#9ca3af; font-size:12px; display:block; margin-top:-6px; margin-bottom:8px; }
.stButton>button {
    background: linear-gradient(90deg, #22c55e, #16a34a);
    color: white; border: none; border-radius: 12px;
    padding: 0.6rem 1rem; font-weight: 700; transition: 0.3s;
}
.stButton>button:hover { background: linear-gradient(90deg, #16a34a, #15803d); color: white; }
.metric-card { border-radius: 18px; padding: 18px; background: linear-gradient(135deg, #2563eb, #9333ea); color: white; text-align: center; box-shadow: 0 6px 24px rgba(0,0,0,.25); }
.metric-card h2 { margin: 0; font-size: 1.0rem; opacity:.95; }
.metric-card p { margin: 0; font-size: 1.8rem; font-weight: 800; }
.badge-err { display:inline-block; padding:4px 10px; border-radius:999px; background:#5a0b0b; color:#fecaca; font-weight:700; font-size:12px; }
.input-badge { border-radius: 14px; padding: 8px 12px; background:#0f172a; border:1px solid #1f2a44; color:#e5e7eb; font-weight:700; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
footer:after { content:'Developed by Praji'; visibility: visible; display:block; position: relative; padding: 5px; top: 2px; color: gray; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ---------- Load Data ----------
DATA_PATH = Path(__file__).parent / "heat_transfer_dataset.csv"
df = pd.read_csv(DATA_PATH)

# ---------- Limits ----------
LIMITS = {
    "ThermalCond": (50, 500),
    "BlockSize": (5, 50),
    "SourceTemp": (30, 150),
    "AmbientTemp": (0, 50),
}

# ---------- Functions ----------
def check_limits(vals: dict):
    issues = []
    for k,(lo,hi) in LIMITS.items():
        v = vals[k]
        if not (lo <= v <= hi):
            issues.append(f"{k} should be between {lo} and {hi}")
    return issues

def efficiency(max_temp, avg_temp, ambient_temp):
    denom = (max_temp - ambient_temp)
    if denom == 0:
        return 0.0
    return (max_temp - avg_temp) / denom

def coolant_suggestion(avg_temp):
    if avg_temp > 80: return "Liquid Nitrogen"
    elif avg_temp > 60: return "Water Cooling"
    elif avg_temp > 40: return "Oil Cooling"
    else: return "Air Cooling"

def material_suggestion(tc):
    if tc > 300: return "Copper"
    elif tc > 150: return "Aluminium"
    elif tc > 80: return "Steel"
    else: return "Ceramic"

def nearest_row_predict(tc, bs, stemp, atemp):
    d2 = (df["ThermalCond"]-tc)**2 + (df["BlockSize"]-bs)**2 + (df["SourceTemp"]-stemp)**2 + (df["AmbientTemp"]-atemp)**2
    row = df.loc[d2.idxmin()]
    return float(row["AvgTemp"]), float(row["MaxTemp"]), float(row["CenterTemp"])

# ---------- Header ----------
st.markdown("<h1 style='text-align:center;'>🔥 Heat Transfer Analysis</h1>", unsafe_allow_html=True)
st.caption("Enter inputs clearly with units. Predicts Avg/Max/Center Temperatures, Efficiency, Coolant & Material suggestions.")

# ---------- Sidebar Inputs ----------
st.sidebar.title("Inputs")

st.sidebar.subheader("Material & Geometry")
tc = st.sidebar.number_input(
    "Thermal Conductivity (W/m·K)",
    min_value=int(LIMITS["ThermalCond"][0]), max_value=int(LIMITS["ThermalCond"][1]), value=100, step=5,
    help="Example: Copper≈400, Aluminium≈205, Steel≈50–60 W/m·K"
)
st.sidebar.markdown(f"<span class='input-badge'>Current: {tc} W/m·K</span>", unsafe_allow_html=True)

bs = st.sidebar.number_input(
    "Block Size (mm)",
    min_value=int(LIMITS["BlockSize"][0]), max_value=int(LIMITS["BlockSize"][1]), value=10, step=1,
    help="Block thickness in millimetres (mm)"
)
st.sidebar.markdown(f"<span class='input-badge'>Current: {bs} mm</span>", unsafe_allow_html=True)

st.sidebar.write("---")
st.sidebar.subheader("Temperatures")
stemp = st.sidebar.slider(
    "Source Temperature (°C)", LIMITS["SourceTemp"][0], LIMITS["SourceTemp"][1], 60,
    help="Heat source temperature"
)
st.sidebar.markdown(f"<span class='input-badge'>Current: {stemp} °C</span>", unsafe_allow_html=True)

atemp = st.sidebar.slider(
    "Ambient Temperature (°C)", LIMITS["AmbientTemp"][0], LIMITS["AmbientTemp"][1], 25,
    help="Surrounding air temperature"
)
st.sidebar.markdown(f"<span class='input-badge'>Current: {atemp} °C</span>", unsafe_allow_html=True)

with st.sidebar:
    st.write("---")
    run = st.button("Calculate")

# ---------- Validation ----------
values = {"ThermalCond": tc, "BlockSize": bs, "SourceTemp": stemp, "AmbientTemp": atemp}
issues = check_limits(values)

if issues:
    st.markdown('<span class="badge-err">Out of range</span> Please fix the following:', unsafe_allow_html=True)
    for msg in issues:
        st.error(msg)

# ---------- Show current inputs ----------
box1, box2, box3, box4 = st.columns(4)
with box1:
    st.markdown(f"<div class='metric-card'><h2>Thermal Cond. (W/m·K)</h2><p>{tc}</p></div>", unsafe_allow_html=True)
with box2:
    st.markdown(f"<div class='metric-card'><h2>Block Size (mm)</h2><p>{bs}</p></div>", unsafe_allow_html=True)
with box3:
    st.markdown(f"<div class='metric-card'><h2>Source Temp (°C)</h2><p>{stemp}</p></div>", unsafe_allow_html=True)
with box4:
    st.markdown(f"<div class='metric-card'><h2>Ambient Temp (°C)</h2><p>{atemp}</p></div>", unsafe_allow_html=True)

# ---------- Results ----------
if run and not issues:
    avg_t, max_t, ctr_t = nearest_row_predict(tc, bs, stemp, atemp)
    eff = efficiency(max_t, avg_t, atemp)
    cool = coolant_suggestion(avg_t)
    mat = material_suggestion(tc)

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><h2>Avg Temp (°C)</h2><p>{avg_t:.2f}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h2>Max Temp (°C)</h2><p>{max_t:.2f}</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h2>Center Temp (°C)</h2><p>{ctr_t:.2f}</p></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-card'><h2>Efficiency</h2><p>{eff:.2%}</p></div>", unsafe_allow_html=True)

    st.write("")
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Coolant Suggestion")
        st.success(f"💧 {cool}")
    with colB:
        st.subheader("Material Suggestion")
        st.info(f"🛠 {mat}")

    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=eff*100,
        title={'text': "Efficiency (%)"},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "#22c55e"},
               'steps': [
                   {'range': [0, 50], 'color': "#fecaca"},
                   {'range': [50, 80], 'color': "#fef08a"},
                   {'range': [80, 100], 'color': "#bbf7d0"}
               ]}
    ))
    st.plotly_chart(gauge_fig, use_container_width=True)

    with st.expander("See nearest dataset match"):
        nn = df.loc[((df["ThermalCond"]-tc)**2 + (df["BlockSize"]-bs)**2 + (df["SourceTemp"]-stemp)**2 + (df["AmbientTemp"]-atemp)**2).idxmin()]
        st.dataframe(nn.to_frame().T)
else:
    st.info("Adjust inputs in the sidebar and click **Calculate**.")
