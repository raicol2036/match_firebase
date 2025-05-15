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

  # 创建带有hcp的DataFrame
    try:
        # 先创建基本DataFrame
        scores_df = pd.DataFrame(scores_data, index=holes)
        scores_df = scores_df.astype(int)
        
        # 添加hcp列
        scores_df.insert(0, '球洞难度(hcp)', hcp)
        
        # 显示成绩表（不使用Styler避免错误）
        st.write("### 逐洞成绩（含球洞难度指数）：")
        
        # 创建副本用于显示，避免修改原始数据
        display_df = scores_df.copy()
        display_df.index.name = '球洞'
        
        # 格式化显示
        st.dataframe(display_df.style.format("{:.0f}"))
        
    except Exception as e:
        st.error(f"创建成绩表时出错: {str(e)}")
        st.stop()

    
