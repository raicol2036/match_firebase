# ✅ Golf Match Play - 支援多對手、JSON 儲存
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from streamlit.components.v1 import html

st.set_page_config(page_title="高爾夫Match play-1 vs N", layout="wide")
st.title("⛳ 高爾夫Match play - 1 vs N")

# 自定義快速成績輸入框

def numeric_input_html(label, key):
    value = st.session_state.get(key, "")
    html(f"""
        <label for=\"{key}\" style=\"font-weight:bold\">{label}</label><br>
        <input id=\"{key}\" name=\"{key}\" inputmode=\"numeric\" pattern=\"[0-9]*\" maxlength=\"18\"
               style=\"width:100%; font-size:1.1em; padding:0.5em;\" value=\"{value}\" />
        <script>
        const input = window.parent.document.getElementById('{key}');
        input.addEventListener('input', () => {{
            const value = input.value;
            window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: '{key}', value}}, '*');
        }});
        </script>
    """, height=100)

# 載入資料
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players_db.csv")

course_name = st.selectbox("選擇球場", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("前九洞區域", zones)
zone_back = st.selectbox("後九洞區域", zones)

holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

# 設定球員
st.markdown("### 🎯 球員設定")
player_list = ["請選擇球員"] + players_df["name"].tolist()
player_list_with_done = player_list + ["✅ Done"]

player_a = st.selectbox("選擇主球員 A", player_list)
if player_a == "請選擇球員":
    st.warning("⚠️ 請選擇主球員 A 才能繼續操作。")
    st.stop()

numeric_input_html("主球員快速成績輸入（18位數）", key=f"quick_{player_a}")
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
    numeric_input_html(f"{name} 快速成績輸入（18位數）", key=f"quick_{name}")
    with cols[1]:
        handicaps[name] = st.number_input("差點：", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

# 初始化結構
game_data = {
    "game_id": f"matchplay_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "course": {
        "name": course_name,
        "front_area": zone_front,
        "back_area": zone_back,
        "par": par,
        "hcp": hcp
    },
    "players": {},
    "bets": bets,
    "holes": [],
    "created": datetime.now().isoformat()
}

all_players = [player_a] + opponents
score_data = {p: [] for p in all_players}
total_earnings = {p: 0 for p in all_players}
result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in all_players}

quick_scores = {}
for p in all_players:
    value = st.session_state.get(f"quick_{p}", "")
    if value and len(value) == 18 and value.isdigit():
        scores = [int(c) for c in value]
        if all(1 <= s <= 15 for s in scores):
            quick_scores[p] = scores
        else:
            st.error(f"⚠️ {p} 的每洞桿數需為 1~15。")
    elif value:
        st.error(f"⚠️ {p} 快速成績輸入需為18位數字串。")

st.markdown("### 📝 輸入每洞成績與賭金")
for i in range(18):
    st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    cols = st.columns(1 + len(opponents))
    hole_scores = {}
    adjusted_scores = {}
    result_detail = {}

    default_score = quick_scores.get(player_a, [par[i]])[i]
    score_main = cols[0].number_input("", 1, 15, default_score, key=f"{player_a}_score_{i}", label_visibility="collapsed")
    score_data[player_a].append(score_main)
    hole_scores[player_a] = score_main
    adj_main = score_main

    with cols[0]:
        st.markdown(f"<div style='text-align:center; margin-bottom:-10px'><strong>{player_a} 桿數{' 🐦' if score_main < par[i] else ''}</strong></div>", unsafe_allow_html=True)

    for idx, op in enumerate(opponents):
        default_score = quick_scores.get(op, [par[i]])[i]
        score_op = cols[idx+1].number_input("", 1, 15, default_score, key=f"{op}_score_{i}", label_visibility="collapsed")
        score_data[op].append(score_op)
        hole_scores[op] = score_op

        adj_op = score_op
        if handicaps[op] > handicaps[player_a] and hcp[i] <= (handicaps[op] - handicaps[player_a]):
            adj_op -= 1
        elif handicaps[player_a] > handicaps[op] and hcp[i] <= (handicaps[player_a] - handicaps[op]):
            adj_main -= 1

        adjusted_scores[op] = adj_op
        result = "tie"

        if adj_op < adj_main:
            result = "win"
            bonus = 2 if score_op < par[i] else 1
            total_earnings[op] += bets[op] * bonus
            total_earnings[player_a] -= bets[op] * bonus
            result_tracker[op]["win"] += 1
            result_tracker[player_a]["lose"] += 1
            emoji = "👑"
        elif adj_op > adj_main:
            result = "lose"
            bonus = 2 if score_main < par[i] else 1
            total_earnings[op] -= bets[op] * bonus
            total_earnings[player_a] += bets[op] * bonus
            result_tracker[player_a]["win"] += 1
            result_tracker[op]["lose"] += 1
            emoji = "👽"
        else:
            result_tracker[player_a]["tie"] += 1
            result_tracker[op]["tie"] += 1
            emoji = "⚖️"

        with cols[idx+1]:
            st.markdown(f"<div style='text-align:center; margin-bottom:-10px'><strong>{op} 桿數 {emoji}{' 🐦' if score_op < par[i] else ''}</strong></div>", unsafe_allow_html=True)

        result_detail[op] = result

    adjusted_scores[player_a] = adj_main
    result_detail[player_a] = "tie"

    game_data["holes"].append({
        "hole": i+1,
        "par": par[i],
        "hcp": hcp[i],
        "scores": hole_scores,
        "adjusted_scores": adjusted_scores,
        "result": {"winner": None, "details": result_detail}
    })

# 總結
for p in all_players:
    game_data["players"][p] = {
        "handicap": handicaps[p],
        "scores": score_data[p],
        "earnings": total_earnings[p],
        "results": result_tracker[p]
    }

st.markdown("### 📊 總結結果（含勝負平統計）")
summary_df = pd.DataFrame([
    {"球員": p, "總賭金結算": total_earnings[p], "勝": result_tracker[p]["win"], "負": result_tracker[p]["lose"], "平": result_tracker[p]["tie"]}
    for p in all_players
])
st.dataframe(summary_df.set_index("球員"))

# 儲存 JSON
with st.expander("💾 儲存對戰記錄 JSON"):
    json_str = json.dumps(game_data, ensure_ascii=False, indent=2)
    st.download_button("📥 下載 JSON", data=json_str, file_name=f"{game_data['game_id']}.json", mime="application/json")
