# eda_07_quan_he_duong_gio.py
# Mục đích: tìm hiểu LOS liên quan thế nào đến:
#   A. giá trị velocity = 1 (giá trị lạ ở cột mốc 5)
#   B. đặc điểm đường: cấp đường, loại đường, độ dài
#   C. thời gian theo GIỜ VIỆT NAM (train.date / period là giờ UTC nên cộng 7 giờ)
# Các phần B và C bỏ 2 ngày đột biến (02-03/08/2020) vì phân bố LOS của chúng khác hẳn.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import LOS_ORDER, load, save_fig

train = load("train")
status = load("segment_status")
train["los_num"] = train["LOS"].map({c: i for i, c in enumerate(LOS_ORDER)})  # A=0 ... F=5
train["key"] = train["segment_id"].astype(str) + "|" + train["date"] + "|" + train["period"]

TEN_THU = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
MIN_N = 30  # ô có ít hơn 30 dòng thì coi là không đủ tin cậy

# ================= A. velocity = 1 và LOS =================
# Gán cho mỗi dòng segment_status khóa (đoạn, ngày, khung 30 phút UTC) rồi ghép với LOS của train
t = pd.to_datetime(status["updated_at"], utc=True).dt.tz_localize(None).dt.floor("30min")
status["key"] = (status["segment_id"].astype(str) + "|" + t.dt.strftime("%Y-%m-%d")
                 + "|period_" + t.dt.hour.astype(str) + "_" + t.dt.minute.map(lambda m: f"{m:02d}"))
s = status.merge(train[["key", "LOS"]], on="key", how="left")
s["mot"] = s["velocity"] == 1
s["n_khung"] = s.groupby("key")["velocity"].transform("size")  # số bản ghi trong cùng khung
s["nhom_n"] = pd.cut(s["n_khung"], [0, 1, 2, 5, 10, 50, 5000],
                     labels=["1", "2", "3-5", "6-10", "11-50", ">50"])

los_mot = (s.groupby("LOS")["mot"].mean() * 100).reindex(LOS_ORDER)
phan_bo_mot = (s[s["mot"]]["LOS"].value_counts(normalize=True) * 100).reindex(LOS_ORDER).fillna(0)
theo_n = s.groupby("nhom_n", observed=True)["mot"].agg(["mean", "size"])
theo_n["mean"] = theo_n["mean"] * 100

print("=== A. velocity = 1 VÀ LOS ===")
print("% dòng có velocity = 1, theo LOS của khung chứa nó:")
print(los_mot.round(1).to_string())
print("Các dòng velocity = 1 nằm ở LOS nào (% của tất cả dòng velocity = 1):")
print(phan_bo_mot.round(1).to_string())
print("% dòng velocity = 1 theo số bản ghi trong cùng khung:")
print(theo_n.rename(columns={"mean": "ti_le_%", "size": "so_dong"}).round(1).to_string())
print()

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
bars = axes[0].bar(LOS_ORDER, los_mot.values, color=sns.color_palette("RdYlGn_r", 6))
axes[0].bar_label(bars, fmt="%.1f%%")
axes[0].set_title("% dòng velocity = 1 theo LOS của khung")
axes[0].set_xlabel("LOS")
axes[0].set_ylabel("Tỉ lệ (%)")
bars = axes[1].bar(theo_n.index.astype(str), theo_n["mean"].values)
axes[1].bar_label(bars, fmt="%.1f%%")
axes[1].set_title("% dòng velocity = 1 theo số bản ghi trong cùng khung")
axes[1].set_xlabel("Số bản ghi trong khung")
axes[1].set_ylabel("Tỉ lệ (%)")
save_fig("07_velocity_bang_1_theo_los.png")

# ================= Chuẩn bị cho B và C: bỏ 2 ngày đột biến =================
top2 = train["date"].value_counts().head(2).index.tolist()
rest = train[~train["date"].isin(top2)].copy()
print(f"Bỏ 2 ngày đột biến {top2}: còn {len(rest):,}/{len(train):,} dòng")
print()


def ti_le_los(d, cot):
    """Tỉ lệ % mỗi mức LOS trong từng giá trị của cột `cot`."""
    return pd.crosstab(d[cot], d["LOS"], normalize="index").reindex(columns=LOS_ORDER).fillna(0) * 100


# ================= B. LOS theo đặc điểm đường =================
rest["nhom_dai"] = pd.cut(rest["length"], [-1, 10, 25, 50, 100, 200, 5000],
                          labels=["0-10", "11-25", "26-50", "51-100", "101-200", ">200"])
loai = rest["street_type"].value_counts()
loai_chinh = loai[loai >= 300].index.tolist()  # chỉ lấy loại đường có từ 300 dòng

