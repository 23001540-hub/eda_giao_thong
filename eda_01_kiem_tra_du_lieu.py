# eda_01_kiem_tra_du_lieu.py
# Mục đích: "khám sức khoẻ" dữ liệu thô trước khi vẽ bất kỳ biểu đồ nào:
#   A. cấu trúc từng bảng      B. dòng trùng
#   C. khoá nối giữa các bảng  D. train có khớp với segments / nodes không
#   E. giá trị có hợp lý không F. nhãn và thời gian có nhất quán không
# Kết quả vừa in ra màn hình, vừa lưu vào outputs/01_kiem_tra_du_lieu.txt

import numpy as np
import pandas as pd

from common import OUT_DIR, load

lines = []


def log(text=""):
    """In ra màn hình và nhớ lại để lưu vào tệp ở cuối."""
    print(text)
    lines.append(str(text))


nodes = load("nodes")
streets = load("streets")
segments = load("segments")
status = load("segment_status")
train = load("train")
tables = {"nodes": nodes, "streets": streets, "segments": segments,
          "segment_status": status, "train": train}

# ---------- A. Cấu trúc từng bảng ----------
log("=" * 70)
log("A. CẤU TRÚC TỪNG BẢNG (kiểu dữ liệu, ô thiếu, số giá trị khác nhau)")
for name, df in tables.items():
    log("")
    log(f"--- {name}: {df.shape[0]:,} dòng x {df.shape[1]} cột")
    info = pd.DataFrame({
        "kieu": df.dtypes.astype(str),
        "thieu": df.isnull().sum(),
        "thieu_%": (df.isnull().mean() * 100).round(1),
        "so_gia_tri_khac_nhau": df.nunique(),
    })
    log(info.to_string())

# ---------- B. Dòng trùng ----------
log("")
log("=" * 70)
log("B. DÒNG TRÙNG LẶP VÀ CỘT _id")
for name, df in tables.items():
    log(f"{name}: dòng trùng hoàn toàn = {df.duplicated().sum()}; _id có duy nhất = {df['_id'].is_unique}")

# ---------- C. Khoá nối giữa các bảng ----------
log("")
log("=" * 70)
log("C. KHOÁ NỐI: giá trị ở bảng con có tồn tại ở bảng cha không")


def check_key(child, col, parent, parent_col, label):
    ok = child[col].isin(parent[parent_col])
    log(f"{label}: khớp {ok.mean() * 100:.2f}% (không khớp {(~ok).sum():,} dòng)")


check_key(segments, "s_node_id", nodes, "_id", "segments.s_node_id -> nodes._id")
check_key(segments, "e_node_id", nodes, "_id", "segments.e_node_id -> nodes._id")
check_key(segments, "street_id", streets, "_id", "segments.street_id -> streets._id")
check_key(status, "segment_id", segments, "_id", "segment_status.segment_id -> segments._id")
check_key(train, "segment_id", segments, "_id", "train.segment_id -> segments._id")
check_key(train, "street_id", streets, "_id", "train.street_id -> streets._id")
check_key(train, "s_node_id", nodes, "_id", "train.s_node_id -> nodes._id")
check_key(train, "e_node_id", nodes, "_id", "train.e_node_id -> nodes._id")

# ---------- D. train có khớp với segments và nodes không ----------
log("")
log("=" * 70)
log("D. train ĐƯỢC SAO CHÉP TỪ segments / nodes: các cột có khớp nhau không")
seg = segments.rename(columns={"_id": "segment_id"})
m = train.merge(seg, on="segment_id", how="left", suffixes=("", "_seg"))
for c in ["s_node_id", "e_node_id", "length", "street_id", "max_velocity",
          "street_level", "street_name", "street_type"]:
    a, b = m[c], m[c + "_seg"]
    same = (a == b) | (a.isnull() & b.isnull())  # hai ô cùng thiếu cũng tính là khớp
    log(f"{c}: khớp {same.mean() * 100:.2f}% (lệch {(~same).sum():,} dòng)")

# Toạ độ nút đầu / nút cuối trong train so với nodes.csv
for prefix, node_col, lon_col, lat_col in [("đầu", "s_node_id", "long_snode", "lat_snode"),
                                          ("cuối", "e_node_id", "long_enode", "lat_enode")]:
    nd = nodes.rename(columns={"_id": node_col, "long": "long_ref", "lat": "lat_ref"})
    mm = train.merge(nd, on=node_col, how="left")
    same = np.isclose(mm[lon_col], mm["long_ref"]) & np.isclose(mm[lat_col], mm["lat_ref"])
    log(f"toạ độ nút {prefix}: khớp {same.mean() * 100:.2f}% (lệch {(~same).sum():,} dòng)")

# ---------- E. Giá trị có hợp lý không ----------
log("")
log("=" * 70)
log("E. KHOẢNG GIÁ TRỊ")
log(f"nodes: long {nodes['long'].min():.4f} -> {nodes['long'].max():.4f}; "
    f"lat {nodes['lat'].min():.4f} -> {nodes['lat'].max():.4f}")
log(f"segments.length: nhỏ nhất {segments['length'].min()}, trung vị {segments['length'].median()}, "
    f"lớn nhất {segments['length'].max()}; số đoạn có length = 0: {(segments['length'] == 0).sum()}")
log(f"train.length: số dòng có length = 0: {(train['length'] == 0).sum()}")
log(f"max_velocity (segments) các giá trị có mặt: {sorted(segments['max_velocity'].dropna().unique().tolist())}")
log(f"segment_status.velocity: nhỏ nhất {status['velocity'].min()}, lớn nhất {status['velocity'].max()}")
log(f"street_level (segments) các giá trị: {sorted(segments['street_level'].unique().tolist())}")
log(f"LOS (train) các giá trị: {sorted(train['LOS'].unique().tolist())}")
log(f"weekday (train) các giá trị: {sorted(train['weekday'].unique().tolist())}")

expected = {f"period_{h}_{mi:02d}" for h in range(24) for mi in (0, 30)}
present = set(train["period"].unique())
log(f"period: có {len(present)}/48 khung; thiếu: {sorted(expected - present)}; "
    f"lạ (ngoài 48 khung chuẩn): {sorted(present - expected)}")

# ---------- F. Nhãn và thời gian ----------
log("")
log("=" * 70)
log("F. NHẤT QUÁN NHÃN VÀ THỜI GIAN")
dates = pd.to_datetime(train["date"], errors="coerce")
log(f"train.date không đọc được thành ngày: {dates.isnull().sum()} dòng")
log(f"train.weekday khớp với thứ tính từ date: {(dates.dt.day_of_week == train['weekday']).mean() * 100:.2f}%")
log(f"train: số dòng lặp cùng (segment_id, date, period): "
    f"{train.duplicated(['segment_id', 'date', 'period'], keep=False).sum()}")
g = train.groupby(["segment_id", "date", "period"])["LOS"].nunique()
log(f"train: số cụm (segment_id, date, period) có nhãn LOS mâu thuẫn: {(g > 1).sum()}")
ts = pd.to_datetime(status["updated_at"], utc=True, errors="coerce")
log(f"segment_status.updated_at không đọc được thành thời gian: {ts.isnull().sum()} dòng")
log(f"segment_status.updated_at: {ts.min()} -> {ts.max()}")

# ---------- Lưu báo cáo ----------
out_path = f"{OUT_DIR}/01_kiem_tra_du_lieu.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print()
print(f"Đã lưu báo cáo vào {out_path}")