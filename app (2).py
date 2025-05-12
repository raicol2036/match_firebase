import streamlit as st
import pandas as pd

st.set_page_config(page_title="高爾夫 Match play - 1 vs N", layout="wide")
st.title("高爾夫 Match play - 1 vs N")

# 讀取資料
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players.csv")

# 選擇球場與區域
course_name = st.selectbox("選擇球場", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("前九洞區域", zones)
zone_back = st.selectbox("後九洞區域", zones)

# 整理球場資料
holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

# 選擇參賽球員
st.markdown("### 參賽球員設定")
player_list = players_df["name"].tolist()
selected_players = st.multiselect("選擇參賽球員（至少兩位）", player_list)

# 初始化 Session State
if 'players' not in st.session_state:
    st.session_state['players'] = []
if 'score_tracker' not in st.session_state:
    st.session_state['score_tracker'] = {}

# 生成設定
if st.button("生成快速輸入與差點設定"):
    if len(selected_players) < 2:
        st.warning("⚠️ 至少需要兩位球員才能進行比賽。")
    else:
        st.session_state['players'] = selected_players
        st.session_state['score_tracker'] = {
            f"score_{p}_{i}": par[i] for p in selected_players for i in range(18)
        }
        st.success("初始化完成！")

# 顯示快速輸入
if st.session_state['players']:
    st.markdown("### 快速成績輸入")
    for player in st.session_state['players']:
        st.subheader(f"{player} - 成績輸入")
        for i in range(18):
            st.number_input(f"{player} - 第 {i+1} 洞", min_value=1, max_value=15, 
                            value=st.session_state['score_tracker'][f"score_{player}_{i}"], 
                            key=f"score_{player}_{i}")

# 對戰比分計算
if st.button("同步更新所有比分"):
    for key in st.session_state['score_tracker']:
        st.session_state['score_tracker'][key] = st.session_state.get(key, par[0])
    st.success("所有比分已同步更新")

