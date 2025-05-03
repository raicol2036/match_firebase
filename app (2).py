import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏌️ Golf Match - Manual Input", layout="wide")
st.title("🏌️ 高爾夫一對多比分系統（手動輸入版）")

# ========== 1. 資料來源選擇 ==========
st.header("1️⃣ 選擇資料來源")
data_source = st.radio("選擇資料來源", ["手動輸入"], index=0)

# ========== 2. 從 CSV 載入球員名單 ==========
@st.cache_data
def load_players():
    return pd.read_csv("players.csv")

df_players = load_players()
player_names = df_players["name"].dropna().tolist()

# ========== 3. 選擇球員與設定差點賭金 ==========
st.header("2️⃣ 選擇球員與設定差點、賭金")

selected_players = st.multiselect("選擇參賽球員（至少兩位）", player_names)

if len(selected_players) >= 2:
    st.subheader("🎯 設定每位球員的差點與賭金")
    player_info = {}
    for p in selected_players:
        col1, col2 = st.columns(2)
        with col1:
            handicap = st.number_input(f"{p} 的差點", min_value=0, max_value=36, step=1, key=f"{p}_hcp")
        with col2:
            bet = st.number_input(f"{p} 的賭金", min_value=0, step=100, key=f"{p}_bet")
        player_info[p] = {"hcp": handicap, "bet": bet}
else:
    st.warning("請至少選擇兩位球員")

# ========== 4. 快速輸入 18 洞桿數 ==========
if len(selected_players) >= 2:
    st.header("3️⃣ 快速輸入 18 洞桿數")
    scores = {}
    for p in selected_players:
        raw_input = st.text_input(f"{p} 的18洞桿數（請輸入18個數字，例如 455344...）", max_chars=18, key=f"{p}_score")
        if len(raw_input) == 18 and raw_input.isdigit():
            scores[p] = [int(c) for c in raw_input]
        else:
            scores[p] = []

# ========== 5. 選擇主要選手 ==========
    st.header("4️⃣ 選擇主要選手")
    main_player = st.selectbox("指定主要選手", selected_players)

    if st.button("✅ 產生比分結果"):
        if all(len(s) == 18 for s in scores.values()):
            st.success("比賽結果如下：")
            for opponent in selected_players:
                if opponent == main_player:
                    continue
                main_score = scores[main_player]
                opp_score = scores[opponent]
                main_wins = sum([1 for m, o in zip(main_score, opp_score) if m < o])
                opp_wins = sum([1 for m, o in zip(main_score, opp_score) if m > o])
                ties = 18 - main_wins - opp_wins

                st.markdown(f"""
                ### 📊 {main_player} vs {opponent}
                - 🏆 {main_player} 勝洞數: {main_wins}
                - 🏆 {opponent} 勝洞數: {opp_wins}
                - ⚖️ 平手洞數: {ties}
                """)
        else:
            st.error("請確認每位球員皆輸入完整 18 洞桿數")
