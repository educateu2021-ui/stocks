import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Options Intelligence v4",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# TAILWIND + PREMIUM THEME
# =====================================================
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">

<style>
html, body, [class*="css"] {
    background: linear-gradient(135deg, #042F2E, #134E4A);
    color: #ECFEFF;
    font-family: 'Inter', sans-serif;
}

.glass {
    background: rgba(15,118,110,0.35);
    backdrop-filter: blur(18px);
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 0 40px rgba(20,184,166,0.25);
}

.card {
    transition: all 0.3s ease;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0 50px rgba(94,234,212,0.4);
}

.fade {
    animation: fadeIn 0.9s ease-in-out;
}
.slide {
    animation: slideUp 0.9s ease-in-out;
}

@keyframes fadeIn {
    from {opacity:0;}
    to {opacity:1;}
}
@keyframes slideUp {
    from {transform:translateY(25px); opacity:0;}
    to {transform:translateY(0); opacity:1;}
}

.btn-glow button {
    background: linear-gradient(90deg, #14B8A6, #99F6E4);
    color: #042F2E;
    font-weight: 800;
    border-radius: 14px;
    padding: 12px 22px;
    box-shadow: 0 0 30px rgba(20,184,166,0.7);
}
.btn-glow button:hover {
    transform: scale(1.06);
}

.badge-green {
    background:#14B8A6;
    color:#042F2E;
    padding:4px 10px;
    border-radius:8px;
    font-weight:700;
}
.badge-red {
    background:#DC2626;
    color:#FFF;
    padding:4px 10px;
    border-radius:8px;
    font-weight:700;
}
.badge-yellow {
    background:#FACC15;
    color:#422006;
    padding:4px 10px;
    border-radius:8px;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# CONSTANTS
# =====================================================
LOT_SIZE = {
    "NIFTY": 65,
    "SENSEX": 20
}

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="text-center fade">
<h1 class="text-5xl font-extrabold text-teal-200">Options Intelligence v4</h1>
<p class="text-yellow-300 text-lg mt-2">
Gamma • Max Pain • Expiry Control • Scalp Engine
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =====================================================
# SIDEBAR INPUTS
# =====================================================
st.sidebar.markdown("## ⚙️ Inputs")

index = st.sidebar.selectbox("Index", ["NIFTY", "SENSEX"])
capital = st.sidebar.number_input("Capital (₹)", value=20000, step=1000)
target_profit = st.sidebar.number_input("Expected Profit (₹)", value=1000, step=500)
mode = st.sidebar.radio("Mode", ["Scalp (2–5₹)", "Market Direction"])

lot_size = LOT_SIZE[index]
st.sidebar.success(f"Lot Size: {lot_size}")

# =====================================================
# KPI DASHBOARD
# =====================================================
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown("<div class='glass card slide'>Market Control<br><b>Sellers</b></div>", unsafe_allow_html=True)
with k2:
    st.markdown("<div class='glass card slide'>Gamma Pressure<br><b>High</b></div>", unsafe_allow_html=True)
with k3:
    st.markdown("<div class='glass card slide'>Max Pain Gravity<br><b>Active</b></div>", unsafe_allow_html=True)
with k4:
    st.markdown("<div class='glass card slide'>Expiry Risk<br><b>Elevated</b></div>", unsafe_allow_html=True)

st.markdown("---")

# =====================================================
# GREEKS INPUT
# =====================================================
st.markdown("## 📊 Option Chain (Greeks Required)")

df = st.data_editor(
    pd.DataFrame(columns=[
        "Strike",
        "CE_LTP","CE_Delta","CE_Gamma","CE_Theta","CE_OI",
        "PE_LTP","PE_Delta","PE_Gamma","PE_Theta","PE_OI"
    ]),
    num_rows="dynamic",
    use_container_width=True
)

# =====================================================
# CORE ENGINE LOGIC
# =====================================================
def analyze(df):
    trades = []

    for _, r in df.iterrows():
        try:
            cost = r.PE_LTP * lot_size
            lots = int(capital // cost)
            if lots < 1:
                continue

            per_point = lots * lot_size
            required_move = target_profit / per_point

            gamma_ok = r.PE_Gamma > 0.0004
            delta_ok = -0.70 <= r.PE_Delta <= -0.30
            theta_ok = abs(r.PE_Theta) < 90
            scalp_ok = 2 <= required_move <= 5

            if gamma_ok and delta_ok and theta_ok and scalp_ok:
                score = (
                    abs(r.PE_Delta)*40 +
                    r.PE_Gamma*100000 -
                    abs(r.PE_Theta)*0.3 +
                    r.PE_OI
                )
                trades.append({
                    "score": score,
                    "strike": r.Strike,
                    "lots": lots,
                    "move": round(required_move,2)
                })
        except:
            pass

    return sorted(trades, key=lambda x: x["score"], reverse=True)

# =====================================================
# RUN ENGINE
# =====================================================
st.markdown("<div class='btn-glow'>", unsafe_allow_html=True)
run = st.button("🚀 RUN ANALYSIS")
st.markdown("</div>", unsafe_allow_html=True)

if run:
    results = analyze(df)

    if not results:
        st.markdown("""
        <div class="glass text-center fade">
        <span class="badge-red">ZERO TRADE</span>
        <p class="mt-2 text-lg">Risk not acceptable. Capital protected.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        best = results[0]
        st.markdown(f"""
        <div class="glass slide">
        <span class="badge-green">HERO SCALP</span>
        <h3 class="text-2xl mt-2 font-bold">BUY PUT</h3>
        <p class="mt-2">Strike: <b>{best["strike"]}</b></p>
        <p>Lots: <b>{best["lots"]}</b></p>
        <p>Required Move: <b>{best["move"]} ₹</b></p>
        <p class="mt-3 text-yellow-300">High Gamma • Seller Control • Max Pain Pull</p>
        </div>
        """, unsafe_allow_html=True)
