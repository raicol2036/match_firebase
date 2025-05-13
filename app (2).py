import streamlit as st
import pandas as pd
import numpy as np

# 設定頁面配置
st.set_page_config(page_title='⛳ 高爾夫比洞賽模擬器', layout='wide')
st.title('⛳ 高爾夫比洞賽模擬器')

# 初始化球員與洞數
players = ['A', 'B', 'C', 'D']
holes = list(range(1, 19))

# 初始化差點與賭金
if 'handicaps' not in st.session_state:
    st.session_state.handicaps = {'A': 0, 'B': 3, 'C': 5, 'D': 8}
if 'bets' not in st.session_state:
    st.session_state.bets = {i: 100 for i in holes}

# 初始化成績資料
if 'scores_df' not in st.session_state:
    np.random.seed(42)
    scores_data = {player: np.random.randint(3, 6, size=18) for player in players}
    st.session_state.scores_df = pd.DataFrame(scores_data, index=holes)

# 顯示可編輯的成績表格
st.subheader('逐洞成績（可編輯）')
edited_scores = st.data_editor(
    st.session_state.scores_df,
    num_rows="dynamic",
    use_container_width=True,
    key="scores_editor"
)
st.session_state.scores_df = edited_scores

# 計算對戰結果
match_results_df = pd.DataFrame(0, index=players, columns=players)
match_summary_df = pd.DataFrame('', index=players, columns=players)
match_result_counts = {p: {op: {'win': 0, 'draw': 0, 'lose': 0} for op in players} for p in players}

for hole in holes:
    for p1 in players:
        for p2 in players:
            if p1 != p2:
                score1 = st.session_state.scores_df.loc[hole, p1] - st.session_state.handicaps[p1]
                score2 = st.session_state.scores_df.loc[hole, p2] - st.session_state.handicaps[p2]
                diff = score1 - score2
                match_results_df.loc[p1, p2] += diff * st.session_state.bets[hole]
                if diff < 0:
                    match_result_counts[p1][p2]['win'] += 1
                elif diff > 0:
                    match_result_counts[p1][p2]['lose'] += 1
                else:
                    match_result_counts[p1][p2]['draw'] += 1

# 顯示比賽結果（含賭金結算）
st.subheader("比賽結果（含賭金結算）")
for p1 in players:
    for p2 in players:
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
