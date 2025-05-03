import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏌️ Golf Match - Manual Input", layout="wide")
st.title("🏌️ 高爾夫一對多比分系統（手動輸入）")

# ========== 載入資料 ==========
@st.cache_data
def load_players():
    return pd.read_csv("players.csv")

@st.cache_data
def load_course_db():
    df = pd.read_csv("course_db.csv")
    df["area_name"] = df["course_name"] + " - " + df["area"]
    return df

df_players = load_players()
course_df = load_course_db()
player_names = df_players["name"].dropna().tolist()

# ========== 選擇球員與設定 ==========
st.header("1️⃣ 選擇球員與設定")

selected_players = st.multiselect("選擇參賽球員（至少兩位）", player_names)

if len(selected_players) >= 2:
    st.subheader("🎯 差點與賭金")
    player_info = {}
    for p in selected_players:
        col1, col2 = st.columns(2)
        with col1:
            hcp = st.number_input(f"{p} 的差點", min_value=0, max_value=36, step=1, key=f"{p}_hcp")
        with col2:
            bet = st.number_input(f"{p} 的賭金", min_value=0, step=100, key=f"{p}_bet")
        player_info[p] = {"hcp": hcp, "bet": bet}

    # ========== 選擇球場區域 ==========
    st.header("2️⃣ 選擇前9/後9球場區域")
    areas = course_df["area_name"].unique().tolist()
    col1, col2 = st.columns(2)
    with col1:
        front_area = st.selectbox("前9洞區域", areas, key="front")
    with col2:
        back_area = st.selectbox("後9洞區域", areas, key="back")

    def get_area_par_hcp(df, area_name):
        course, area = area_name.split(" - ")
        sub_df = df[(df["course_name"] == course) & (df["area"] == area)]
        sub_df = sub_df.sort_values("hole")
        return sub_df["par"].tolist(), sub_df["hcp"].tolist()

    front_par, front_hcp = get_area_par_hcp(course_df, front_area)
    back_par, back_hcp = get_area_par_hcp(course_df, back_area)
    full_par = front_par + back_par
    full_hcp = front_hcp + back_hcp

    # ========== 快速輸入桿數 ==========
    st.header("3️⃣ 快速輸入每位球員的桿數（前9+後9）")
    scores = {}
    for p in selected_players:
        f9 = st.text_input(f"{p} 的前9洞桿數（9碼）", max_chars=9, key=f"{p}_f9")
        b9 = st.text_input(f"{p} 的後9洞桿數（9碼）", max_chars=9, key=f"{p}_b9")
        if len(f9) == 9 and f9.isdigit() and len(b9) == 9 and b9.isdigit():
            scores[p] = [int(x) for x in f9 + b9]
        else:
            scores[p] = []

    # ========== 指定主角 ==========
    st.header("4️⃣ 選擇主要選手並計算比分")
    main_player = st.selectbox("指定主要選手", selected_players)

    # ========== 計算勝負 ==========
    if st.button("✅ 產生比分結果"):
        if all(len(s) == 18 for s in scores.values()):
            st.success("比賽結果如下：")
            for opp in selected_players:
                if opp == main_player:
                    continue
                main_score = scores[main_player]
                opp_score = scores[opp]
                wins = sum(1 for m, o in zip(main_score, opp_score) if m < o)
                losses = sum(1 for m, o in zip(main_score, opp_score) if m > o)
                ties = 18 - wins - losses

                st.markdown(f"""
                ### 📊 {main_player} vs {opp}
                - 🏆 {main_player} 勝洞數：{wins}
                - 🏆 {opp} 勝洞數：{losses}
                - ⚖️ 平手洞數：{ties}
                """)
        else:
            st.error("請確認每位球員皆已正確輸入前後9洞共18碼桿數")
