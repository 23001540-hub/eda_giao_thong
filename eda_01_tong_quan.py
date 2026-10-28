# eda_01_tong_quan.py
# Mục đích: đọc 5 tệp CSV và in thông tin tổng quan (kích thước, kiểu dữ liệu, ô thiếu)

import pandas as pd

# Đường dẫn tới thư mục chứa dữ liệu (tính từ nơi bạn chạy lệnh)
DATA_DIR = "data"

# Tên tệp -> đọc vào DataFrame (bảng trong pandas)
files = ["nodes", "streets", "segments", "segment_status", "train"]
dfs = {name: pd.read_csv(f"{DATA_DIR}/{name}.csv") for name in files}

for name, df in dfs.items():
    print("=" * 60)
    print(f"BẢNG: {name}")
    print(f"Số dòng, số cột: {df.shape}")

    # Số ô thiếu (NaN) ở mỗi cột, chỉ in các cột có thiếu
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) == 0:
        print("Ô thiếu: không có")
    else:
        print("Ô thiếu theo cột:")
        print(missing.to_string())

    # Số dòng bị trùng lặp hoàn toàn
    print(f"Số dòng trùng lặp: {df.duplicated().sum()}")