import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Options Intelligence v3",
    layout="wide"
)

# =====================================================
# TAILWIND + ANIMATIONS
# =====================================================
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">

<style>
body {
    background: linear-gradient(135deg, #0F766E, #134E4A);
    color: #ECFEFF;
}

.glass {
    background: rgba(15, 118, 110, 0.35);
    backdrop-filter: blur(14px);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 0 25px rgba(20,184,166,0.25);
}

.fade-in {
    animation: fadeIn 0.8s ease-in-out;
}

.slide-up {
    animation: slideUp 0.8s ease-out;
}

@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}

@keyframes slideUp {
    from {transform: translateY(20px); opacity:0;}
    to {transform: translateY(0); opacity:1;}
}

.glow-btn button {
    background: linear-gradient(90deg, #14B8A6, #99F6E4);
    color: #042F2E;
    font-weight: 700;
    border-radius: 12px;
    padding: 10px 18px;
    box-shadow: 0 0 20px rgba(20,184,166,0.6);
}

.glow-btn button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# CONSTANTS
# =====================================================
LOT_SIZE = {"NIFTY": 65, "SENSEX": 20}

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="text-center fade-in">
<h1 class="text-4xl font-bold text-teal-200">Options Intelligence Engine</h1>
<p class="text-yellow-200">Scalp • Gamma • Max Pain • Expiry Control</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.markdown("## ⚙️ Trade Inputs")

index = st.sidebar.selectbox("Index", ["NIFTY", "SENSEX"])
capital = st.sidebar.number_input("Capital (₹)", value=20000, step=1000)
target = st.sidebar.number_input("Target Profit (₹)", value=1000, step=500)
mode = st.sidebar.radio("Mode", ["Scalp", "Market Direction"])

lot_size = LOT_SIZE[index]

st.sidebar.info(f"Lot Size: {lot_size}")

# =====================================================
# KPI PLACEHOLDERS
# =====================================================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown("<div class='glass slide-up'>Market Control<br><b>Sellers</b></div>", unsafe_allow_html=True)

with kpi2:
    st.markdown("<div class='glass slide-up'>Gamma State<br><b>Active</b></div>", unsafe_allow_html=True)

with kpi3:
    st.markdown("<div class='glass slide-up'>Max Pain Bias<br><b>Downside</b></div>", unsafe_allow_html=True)

with kpi4:
    st.markdown("<div class='glass slide-up'>Expiry Risk<br><b>High</b></div>", unsafe_allow_html=True)

# =====================================================
# DATA INPUT
# =====================================================
st.markdown("## 📊 Greek Matrix")
df = st.data_editor(
    pd.DataFrame(columns=[
        "Strike",
        "CE_LTP","CE_Delta","CE_Gamma","CE_Theta","CE_OI",
        "PE_LTP","PE_Delta","PE_Gamma","PE_Theta","PE_OI"
    ]),
    use_container_width=True,
    num_rows="dynamic"
)

# =====================================================
# ENGINE
# =====================================================
def scalp_engine(df):
    ideas = []
    for _, r in df.iterrows():
        try:
            cost = r.PE_LTP * lot_size
            lots = int(capital // cost)
            if lots < 1:
                continue
            move = target / (lots * lot_size)
            if 2 <= move <= 5 and -0.65 <= r.PE_Delta <= -0.30:
                score = abs(r.PE_Delta)*30 + r.PE_Gamma*100000 - abs(r.PE_Theta)*0.4
                ideas.append((score, r.Strike, lots, round(move,2)))
        except:
            continue
    return sorted(ideas, reverse=True)

# =====================================================
# RUN
# =====================================================
st.markdown("<div class='glow-btn'>", unsafe_allow_html=True)
run = st.button("🚀 Run Intelligence Engine")
st.markdown("</div>", unsafe_allow_html=True)

if run:
    ideas = scalp_engine(df)

    if not ideas:
        st.error("❌ ZERO TRADE — Risk not acceptable")
    else:
        best = ideas[0]
        st.success("🔥 HERO SCALP FOUND")

        st.markdown(f"""
        <div class="glass slide-up text-xl">
        <b>BUY PUT</b><br>
        Strike: <b>{best[1]}</b><br>
        Lots: <b>{best[2]}</b><br>
        Required Move: <b>{best[3]} ₹</b><br>
        Confidence: <b>HIGH</b>
        </div>
        """, unsafe_allow_html=True)
