import streamlit as st
import pandas as pd
import numpy as np

# 設定頁面配置
st.set_page_config(page_title='⛳ 高爾夫比洞賽模擬器', layout='wide')
st.title('⛳ 高爾夫比洞賽模擬器')

# 上傳並選擇球場
st.subheader('1. 選擇球場')
course_df = pd.read_csv('course_db.csv')
course_names = course_df['course_name'].unique()
selected_course = st.selectbox("選擇球場", course_names)
course_info = course_df[course_df['course_name'] == selected_course]
areas = course_info['area'].unique().tolist()
st.subheader('前九洞區域選擇')
front_area = st.selectbox('前九洞區域', areas, key='front_area')

st.subheader('後九洞區域選擇')
back_area = st.selectbox('後九洞區域', areas, key='back_area')

# 讀取前後九洞的資料
front_info = course_info[course_info['area'] == front_area]
back_info = course_info[course_info['area'] == back_area]

# 組合資料
holes = front_info['hole'].tolist() + back_info['hole'].tolist()
pars = front_info['par'].tolist() + back_info['par'].tolist()
hcp = front_info['hcp'].tolist() + back_info['hcp'].tolist()


# 上傳並選擇球員
st.subheader('2. 輸入參賽球員')
players_df = pd.read_csv('players.csv')
player_names = players_df['name'].tolist()
selected_players = st.multiselect("選擇參賽球員（至少2人）", player_names)
if len(selected_players) < 2:
    st.warning("請選擇至少兩位球員參賽。")
    st.stop()
else:
    st.warning("請上傳包含欄位 'name' 的 players.csv 檔案。")
    st.stop()

# 輸入個人差點
st.subheader('3. 輸入個人差點')
handicaps = {}
for player in selected_players:
    handicaps[player] = st.number_input(f"{player} 的差點", min_value=0, max_value=54, value=0, step=1)

# 輸入每洞賭金
st.subheader('4. 輸入每洞賭金')
bets = {}
for i, hole in enumerate(holes):
    bets[hole] = st.number_input(f"第 {hole} 洞的賭金", min_value=0, value=100, step=10)

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
