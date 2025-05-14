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
selected_players = st.multiselect('選擇參賽球員（至少2人）', player_names)

if len(selected_players) < 2:
    st.warning('請選擇至少兩位球員參賽。')
    st.stop()

# 輸入個人差點
st.subheader('3. 輸入個人差點、賭金與快速成績')
handicaps = {}
bets = {}
quick_scores = {}

for player in selected_players:
    st.markdown(f'### {player}')
    handicaps[player] = st.number_input(f'{player} 的差點', min_value=0, max_value=54, value=0, step=1)
    bets[player] = st.number_input(f'{player} 的賭金設定', min_value=0, value=100, step=10)
    quick_scores[player] = st.text_input(f'{player} 的快速成績輸入（18碼）', max_chars=18)
    if len(quick_scores[player]) == 18:
        st.success(f'✅ {player} 成績已完成輸入')

# 初始化成績資料
if 'scores_df' not in st.session_state:
    st.session_state.scores_df = pd.DataFrame('', index=holes, columns=selected_players)

if st.button('生成逐洞成績'):
    scores_data = {}
    for player in selected_players:
        if len(quick_scores[player]) == 18 and quick_scores[player].isdigit():
            scores_data[player] = [int(d) for d in quick_scores[player]]
        else:
            st.error(f'⚠️ {player} 的快速成績輸入錯誤，請檢查')
            continue
    st.session_state.scores_df = pd.DataFrame(scores_data, index=holes)
    st.success('✅ 成績已成功生成！')
    st.dataframe(st.session_state.scores_df)
# 初始化賭金結算與結果追蹤
total_earnings = {p: 0 for p in selected_players}
result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in selected_players}

# 假設這裡有一個判斷勝負的邏輯（範例）
for hole in holes:
    scores = st.session_state.scores_df.loc[hole]
    min_score = scores.min()
    winners = scores[scores == min_score].index.tolist()
    
    if len(winners) == 1:
        winner = winners[0]
        total_earnings[winner] += bets[winner]
        result_tracker[winner]["win"] += 1
        for player in selected_players:
            if player != winner:
                total_earnings[player] -= bets[player]
                result_tracker[player]["lose"] += 1
    else:
        for player in winners:
            result_tracker[player]["tie"] += 1

# 📊 總結
st.markdown("### 📊 總結結果（含勝負平統計）")
summary_data = []
for p in selected_players:
    summary_data.append({
        "球員": p,
        "總賭金結算": total_earnings[p],
        "勝": result_tracker[p]["win"],
        "負": result_tracker[p]["lose"],
        "平": result_tracker[p]["tie"]
    })
summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df.set_index("球員"))

