# eda_05_segment_status.py
# Mục đích: tìm hiểu bảng segment_status (vận tốc đo được theo thời gian):
#   1. phân bố vận tốc, ngoại lai, giá trị 1 đặc biệt
#   2. ngày đột biến và phân bố theo giờ (so sánh giờ UTC và giờ Việt Nam)
#   3. vận tốc theo cấp đường / loại đường / giới hạn tốc độ
# Lưu ý: updated_at đang ở giờ UTC; giờ Việt Nam = UTC + 7.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import load, save_fig

status = load("segment_status")
seg = load("segments")[["_id", "street_level", "street_type", "max_velocity"]].rename(
    columns={"_id": "segment_id"})

# ---------- Chuẩn bị thời gian ----------
ts_utc = pd.to_datetime(status["updated_at"], utc=True).dt.tz_localize(None)  # giờ UTC
ts_vn = ts_utc + pd.Timedelta(hours=7)                                        # giờ Việt Nam
status["hour_utc"] = ts_utc.dt.hour
status["hour_vn"] = ts_vn.dt.hour
status["date_vn"] = ts_vn.dt.strftime("%Y-%m-%d")

df = status.merge(seg, on="segment_id", how="left")  # ghép thêm thông tin đường

# Ngày có nhiều bản ghi nhất (theo giờ VN) coi là "ngày đột biến"
event_date = df["date_vn"].value_counts().index[0]
df["nhom"] = np.where(df["date_vn"] == event_date, "Ngày đột biến", "Các ngày còn lại")
rest = df[df["nhom"] == "Các ngày còn lại"]

# ---------- 1. Vận tốc: phân vị, ngoại lai, giá trị đặc biệt ----------
print("=== 1. VẬN TỐC ===")
print("Các phân vị:")
print(df["velocity"].quantile([0.5, 0.9, 0.99, 0.999]).to_string())
print(f"Số dòng vận tốc > 80: {(df['velocity'] > 80).sum()}; > 100: {(df['velocity'] > 100).sum()}; "
      f"= 200: {(df['velocity'] == 200).sum()}")
print("10 giá trị vận tốc xuất hiện nhiều nhất:")
print(df["velocity"].value_counts().head(10).to_string())
print()

# ---------- 2. Ngày đột biến ----------
ev = df[df["nhom"] == "Ngày đột biến"]
print("=== 2. NGÀY ĐỘT BIẾN ===")
print(f"Ngày nhiều bản ghi nhất (giờ VN): {event_date}: {len(ev):,}/{len(df):,} bản ghi "
      f"({len(ev) / len(df) * 100:.1f}%), {ev['segment_id'].nunique():,} đoạn đường khác nhau")
print("Bản ghi của ngày này theo giờ VN:")
print(ev["hour_vn"].value_counts().sort_index().to_string())
print("Top 3 ngày nhiều bản ghi nhất theo giờ UTC (để đối chiếu):")
print(ts_utc.dt.strftime("%Y-%m-%d").value_counts().head(3).to_string())
print()
print(f"Tỉ lệ velocity = 1: ngày đột biến {(ev['velocity'] == 1).mean() * 100:.1f}%; "
      f"các ngày còn lại {(rest['velocity'] == 1).mean() * 100:.1f}%")
print("Tỉ lệ velocity = 1 (%) theo street_level (các ngày còn lại):")
share1 = rest.assign(mot=(rest["velocity"] == 1)).groupby("street_level")["mot"].mean() * 100
print(share1.round(1).to_string())
print()

# ---------- 3. Số bản ghi trên mỗi đoạn đường ----------
print("=== 3. SỐ BẢN GHI TRÊN MỖI ĐOẠN ===")
print(df["segment_id"].value_counts().describe().round(1).to_string())
print("5 đoạn nhiều bản ghi nhất:")
print(df["segment_id"].value_counts().head(5).to_string())
print()

# ---------- 4. Bản ghi theo giờ: UTC và Việt Nam ----------
h = pd.DataFrame({
    "UTC_tatca": df["hour_utc"].value_counts(),
    "VN_tatca": df["hour_vn"].value_counts(),
    "UTC_bo_dotbien": rest["hour_utc"].value_counts(),
    "VN_bo_dotbien": rest["hour_vn"].value_counts(),
}).reindex(range(24)).fillna(0).astype(int)
print("=== 4. SỐ BẢN GHI THEO GIỜ (0-23) ===")
print(h.to_string())
print()