print("=== B. LOS THEO ĐẶC ĐIỂM ĐƯỜNG (bỏ 2 ngày đột biến) ===")
print("Tỉ lệ LOS (%) theo street_level:")
print(ti_le_los(rest, "street_level").round(1).to_string())
print("Tỉ lệ LOS (%) theo street_type (loại có >= 300 dòng):")
print(ti_le_los(rest[rest["street_type"].isin(loai_chinh)], "street_type").loc[loai_chinh].round(1).to_string())
theo_dai = rest.groupby("nhom_dai", observed=True)["los_num"].agg(["mean", "size"])
print("LOS trung bình (A=0 ... F=5) theo độ dài đoạn:")
print(theo_dai.rename(columns={"mean": "los_tb", "size": "so_dong"}).round(2).to_string())
print()

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for ax, (cot, d, tieu_de) in zip(axes[:2], [
        ("street_level", rest, "Tỉ lệ LOS theo cấp đường"),
        ("street_type", rest[rest["street_type"].isin(loai_chinh)], "Tỉ lệ LOS theo loại đường")]):
    ct = ti_le_los(d, cot)
    if cot == "street_type":
        ct = ct.loc[loai_chinh]
    n = d[cot].value_counts()
    ct.plot(kind="bar", stacked=True, colormap="RdYlGn_r", ax=ax, legend=False)
    ax.set_xticklabels([f"{i}\nn={n[i]:,}" for i in ct.index], rotation=0 if cot == "street_level" else 30)
    ax.set_title(tieu_de)
    ax.set_xlabel(cot)
    ax.set_ylabel("Tỉ lệ (%)")
axes[1].legend(title="LOS", bbox_to_anchor=(1.02, 1), loc="upper left")
bars = axes[2].bar(theo_dai.index.astype(str), theo_dai["mean"].values)
axes[2].bar_label(bars, labels=[f"n={n:,}" for n in theo_dai["size"]])
axes[2].set_title("LOS trung bình theo độ dài đoạn (A = 0 ... F = 5)")
axes[2].set_xlabel("length")
axes[2].set_ylabel("LOS trung bình")
axes[2].set_ylim(0, theo_dai["mean"].max() * 1.15)  # chừa chỗ cho nhãn n=
save_fig("07_los_theo_duong.png")

# ================= C. LOS theo giờ Việt Nam =================
# train.date + train.period là giờ UTC; cộng 7 giờ để ra giờ Việt Nam (có thể sang ngày hôm sau)
parts = rest["period"].str.split("_", expand=True)  # "period_23_30" -> ["period", "23", "30"]
phut_utc = parts[1].astype(int) * 60 + parts[2].astype(int)
dt_vn = pd.to_datetime(rest["date"]) + pd.to_timedelta(phut_utc, unit="m") + pd.Timedelta(hours=7)
rest["gio_vn"] = dt_vn.dt.hour
rest["thu_vn"] = dt_vn.dt.day_of_week  # 0 = Thứ Hai ... 6 = Chủ Nhật

n_gio = rest["gio_vn"].value_counts().reindex(range(24)).fillna(0).astype(int)
print("=== C. LOS THEO GIỜ VIỆT NAM (bỏ 2 ngày đột biến) ===")
print("Số dòng theo giờ VN (0-23):")
print(n_gio.to_string())
print("Giờ VN có ít hơn 30 dòng (bị che):", [h for h in range(24) if n_gio[h] < MIN_N])

ct_h = ti_le_los(rest, "gio_vn").reindex(range(24)).fillna(0)
ct_h.loc[n_gio < MIN_N] = 0  # che giờ ít dữ liệu
ax = ct_h.plot(kind="bar", stacked=True, colormap="RdYlGn_r", figsize=(13, 4.5), width=0.85)
ax.set_title("Tỉ lệ LOS theo giờ Việt Nam (giờ không có cột = dưới 30 dòng)")
ax.set_xlabel("Giờ Việt Nam")
ax.set_ylabel("Tỉ lệ (%)")
ax.legend(title="LOS", bbox_to_anchor=(1.01, 1), loc="upper left")
save_fig("07_los_theo_gio_vn.png")

piv = rest.pivot_table(index="thu_vn", columns="gio_vn", values="los_num", aggfunc="mean")
cnt = rest.pivot_table(index="thu_vn", columns="gio_vn", values="los_num", aggfunc="count")
piv = piv.reindex(index=range(7), columns=range(24))
cnt = cnt.reindex(index=range(7), columns=range(24))
piv = piv.where(cnt >= MIN_N)
piv.index = TEN_THU
print(f"Số ô (thứ x giờ VN) có từ {MIN_N} dòng trở lên: {int((cnt >= MIN_N).sum().sum())}/168")

plt.figure(figsize=(13, 4))
sns.heatmap(piv, cmap="RdYlGn_r", vmin=0, vmax=5, cbar_kws={"label": "LOS trung bình (A = 0 ... F = 5)"})
plt.title("LOS trung bình theo thứ và giờ Việt Nam (ô trống = dưới 30 dòng)")
plt.xlabel("Giờ Việt Nam")
plt.ylabel("")
save_fig("07_los_trung_binh_thu_gio_vn.png")