# eda_04_ban_do.py
# Mục đích: vẽ bản đồ các nút giao và các đoạn đường tô màu theo mức ùn tắc

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

DATA_DIR = "data"
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)

nodes = pd.read_csv(f"{DATA_DIR}/nodes.csv")
segments = pd.read_csv(f"{DATA_DIR}/segments.csv")
train = pd.read_csv(f"{DATA_DIR}/train.csv")

# ---------- Biểu đồ 7: bản đồ tất cả các nút giao ----------
# Mỗi chấm là 1 nút (kinh độ = trục x, vĩ độ = trục y).
# Chấm rất nhỏ (s=0.05) vì có gần 578 nghìn nút.
fig, ax = plt.subplots(figsize=(9, 9))
ax.scatter(nodes["long"], nodes["lat"], s=0.05, alpha=0.4, color="steelblue", rasterized=True)
ax.set_aspect("equal")  # giữ tỉ lệ x:y để bản đồ không bị méo
ax.set_title("Vị trí các nút giao (nodes.csv)")
ax.set_xlabel("Kinh độ")
ax.set_ylabel("Vĩ độ")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/07_ban_do_nodes.png", dpi=130)
plt.close()

# ---------- Biểu đồ 8: các đoạn đường trong train, tô màu theo LOS ----------
# Đổi chữ cái LOS thành số để tính trung bình: A=0, B=1, ..., F=5
train["los_num"] = train["LOS"].map({c: i for i, c in enumerate("ABCDEF")})

# Mỗi segment_id lấy 1 dòng: toạ độ đầu/cuối và mức LOS trung bình
seg = train.groupby("segment_id").agg(
    long_s=("long_snode", "first"), lat_s=("lat_snode", "first"),
    long_e=("long_enode", "first"), lat_e=("lat_enode", "first"),
    los_mean=("los_num", "mean"),
    so_dong=("los_num", "size"),
).reset_index()

# Mỗi đoạn đường là 1 đoạn thẳng nối (nút đầu) -> (nút cuối)
lines = [[(r.long_s, r.lat_s), (r.long_e, r.lat_e)] for r in seg.itertuples()]
lc = LineCollection(lines, array=seg["los_mean"].values, cmap="RdYlGn_r", linewidths=1.5)
lc.set_clim(0, 5)

fig, ax = plt.subplots(figsize=(9, 9))
ax.add_collection(lc)
ax.autoscale()
ax.set_aspect("equal")
cb = fig.colorbar(lc, ax=ax, shrink=0.7)
cb.set_ticks(range(6))
cb.set_ticklabels(list("ABCDEF"))
cb.set_label("LOS trung bình của đoạn đường")
ax.set_title("Các đoạn đường trong train, tô màu theo LOS trung bình")
ax.set_xlabel("Kinh độ")
ax.set_ylabel("Vĩ độ")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/08_ban_do_los.png", dpi=130)
plt.close()

# ---------- In số liệu để kiểm tra ----------
print("Khoảng toạ độ của nodes:")
print(nodes[["long", "lat"]].describe().loc[["min", "max"]].round(4).to_string())
print()
print("Số đoạn đường (segment_id) khác nhau trong train:", train["segment_id"].nunique())
print("Tổng số đoạn đường trong segments.csv:", segments["_id"].nunique())
print()
print("Số dòng train trên mỗi đoạn đường:")
print(seg["so_dong"].describe().round(1).to_string())
print()
print("Đã lưu 2 biểu đồ vào thư mục figures/")