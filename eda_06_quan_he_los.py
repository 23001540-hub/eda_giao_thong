# eda_06_quan_he_los.py
# Mục đích: tìm mối liên hệ giữa segment_status (vận tốc đo được) và train (nhãn LOS):
#   1. train.date / train.period tính theo múi giờ nào? (thử ghép với nhiều độ lệch giờ)
#   2. train có phải là segment_status gộp theo từng (đoạn, ngày, khung 30 phút) không?
#   3. vận tốc trung bình của từng khung liên quan thế nào đến LOS?
#   4. tỉ lệ velocity = 1 theo tháng

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import LOS_ORDER, load, save_fig

train = load("train")
status = load("segment_status")

ts_utc = pd.to_datetime(status["updated_at"], utc=True).dt.tz_localize(None)  # giờ UTC
train["key"] = train["segment_id"].astype(str) + "|" + train["date"] + "|" + train["period"]


def tao_khoa(lech_gio):
    """Tạo khóa 'segment_id|date|period' cho từng dòng segment_status:
    dịch thời gian đi `lech_gio` giờ rồi làm tròn xuống mốc 30 phút (ví dụ 23:47 -> 23:30)."""
    t = (ts_utc + pd.Timedelta(hours=lech_gio)).dt.floor("30min")
    period = "period_" + t.dt.hour.astype(str) + "_" + t.dt.minute.map(lambda m: f"{m:02d}")
    return status["segment_id"].astype(str) + "|" + t.dt.strftime("%Y-%m-%d") + "|" + period


# ---------- 1. Thử các độ lệch giờ ----------
# Với mỗi độ lệch, tính % dòng train có ít nhất 1 dòng segment_status trùng (đoạn, ngày, khung giờ)
print("=== 1. ĐỘ LỆCH GIỜ GIỮA updated_at VÀ train.period ===")
ket_qua = {}
for lech in range(-12, 13):
    ket_qua[lech] = train["key"].isin(set(tao_khoa(lech))).mean() * 100
kq = pd.Series(ket_qua)
print("Lệch (giờ) -> % dòng train có dòng segment_status trùng khóa:")
print(kq.round(1).to_string())
print(f"Độ lệch khớp nhất: {kq.idxmax()} giờ ({kq.max():.1f}%)")
print()

fig, ax = plt.subplots(figsize=(10, 4))
mau = ["crimson" if v == kq.idxmax() else "steelblue" for v in kq.index]
ax.bar(kq.index, kq.values, color=mau)
ax.set_title("Dịch updated_at bao nhiêu giờ thì khớp với train.date / train.period?")
ax.set_xlabel("Độ lệch giờ so với UTC (0 = giữ nguyên giờ UTC)")
ax.set_ylabel("% dòng train khớp")
ax.set_xticks(range(-12, 13, 2))
save_fig("06_khop_mui_gio.png")

# ---------- 2. train có phải là segment_status gộp theo khung 30 phút? ----------
khoa0 = tao_khoa(0)  # lệch 0 giờ = giữ nguyên UTC
print("=== 2. CẤU TRÚC GỘP ===")
print(f"Số khóa (đoạn, ngày, khung) duy nhất trong segment_status: {khoa0.nunique():,}")
print(f"Số dòng train: {len(train):,}")
print(f"Khóa của train có trong segment_status: {train['key'].isin(set(khoa0)).mean() * 100:.1f}%")
print(f"Khóa của segment_status có trong train: {khoa0.isin(set(train['key'])).mean() * 100:.1f}%")
print()

# ---------- 3. Vận tốc trung bình của khung và LOS ----------
status["key"] = khoa0
agg = status.groupby("key")["velocity"].agg(v_mean="mean", v_median="median", n_doc="size")
m = train.merge(agg, left_on="key", right_index=True, how="left")
print("=== 3. VẬN TỐC TRUNG BÌNH CỦA KHUNG THEO LOS ===")
print(m.groupby("LOS")["v_mean"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
      .reindex(LOS_ORDER).round(1).to_string())
print()
print("Số bản ghi segment_status trong mỗi khung, theo LOS:")
print(m.groupby("LOS")["n_doc"].describe().reindex(LOS_ORDER).round(1).to_string())
print()

# Thử nghiệm minh hoạ (KHÔNG phải mô hình): chỉ dùng v_mean và ngưỡng nằm giữa các trung vị liền kề
med = m.groupby("LOS")["v_mean"].median().reindex(LOS_ORDER).values
nguong = (med[:-1] + med[1:]) / 2
chi_so = np.searchsorted(-nguong, -m["v_mean"].values, side="left")
du_doan = np.array(LOS_ORDER)[chi_so]
print("Trung vị v_mean của A..F:", med.round(1), "-> ngưỡng:", nguong.round(1))
print(f"Chỉ dùng v_mean + ngưỡng đơn giản, đoán đúng LOS ở {(du_doan == m['LOS'].values).mean() * 100:.1f}% số dòng")
print("Bảng đối chiếu (hàng = LOS thật, cột = LOS đoán):")
print(pd.crosstab(m["LOS"], pd.Series(du_doan, index=m.index, name="đoán")).to_string())
print()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(data=m, x="LOS", y="v_mean", order=LOS_ORDER, showfliers=False,
            palette="RdYlGn_r", hue="LOS", legend=False, ax=axes[0])
axes[0].set_title("Vận tốc trung bình của khung theo LOS")
axes[0].set_xlabel("LOS")
axes[0].set_ylabel("Vận tốc trung bình (v_mean)")
sns.boxplot(data=m, x="LOS", y="n_doc", order=LOS_ORDER, showfliers=False,
            palette="RdYlGn_r", hue="LOS", legend=False, ax=axes[1])
axes[1].set_title("Số bản ghi segment_status trong khung theo LOS")
axes[1].set_xlabel("LOS")
axes[1].set_ylabel("Số bản ghi trong khung")
save_fig("06_van_toc_theo_los.png")

# ---------- 4. Tỉ lệ velocity = 1 theo tháng ----------
print("=== 4. TỈ LỆ velocity = 1 THEO THÁNG (theo UTC) ===")
t4 = status.assign(mot=status["velocity"] == 1, thang=ts_utc.dt.strftime("%Y-%m")).groupby("thang")["mot"].agg(
    ["mean", "size"])
t4["mean"] = (t4["mean"] * 100).round(1)
t4.columns = ["ti_le_%", "so_ban_ghi"]
print(t4.to_string())