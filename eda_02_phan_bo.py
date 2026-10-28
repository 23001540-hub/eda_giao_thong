# eda_02_phan_bo.py
# Mục đích: xem từng biến riêng lẻ ("phân bố một biến"):
#   LOS, loại đường, cấp đường, độ dài đoạn, giới hạn tốc độ, vận tốc.
# Với các thuộc tính của đường, ta so sánh "toàn mạng lưới" (segments)
# với "các đoạn có mặt trong train" để biết train có đại diện cho cả mạng lưới không.

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import LOS_ORDER, load, save_fig

train = load("train")
segments = load("segments")
status = load("segment_status")

# Các đoạn đường (không lặp) có mặt trong train
seg_in_train = segments[segments["_id"].isin(train["segment_id"].unique())]
print(f"Số đoạn: toàn mạng lưới = {len(segments):,}; có trong train = {len(seg_in_train):,}")
print()

# ---------- 1. Phân bố LOS (biến mục tiêu) ----------
# Mục đích: các mức A-F có cân bằng không
counts = train["LOS"].value_counts().reindex(LOS_ORDER)
fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(counts.index, counts.values, color=sns.color_palette("RdYlGn_r", 6))
ax.bar_label(bars, labels=[f"{n:,}\n({n / counts.sum() * 100:.1f}%)" for n in counts.values])
ax.set_ylim(0, counts.max() * 1.18)
ax.set_title("Phân bố mức độ ùn tắc LOS (train)")
ax.set_xlabel("LOS (A = thoáng, F = kẹt nặng)")
ax.set_ylabel("Số dòng")
save_fig("02_los.png")


def so_sanh_ti_le(col, tieu_de, ten_file, top=None, theo_gia_tri=False):
    """Vẽ tỉ lệ % của cột `col`: toàn mạng lưới so với các đoạn có trong train."""
    toan = segments[col].value_counts(normalize=True) * 100
    trong = seg_in_train[col].value_counts(normalize=True) * 100
    bang = pd.DataFrame({"Toàn mạng lưới": toan, "Có trong train": trong}).fillna(0)
    if theo_gia_tri:
        bang = bang.sort_index()
    else:
        bang = bang.sort_values("Toàn mạng lưới", ascending=False)
    if top is not None and len(bang) > top:
        con_lai = bang.iloc[top:].sum()
        bang = bang.iloc[:top].copy()
        bang.loc["Khác (gộp)"] = con_lai
    print(tieu_de)
    print(bang.round(2).to_string())
    print()
    ax = bang.plot(kind="barh", figsize=(9, 5))
    ax.invert_yaxis()  # giá trị lớn nhất nằm trên cùng
    ax.set_title(tieu_de)
    ax.set_xlabel("Tỉ lệ (%)")
    ax.set_ylabel("")
    save_fig(ten_file)


# ---------- 2. Loại đường ----------
so_sanh_ti_le("street_type", "Tỉ lệ theo loại đường (8 loại lớn nhất, còn lại gộp)",
              "02_street_type.png", top=8)

# ---------- 3. Cấp đường ----------
so_sanh_ti_le("street_level", "Tỉ lệ theo cấp đường (street_level)",
              "02_street_level.png", theo_gia_tri=True)

# ---------- 4. Độ dài đoạn đường ----------
# Cắt ở phân vị 99% để vài đoạn quá dài không làm biểu đồ bị kéo giãn
ln = pd.concat([
    pd.DataFrame({"length": segments["length"], "nhom": "Toàn mạng lưới"}),
    pd.DataFrame({"length": seg_in_train["length"], "nhom": "Có trong train"}),
])
gioi_han = ln["length"].quantile(0.99)
print("Thống kê length (toàn mạng lưới):")
print(segments["length"].describe().round(1).to_string())
print("Thống kê length (có trong train):")
print(seg_in_train["length"].describe().round(1).to_string())
print(f"Phân vị 99% của length: {gioi_han:.0f}")
print()
plt.figure(figsize=(9, 4))
sns.histplot(data=ln[ln["length"] <= gioi_han], x="length", hue="nhom",
             bins=40, stat="density", common_norm=False, element="step")
plt.title(f"Phân bố độ dài đoạn đường (cắt ở phân vị 99% = {gioi_han:.0f})")
plt.xlabel("length")
plt.ylabel("Mật độ")
save_fig("02_length.png")

# ---------- 5. Giới hạn tốc độ max_velocity ----------
# Ô thiếu được gom thành nhóm "Thiếu" để thấy rõ nó chiếm bao nhiêu
mv = seg_in_train["max_velocity"].fillna(-1).value_counts().sort_index()
nhan = ["Thiếu" if v == -1 else str(int(v)) for v in mv.index]
plt.figure(figsize=(9, 4))
bars = plt.bar(nhan, mv.values)
plt.bar_label(bars)
plt.title("Giới hạn tốc độ max_velocity của các đoạn trong train")
plt.xlabel("max_velocity")
plt.ylabel("Số đoạn đường")
save_fig("02_max_velocity.png")

# ---------- 6. Vận tốc trong segment_status ----------
# Hình trái: toàn bộ, trục y dạng log để thấy cả phần đuôi (giá trị lớn, hiếm)
# Hình phải: phóng to vận tốc 0-60, mỗi cột là 1 giá trị nguyên
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
sns.histplot(data=status, x="velocity", bins=50, ax=axes[0])
axes[0].set_yscale("log")
axes[0].set_title("Toàn bộ vận tốc (trục y dạng log)")
axes[0].set_xlabel("velocity")
axes[0].set_ylabel("Số dòng (log)")
sns.histplot(data=status[status["velocity"] <= 60], x="velocity", discrete=True, ax=axes[1])
axes[1].set_title("Phóng to: vận tốc 0-60")
axes[1].set_xlabel("velocity")
axes[1].set_ylabel("Số dòng")
save_fig("02_velocity.png")

print("Số dòng theo vận tốc 0-5:")
print(status["velocity"].value_counts().sort_index().head(6).to_string())
print(f"Tỉ lệ velocity = 1: {(status['velocity'] == 1).mean() * 100:.1f}%")