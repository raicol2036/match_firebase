import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# 初始化 Firebase（只做一次）
if "firebase_initialized" not in st.session_state:
    cred = credentials.Certificate(st.secrets["firebase"])
    firebase_admin.initialize_app(cred)
    st.session_state["firebase_initialized"] = True

db = firestore.client()

st.title("🏌️ 即時高爾夫比分系統")

# ========== 選擇資料來源 ==========
source_option = st.radio("📁 選擇球員來源", ["從 JSON 取得", "從 players.csv 取得"])
score_option = st.radio("⛳ 比賽桿數來源", ["從 Firebase JSON 取得", "手動快速輸入"])

# ========== 取得球員名單 ==========
players = []

if source_option == "從 JSON 取得":
    game_id = st.text_input("輸入比賽 Game ID（Firebase）")
    if game_id:
        doc = db.collection("golf_games").document(game_id).get()
        if doc.exists:
            data = doc.to_dict()
            players = data.get("players", [])
else:
    try:
        df = pd.read_csv("players.csv")
        players = df["name"].dropna().tolist()
    except:
        st.error("⚠️ 找不到 players.csv")

# ========== 輸入差點與賭金 ==========
handicaps = {}
bets = {}

if players:
    st.subheader("👥 輸入球員差點與賭金")
    for p in players:
        col1, col2 = st.columns(2)
        with col1:
            handicaps[p] = st.number_input(f"{p} 差點", value=0, step=1)
        with col2:
            bets[p] = st.number_input(f"{p} 賭金", value=100, step=10)

# ========== 選擇主要球員 ==========
if players:
    main_player = st.selectbox("🎯 選擇主要比較球員", players)

# ========== 取得桿數 ==========
scores = {}
if players:
    st.subheader("📊 輸入或讀取球員桿數")
    if score_option == "從 Firebase JSON 取得" and game_id:
        scores = data.get("scores", {})
    else:
        for p in players:
            scores[p] = st.number_input(f"{p} 的桿數", min_value=1, max_value=10, key=f"score_{p}")

# ========== 判定勝負 ==========
if players and scores:
    st.subheader("🏆 勝負資訊")
    main_score = scores.get(main_player)
    if main_score is not None:
        result = []
        for p in players:
            if p == main_player:
                continue
            diff = scores[p] - main_score
            outcome = "勝" if diff > 0 else "負" if diff < 0 else "平手"
            result.append(f"{main_player} 對 {p} ➜ {outcome}（差 {abs(diff)} 桿）")
        st.markdown("\n".join(result))

# ========== 勝者統計表 ==========
if players and scores:
    st.subheader("📈 排名資訊")
    df_score = pd.DataFrame({
        "球員": players,
        "桿數": [scores[p] for p in players],
        "差點": [handicaps[p] for p in players],
        "賭金": [bets[p] for p in players]
    }).sort_values("桿數")
    st.table(df_score)
