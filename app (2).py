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
st.subheader('2. 輸入參賽球員')
players_df = pd.read_csv('players.csv')
player_names = players_df['name'].tolist()
selected_players = st.multiselect('選擇參賽球員（至少2人）', player_names)

if len(selected_players) < 2:
    st.warning('請選擇至少兩位球員參賽。')
    st.stop()
if len(selected_players) < 2:
    st.warning('請輸入至少兩位球員名稱。')
    st.stop()

# 輸入個人差點
st.subheader('3. 輸入個人差點、賭金與快速成績')
handicaps = {}
bets = {}
quick_scores = {}

for player in selected_players:
    st.markdown(f'### {player}')
    handicaps[player] = st.number_input(f'{player} 的差點', min_value=0, max_value=54, value=0, step=1, key=f'{player}_hcp')
    bets[player] = st.number_input(f'{player} 的賭金設定', min_value=0, value=100, step=10, key=f'{player}_bet')
    quick_scores[player] = st.text_input(f'{player} 的快速成績輸入（18碼）', key=f'{player}_quick', max_chars=18)
    current_length = len(quick_scores[player])
    if current_length > 18:
        st.error(f'⚠️ 輸入過長，目前長度為 {current_length}/18')
    
    
        st.success('✅ 完成 18 碼輸入')

# 輸入每洞賭金


# 初始化成績資料
if 'scores_df' not in st.session_state:
    np.random.seed(42)
    scores_data = {player: np.random.randint(3, 6, size=len(holes)) for player in selected_players}
    st.session_state.scores_df = pd.DataFrame(scores_data, index=[str(h) for h in holes])
    st.session_state.scores_df.index = st.session_state.scores_df.index.map(str)

if st.button('生成逐洞成績'):
    st.subheader('5. 逐洞成績 (自動填入)')

# 根據快速輸入的值填入成績表
scores_data = {}
for player in selected_players:
    if len(quick_scores[player]) == 18 and quick_scores[player].isdigit():
        try:
            scores_data[player] = [int(d) for d in quick_scores[player]]
        except ValueError:
            st.error(f'{player} 的快速成績包含非數字的字符')  

# 更新到 DataFrame
if scores_data:
    st.session_state.scores_df = pd.DataFrame(scores_data, index=[str(h) for h in holes])
    if not st.session_state.scores_df.empty:
        st.success('✅ 成績已成功生成！')
        st.dataframe(st.session_state.scores_df)
    else:
        st.error('⚠️ 成績表生成失敗，請確認快速輸入是否正確填滿 18 碼。')

    st.warning('⚠️ 尚未完成所有球員的成績輸入')

if st.button('計算賭金結果'):
    st.subheader("6. 比賽結果（含賭金結算）")
match_summary_df = pd.DataFrame('', index=selected_players, columns=selected_players)
match_result_counts = {p: {op: {'win': 0, 'draw': 0, 'lose': 0} for op in selected_players} for p in selected_players}

for hole in holes:
    for p1 in selected_players:
        for p2 in selected_players:
            if p1 != p2:
                try:
                    score1 = st.session_state.scores_df.loc[str(hole), p1]
                    score2 = st.session_state.scores_df.loc[str(hole), p2]

                    # 修正 Series 問題，確保取得的是單一數值
                    try:
                        score1 = float(score1) if isinstance(score1, (int, float)) else float(score1.iloc[0])
                        score2 = float(score2) if isinstance(score2, (int, float)) else float(score2.iloc[0])
                    except (ValueError, IndexError):
                        st.error(f'成績讀取錯誤，無法正確讀取第 {hole} 洞的 {p1} 或 {p2} 成績')
                        continue
                except KeyError:
                    continue
                score1_adj = score1 - handicaps[p1]
                score2_adj = score2 - handicaps[p2]

                        if score1_adj < score2_adj:
                            match_result_counts[p1][p2]['win'] += 1
                        elif score1_adj > score2_adj:
                            match_result_counts[p1][p2]['lose'] += 1
                        else:
                            match_result_counts[p1][p2]['draw'] += 1

for p1 in selected_players:
    for p2 in selected_players:
        if p1 != p2:
            win = match_result_counts[p1][p2]['win']
            draw = match_result_counts[p1][p2]['draw']
            lose = match_result_counts[p1][p2]['lose']
            total_amount = (win - lose) * bets[p1]
            match_summary_df.loc[p1, p2] = f"{win}/{draw}/{lose}  $ {'+' if total_amount >= 0 else ''}{total_amount}"

st.dataframe(match_summary_df)

# 重置功能
if st.button("重置所有資料"):
    st.session_state.clear()
    st.experimental_rerun()
