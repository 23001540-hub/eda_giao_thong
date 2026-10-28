# eda_03_quan_he.py
# Mục đích: xem LOS thay đổi thế nào theo thứ trong tuần và theo khung giờ

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = "data"
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)
sns.set_theme(style="whitegrid")

train = pd.read_csv(f"{DATA_DIR}/train.csv")
los_order = sorted(train["LOS"].unique())

# ---------- Biểu đồ 5: tỉ lệ LOS theo thứ trong tuần ----------
# weekday: 0 = Thứ Hai ... 6 = Chủ Nhật (đã đối chiếu với cột date)
# normalize="index": mỗi cột cộng lại = 100%, để so sánh công bằng giữa các thứ
ct_wd = pd.crosstab(train["weekday"], train["LOS"], normalize="index")[los_order] * 100
ct_wd.index = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

ct_wd.plot(kind="bar", stacked=True, figsize=(8, 5), colormap="RdYlGn_r")
plt.title("Tỉ lệ LOS theo thứ trong tuần (%)")
plt.xlabel("Thứ")
plt.ylabel("Tỉ lệ (%)")
plt.xticks(rotation=0)
plt.legend(title="LOS", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/05_los_theo_thu.png", dpi=120)
plt.close()

# ---------- Biểu đồ 6: heatmap LOS theo khung giờ ----------
# Mỗi cột là một khung giờ, màu càng đậm = tỉ lệ LOS đó càng cao
def period_to_minutes(p):
    _, h, m = p.split("_")
    return int(h) * 60 + int(m)

order_period = sorted(train["period"].unique(), key=period_to_minutes)
ct_pd = pd.crosstab(train["LOS"], train["period"], normalize="columns") * 100
ct_pd = ct_pd.reindex(index=los_order, columns=order_period)

plt.figure(figsize=(16, 4))
sns.heatmap(ct_pd, cmap="YlOrRd", cbar_kws={"label": "Tỉ lệ (%)"})
plt.title("Tỉ lệ LOS theo khung giờ (mỗi cột cộng lại = 100%)")
plt.xlabel("Khung giờ")
plt.ylabel("LOS")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/06_los_theo_gio.png", dpi=120)
plt.close()

# ---------- In số liệu để kiểm tra 2 khung giờ bất thường ----------
spike = train["period"].isin(["period_0_00", "period_23_30"])
print("Tỉ lệ LOS (%) ở 2 khung giờ 0:00 và 23:30:")
print((train.loc[spike, "LOS"].value_counts(normalize=True).sort_index() * 100).round(2).to_string())
print()
print("Tỉ lệ LOS (%) ở các khung giờ còn lại:")
print((train.loc[~spike, "LOS"].value_counts(normalize=True).sort_index() * 100).round(2).to_string())
print()
print("Khoảng ngày của train:", train["date"].min(), "->", train["date"].max())
print("Số ngày khác nhau:", train["date"].nunique())
print()
print("Số dòng theo thứ (0 = T2 ... 6 = CN):")
print(train["weekday"].value_counts().sort_index().to_string())
print()
print("Đã lưu 2 biểu đồ vào thư mục figures/")