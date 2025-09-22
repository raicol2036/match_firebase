import streamlit as st
import pandas as pd
import io

st.title("🏌️ 球隊成績管理系統 (快速輸入版)")

# === 安全讀取 CSV ===
def read_csv_safe(file):
    encodings = ["utf-8-sig", "utf-8", "big5", "cp950"]
    for enc in encodings:
        try:
            return pd.read_csv(file, encoding=enc)
        except Exception:
            file.seek(0)
            continue
    st.error("❌ 無法讀取檔案，請確認格式與編碼")
    return pd.DataFrame()

# === 上傳 CSV ===
st.header("1. 上傳資料檔案")
player_file = st.file_uploader("📂 上傳球員資料 (players.csv)", type=["csv"])
course_file = st.file_uploader("📂 上傳球場資料 (course.csv)", type=["csv"])

if player_file and course_file:
    players = read_csv_safe(player_file)
    courses = read_csv_safe(course_file)

    # 驗證欄位
    if not set(["name","handicap","champion","runnerup"]).issubset(players.columns):
        st.error("❌ players.csv 欄位必須包含: name, handicap, champion, runnerup")
        st.stop()
    if not set(["course_name","area","hole","hcp","par"]).issubset(courses.columns):
        st.error("❌ course.csv 欄位必須包含: course_name, area, hole, hcp, par")
        st.stop()

    st.success("✅ 檔案載入成功！")

    # === 設定比賽人數 ===
    st.header("2. 設定比賽人數")
    num_players = st.number_input("請輸入參賽人數 (1~24)", min_value=1, max_value=24, value=4, step=1)

    # === 選擇球員並輸入成績 ===
    st.header("3. 輸入比賽成績 (18位數字，依序代表1~18洞桿數)")
    scores = {}
    selected_players = []

    for i in range(num_players):
        st.subheader(f"球員 {i+1}")
        player_name = st.selectbox(f"選擇球員 {i+1}", players["name"].values, key=f"player_{i}")
        selected_players.append(player_name)

        score_str = st.text_input(f"{player_name} 的成績 (18位數字)", key=f"scores_{i}")
        if score_str and score_str.isdigit() and len(score_str) == 18:
            scores[player_name] = [int(x) for x in score_str]
        else:
            scores[player_name] = []

    # === 計算函式 ===
    def calculate_gross(scores):
        return {p: sum(s) for p, s in scores.items() if s}

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
                if i < len(courses):
                    par = courses.iloc[i]["par"]
                    if score == par - 1:
                        birdies.append((p, i+1))
        return birdies

    def get_winners(scores):
        gross = calculate_gross(scores)
        net = calculate_net(gross)

        # === 總桿排序 ===
        gross_sorted = sorted(gross.items(), key=lambda x: x[1])

        # 總桿冠軍：排除曾經得過冠軍
        gross_champ = None
        for p, _ in gross_sorted:
            if players.loc[players["name"]==p,"champion"].values[0] == "No":
                gross_champ = p
                break

    # 總桿亞軍：排除曾經得過亞軍
        gross_runner = None
        for p, _ in gross_sorted:
            if p != gross_champ and players.loc[players["name"]==p,"runnerup"].values[0] == "No":
                gross_runner = p
                break

    # === 淨桿冠亞軍 (排除總桿前兩名) ===
        exclude_players = [gross_champ, gross_runner]
        net_candidates = {p:s for p,s in net.items() if p not in exclude_players}
        net_sorted = sorted(net_candidates.items(), key=lambda x: x[1])

        net_champ, net_runner = None, None
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

    # === 開始計算 ===
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

        # Leaderboard
            st.subheader("📊 Leaderboard 排名表")
            df_leader = pd.DataFrame({
                "球員": list(winners["gross"].keys()),
                "總桿": list(winners["gross"].values()),
                "淨桿": [winners["net"][p] for p in winners["gross"].keys()]
            })
            df_leader["總桿排名"] = df_leader["總桿"].rank(method="min").astype(int)
            df_leader["淨桿排名"] = df_leader["淨桿"].rank(method="min").astype(int)
            st.dataframe(df_leader.sort_values("淨桿排名"))

        # 匯出功能
            st.subheader("💾 匯出比賽結果")
            csv_buffer = io.StringIO()
            df_leader.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
            st.download_button("📥 下載 CSV", data=csv_buffer.getvalue(),
                               file_name="leaderboard.csv", mime="text/csv")

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df_leader.to_excel(writer, sheet_name="Leaderboard", index=False)
            st.download_button("📥 下載 Excel", data=excel_buffer.getvalue(),
                               file_name="leaderboard.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

