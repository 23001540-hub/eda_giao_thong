# eda_05_segment_status.py
# Mục đích: kiểm tra ngoại lai vận tốc, khả năng nối bảng, và xu hướng theo thời gian

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = "data"
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)
sns.set_theme(style="whitegrid")

status = pd.read_csv(f"{DATA_DIR}/segment_status.csv")
segments = pd.read_csv(f"{DATA_DIR}/segments.csv")
train = pd.read_csv(f"{DATA_DIR}/train.csv")

# Đổi cột thời gian (đang ở dạng chữ, múi giờ UTC) sang giờ Việt Nam (UTC+7)
status["time"] = pd.to_datetime(status["updated_at"], utc=True).dt.tz_convert("Asia/Ho_Chi_Minh")
status["hour"] = status["time"].dt.hour
status["date"] = status["time"].dt.normalize().dt.tz_localize(None)  # bỏ múi giờ để vẽ cho dễ

# ---------- Phần 1: ngoại lai của vận tốc ----------
print("=== VẬN TỐC ===")
print("Các phân vị:")
print(status["velocity"].quantile([0.5, 0.9, 0.99, 0.999]).to_string())
print("Số dòng có vận tốc > 80:", (status["velocity"] > 80).sum())
print("Số dòng có vận tốc > 100:", (status["velocity"] > 100).sum())
print("10 giá trị vận tốc xuất hiện nhiều nhất:")
print(status["velocity"].value_counts().head(10).to_string())
print()

# ---------- Phần 2: kiểm tra khả năng nối bảng ----------
print("=== NỐI BẢNG ===")
ids_status = set(status["segment_id"].unique())
print("Số đoạn đường khác nhau trong segment_status:", len(ids_status))
print("  trong đó có mặt ở segments.csv:", len(ids_status & set(segments["_id"])))
print("  trong đó có mặt ở train.csv:", len(ids_status & set(train["segment_id"])))
print()

# Ghép thêm loại đường và vận tốc tối đa từ segments vào status
seg = segments[["_id", "street_type", "max_velocity"]].rename(columns={"_id": "segment_id"})
merged = status.merge(seg, on="segment_id", how="left")

print("Vận tốc trung bình theo loại đường (chỉ in các loại có > 500 dòng):")
by_type = merged.groupby("street_type")["velocity"].agg(["mean", "size"])
print(by_type[by_type["size"] > 500].sort_values("mean", ascending=False).round(2).to_string())
print()

has_max = merged["max_velocity"].notna()
over = (merged.loc[has_max, "velocity"] > merged.loc[has_max, "max_velocity"]).sum()
print(f"Số dòng có max_velocity: {has_max.sum()}; trong đó vận tốc vượt max_velocity: {over}")
print()

# ---------- Phần 3: thời gian ----------
print("=== THỜI GIAN ===")
print("Khoảng thời gian của segment_status:", status["time"].min(), "->", status["time"].max())
print("Số ngày khác nhau:", status["date"].nunique())
print()

# ---------- Biểu đồ 9: vận tốc trung bình theo giờ trong ngày ----------
by_hour = status.groupby("hour")["velocity"].agg(["mean", "median", "size"])
fig, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(by_hour.index, by_hour["mean"], marker="o", label="Trung bình")
ax1.plot(by_hour.index, by_hour["median"], marker="s", label="Trung vị")
ax1.set_xlabel("Giờ trong ngày (giờ Việt Nam)")
ax1.set_ylabel("Vận tốc")
ax1.set_xticks(range(0, 24))
ax1.legend()
plt.title("Vận tốc theo giờ trong ngày (segment_status)")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/09_van_toc_theo_gio.png", dpi=120)
plt.close()

# ---------- Biểu đồ 10: số bản ghi mỗi ngày ----------
per_day = status.groupby("date").size()
plt.figure(figsize=(12, 4))
plt.plot(per_day.index, per_day.values, ".", markersize=4)
plt.title("Số bản ghi segment_status theo ngày")
plt.xlabel("Ngày")
plt.ylabel("Số bản ghi")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/10_so_ban_ghi_theo_ngay.png", dpi=120)
plt.close()

print("Số bản ghi mỗi giờ (để biết giờ nào ít dữ liệu):")
print(by_hour["size"].to_string())
print()
print("Đã lưu 2 biểu đồ vào thư mục figures/")