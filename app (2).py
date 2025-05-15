import streamlit as st
import pandas as pd
import numpy as np
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
    quick_scores[player] = st.text_input(f'{player} 的快速成績輸入（18碼）', max_chars=18, key=f"score_{player}")
    if len(quick_scores[player]) == 18:
        st.success(f'✅ {player} 成績已完成輸入')

# 添加生成結果按鈕
if st.button('生成逐洞成績及對戰結果'):
    # 檢查所有成績是否已輸入
    all_scores_entered = all(len(quick_scores[player]) == 18 for player in selected_players)
    
    if not all_scores_entered:
        st.error("請確保所有球員的18洞成績已完整輸入")
        st.stop()
    
       # 初始化成绩数据
    scores_data = {}
    for player in selected_players:
        try:
            # 处理成绩输入 - 确保是18个数字
            score_str = quick_scores[player].strip().replace(" ", "")  # 移除所有空格
            if not score_str.isdigit():
                st.error(f"{player}的成绩包含非数字字符: {quick_scores[player]}")
                st.stop()
                
            if len(score_str) != 18:
                st.error(f"{player}必须输入18洞成绩，当前输入了{len(score_str)}个数字")
                st.stop()
                
            scores_data[player] = [int(c) for c in score_str]
        except Exception as e:
            st.error(f"处理{player}的成绩时出错: {str(e)}")
            st.stop()

    # 创建DataFrame时明确指定索引和列
    scores_df = pd.DataFrame(scores_data, index=holes)
    scores_df.columns = selected_players  # 明确设置列名

    # 显示生成的成绩表
    st.write("### 逐洞成绩：")
    st.dataframe(scores_df)

    # 确保DataFrame中的数据是整数类型
    scores_df = scores_df.astype(int)

    # 初始化賭金結算與結果追蹤
    total_earnings = {p: 0 for p in selected_players}
    result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})
    head_to_head = defaultdict(lambda: defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0}))

    # ... (前面的代碼保持不變，直到計算逐洞結果的部分)

    # 🎯 计算逐洞结果
    for hole_idx, hole in enumerate(holes):
        # 取得该洞的原始成绩
        scores = scores_df.loc[hole]
        
        # 取得该洞的难度指数 (hcp)
        hole_hcp = hcp[hole_idx]
        
        # 计算调整后的成绩
        adjusted_scores = {}
        for player in selected_players:
            try:
                # 初始调整成绩 = 原始成绩 - 球员差点
                adjusted_score = int(scores[player]) - handicaps[player]
                
                # 检查是否需要让杆
                for other_player in selected_players:
                    if player != other_player:
                        # 计算差点差
                        hdcp_diff = handicaps[player] - handicaps[other_player]
                        
                        # 如果当前球员差点较低，且此洞难度在让杆范围内
                        if hdcp_diff < 0 and 1 <= hole_hcp <= abs(hdcp_diff):
                            # 当前球员需要让杆给其他球员 (增加一杆)
                            adjusted_score += 1
                
                adjusted_scores[player] = adjusted_score
            except (ValueError, TypeError):
                st.error(f"无效的成绩数据: 球员 {player} 在洞 {hole} 的成绩 '{scores[player]}' 不是有效数字")
                st.stop()
        
        # 检查是否有有效数据
        if not adjusted_scores:
            st.error("没有有效的成绩数据可供计算")
            st.stop()
        
        try:
            # 找出最低成绩
            min_score = min(adjusted_scores.values())
            winners = [p for p, s in adjusted_scores.items() if s == min_score]
        except ValueError as e:
            st.error(f"计算最小值时出错: {str(e)}")
            st.stop()

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
                    head_to_head[winner][player]["win"] += 1
                    head_to_head[player][winner]["lose"] += 1
        else:
            # 平手情況
            for player in winners:
                result_tracker[player]["tie"] += 1
                for other in winners:
                    if player != other:
                        head_to_head[player][other]["tie"] += 1

    # ✅ 顯示總表
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
    st.dataframe(summary_df)

   # 顯示隊員對戰結果表
    st.markdown("### 🆚 隊員對戰結果 (各自比分模式)")
    
    # 創建對戰結果表
    match_results = pd.DataFrame(index=selected_players, columns=selected_players)
    
    for player1 in selected_players:
        for player2 in selected_players:
            if player1 == player2:
                match_results.loc[player1, player2] = "-"
            else:
                result = head_to_head[player1][player2]
                # 計算淨勝洞數 (勝洞 - 負洞)
                net_holes = result['win'] - result['lose']
                # 計算賭金差額
                money_diff = total_earnings[player1] - total_earnings[player2]
                
                # 格式化顯示
                if net_holes > 0:
                    result_str = f"{net_holes}↑ ${money_diff}"
                elif net_holes < 0:
                    result_str = f"{abs(net_holes)}↓ ${money_diff}"
                else:
                    result_str = f"平 ${money_diff}"
                
                match_results.loc[player1, player2] = result_str
    
    # 使用Styler來美化表格
    def color_negative_red(val):
        if isinstance(val, str) and '↓' in val:
            return 'color: red'
        elif isinstance(val, str) and '↑' in val:
            return 'color: green'
        return ''
    
    styled_table = match_results.style.applymap(color_negative_red)
    st.dataframe(styled_table)
