# 匯出 canvas 的內容為 Python 檔案
with open('/mnt/data/Golf_Match_Play_Streamlit.py', 'w') as file:
    file.write("""import streamlit as st
import pandas as pd
from collections import defaultdict

# 初始化頁面設定
st.set_page_config(page_title='⛳ 高爾夫比洞賽模擬器', layout='wide')
st.title('⛳ 高爾夫比洞賽模擬器')

# 初始化結果跟踪器
result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})

# 1. 選擇球場
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

# 讀取前後九洞資料
front_info = course_info[course_info['area'] == front_area]
back_info = course_info[course_info['area'] == back_area]

holes = front_info['hole'].tolist() + back_info['hole'].tolist()
pars = front_info['par'].tolist() + back_info['par'].tolist()
hcp = front_info['hcp'].tolist() + back_info['hcp'].tolist()

# 2. 輸入參賽球員
st.subheader('2. 輸入參賽球員')
players_df = pd.read_csv('players.csv')
player_names = players_df['name'].tolist()
selected_players = st.multiselect('選擇參賽球員（至少2人）', player_names)

if len(selected_players) < 2:
    st.warning('請選擇至少兩位球員參賽。')
    st.stop()

# 3. 輸入個人差點、賭金與快速成績
st.subheader('3. 輸入個人差點、賭金與快速成績')
handicaps = {}
bets = {}
quick_scores = {}

for player in selected_players:
    st.markdown(f'### {player}')
    handicaps[player] = st.number_input(f'{player} 的差點', min_value=0, max_value=54, value=0, step=1, key=f"hdcp_{player}")
    bets[player] = st.number_input(f'{player} 的賭金設置', min_value=0, value=100, step=10, key=f"bet_{player}")
    quick_scores[player] = st.text_input(f'{player} 的快速成績輸入（18碼）', max_chars=18, key=f"score_{player}")
    if len(quick_scores[player]) == 18:
        st.success(f'✅ {player} 成績已完成輸入')

# 檢查快速成績是否完整
all_scores_entered = all(len(quick_scores.get(player, '')) == 18 for player in selected_players)
if not all_scores_entered:
    st.error("請確保所有球員的18洞成績已完整輸入")
    st.stop()

# 初始化成績資料
scores_data = {}
for player in selected_players:
    score_str = quick_scores[player].strip().replace(' ', '')
    scores_data[player] = [int(c) for c in score_str]

# 建立 DataFrame
scores_df = pd.DataFrame(scores_data, index=holes)
scores_df.insert(0, '球洞難度(hcp)', hcp)

# 顯示逐洞成績
st.write("### 逐洞成績（含球洞難度）：")
display_df = scores_df.copy()
display_df.index.name = '球洞'
st.dataframe(display_df)

# 初始化結果統計
total_earnings = {p: 0 for p in selected_players}
result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})
head_to_head = defaultdict(lambda: defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0}))
hole_by_hole_results = []

# 讓桿邏輯計算
def calculate_adjusted_scores(raw_scores, handicaps, hole_hcp):
    adjusted_scores = {}
    for player, score in raw_scores.items():
        total_adjustment = 0
        for opponent, opp_score in raw_scores.items():
            if player != opponent:
                diff = handicaps[opponent] - handicaps[player]
                if diff > 0 and hole_hcp <= diff:
                    total_adjustment += 1
        adjusted_scores[player] = score + total_adjustment
    return adjusted_scores

# 計算逐洞結果
for hole_idx, hole in enumerate(holes):
    hole_hcp = hcp[hole_idx]
    hole_results = {"球洞": hole, "難度": hole_hcp}
    raw_scores = scores_df.loc[hole][selected_players].to_dict()
    adjusted_scores = calculate_adjusted_scores(raw_scores, handicaps, hole_hcp)
    min_score = min(adjusted_scores.values())
    winners = [p for p, s in adjusted_scores.items() if s == min_score]

    if len(winners) == 1:
        winner = winners[0]
        hole_results["結果"] = f"{winner} 胜"
        total_earnings[winner] += sum(bets.values())
        result_tracker[winner]["win"] += 1
    else:
        hole_results["結果"] = "平局"
        for player in winners:
            result_tracker[player]["tie"] += 1

    hole_by_hole_results.append(hole_results)

# 顯示逐洞詳細結果
st.write("### 逐洞詳細結果（含讓桿調整）：")
hole_results_df = pd.DataFrame(hole_by_hole_results)
st.dataframe(hole_results_df.set_index('球洞'))
""")
