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

st.markdown("### 球員設定")
player_list = ["請選擇球員"] + players_df["name"].tolist()
player_list_with_done = player_list + ["✅ Done"]

player_a = st.selectbox("選擇主球員 A", player_list)
if player_a == "請選擇球員":
    st.warning("⚠️ 請選擇主球員 A 才能繼續操作。")
    st.stop()

st.subheader("主球員快速成績輸入")

st.markdown("**前九洞成績**")
numeric_input_html("主球員前9洞成績輸入（9位數）", key=f"quick_front_{player_a}")

st.markdown("**後九洞成績**")
numeric_input_html("主球員後9洞成績輸入（9位數）", key=f"quick_back_{player_a}")

handicaps = {player_a: st.number_input(f"{player_a} 差點", 0, 54, 0, key="hcp_main")}

opponents = []
bets = {}
for i in range(1, 5):
    st.markdown(f"#### 對手球員 B{i}")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f"球員 B{i} 名稱", player_list_with_done, key=f"b{i}_name")
    if name == "請選擇球員":
        st.warning(f"⚠️ 請選擇對手球員 B{i}。")
        st.stop()
    if name == "✅ Done":
        break
    if name in [player_a] + opponents:
        st.warning(f"⚠️ {name} 已被選擇，請勿重複。")
        st.stop()
    opponents.append(name)

    st.subheader(f"{name} 快速成績輸入")
    st.markdown("**前九洞成績**")
    numeric_input_html(f"{name} 前9洞成績輸入（9位數）", key=f"quick_front_{name}")
    st.markdown("**後九洞成績**")
    numeric_input_html(f"{name} 後9洞成績輸入（9位數）", key=f"quick_back_{name}")

    with cols[1]:
        handicaps[name] = st.number_input("差點：", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

if st.button("載入快速成績"):
    st.experimental_rerun()

