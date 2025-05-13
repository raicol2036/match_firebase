import streamlit as st
import pandas as pd
import numpy as np

# 設定頁面配置
st.set_page_config(page_title='⛳ 高爾夫比洞賽模擬器', layout='wide')
st.title('⛳ 高爾夫比洞賽模擬器')

# --- 球場選擇 ---
course_options = course_df["course_name"].unique().tolist()
selected_course = st.selectbox("選擇球場", course_options)

filtered_area = course_df[course_df["course_name"] == selected_course]["area"].unique().tolist()
front_area = st.selectbox("前九洞區域", filtered_area, key="front_area")
back_area = st.selectbox("後九洞區域", filtered_area, key="back_area")

def get_course_info(cname, area):
    temp = course_df[(course_df["course_name"] == cname) & (course_df["area"] == area)]
    temp = temp.sort_values("hole")
    return temp["par"].tolist(), temp["hcp"].tolist()

front_par, front_hcp = get_course_info(selected_course, front_area)
back_par, back_hcp = get_course_info(selected_course, back_area)
par = front_par + back_par
hcp = front_hcp + back_hcp

# --- 球員設定 ---
players = st.multiselect("選擇參賽球員（最多4位）", st.session_state.players, max_selections=4)

new = st.text_input("新增球員")
if new:
    if new not in st.session_state.players:
        st.session_state.players.append(new)
        pd.DataFrame({"name": st.session_state.players}).to_csv(CSV_PATH, index=False)
        st.success(f"✅ 已新增球員 {new} 至資料庫")
    if new not in players and len(players) < 4:
        players.append(new)

if len(players) == 0:
    st.warning("⚠️ 請先選擇至少一位球員")
    st.stop()

handicaps = {p: st.number_input(f"{p} 差點", 0, 54, 0, key=f"hcp_{p}") for p in players}
bet_per_person = st.number_input("單局賭金（每人）", 10, 1000, 100)

# 初始化成績資料
if 'scores_df' not in st.session_state:
    np.random.seed(42)
    scores_data = {player: np.random.randint(3, 6, size=len(holes)) for player in selected_players}
    st.session_state.scores_df = pd.DataFrame(scores_data, index=holes)

# 顯示可編輯的成績表格
st.subheader('5. 逐洞成績（可編輯）')
edited_scores = st.data_editor(
    st.session_state.scores_df,
    num_rows="dynamic",
    use_container_width=True,
    key="scores_editor"
)
st.session_state.scores_df = edited_scores

# 計算比賽結果（含賭金結算）
st.subheader("6. 比賽結果（含賭金結算）")
match_summary_df = pd.DataFrame('', index=selected_players, columns=selected_players)
match_result_counts = {p: {op: {'win': 0, 'draw': 0, 'lose': 0} for op in selected_players} for p in selected_players}

for hole in holes:
    for p1 in selected_players:
        for p2 in selected_players:
            if p1 != p2:
                score1 = st.session_state.scores_df.loc[hole, p1] - handicaps[p1]
                score2 = st.session_state.scores_df.loc[hole, p2] - handicaps[p2]
                if score1 < score2:
                    match_result_counts[p1][p2]['win'] += 1
                elif score1 > score2:
                    match_result_counts[p1][p2]['lose'] += 1
                else:
                    match_result_counts[p1][p2]['draw'] += 1

for p1 in selected_players:
    for p2 in selected_players:
        if p1 != p2:
            win = match_result_counts[p1][p2]['win']
            draw = match_result_counts[p1][p2]['draw']
            lose = match_result_counts[p1][p2]['lose']
            total_amount = (win - lose) * 100
            match_summary_df.loc[p1, p2] = f"{win}/{draw}/{lose}  $ {'+' if total_amount >= 0 else ''}{total_amount}"

st.dataframe(match_summary_df)

# 重置功能
if st.button("重置所有資料"):
    st.session_state.clear()
    st.experimental_rerun()