# ---------- 5. Vận tốc theo loại đường (bỏ ngày đột biến) ----------
print("=== 5. VẬN TỐC THEO ĐƯỜNG (bỏ ngày đột biến) ===")
print("Theo street_level:")
print(rest.groupby("street_level")["velocity"].agg(["median", "mean", "size"]).round(1).to_string())
g = rest.groupby("street_type")["velocity"].agg(["median", "mean", "size"])
top_types = g[g["size"] > 500].sort_values("size", ascending=False)
print("Theo street_type (chỉ loại có > 500 dòng):")
print(top_types.round(1).to_string())
r = rest[rest["max_velocity"].notna()].copy()
r["ti_le"] = r["velocity"] / r["max_velocity"]
print(f"Số dòng có max_velocity: {len(r):,}; vận tốc vượt giới hạn: {(r['ti_le'] > 1).sum():,} "
      f"({(r['ti_le'] > 1).mean() * 100:.1f}%)")
print()

# ================= BIỂU ĐỒ =================

# --- Biểu đồ 1: số bản ghi theo ngày (trục y dạng log) ---
per_day = df["date_vn"].value_counts().sort_index()
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(pd.to_datetime(per_day.index), per_day.values, ".", markersize=6)
ax.set_yscale("log")
for i, d in enumerate(df["date_vn"].value_counts().head(3).index):
    ax.annotate(d, (pd.to_datetime(d), per_day[d]), textcoords="offset points", xytext=(8, -4 - 11 * i))
ax.set_title("Số bản ghi segment_status theo ngày (giờ VN, trục y dạng log)")
ax.set_xlabel("Ngày")
ax.set_ylabel("Số bản ghi (log)")
save_fig("05_ban_ghi_theo_ngay.png")

# --- Biểu đồ 2: số bản ghi theo giờ, so sánh UTC và VN ---
fig, axes = plt.subplots(1, 2, figsize=(15, 4))
for ax, (tieu_de, cols) in zip(axes, [("Tất cả", ["UTC_tatca", "VN_tatca"]),
                                       ("Bỏ ngày đột biến", ["UTC_bo_dotbien", "VN_bo_dotbien"])]):
    bang = h[cols].copy()
    bang.columns = ["Giờ UTC", "Giờ VN (UTC+7)"]
    bang.plot(kind="bar", ax=ax, width=0.85)
    ax.set_title(f"Số bản ghi theo giờ: {tieu_de}")
    ax.set_xlabel("Giờ trong ngày")
    ax.set_ylabel("Số bản ghi")
save_fig("05_ban_ghi_theo_gio.png")

# --- Biểu đồ 3: vận tốc theo cấp đường và loại đường ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
sns.boxplot(data=rest, x="street_level", y="velocity", showfliers=False, ax=axes[0])
axes[0].set_title("Vận tốc theo cấp đường (bỏ ngày đột biến)")
axes[0].set_xlabel("street_level")
axes[0].set_ylabel("velocity")
sns.boxplot(data=rest[rest["street_type"].isin(top_types.index)], x="street_type", y="velocity",
            order=top_types.index.tolist(), showfliers=False, ax=axes[1])
axes[1].set_title("Vận tốc theo loại đường (loại có > 500 dòng)")
axes[1].set_xlabel("street_type")
axes[1].tick_params(axis="x", rotation=30)
save_fig("05_van_toc_theo_duong.png")

# --- Biểu đồ 4: vận tốc so với giới hạn tốc độ ---
plt.figure(figsize=(9, 4))
sns.histplot(r[r["ti_le"] <= 2], x="ti_le", bins=40)
plt.axvline(1, color="red", linestyle="--", label="Bằng giới hạn")
plt.legend()
plt.title("Vận tốc / giới hạn tốc độ (chỉ đoạn có max_velocity, tỉ lệ ≤ 2)")
plt.xlabel("velocity / max_velocity")
plt.ylabel("Số dòng")
save_fig("05_van_toc_so_voi_gioi_han.png")

# --- Biểu đồ 5: tỉ lệ velocity = 1 theo cấp đường ---
plt.figure(figsize=(7, 4))
ax = share1.plot(kind="bar", label="Tỉ lệ velocity = 1")
ax.bar_label(ax.containers[0], fmt="%.1f%%")
plt.axhline((rest["velocity"] == 1).mean() * 100, color="red", linestyle="--", label="Trung bình chung")
plt.legend()
plt.title("Tỉ lệ velocity = 1 theo cấp đường (bỏ ngày đột biến)")
plt.xlabel("street_level")
plt.ylabel("Tỉ lệ (%)")
plt.xticks(rotation=0)
save_fig("05_velocity_bang_1.png")