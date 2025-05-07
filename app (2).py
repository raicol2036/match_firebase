import streamlit as st
import pandas as pd
from streamlit.components.v1 import html

st.set_page_config(page_title="高爾夫Match play-1 vs N", layout="wide")
st.title("\u26f3\ufe0f \u9ad8\u723e\u592bMatch play - 1 vs N")

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
        }});
        </script>
    """, height=100)

def adjust_scores(main, opp, hcp_value, hcp_main, hcp_opp):
    adj_main, adj_opp = main, opp
    diff = hcp_opp - hcp_main
    if diff > 0 and hcp_value <= diff:
        adj_opp -= 1
    elif diff < 0 and hcp_value <= -diff:
        adj_main -= 1
    return adj_main, adj_opp

# \u8f09\u5165\u8cc7\u6599
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players.csv")

course_name = st.selectbox("\u9078\u64c7\u7403\u5834", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("\u524d\u4e5d\u6d1e\u5340\u57df", zones)
zone_back = st.selectbox("\u5f8c\u4e5d\u6d1e\u5340\u57df", zones)

holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

st.markdown("### \ud83c\udfaf \u7403\u54e1\u8a2d\u5b9a")
player_list = ["\u8acb\u9078\u64c7\u7403\u54e1"] + players_df["name"].tolist()
player_list_with_done = player_list + ["\u2705 Done"]

player_a = st.selectbox("\u9078\u64c7\u4e3b\u7403\u54e1 A", player_list)
if player_a == "\u8acb\u9078\u64c7\u7403\u54e1":
    st.warning("\u26a0\ufe0f \u8acb\u9078\u64c7\u4e3b\u7403\u54e1 A \u624d\u80fd\u7e7c\u7e8c\u64cd\u4f5c\u3002")
    st.stop()

numeric_input_html("\u4e3b\u7403\u54e1\u524d9\u6d1e\u6210\u7e3e\u8f38\u5165\uff089\u4f4d\u6578\uff09", key=f"quick_front_{player_a}")
numeric_input_html("\u4e3b\u7403\u54e1\u5f8c9\u6d1e\u6210\u7e3e\u8f38\u5165\uff089\u4f4d\u6578\uff09", key=f"quick_back_{player_a}")
handicaps = {player_a: st.number_input(f"{player_a} \u5dee\u9ede", 0, 54, 0, key="hcp_main")}

opponents = []
bets = {}
for i in range(1, 5):
    st.markdown(f"#### \u5c0d\u624b\u7403\u54e1 B{i}")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f"\u7403\u54e1 B{i} \u540d\u7a31", player_list_with_done, key=f"b{i}_name")
    if name == "\u8acb\u9078\u64c7\u7403\u54e1":
        st.warning(f"\u26a0\ufe0f \u8acb\u9078\u64c7\u5c0d\u624b\u7403\u54e1 B{i}\u3002")
        st.stop()
    if name == "\u2705 Done":
        break
    if name in [player_a] + opponents:
        st.warning(f"\u26a0\ufe0f {name} \u5df2\u88ab\u9078\u64c7\uff0c\u8acb\u52ff\u91cd\u8907\u3002")
        st.stop()
    opponents.append(name)
    numeric_input_html(f"{name} \u524d9\u6d1e\u6210\u7e3e\u8f38\u5165\uff089\u4f4d\u6578\uff09", key=f"quick_front_{name}")
    numeric_input_html(f"{name} \u5f8c9\u6d1e\u6210\u7e3e\u8f38\u5165\uff089\u4f4d\u6578\uff09", key=f"quick_back_{name}")
    with cols[1]:
        handicaps[name] = st.number_input("\u5dee\u9ede\uff1a", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("\u6bcf\u6d1e\u8ced\u91d1", 10, 1000, 100, key=f"bet_b{i}")

if st.button("\ud83d\udcc5 \u8f09\u5165\u5feb\u901f\u6210\u7e3e"):
    st.experimental_rerun()

all_players = [player_a] + opponents
quick_scores = {}
for p in all_players:
    front = st.session_state.get(f"quick_front_{p}", "")
    back = st.session_state.get(f"quick_back_{p}", "")
    full = front + back
    if full and len(full) == 18 and full.isdigit():
        quick_scores[p] = [int(c) for c in full]
        if not all(1 <= s <= 15 for s in quick_scores[p]):
            st.error(f"\u26a0\ufe0f {p} \u7684\u6bcf\u6d1e\u6851\u6578\u9808\u70ba 1~15\u3002")
            quick_scores[p] = []
    elif front or back:
        st.error(f"\u26a0\ufe0f {p} \u5feb\u901f\u6210\u7e3e\u8f38\u5165\u9808\u70ba 9+9 \u517118\u4f4d\u6578\u5b57\u4e32\u3002")

if st.button("\u2705 \u78ba\u8a8d\u8a2d\u5b9a\u4e26\u958b\u59cb\u8f38\u5165\u6bcf\u6d1e\u6210\u7e3e"):
    score_data = {p: [] for p in all_players}
    total_earnings = {p: 0 for p in all_players}
    result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in all_players}

    st.markdown("### \ud83d\udcdd \u8f38\u5165\u6bcf\u6d1e\u6210\u7e3e\u8207\u8ced\u91d1")

    for i in range(18):
        st.markdown(f"#### \u7b2c{i+1}\u6d1e (Par {par[i]}, HCP {hcp[i]})")
        cols = st.columns(1 + len(opponents))

        default_score_main = quick_scores[player_a][i] if player_a in quick_scores and len(quick_scores[player_a]) == 18 else par[i]
        score_main = cols[0].number_input("", 1, 15, default_score_main, key=f"{player_a}_score_{i}", label_visibility="collapsed")
        score_data[player_a].append(score_main)
        birdie_main = " \ud83d\udc1f" if score_main < par[i] else ""
        with cols[0]:
            st.markdown(f"<div style='text-align:center; margin-bottom:-10px'><strong>{player_a} \u6851\u6578{birdie_main}</strong></div>", unsafe_allow_html=True)

        for idx, op in enumerate(opponents):
            default_score_op = quick_scores[op][i] if op in quick_scores and len(quick_scores[op]) == 18 else par[i]
            score_op = cols[idx + 1].number_input("", 1, 15, default_score_op, key=f"{op}_score_{i}", label_visibility="collapsed")
            score_data[op].append(score_op)

            adj_main, adj_op = adjust_scores(score_main, score_op, hcp[i], handicaps[player_a], handicaps[op])

            if adj_op < adj_main:
                emoji = "\ud83d\udc51"
                bonus = 2 if score_op < par[i] else 1
                total_earnings[op] += bets[op] * bonus
                total_earnings[player_a] -= bets[op] * bonus
                result_tracker[op]["win"] += 1
                result_tracker[player_a]["lose"] += 1
            elif adj_op > adj_main:
                emoji = "\ud83d\udc7d"
                bonus = 2 if score_main < par[i] else 1
                total_earnings[op] -= bets[op] * bonus
                total_earnings[player_a] += bets[op] * bonus
                result_tracker[player_a]["win"] += 1
                result_tracker[op]["lose"] += 1
            else:
                emoji = "\u2696\ufe0f"
                result_tracker[player_a]["tie"] += 1
                result_tracker[op]["tie"] += 1

            birdie_icon = " \ud83d\udc1f" if score_op < par[i] else ""
            with cols[idx + 1]:
                st.markdown(f"<div style='text-align:center; margin-bottom:-10px'><strong>{op} \u6851\u6578 {emoji}{birdie_icon}</strong></div>", unsafe_allow_html=True)

    st.markdown("### \ud83d\udcca \u7e3d\u7d50\u7d71\u8a08\uff08\u542b\u52dd\u8ca0\u5e73\u7d71\u8a08\uff09")
    summary_data = []
    for p in all_players:
        summary_data.append({
            "\u7403\u54e1": p,
            "\u7e3d\u8ced\u91d1\u7d50\u7b97": total_earnings[p],
            "\u52dd": result_tracker[p]["win"],
            "\u8ca0": result_tracker[p]["lose"],
            "\u5e73": result_tracker[p]["tie"]
        })

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df.set_index("\u7403\u54e1").sort_values("\u7e3d\u8ced\u91d1\u7d50\u7b97", ascending=False))
