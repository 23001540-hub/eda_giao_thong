# eda_02_phan_bo.py
# Mục đích: vẽ 4 biểu đồ phân bố cơ bản và lưu thành ảnh trong thư mục figures/

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = "data"
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)  # tạo thư mục figures nếu chưa có

sns.set_theme(style="whitegrid")  # giao diện biểu đồ sáng, có lưới cho dễ đọc

train = pd.read_csv(f"{DATA_DIR}/train.csv")
status = pd.read_csv(f"{DATA_DIR}/segment_status.csv")

# ---------- Biểu đồ 1: phân bố LOS (mức ùn tắc, cột mục tiêu) ----------
# Mục đích: xem các mức A-F có cân bằng không
order_los = sorted(train["LOS"].unique())
plt.figure(figsize=(7, 4))
ax = sns.countplot(data=train, x="LOS", order=order_los)
ax.bar_label(ax.containers[0])  # ghi số lượng trên đầu cột
plt.title("Phân bố mức độ ùn tắc (LOS)")
plt.xlabel("LOS")
plt.ylabel("Số dòng")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/01_los.png", dpi=120)
plt.close()

# ---------- Biểu đồ 2: số dòng theo loại đường ----------
# Mục đích: biết dữ liệu tập trung ở loại đường nào
plt.figure(figsize=(9, 4))
sns.countplot(
    data=train, y="street_type",
    order=train["street_type"].value_counts().index,
)
plt.title("Số dòng theo loại đường (street_type)")
plt.xlabel("Số dòng")
plt.ylabel("")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/02_street_type.png", dpi=120)
plt.close()

# ---------- Biểu đồ 3: số dòng theo khung giờ (period) ----------
# period có dạng "period_9_30" = khung 9h30. Tách giờ/phút để sắp xếp đúng thứ tự.
def period_to_minutes(p):
    _, h, m = p.split("_")
    return int(h) * 60 + int(m)

order_period = sorted(train["period"].unique(), key=period_to_minutes)
plt.figure(figsize=(12, 4))
sns.countplot(data=train, x="period", order=order_period)
plt.xticks(rotation=90)
plt.title("Số dòng theo khung giờ trong ngày")
plt.xlabel("Khung giờ")
plt.ylabel("Số dòng")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/03_period.png", dpi=120)
plt.close()

# ---------- Biểu đồ 4: phân bố vận tốc trong segment_status ----------
# Mục đích: xem xe thường chạy ở tốc độ nào
plt.figure(figsize=(8, 4))
sns.histplot(data=status, x="velocity", bins=30)
plt.title("Phân bố vận tốc (segment_status)")
plt.xlabel("Vận tốc")
plt.ylabel("Số dòng")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/04_velocity.png", dpi=120)
plt.close()

# In vài số thống kê để đối chiếu với biểu đồ
print("Tỉ lệ mỗi mức LOS (%):")
print((train["LOS"].value_counts(normalize=True).sort_index() * 100).round(2).to_string())
print()
print("Thống kê vận tốc:")
print(status["velocity"].describe().round(2).to_string())
print()
print("Đã lưu 4 biểu đồ vào thư mục figures/")