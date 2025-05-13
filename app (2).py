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
if 'quick_scores' not in st.session_state:
    st.session_state['quick_scores'] = {}

# 生成設定
if st.button("生成快速輸入與差點設定"):
    if len(selected_players) < 2:
        st.warning("⚠️ 至少需要兩位球員才能進行比賽。")
    else:
        st.session_state['players'] = selected_players
        st.session_state['quick_scores'] = {p: "" for p in selected_players}
        st.success("初始化完成！")

# 顯示快速輸入
if st.session_state['players']:
    st.markdown("### 快速成績輸入 (18碼)")
    for player in st.session_state['players']:
        st.subheader(f"{player} - 成績輸入")
        # 顯示輸入框，限制最大長度為 18
        input_value = st.text_input(f"{player} 18 碼成績（18位數）", 
                                    value=st.session_state['quick_scores'][player], 
                                    max_chars=18, key=f"quick_input_{player}")
        
        # 顯示目前輸入的長度
        st.markdown(f"📝 已輸入長度: **{len(input_value)} / 18**")
        
        # 更新 Session State
        st.session_state['quick_scores'][player] = input_value

# 對戰比分計算
if st.button("同步更新所有比分"):
    all_valid = True
    for player, score_str in st.session_state['quick_scores'].items():
        if len(score_str) != 18 or not score_str.isdigit():
            st.error(f"⚠️ {player} 的成績輸入無效，必須是 18 位數字！")
            all_valid = False
    
    if all_valid:
        st.success("所有成績已同步更新！")
        # 解析成績並儲存
        for player, score_str in st.session_state['quick_scores'].items():
            st.session_state[f"score_{player}"] = [int(c) for c in score_str]
