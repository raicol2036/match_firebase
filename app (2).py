import streamlit as st
import pandas as pd
from collections import defaultdict

# 初始化结果跟踪器
result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})

# 页面设置
st.set_page_config(page_title='⛳ 高尔夫比洞赛模拟器', layout='wide')
st.title('⛳ 高尔夫比洞赛模拟器')

# 1. 选择球场
st.subheader('1. 选择球场')
course_df = pd.read_csv('course_db.csv')
course_names = course_df['course_name'].unique()
selected_course = st.selectbox("选择球场", course_names)
course_info = course_df[course_df['course_name'] == selected_course]
areas = course_info['area'].unique().tolist()

st.subheader('前九洞区域选择')
front_area = st.selectbox('前九洞区域', areas, key='front_area')
st.subheader('后九洞区域选择')
back_area = st.selectbox('后九洞区域', areas, key='back_area')

# 读取前后九洞数据
front_info = course_info[course_info['area'] == front_area]
back_info = course_info[course_info['area'] == back_area]

# 组合数据
holes = front_info['hole'].tolist() + back_info['hole'].tolist()
pars = front_info['par'].tolist() + back_info['par'].tolist()
hcp = front_info['hcp'].tolist() + back_info['hcp'].tolist()

# 2. 输入参赛球员
st.subheader('2. 输入参赛球员')
players_df = pd.read_csv('players.csv')
player_names = players_df['name'].tolist()
selected_players = st.multiselect('选择参赛球员（至少2人）', player_names)

if len(selected_players) < 2:
    st.warning('请选择至少两位球员参赛。')
    st.stop()

# 3. 输入个人差点、赌金与快速成绩
st.subheader('3. 输入个人差点、赌金与快速成绩')
handicaps = {}
bets = {}
quick_scores = {}

for player in selected_players:
    st.markdown(f'### {player}')
    handicaps[player] = st.number_input(f'{player} 的差点', min_value=0, max_value=54, value=0, step=1, key=f"hdcp_{player}")
    bets[player] = st.number_input(f'{player} 的赌金设定', min_value=0, value=100, step=10, key=f"bet_{player}")
    quick_scores[player] = st.text_input(f'{player} 的快速成绩输入（18码）', max_chars=18, key=f"score_{player}")
    if len(quick_scores[player]) == 18:
        st.success(f'✅ {player} 成绩已完成输入')

# 生成结果按钮
if st.button('生成逐洞成绩及对战结果'):
    # 检查所有成绩是否已输入
    all_scores_entered = all(len(quick_scores.get(player, '')) == 18 for player in selected_players)
    
    if not all_scores_entered:
        st.error("请确保所有球员的18洞成绩已完整输入")
        st.stop()
    
    # 初始化成绩数据
    scores_data = {}
    for player in selected_players:
        try:
            score_str = quick_scores[player].strip().replace(" ", "")
            if not score_str.isdigit() or len(score_str) != 18:
                st.error(f"{player}的成绩必须是18位数字")
                st.stop()
            scores_data[player] = [int(c) for c in score_str]
        except Exception as e:
            st.error(f"处理{player}的成绩时出错: {str(e)}")
            st.stop()

    # 创建基本DataFrame
    try:
        scores_df = pd.DataFrame(scores_data, index=holes)
        scores_df = scores_df.astype(int)
    except Exception as e:
        st.error(f"创建成绩表时出错: {str(e)}")
        st.stop()

    # 添加hcp列
    scores_df.insert(0, '球洞难度(hcp)', hcp)
    
    # 显示成绩表
    st.write("### 逐洞成绩（含球洞难度指数）：")
    display_df = scores_df.copy()
    display_df.index.name = '球洞'
    st.dataframe(display_df)

    # 初始化结果跟踪
    total_earnings = {p: 0 for p in selected_players}
    result_tracker = defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0})
    head_to_head = defaultdict(lambda: defaultdict(lambda: {"win": 0, "lose": 0, "tie": 0}))
    hole_by_hole_results = []

    # 计算逐洞结果（含让杆逻辑）
    for hole_idx, hole in enumerate(holes):
        hole_hcp = hcp[hole_idx]
        hole_results = {"球洞": hole, "难度": hole_hcp}
        
       # 不在此處調整成績，直接用 raw_scores
    raw_scores = scores_df.loc[hole][selected_players].to_dict()

# 設置讓桿的玩家和洞
player_scores_for_comparison = {}

for player in selected_players:
    # 確定是否該玩家的洞該讓桿
    is_handed = False
    for other in selected_players:
        if player != other:
            hdcap_diff = handicaps[player] - handicaps[other]
            # 若差點較低，且此洞HCP在差點差範圍內，則讓他
            if hdcap_diff < 0 and 1 <= hole_hcp <= abs(hdcap_diff):
                is_handed = True
                break

    # 該玩家的分數，根據讓桿效果修正
    score = raw_scores[player]
    if is_handed:
        score += 1  # 模擬讓一桿的效果

    player_scores_for_comparison[player] = score

# 找出最小分數，即勝利者（讓桿後）
    min_score = min(player_scores_for_comparison.values())
    winners = [p for p, s in player_scores_for_comparison.items() if s == min_score]

        # 记录洞结果
    if len(winners) == 1:
        winner = winners[0]
        hole_results["结果"] = f"{winner} 胜"
            
            # 更新统计
        total_earnings[winner] += sum(bets.values())
        result_tracker[winner]["win"] += 1
            
            for player in selected_players:
                if player != winner:
                    total_earnings[player] -= bets[player]
                    result_tracker[player]["lose"] += 1
                    head_to_head[winner][player]["win"] += 1
                    head_to_head[player][winner]["lose"] += 1
        else:
            hole_results["结果"] = "平局"
            for player in winners:
                result_tracker[player]["tie"] += 1
                for other in winners:
                    if player != other:
                        head_to_head[player][other]["tie"] += 1
        
        hole_by_hole_results.append(hole_results)

    # 显示逐洞详细结果
    st.write("### 逐洞详细结果（含让杆调整）：")
    hole_results_df = pd.DataFrame(hole_by_hole_results)
    st.dataframe(hole_results_df.set_index('球洞'))

    # 显示总结结果
    st.markdown("### 📊 总结结果（含胜负平统计）")
    summary_data = []
    for p in selected_players:
        summary_data.append({
            "球员": p,
            "总赌金结算": total_earnings[p],
            "胜": result_tracker[p]["win"],
            "负": result_tracker[p]["lose"],
            "平": result_tracker[p]["tie"]
        })
    st.dataframe(pd.DataFrame(summary_data))

    # 显示队员对战结果
    st.markdown("### 🆚 队员对战结果")
    match_results = pd.DataFrame(index=selected_players, columns=selected_players)
    
    for p1 in selected_players:
        for p2 in selected_players:
            if p1 == p2:
                match_results.loc[p1, p2] = "-"
            else:
                res = head_to_head[p1][p2]
                net = res["win"] - res["lose"]
                money = total_earnings[p1] - total_earnings[p2]
                if net > 0:
                    match_results.loc[p1, p2] = f"{net}↑ ${money}"
                elif net < 0:
                    match_results.loc[p1, p2] = f"{abs(net)}↓ ${money}"
                else:
                    match_results.loc[p1, p2] = f"平 ${money}"
    
    # 简单的颜色设置
    def color_results(val):
        if isinstance(val, str):
            if '↑' in val: return 'color: green'
            if '↓' in val: return 'color: red'
        return ''
    
    st.dataframe(match_results.style.applymap(color_results))
