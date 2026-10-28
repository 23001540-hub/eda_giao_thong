# eda_03_quan_he.py
# Mục đích: phân tích theo THỜI GIAN trong train:
#   số dòng theo ngày / khung giờ / thứ, và LOS thay đổi thế nào theo thời gian.
# Điểm mới so với bản cũ: tìm nguyên nhân của hai khung giờ 0:00 và 23:30 bất thường,
# so sánh kết quả "có" và "không có" những ngày đột biến, và che các ô quá ít dữ liệu.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import LOS_ORDER, load, save_fig

train = load("train")
train["dt"] = pd.to_datetime(train["date"])
train["hour"] = train["period"].str.split("_").str[1].astype(int)
train["los_num"] = train["LOS"].map({c: i for i, c in enumerate(LOS_ORDER)})  # A=0 ... F=5

TEN_THU = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]  # weekday 0 = Thứ Hai ... 6 = Chủ Nhật
# Đủ 48 khung giờ theo đúng thứ tự trong ngày (để khung nào thiếu vẫn hiện, với giá trị 0)
KHUNG_DU = [f"period_{h}_{m:02d}" for h in range(24) for m in (0, 30)]
NHAN_KHUNG = [p.replace("period_", "").replace("_", ":") for p in KHUNG_DU]  # "0:00", "0:30", ...
MIN_N = 30  # ô có ít hơn 30 dòng thì coi là không đủ tin cậy

# ---------- 1. Số dòng theo ngày ----------
# Mục đích: xem dữ liệu có dàn đều theo ngày không
per_day = train["date"].value_counts()
top2 = per_day.head(2).index.tolist()  # 2 ngày nhiều dòng nhất
train["nhom"] = np.where(train["date"].isin(top2), "2 ngày đột biến", "Các ngày còn lại")
rest = train[train["nhom"] == "Các ngày còn lại"]

print("=== 1. SỐ DÒNG THEO NGÀY ===")
print(f"Số ngày khác nhau: {len(per_day)}; trung vị số dòng mỗi ngày: {per_day.median():.0f}")
print("5 ngày nhiều dòng nhất:")
print(per_day.head(5).to_string())
print(f"2 ngày nhiều nhất {top2} chiếm {per_day.head(2).sum() / len(train) * 100:.1f}% tổng số dòng")
print("Số đoạn đường khác nhau và thứ trong tuần của 2 ngày này:")
print(train[train["date"].isin(top2)].groupby("date").agg(
    so_dong=("_id", "size"), so_doan=("segment_id", "nunique"), weekday=("weekday", "first")).to_string())
print("Số dòng theo tháng:")
print(train.groupby(train["dt"].dt.to_period("M")).size().to_string())
print()

daily = per_day.sort_index()
daily.index = pd.to_datetime(daily.index)
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(daily.index, daily.values, ".", markersize=6)
for i, d in enumerate(top2):
    ax.annotate(d, (pd.to_datetime(d), per_day[d]), textcoords="offset points",
                xytext=(8, -4 - 12 * i))
ax.set_title("Số dòng train theo ngày")
ax.set_xlabel("Ngày")
ax.set_ylabel("Số dòng")
save_fig("03_ngay.png")

# ---------- 2. Số dòng theo khung giờ ----------
# Mục đích: hai khung 0:00 và 23:30 cao bất thường là do đâu?
is_spike = train["period"].isin(["period_0_00", "period_23_30"])
spike_top2 = is_spike & (train["nhom"] == "2 ngày đột biến")
print("=== 2. SỐ DÒNG THEO KHUNG GIỜ ===")
print(f"Hai khung 0:00 và 23:30 chiếm {is_spike.mean() * 100:.1f}% số dòng ({is_spike.sum():,} dòng)")
print(f"  trong đó đến từ 2 ngày đột biến: {spike_top2.sum():,}/{is_spike.sum():,} dòng")
print(f"  số dòng của hai khung này ở các ngày còn lại: {(is_spike & (train['nhom'] == 'Các ngày còn lại')).sum():,}")
print()

bang = pd.crosstab(train["period"], train["nhom"]).reindex(KHUNG_DU).fillna(0)
ax = bang.plot(kind="bar", stacked=True, figsize=(14, 4), width=0.85)
ax.set_xticklabels(NHAN_KHUNG, rotation=90)
ax.set_title("Số dòng theo khung giờ (tách 2 ngày đột biến)")
ax.set_xlabel("Khung giờ (khung không có cột = không có dòng nào)")
ax.set_ylabel("Số dòng")
ax.legend(title="")
save_fig("03_period.png")

