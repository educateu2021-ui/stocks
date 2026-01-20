import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import pytesseract
import cv2
from PIL import Image
import os

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="Options Intelligence V5")

LOT_SIZE = {
    "NIFTY": 65,
    "SENSEX": 20
}

THEME_COLORS = [
    "#134E4A", "#0F766E", "#14B8A6",
    "#FACC15", "#F59E0B", "#DC2626"
]

# ---------------- LOGIN ----------------
USERS = {
    "trader": {"pwd": "trade123", "role": "trader"},
    "admin": {"pwd": "admin123", "role": "admin"}
}

def authenticate(u, p):
    return USERS.get(u, {}).get("role") if USERS.get(u, {}).get("pwd") == p else None

st.sidebar.title("🔐 Login")
user = st.sidebar.text_input("User")
pwd = st.sidebar.text_input("Password", type="password")
role = authenticate(user, pwd)

if not role:
    st.stop()

# ---------------- INPUTS ----------------
st.sidebar.title("⚙️ Controls")
index = st.sidebar.selectbox("Index", ["NIFTY", "SENSEX"])
capital = st.sidebar.number_input("Capital ₹", min_value=5000, value=20000, step=1000)
expected_profit = st.sidebar.slider("Expected Profit ₹", 2, 5, 3)

lot_size = LOT_SIZE[index]

# ---------------- DATA INPUT ----------------
st.title("📊 Options Intelligence Dashboard")

tab1, tab2, tab3 = st.tabs(["📥 Upload CSV", "🖼️ Upload Greek Image", "✍️ Manual Entry"])

df = None

with tab1:
    file = st.file_uploader("Upload Option Chain CSV", type="csv")
    if file:
        df = pd.read_csv(file)

with tab2:
    img = st.file_uploader("Upload Greek Screenshot", type=["png", "jpg"])
    if img:
        image = Image.open(img)
        text = pytesseract.image_to_string(image)
        rows = []
        for line in text.split("\n"):
            parts = line.split()
            if len(parts) >= 6:
                rows.append(parts[:6])
        df = pd.DataFrame(rows, columns=["Strike","CE_LTP","CE_OI","CE_Gamma","PE_LTP","PE_OI"])

with tab3:
    df = st.data_editor(
        pd.DataFrame(columns=[
            "Strike","CE_LTP","CE_OI","CE_Gamma",
            "PE_LTP","PE_OI","PE_Gamma"
        ]),
        num_rows="dynamic"
    )

if df is None or df.empty:
    st.stop()

# ---------------- CLEAN DATA ----------------
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df.dropna(inplace=True)

# ---------------- CORE LOGIC ----------------

# Max Pain
df["Pain"] = abs(df["Strike"] - df["Strike"].median()) * (df["CE_OI"] + df["PE_OI"])
max_pain = df.loc[df["Pain"].idxmin(), "Strike"]

# Gamma Pressure
df["GammaPressure"] = abs(df["PE_Gamma"]) * df["PE_OI"] * lot_size

# Best Scalp Strike
df["CapitalNeeded"] = df["PE_LTP"] * lot_size
df_valid = df[df["CapitalNeeded"] <= capital]

best = df_valid.sort_values(
    by=["GammaPressure","PE_LTP"],
    ascending=[False, True]
).iloc[0]

lots = int(capital // best["CapitalNeeded"])

# ---------------- OUTPUT ----------------
col1, col2, col3 = st.columns(3)

col1.metric("📌 Max Pain", int(max_pain))
col2.metric("🎯 Selected Strike", int(best["Strike"]))
col3.metric("📦 Lots", lots)

st.success(
    f"BUY {index} {int(best['Strike'])} PUT | "
    f"LTP {best['PE_LTP']} | "
    f"Target ₹{expected_profit}"
)

# ---------------- GAMMA HEATMAP ----------------
fig = px.bar(
    df,
    x="Strike",
    y="GammaPressure",
    color="GammaPressure",
    color_continuous_scale=THEME_COLORS
)
st.plotly_chart(fig, use_container_width=True)

# ---------------- LAST 30 MIN ALARM ----------------
now = datetime.now().strftime("%H:%M")
if now >= "14:30":
    if abs(best["Strike"] - max_pain) / max_pain < 0.002:
        st.warning("🔔 LAST 30-MINUTE GAMMA RELEASE ZONE")

# ---------------- JOURNAL ----------------
if st.button("🧾 Save Trade"):
    log = {
        "Time": datetime.now(),
        "Index": index,
        "Strike": best["Strike"],
        "Lots": lots,
        "Entry": best["PE_LTP"],
        "Reason": "Gamma + MaxPain"
    }
    pd.DataFrame([log]).to_csv(
        "trade_journal.csv",
        mode="a",
        header=not os.path.exists("trade_journal.csv"),
        index=False
    )
    st.success("Trade logged")

# ---------------- FOOTER ----------------
st.caption("⚠️ Tool shows probability zones, not predictions. Risk is yours.")
