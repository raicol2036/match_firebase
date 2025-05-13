import pandas as pd
import numpy as np

# 初始化資料
players = ['A', 'B', 'C', 'D']
holes = list(range(1, 19))

# 初始化逐洞成績紀錄
scores_df = pd.DataFrame(index=holes, columns=players)
scores_df.fillna('', inplace=True)

# 初始化對戰結果紀錄
match_results_df = pd.DataFrame(index=players, columns=players)
match_results_df.fillna(0, inplace=True)

# 假設一些差點與賭金
handicaps = {'A': 0, 'B': 3, 'C': 5, 'D': 8}
bets = {i: 100 for i in range(1, 19)}

# 隨機生成成績
np.random.seed(42)
for player in players:
    scores_df[player] = np.random.randint(3, 6, size=18)

# 計算逐洞結果
for i in range(18):
    for p1 in players:
        for p2 in players:
            if p1 != p2:
                score1 = scores_df.loc[i + 1, p1]
                score2 = scores_df.loc[i + 1, p2]
                # 考慮差點
                adj_score1 = score1 - handicaps[p1]
                adj_score2 = score2 - handicaps[p2]
                # 勝負計算
                diff = adj_score1 - adj_score2
                match_results_df.loc[p1, p2] += diff * bets[i + 1]

import ace_tools as tools; tools.display_dataframe_to_user(name="逐洞成績", dataframe=scores_df)
tools.display_dataframe_to_user(name="對戰結算結果", dataframe=match_results_df)
# 增加比賽結果顯示：勝 / 平 / 負
match_summary_df = pd.DataFrame(index=players, columns=players)
match_summary_df.fillna('', inplace=True)

# 初始化比賽結果紀錄
match_result_counts = {p: {op: {'win': 0, 'draw': 0, 'lose': 0} for op in players} for p in players}

# 計算逐洞的勝平負結果
for hole in holes:
    for p1 in players:
        for p2 in players:
            if p1 != p2:
                score1 = scores_df.loc[hole, p1] - handicaps[p1]
                score2 = scores_df.loc[hole, p2] - handicaps[p2]

                if score1 < score2:
                    match_result_counts[p1][p2]['win'] += 1
                elif score1 > score2:
                    match_result_counts[p1][p2]['lose'] += 1
                else:
                    match_result_counts[p1][p2]['draw'] += 1

# 更新比賽結果顯示，增加賭金結算
match_summary_df = pd.DataFrame(index=players, columns=players)
match_summary_df.fillna('', inplace=True)

# 更新顯示：勝/平/負 + 金額結算
for p1 in players:
    for p2 in players:
        if p1 != p2:
            win = match_result_counts[p1][p2]['win']
            draw = match_result_counts[p1][p2]['draw']
            lose = match_result_counts[p1][p2]['lose']
            # 計算賭金結果：每洞 100 元
            total_amount = (win - lose) * 100
            # 格式化顯示
            if total_amount >= 0:
                match_summary_df.loc[p1, p2] = f"{win}/{draw}/{lose}  $ +{total_amount}"
            else:
                match_summary_df.loc[p1, p2] = f"{win}/{draw}/{lose}  $ {total_amount}"

import ace_tools as tools; tools.display_dataframe_to_user(name="比賽結果（含賭金結算）", dataframe=match_summary_df)
