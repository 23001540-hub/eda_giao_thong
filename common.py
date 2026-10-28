# common.py
# Mục đích: chứa những thứ dùng chung cho mọi bước EDA (đường dẫn, hàm đọc dữ liệu,
# cách vẽ và lưu biểu đồ...) để các tệp khác không phải lặp lại.

import os

import matplotlib

matplotlib.use("Agg")  # chỉ lưu ảnh vào tệp, không mở cửa sổ biểu đồ
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DATA_DIR = "data"      # dữ liệu thô: chỉ đọc, không bao giờ sửa
FIG_DIR = "figures"    # nơi lưu biểu đồ
OUT_DIR = "outputs"    # nơi lưu bảng kết quả / báo cáo văn bản

LOS_ORDER = list("ABCDEF")  # thứ tự mức ùn tắc: A (thoáng) -> F (kẹt nặng)

# Tạo thư mục kết quả nếu chưa có
for _d in (FIG_DIR, OUT_DIR):
    os.makedirs(_d, exist_ok=True)

sns.set_theme(style="whitegrid")  # giao diện biểu đồ sáng, có lưới cho dễ đọc


def load(name):
    """Đọc 1 tệp CSV trong thư mục data (truyền tên không cần đuôi .csv)."""
    return pd.read_csv(f"{DATA_DIR}/{name}.csv")


def save_fig(file_name):
    """Căn lề, lưu biểu đồ hiện tại vào figures/ rồi đóng lại."""
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/{file_name}", dpi=120)
    plt.close()
    print(f"  -> đã lưu {FIG_DIR}/{file_name}")