# ---------- 3. LOS: có và không có 2 ngày đột biến ----------
cmp = pd.DataFrame({
    "Tất cả": train["LOS"].value_counts(normalize=True),
    "2 ngày đột biến": train[train["nhom"] == "2 ngày đột biến"]["LOS"].value_counts(normalize=True),
    "Các ngày còn lại": rest["LOS"].value_counts(normalize=True),
}).reindex(LOS_ORDER) * 100
print("=== 3. TỈ LỆ LOS (%) ===")
print(cmp.round(1).to_string())
print()

# ---------- 4. LOS theo thứ trong tuần ----------
cnt_wd = pd.DataFrame({
    "Tất cả": train["weekday"].value_counts().sort_index(),
    "Các ngày còn lại": rest["weekday"].value_counts().sort_index(),
})
cnt_wd.index = TEN_THU
print("=== 4. SỐ DÒNG THEO THỨ ===")
print(cnt_wd.to_string())
print()

fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
for ax, (tieu_de, d) in zip(axes, [("Tất cả dữ liệu", train), ("Bỏ 2 ngày đột biến", rest)]):
    ct = (pd.crosstab(d["weekday"], d["LOS"], normalize="index")
          .reindex(index=range(7), columns=LOS_ORDER).fillna(0) * 100)
    n = d["weekday"].value_counts().reindex(range(7)).fillna(0).astype(int)
    ct.plot(kind="bar", stacked=True, colormap="RdYlGn_r", ax=ax, legend=False)
    ax.set_xticklabels([f"{TEN_THU[i]}\nn={n[i]:,}" for i in range(7)], rotation=0)
    ax.set_title(tieu_de)
    ax.set_xlabel("Thứ (n = số dòng)")
axes[0].set_ylabel("Tỉ lệ LOS (%)")
axes[1].legend(title="LOS", bbox_to_anchor=(1.02, 1), loc="upper left")
save_fig("03_los_theo_thu.png")

# ---------- 5. LOS theo khung giờ (bỏ 2 ngày đột biến, che ô ít dữ liệu) ----------
ct = pd.crosstab(rest["LOS"], rest["period"], normalize="columns") * 100
ct = ct.reindex(index=LOS_ORDER, columns=KHUNG_DU)
n_per = rest["period"].value_counts().reindex(KHUNG_DU).fillna(0)
mask = np.tile((n_per < MIN_N).values, (len(LOS_ORDER), 1))
print("=== 5. KHUNG GIỜ ĐỦ DỮ LIỆU (bỏ 2 ngày đột biến) ===")
print(f"Số khung giờ có từ {MIN_N} dòng trở lên: {int((n_per >= MIN_N).sum())}/48")
print("Các khung bị che (ít hơn 30 dòng): " + ", ".join(
    f"{NHAN_KHUNG[i]} (n={int(n_per.iloc[i])})" for i in range(48) if n_per.iloc[i] < MIN_N))
print()

plt.figure(figsize=(16, 4))
sns.heatmap(ct, mask=mask, cmap="YlOrRd", vmin=0, vmax=100,
            xticklabels=NHAN_KHUNG, cbar_kws={"label": "Tỉ lệ (%)"})
plt.title(f"Tỉ lệ LOS theo khung giờ (bỏ 2 ngày đột biến; ô trống = dưới {MIN_N} dòng)")
plt.xlabel("Khung giờ")
plt.ylabel("LOS")
save_fig("03_los_theo_gio.png")

# ---------- 6. LOS trung bình theo thứ x giờ ----------
piv = rest.pivot_table(index="weekday", columns="hour", values="los_num", aggfunc="mean")
cnt = rest.pivot_table(index="weekday", columns="hour", values="los_num", aggfunc="count")
piv = piv.reindex(index=range(7), columns=range(24))
cnt = cnt.reindex(index=range(7), columns=range(24))
piv = piv.where(cnt >= MIN_N)  # che ô ít dữ liệu
piv.index = TEN_THU
print("=== 6. LOS TRUNG BÌNH THEO THỨ x GIỜ ===")
print(f"Số ô (thứ x giờ) có từ {MIN_N} dòng trở lên: {int((cnt >= MIN_N).sum().sum())}/168")

plt.figure(figsize=(13, 4))
sns.heatmap(piv, cmap="RdYlGn_r", vmin=0, vmax=5,
            cbar_kws={"label": "LOS trung bình (A = 0 ... F = 5)"})
plt.title("LOS trung bình theo thứ và giờ (bỏ 2 ngày đột biến; ô trống = dưới 30 dòng)")
plt.xlabel("Giờ trong ngày")
plt.ylabel("")
save_fig("03_los_trung_binh.png")