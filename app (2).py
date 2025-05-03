import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏌️ Golf Match - Manual Input", layout="wide")
st.title("🏌️ 高爾夫一對多比分系統（手動輸入）")

# ========== 載入資料 ==========
@st.cache_data
def load_players():
    return pd.read_csv("players.csv")

@st.cache_data
def load_course_db():
    df = pd.read_csv("course_db.csv")
    df["area_name"] = df["course_name"] + " - " + df["area"]
    return df

df_players = load_players()
course_df = load_course_db()
player_names = df_players["name"].dropna().tolist()

# ========== 選擇球員與設定 ==========
st.header("1️⃣ 選擇球員與設定")

selected_players = st.multiselect("選擇參賽球員（至少兩位）", player_names)

if len(selected_players) >= 2:
    st.subheader("🎯 差點與賭金")
    player_info = {}
    for p in selected_players:
        col1, col2 = st.colum
