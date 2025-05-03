import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏌️ Golf Match - Manual Input", layout="wide")
st.title("🏌️ 高爾夫一對多比分系統（手動輸入 + 讓桿 + 賭金計算）")

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

    # ========== 快速輸入18洞桿數 ==========
    st.header("3️⃣ 快速輸入每位球員的18洞桿數（最多18碼）")
    scores = {}

    for p in selected_players:
        raw = st.text_input(f"{p} 的18洞桿數（請輸入 18 個數字）", max_chars=18, key=f"{p}_input")
        current_len = len(raw)
        st.caption(f"⛳ {p} 已輸入：{current_len} / 18 碼")
        if current_len > 0 and raw.isdigit():
            scores[p] = [int(x) for x in raw]
        else:
            scores[p] = []

    # ========== 指定主角 ==========
    st.header("4️⃣ 選擇主要選手")
    main_player = st.selectbox("指定主要選手", selected_players)

    if st.button("✅ 計算對戰結果與賭金"):
        if all(len(s) == 18 for s in scores.values()):
            st.success(f"🎯 {main_player} 對戰結果如下：")
            results = []

            main_handicap = player_info[main_player]["hcp"]
            main_score = scores[main_player]

            for opp in selected_players:
                if opp == main_player:
                    continue

                opp_handicap = player_info[opp]["hcp"]
                opp_score = scores[opp]
                opp_bet = player_info[opp]["bet"]

                # 計算讓桿差與讓桿洞
                h_diff = opp_handicap - main_handicap
                if h_diff > 0:
                    hcp_df = pd.DataFrame({"idx": range(18), "hcp": full_hcp})
                    give_holes = hcp_df.sort_values("hcp").head(h_diff)["idx"].tolist()
                else:
                    give_holes = []

                # 調整對手分數
                adjusted_opp = opp_score.copy()
                for i in give_holes:
                    adjusted_opp[i] -= 1

                # 勝負計算
                win, lose, tie = 0, 0, 0
                for m, o in zip(main_score, adjusted_opp):
                    if m < o:
                        win += 1
                    elif m > o:
                        lose += 1
                    else:
                        tie += 1

                net = win - lose
                bet_result = net * opp_bet

                results.append({
                    "對手": opp,
                    "勝": win,
                    "負": lose,
                    "平": tie,
                    "賭金結果": bet_result
                })

            df_result = pd.DataFrame(results)
            st.dataframe(df_result, use_container_width=True)
        else:
            st.error("請確認每位球員皆已正確輸入 18 碼桿數")
