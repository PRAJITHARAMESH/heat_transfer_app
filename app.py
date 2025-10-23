# FORCING A CLEAN BUILD TO INSTALL MISSING DEPENDENCIES 
# app.py - Heat Transfer Analysis with clear inputs & styled UI
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import plotly.graph_objects as go
import requests 
from streamlit_autorefresh import st_autorefresh 

# ---------- Page Setup ----------
st.set_page_config(page_title="Heat Transfer Analysis", layout="wide")

# --- ADDED AUTO-REFRESH COMPONENT ---
# Forces the entire script to rerun every 20,000 milliseconds (20 seconds) 
# to fetch new data from ThingSpeak.
st_autorefresh(interval=20000, key="data_refresh_timer")
# ------------------------------------

# ---------- CSS (No Change) ----------
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

# ---------- Load Data (No Change) ----------
DATA_PATH = Path(__file__).parent / "heat_transfer_dataset.csv"
df = pd.read_csv(DATA_PATH)

# ---------- Limits (CLEANED) ----------
LIMITS = {
    "ThermalCond": (50, 500),
    "BlockSize": (5, 50),
    "SourceTemp": (30, 150),
    "AmbientTemp": (0, 50),
}

# ---------------------------------------------------
# !!! FINAL CONFIGURATION (Channel ID Integrated) !!!
# ---------------------------------------------------
THINGSPEAK_CHANNEL_ID = "3111348" 
THINGSPEAK_READ_API_KEY = "8XPUACRYN84UOGJ9" 
# ---------------------------------------------------

# ---------- NEW Function to Fetch BOTH Live Data Points ----------
def fetch_live_data():
    """Fetches the latest entry for ALL fields (Field 1: Ambient, Field 2: Source)."""
    # Use the /feeds/last.json URL to get all fields at once
    url = (
        f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json?"
        f"api_key={THINGSPEAK_READ_API_KEY}"
    )
    
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status() # Raise exception for bad status codes
        data = response.json()
        
        # Check if the required fields exist and are not None
        t_ambient = data.get('field1') # Field 1 from ESP32 code is Ambient Temp
        t_source = data.get('field2')  # Field 2 from ESP32 code is Source Temp

        if t_ambient and t_source:
            # Return both values as floats
            return float(t_ambient), float(t_source)
        else:
            st.warning("ThingSpeak Warning: Live data not available for Ambient (Field 1) and Source (Field 2). Using default sliders.")
            return None, None
            
    except requests.exceptions.RequestException as e:
        st.error(f"ThingSpeak API Error: Could not fetch live data. Check keys/Channel ID/internet. Error: {e}")
        return None, None
    except Exception as e:
        st.error(f"Data Processing Error: {e}")
        return None, None


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

# ---------- Header (No Change) ----------
st.markdown("<h1 style='text-align:center;'>🔥 Heat Transfer Analysis</h1>", unsafe_allow_html=True)
st.caption("Enter inputs clearly with units. Predicts Avg/Max/Center Temperatures, Efficiency, Coolant & Material suggestions.")

# ---------- Sidebar Inputs (Modified for IOT) ----------
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

# --- 1. Fetch Live Data Once ---
live_ambient, live_source = fetch_live_data()


# --- 2. Ambient Temperature (T_cold) Input ---
atemp_min, atemp_max = LIMITS["AmbientTemp"]

if live_ambient is not None:
    st.sidebar.markdown("**Ambient Temp (°C) - 📡 Field 1 (Live)**", unsafe_allow_html=True)
    st.sidebar.metric(label="Live Ambient Temp", value=f"{live_ambient:.2f} °C")
    # Cap the live value to stay within the model's limits
    atemp = max(atemp_min, min(atemp_max, live_ambient))
    st.sidebar.caption("Value automatically used for calculation.")
else:
    # Fallback slider
    default_atemp = 25
    atemp = st.sidebar.slider(
        "Ambient Temperature (°C)", atemp_min, atemp_max, default_atemp, step=0.1, key='ambient_slider'
    )
    st.sidebar.markdown(f"<span class='input-badge'>Current: {atemp} °C (Manual)</span>", unsafe_allow_html=True)


st.sidebar.write("---")

# --- 3. Source Temperature (T_hot) Input ---
stemp_min, stemp_max = LIMITS["SourceTemp"]

if live_source is not None:
    st.sidebar.markdown("**Source Temp (°C) - 📡 Field 2 (Live)**", unsafe_allow_html=True)
    st.sidebar.metric(label="Live Source Temp", value=f"{live_source:.2f} °C")
    # Cap the live value to stay within the model's limits
    stemp = max(stemp_min, min(stemp_max, live_source))
    st.sidebar.caption("Value automatically used for calculation.")
else:
    # Fallback slider
    default_stemp = 60
    stemp = st.sidebar.slider(
        "Source Temperature (°C)", stemp_min, stemp_max, default_stemp, step=1, key='source_slider'
    )
    st.sidebar.markdown(f"<span class='input-badge'>Current: {stemp} °C (Manual)</span>", unsafe_allow_html=True)


with st.sidebar:
    st.write("---")
    run = st.button("Calculate")

# ---------- Validation (No Change) ----------
values = {"ThermalCond": tc, "BlockSize": bs, "SourceTemp": stemp, "AmbientTemp": atemp}
issues = check_limits(values)

if issues:
    st.markdown('<span class="badge-err">Out of range</span> Please fix the following:', unsafe_allow_html=True)
    for msg in issues:
        st.error(msg)

# ---------- Show current inputs (No Change) ----------
box1, box2, box3, box4 = st.columns(4)
with box1:
    st.markdown(f"<div class='metric-card'><h2>Thermal Cond. (W/m·K)</h2><p>{tc}</p></div>", unsafe_allow_html=True)
with box2:
    st.markdown(f"<div class='metric-card'><h2>Block Size (mm)</h2><p>{bs}</p></div>", unsafe_allow_html=True)
with box3:
    st.markdown(f"<div class='metric-card'><h2>Source Temp (°C)</h2><p>{stemp}</p></div>", unsafe_allow_html=True)
with box4:
    st.markdown(f"<div class='metric-card'><h2>Ambient Temp (°C)</h2><p>{atemp}</p></div>", unsafe_allow_html=True)

# ---------- Results (No Change) ----------
if run and not issues:
    # The prediction now uses the live 'stemp' and 'atemp' values
    avg_t, max_t, ctr_t = nearest_row_predict(tc, bs, stemp, atemp)
    eff = efficiency(max_t, avg_t, atemp)
    cool = coolant_suggestion(avg_temp)
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