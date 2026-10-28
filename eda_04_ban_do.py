# eda_04_ban_do.py
# Mục đích: xem dữ liệu trên BẢN ĐỒ (không gian):
#   1. các nút giao (nodes.csv)
#   2. đoạn đường nào có trong train (phạm vi phủ so với toàn mạng lưới)
#   3. mức ùn tắc LOS trung bình của từng đoạn (bỏ 2 ngày đột biến),
#      so sánh "mọi đoạn" với "chỉ đoạn có từ 3 dòng trở lên" để thấy độ tin cậy

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from common import LOS_ORDER, load, save_fig

nodes = load("nodes")
segments = load("segments")
train = load("train")
train["los_num"] = train["LOS"].map({c: i for i, c in enumerate(LOS_ORDER)})  # A=0 ... F=5

# 2 ngày có nhiều dòng bất thường (đã tìm thấy ở cột mốc 3) -> loại ra khi tính LOS trung bình
top2 = train["date"].value_counts().head(2).index.tolist()
rest = train[~train["date"].isin(top2)]
print(f"Bỏ 2 ngày đột biến {top2}: còn {len(rest):,}/{len(train):,} dòng")

# Khung nhìn chung cho mọi bản đồ: lấy theo phạm vi toạ độ của nodes
XLIM = (nodes["long"].min(), nodes["long"].max())
YLIM = (nodes["lat"].min(), nodes["lat"].max())


def dinh_dang_ban_do(ax):
    """Đặt khung nhìn chung và giữ tỉ lệ x:y để bản đồ không bị méo."""
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Kinh độ")
    ax.set_ylabel("Vĩ độ")


# ---------- 1. Bản đồ các nút giao ----------
fig, ax = plt.subplots(figsize=(9, 9))
ax.scatter(nodes["long"], nodes["lat"], s=0.05, alpha=0.4, color="steelblue", rasterized=True)
ax.set_title("Vị trí các nút giao (nodes.csv)")
dinh_dang_ban_do(ax)
save_fig("04_ban_do_nodes.png")

# ---------- Chuẩn bị toạ độ cho TẤT CẢ đoạn đường ----------
# Mỗi đoạn là 1 đoạn thẳng nối nút đầu -> nút cuối; lấy toạ độ từ nodes theo s_node_id / e_node_id
nd = nodes.set_index("_id")[["long", "lat"]]
s_xy = nd.reindex(segments["s_node_id"]).to_numpy()
e_xy = nd.reindex(segments["e_node_id"]).to_numpy()
lines_all = np.stack([s_xy, e_xy], axis=1)  # hình dạng (số đoạn, 2 điểm, 2 toạ độ)
pos = pd.Series(np.arange(len(segments)), index=segments["_id"])  # segment_id -> vị trí trong lines_all

# ---------- 2. Phạm vi phủ của train ----------
in_train = segments["_id"].isin(train["segment_id"].unique()).to_numpy()
print(f"Đoạn đường có trong train: {in_train.sum():,}/{len(segments):,} ({in_train.mean() * 100:.1f}%)")

fig, ax = plt.subplots(figsize=(9, 9))
ax.add_collection(LineCollection(lines_all[~in_train], colors="lightgrey", linewidths=0.3))
ax.add_collection(LineCollection(lines_all[in_train], colors="crimson", linewidths=0.9))
ax.plot([], [], color="lightgrey", label="Toàn mạng lưới (không có trong train)")
ax.plot([], [], color="crimson", label="Có trong train")
ax.legend(loc="lower left")
ax.set_title("Phạm vi phủ của train so với toàn mạng lưới")
dinh_dang_ban_do(ax)
save_fig("04_ban_do_pham_vi.png")

# ---------- 3. LOS trung bình theo từng đoạn ----------
# Mỗi đoạn lấy LOS trung bình (A=0 ... F=5) và số dòng quan sát được (n)
g_all = rest.groupby("segment_id").agg(los_mean=("los_num", "mean"), n=("los_num", "size"))
print("Số dòng quan sát được trên mỗi đoạn (sau khi bỏ 2 ngày đột biến):")
print(g_all["n"].describe().round(1).to_string())
print(f"Số đoạn có từ 3 dòng trở lên: {(g_all['n'] >= 3).sum():,}/{len(g_all):,}")
print()

fig, axes = plt.subplots(1, 3, figsize=(19, 8), gridspec_kw={"width_ratios": [1, 1, 0.04]})
for ax, (tieu_de, min_obs) in zip(axes[:2], [("Mọi đoạn có dữ liệu", 1),
                                              ("Chỉ đoạn có từ 3 dòng trở lên", 3)]):
    g = g_all[g_all["n"] >= min_obs]
    idx = pos.reindex(g.index).to_numpy()
    lc = LineCollection(lines_all[idx], array=g["los_mean"].to_numpy(), cmap="RdYlGn_r", linewidths=1.5)
    lc.set_clim(0, 5)
    ax.add_collection(lc)
    ax.set_title(f"{tieu_de} ({len(g):,} đoạn)")
    dinh_dang_ban_do(ax)
cb = fig.colorbar(lc, cax=axes[2])
cb.set_ticks(range(6))
cb.set_ticklabels(LOS_ORDER)
cb.set_label("LOS trung bình của đoạn đường")
fig.suptitle("LOS trung bình theo đoạn đường (bỏ 2 ngày đột biến)")
save_fig("04_ban_do_los.png")