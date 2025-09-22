import streamlit as st
import pandas as pd

st.title("🏌️ 球隊成績管理系統")

# === 1. 上傳 CSV (只需一次) ===
st.header("1. 上傳資料檔案")

def read_csv_safe(file):
    encodings = ["utf-8-sig", "utf-8", "big5", "cp950"]
    for enc in encodings:
        try:
            return pd.read_csv(file, encoding=enc)
        except Exception:
            file.seek(0)  # 重設檔案指標
            continue
    st.error("❌ 無法讀取檔案，請確認格式與編碼")
    return pd.DataFrame()

# 初始化 session_state
if "players" not in st.session_state:
    st.session_state["players"] = None
if "courses" not in st.session_state:
    st.session_state["courses"] = None

# 檔案上傳
player_file = st.file_uploader("📂 上傳球員資料 (players.csv)", type=["csv"])
course_file = st.file_uploader("📂 上傳球場資料 (course.csv)", type=["csv"])

if player_file is not None:
    st.session_state["players"] = read_csv_safe(player_file)
if course_file is not None:
    st.session_state["courses"] = read_csv_safe(course_file)

players = st.session_state["players"]
courses = st.session_state["courses"]

if players is not None and courses is not None:
    # === 確認欄位正確 ===
    if not set(["name","handicap","champion","runnerup"]).issubset(players.columns):
        st.error("❌ players.csv 欄位必須包含: name, handicap, champion, runnerup")
        st.stop()
    if not set(["course_name","area","hole","hcp","par"]).issubset(courses.columns):
        st.error("❌ course.csv 欄位必須包含: course_name, area, hole, hcp, par")
        st.stop()

    st.success("✅ 檔案載入成功！(已暫存，不需再次上傳)")

    # === 2. 選擇參賽球員 ===
    st.header("2. 選擇參賽球員")
    player_options = list(players["name"].values)
    selected_players = st.multiselect("選擇球員 (最多24名)", player_options, max_selections=24)

    # === 3. 輸入成績 ===
    st.header("3. 輸入成績 (最多18洞)")
    scores = {}
    if selected_players:
        for p in selected_players:
            scores[p] = []
            st.subheader(f"球員：{p}")
            cols = st.columns(9)  # 前九
            for i in range(9):
                val = cols[i].number_input(f"H{i+1}", min_value=1, max_value=15, step=1, key=f"{p}_f{i+1}")
                scores[p].append(val)
            cols2 = st.columns(9)  # 後九
            for i in range(9):
                val = cols2[i].number_input(f"H{i+10}", min_value=1, max_value=15, step=1, key=f"{p}_b{i+10}")
                scores[p].append(val)

# === 下面的計算 & Leaderboard 保持不變 ===


# 計算邏輯
def calculate_gross(scores):
    return {p: sum(s) for p, s in scores.items()}

def calculate_net(gross_scores):
    net_scores = {}
    for p, gross in gross_scores.items():
        hcp = int(players.loc[players["name"] == p, "handicap"].values[0])
        net_scores[p] = gross - hcp
    return net_scores

def find_birdies(scores):
    birdies = []
    for p, s in scores.items():
        for i, score in enumerate(s):
            if i < len(courses):  # 避免洞數不足
                par = courses.iloc[i]["par"]
                if score == par - 1:
                    birdies.append((p, i+1))
    return birdies

def get_winners(scores):
    gross = calculate_gross(scores)
    net = calculate_net(gross)

    eligible_champ = {p: s for p, s in gross.items() if players.loc[players["name"]==p,"champion"].values[0] == "No"}
    eligible_runner = {p: s for p, s in gross.items() if players.loc[players["name"]==p,"runnerup"].values[0] == "No"}

    gross_champ = min(eligible_champ, key=eligible_champ.get, default=None)
    gross_runner = min(eligible_runner, key=eligible_runner.get, default=None)

    net_sorted = sorted(net.items(), key=lambda x: x[1])
    net_champ, net_runner = (None, None)
    if len(net_sorted) > 0: net_champ = net_sorted[0][0]
    if len(net_sorted) > 1: net_runner = net_sorted[1][0]

    # 更新 handicap
    if net_champ:
        players.loc[players["name"]==net_champ,"handicap"] -= 2
    if net_runner:
        players.loc[players["name"]==net_runner,"handicap"] -= 1

    birdies = find_birdies(scores)

    return {
        "gross": gross,
        "net": net,
        "gross_champion": gross_champ,
        "gross_runnerup": gross_runner,
        "net_champion": net_champ,
        "net_runnerup": net_runner,
        "birdies": birdies
    }

# 開始計算
if st.button("開始計算"):
    if not selected_players:
        st.warning("⚠️ 請先選擇球員並輸入成績")
    else:
        winners = get_winners(scores)

        st.subheader("🏆 比賽結果")
        st.write(f"總桿冠軍: {winners['gross_champion']}")
        st.write(f"總桿亞軍: {winners['gross_runnerup']}")
        st.write(f"淨桿冠軍: {winners['net_champion']}")
        st.write(f"淨桿亞軍: {winners['net_runnerup']}")

        if winners["birdies"]:
            st.write("✨ Birdie 紀錄：")
            for player, hole in winners["birdies"]:
                st.write(f"- {player} 在第 {hole} 洞")
        else:
            st.write("無 Birdie 紀錄")

        # === Leaderboard 排名表 ===
        st.subheader("📊 Leaderboard 排名表")
        df_leader = pd.DataFrame({
            "球員": list(winners["gross"].keys()),
            "總桿": list(winners["gross"].values()),
            "淨桿": [winners["net"][p] for p in winners["gross"].keys()]
        })
        df_leader["總桿排名"] = df_leader["總桿"].rank(method="min").astype(int)
        df_leader["淨桿排名"] = df_leader["淨桿"].rank(method="min").astype(int)
        st.dataframe(df_leader.sort_values("淨桿排名"))

        # === 匯出功能 ===
        st.subheader("💾 匯出比賽結果")

        # 匯出 CSV
        csv_buffer = io.StringIO()
        df_leader.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 下載 CSV",
            data=csv_buffer.getvalue(),
            file_name="leaderboard.csv",
            mime="text/csv"
        )

        # 匯出 Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df_leader.to_excel(writer, sheet_name="Leaderboard", index=False)
        st.download_button(
            label="📥 下載 Excel",
            data=excel_buffer.getvalue(),
            file_name="leaderboard.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        st.info("📥 請先上傳 players.csv 與 course.csv")
