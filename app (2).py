import streamlit as st
import pandas as pd
from streamlit.components.v1 import html

st.set_page_config(page_title="高爾夫Match play-1 vs N", layout="wide")
st.title("高爾夫 Match play - 1 vs N")

def numeric_input_html(label, key):
    value = st.session_state.get(key, "")
    html(f"""
        <label for="{key}" style="font-weight:bold">{label}</label><br>
        <input id="{key}" name="{key}" inputmode="numeric" pattern="[0-9]*" maxlength="9"
               style="width:100%; font-size:1.1em; padding:0.5em;" value="{value}" />
        <script>
        const input = window.parent.document.getElementById('{key}');
        input.addEventListener('input', () => {{
            const value = input.value;
            window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: '{key}', value}}, '*');
            const counter = document.getElementById('{key}_counter');
            if (counter) counter.innerText = value.length + ' / 9';
        }});
        </script>
        <div id="{key}_counter" style="font-size: 0.9em; color: gray; text-align: right;">0 / 9</div>
    """, height=120)

def adjust_scores(main, opp, hcp_value, hcp_main, hcp_opp):
    adj_main, adj_opp = main, opp
    diff = hcp_opp - hcp_main
    if diff > 0 and hcp_value <= diff:
        adj_opp -= 1
    elif diff < 0 and hcp_value <= -diff:
        adj_main -= 1
    return adj_main, adj_opp

course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players.csv")

course_name = st.selectbox("選擇球場", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("前九洞區域", zones)
zone_back = st.selectbox("後九洞區域", zones)

holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

st.markdown("### 參賽球員設定")
player_list = players_df["name"].tolist()
selected_players = st.multiselect("選擇參賽球員（至少兩位）", player_list)

if st.button("生成快速輸入與差點設定"):
    if len(selected_players) < 2:
        st.warning("⚠️ 至少需要兩位球員才能進行比賽。")
    else:
        # ✅ 如果未初始化過，進行初始化
        if 'players' not in st.session_state:
            st.session_state['players'] = selected_players
            st.session_state['init_done'] = True

        # ✅ 避免重複刷新：使用 session_state 判斷
        if st.session_state.get('init_done', False):
            st.session_state['init_done'] = False
            st.write("設定完成，請繼續下方設定。")
            
if 'players' in st.session_state:
    st.markdown("### 快速輸入與差點設定")
    for player in st.session_state['players']:
        st.subheader(f"{player}")
        st.markdown("**前九洞成績**")
        numeric_input_html(f"{player} 前9洞成績輸入（9位數）", key=f"quick_front_{player}")
        st.markdown("**後九洞成績**")
        numeric_input_html(f"{player} 後9洞成績輸入（9位數）", key=f"quick_back_{player}")
        st.number_input(f"{player} 差點", 0, 54, 0, key=f"hcp_{player}")
        st.number_input(f"{player} 每洞賭金", 10, 1000, 100, key=f"bet_{player}")

if st.button("生成對戰比分表"):
    if 'players' not in st.session_state:
        st.warning("⚠️ 尚未完成選手設定。")
    else:
        # 讀取快速成績
        quick_scores = {}
        for p in st.session_state['players']:
            front = st.session_state.get(f"quick_front_{p}", "")
            back = st.session_state.get(f"quick_back_{p}", "")
            full = front + back
            if full and len(full) == 18 and full.isdigit():
                quick_scores[p] = [int(c) for c in full]

        st.markdown("### 對戰比分表")
        for i in range(18):
            st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
            cols = st.columns(len(st.session_state['players']))
            for idx, player in enumerate(st.session_state['players']):
                default_score = quick_scores[player][i] if player in quick_scores and len(quick_scores[player]) == 18 else par[i]
                cols[idx].number_input(f"{player} 成績", 1, 15, default_score, key=f"score_{player}_{i}", label_visibility="collapsed")
