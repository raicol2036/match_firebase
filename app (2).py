import streamlit as st
import pandas as pd
import numpy as np
# 匯入 collections 模組
from collections import defaultdict

# 使用 defaultdict 避免 KeyError
result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})

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
scores_data = {}
for player in selected_players:
    scores_data[player] = [int(d) for d in quick_scores[player]]

scores_df = pd.DataFrame(scores_data, index=holes)

# 顯示生成的成績表
st.write("### 逐洞成績：")
st.dataframe(scores_df)

# 初始化賭金結算與結果追蹤
total_earnings = {p: 0 for p in selected_players}
result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})

# 🎯 **計算逐洞結果**
for hole in holes:
    # 取得該洞的成績
    scores = scores_df.loc[hole]
    
    # 計算讓桿後的成績
    adjusted_scores = {player: score - handicaps[player] for player, score in scores.items()}
    
    # 找出最低成績
    min_score = min(adjusted_scores.values())
    winners = [p for p, s in adjusted_scores.items() if s == min_score]

    if len(winners) == 1:
        # 單一贏家
        winner = winners[0]
        total_earnings[winner] += sum(bets.values())
        result_tracker[winner]["win"] += 1
        
        # 其他人減少賭金
        for player in selected_players:
            if player != winner:
                total_earnings[player] -= bets[player]
                result_tracker[player]["lose"] += 1
    else:
        # 平手情況
        for player in winners:
            result_tracker[player]["tie"] += 1

# ✅ **顯示總表**
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
