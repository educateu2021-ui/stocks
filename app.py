import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict

# ===============================
# APP CONFIG
# ===============================
st.set_page_config(
    page_title="Options Scalp Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# THEME OVERRIDE (PALETTE)
# ===============================
st.markdown("""
<style>
body {
    background-color: #0F766E;
}
[data-testid="stSidebar"] {
    background-color: #134E4A;
}
h1, h2, h3, h4 {
    color: #99F6E4;
}
.stButton>button {
    background-color: #14B8A6;
    color: black;
    border-radius: 8px;
    font-weight: 600;
}
.stAlert {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# CONSTANTS (IMMUTABLE)
# ===============================
LOT_SIZE = {
    "NIFTY": 65,
    "SENSEX": 20
}

DELTA_CALL = (0.30, 0.60)
DELTA_PUT = (-0.60, -0.30)
LTP_RANGE = (40.0, 350.0)
REQUIRED_MOVE_RANGE = (2.0, 5.0)

# ===============================
# PURE VALIDATION FUNCTIONS
# ===============================
def validate_numeric(value: float) -> bool:
    return isinstance(value, (int, float)) and not np.isnan(value)

def safe_floor_div(a: float, b: float) -> int:
    if b <= 0:
        return 0
    return int(a // b)

# ===============================
# CORE SCALP LOGIC (PURE FUNCTION)
# ===============================
def evaluate_strikes(
    df: pd.DataFrame,
    capital: float,
    target_profit: float,
    lot_size: int
) -> List[Dict]:

    results = []

    for _, r in df.iterrows():

        # Validate row
        if not all(validate_numeric(r[c]) for c in df.columns if c != "Strike"):
            continue

        # ---- CALL ----
        if (
            LTP_RANGE[0] <= r.CE_LTP <= LTP_RANGE[1]
            and DELTA_CALL[0] <= r.CE_Delta <= DELTA_CALL[1]
        ):
            cost = r.CE_LTP * lot_size
            lots = safe_floor_div(capital, cost)
            if lots >= 1:
                req_move = target_profit / (lots * lot_size)
                if REQUIRED_MOVE_RANGE[0] <= req_move <= REQUIRED_MOVE_RANGE[1]:
                    score = (
                        r.CE_Delta * 30
                        + r.CE_Gamma * 100000
                        - abs(r.CE_Theta) * 0.4
                        + r.CE_OI * 2
                    )
                    results.append({
                        "Side": "CALL",
                        "Strike": r.Strike,
                        "LTP": r.CE_LTP,
                        "Lots": lots,
                        "RequiredMove": round(req_move, 2),
                        "Score": round(score, 2)
                    })

        # ---- PUT ----
        if (
            LTP_RANGE[0] <= r.PE_LTP <= LTP_RANGE[1]
            and DELTA_PUT[0] <= r.PE_Delta <= DELTA_PUT[1]
        ):
            cost = r.PE_LTP * lot_size
            lots = safe_floor_div(capital, cost)
            if lots >= 1:
                req_move = target_profit / (lots * lot_size)
                if REQUIRED_MOVE_RANGE[0] <= req_move <= REQUIRED_MOVE_RANGE[1]:
                    score = (
                        abs(r.PE_Delta) * 30
                        + r.PE_Gamma * 100000
                        - abs(r.PE_Theta) * 0.4
                        + r.PE_OI * 2
                    )
                    results.append({
                        "Side": "PUT",
                        "Strike": r.Strike,
                        "LTP": r.PE_LTP,
                        "Lots": lots,
                        "RequiredMove": round(req_move, 2),
                        "Score": round(score, 2)
                    })

    return results

# ===============================
# UI
# ===============================
st.title("📊 Options Scalp Intelligence Engine")

index = st.sidebar.selectbox("Index", ["NIFTY", "SENSEX"])
capital = st.sidebar.number_input("Capital (₹)", min_value=5000, step=1000, value=20000)
target_profit = st.sidebar.number_input("Expected Profit (₹)", min_value=500, step=500, value=1000)

lot_size = LOT_SIZE[index]
st.sidebar.info(f"Lot Size (auto): {lot_size}")

st.subheader("Greek Input Table (Final Authority)")

df = st.data_editor(
    pd.DataFrame(columns=[
        "Strike",
        "CE_LTP","CE_Delta","CE_Gamma","CE_Theta","CE_OI",
        "PE_LTP","PE_Delta","PE_Gamma","PE_Theta","PE_OI"
    ]),
    num_rows="dynamic",
    use_container_width=True
)

if st.button("Run Scalp Engine"):

    trades = evaluate_strikes(df, capital, target_profit, lot_size)

    if not trades:
        st.error("🚫 NO TRADE — Capital / Greeks / Target mismatch")
    else:
        best = sorted(trades, key=lambda x: (x["Score"], -x["RequiredMove"]), reverse=True)[0]

        st.success("✅ SCALP TRADE IDENTIFIED")

        st.json(best)
