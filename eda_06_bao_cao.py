# eda_06_bao_cao.py
# Mục đích: gom 10 biểu đồ + các phát hiện chính thành 1 tệp HTML duy nhất (bao_cao_eda.html)

import base64
import os
import pandas as pd

DATA_DIR = "data"
FIG_DIR = "figures"
OUT_FILE = "bao_cao_eda.html"


def anh(ten_file, chu_thich):
    """Đọc 1 ảnh PNG và nhúng thẳng vào HTML (base64) để tệp báo cáo tự đủ, không cần kèm ảnh."""
    with open(os.path.join(FIG_DIR, ten_file), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (
        f'<figure><img src="data:image/png;base64,{b64}" alt="{chu_thich}">'
        f"<figcaption>{chu_thich}</figcaption></figure>"
    )


def danh_sach(cac_y):
    """Biến 1 list chữ thành danh sách gạch đầu dòng HTML."""
    return "<ul>" + "".join(f"<li>{y}</li>" for y in cac_y) + "</ul>"


CSS = """
body { font-family: Arial, sans-serif; max-width: 1000px; margin: 30px auto; padding: 0 16px; line-height: 1.6; color: #222; }
h1 { border-bottom: 3px solid #4c72b0; padding-bottom: 8px; }
h2 { margin-top: 40px; color: #4c72b0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
th { background: #f0f4fa; }
figure { margin: 16px 0; text-align: center; }
img { max-width: 100%; }
figcaption { font-size: 0.9em; color: #666; }
"""

# ---------- Bảng tổng quan: tính trực tiếp từ 5 tệp CSV ----------
files = ["nodes", "streets", "segments", "segment_status", "train"]
rows_html = ""
for name in files:
    df = pd.read_csv(f"{DATA_DIR}/{name}.csv")
    thieu = df.isnull().sum()
    thieu = thieu[thieu > 0]
    thieu_text = ", ".join(f"{c} ({n:,})" for c, n in thieu.items()) or "không có"
    rows_html += f"<tr><td>{name}.csv</td><td>{len(df):,}</td><td>{df.shape[1]}</td><td>{thieu_text}</td></tr>"

bang_tong_quan = (
    "<table><tr><th>Tệp</th><th>Số dòng</th><th>Số cột</th><th>Cột có ô thiếu (số ô)</th></tr>"
    + rows_html
    + "</table>"
)

# ---------- Ghép các phần của báo cáo ----------
parts = []
parts.append("<h1>Báo cáo EDA cơ bản: dữ liệu giao thông</h1>")

parts.append("<h2>1. Tổng quan dữ liệu</h2>")
parts.append(bang_tong_quan)
parts.append(danh_sach([
    "Không có dòng trùng lặp ở cả 5 bảng.",
    "<code>train</code> và <code>segment_status</code> cùng có 10.027 đoạn đường, tất cả đều có trong <code>segments</code>, nên nối bảng được qua <code>segment_id</code>.",
    "<code>max_velocity</code> thiếu rất nhiều (74.762/84.633 dòng ở segments; 28.495/33.441 dòng ở train).",
]))

parts.append("<h2>2. Mức ùn tắc (LOS) và loại đường</h2>")
parts.append(anh("01_los.png", "Phân bố LOS"))
parts.append(anh("02_street_type.png", "Số dòng theo loại đường"))
parts.append(danh_sach([
    "LOS lệch về mức A (khoảng 39,7%); các mức B–F mỗi mức chỉ khoảng 11–14%.",
    "<code>tertiary</code> và <code>primary</code> chiếm đa số. Cuối danh sách có các nhãn hiếm (school, cinema, bank...) gần như không có dòng.",
]))

parts.append("<h2>3. Thời gian trong train</h2>")
parts.append(anh("03_period.png", "Số dòng theo khung giờ"))
parts.append(anh("05_los_theo_thu.png", "Tỉ lệ LOS theo thứ trong tuần"))
parts.append(anh("06_los_theo_gio.png", "Tỉ lệ LOS theo khung giờ"))
parts.append(danh_sach([
    "Hai khung giờ <code>period_0_00</code> và <code>period_23_30</code> có số dòng cao bất thường, và phân bố LOS khác hẳn các giờ còn lại (A chỉ 9,43% so với 49,83%).",
    "Từ 16:30 đến 21:30 gần như không có dòng, nên các ô màu đậm ở khung giờ này trên heatmap không đáng tin.",
    "Số dòng giữa các thứ không đều (T6 chỉ 2.011 dòng, T2 có 8.112 dòng). T7 nhiều mức A nhất, T6 nhiều mức F nhất, chỉ là xu hướng sơ bộ.",
    "<code>train</code> có 122 ngày khác nhau, từ 2020-07-03 đến 2021-04-22, không phủ liên tục.",
]))

parts.append("<h2>4. Vị trí trên bản đồ</h2>")
parts.append(anh("07_ban_do_nodes.png", "Các nút giao (nodes.csv)"))
parts.append(anh("08_ban_do_los.png", "Các đoạn đường trong train, tô màu theo LOS trung bình"))
parts.append(danh_sach([
    "Vùng trung tâm ùn tắc hơn (mức D–E), các tuyến ngoại vi thông thoáng (mức A).",
    "<code>train</code> chỉ phủ 10.027 trong 84.633 đoạn đường (khoảng 12%), mỗi đoạn trung bình chỉ có 3,3 dòng.",
]))

parts.append("<h2>5. Vận tốc (segment_status)</h2>")
parts.append(anh("04_velocity.png", "Phân bố vận tốc"))
parts.append(anh("09_van_toc_theo_gio.png", "Vận tốc theo giờ trong ngày"))
parts.append(anh("10_so_ban_ghi_theo_ngay.png", "Số bản ghi theo ngày"))
parts.append(danh_sach([
    "Trung vị vận tốc là 17; 99% giá trị không quá 79. Có 151 dòng vượt 100 (lớn nhất 200), nghi là ngoại lai.",
    "Giá trị 1 xuất hiện 21.235 lần (khoảng 23% số dòng), cần tìm hiểu ý nghĩa (xe dừng hay giá trị mặc định).",
    "Trong 8.618 dòng có <code>max_velocity</code>, có 752 dòng vận tốc vượt giới hạn này.",
    "Dữ liệu tập trung lệch: một ngày đầu tháng 8/2020 có khoảng 36.000 bản ghi, và giờ 7h chiếm 31.576/90.938 bản ghi. Các giờ 0–5h gần như trống, nên đường xu hướng theo giờ rất nhiễu.",
]))

parts.append("<h2>6. Lưu ý khi làm mô hình</h2>")
parts.append(danh_sach([
    "LOS mất cân bằng: nên dùng thêm độ đo như macro-F1, không chỉ accuracy.",
    "Cần quyết định cách xử lý <code>max_velocity</code> bị thiếu nhiều.",
    "Mỗi đoạn đường có rất ít dòng và dữ liệu không đều theo ngày: nên cân nhắc cách chia train/test cho hợp lý.",
]))

html = (
    '<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">'
    "<title>Báo cáo EDA giao thông</title>"
    f"<style>{CSS}</style></head><body>"
    + "\n".join(parts)
    + "</body></html>"
)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Đã tạo {OUT_FILE} ({os.path.getsize(OUT_FILE) / 1024:.0f} KB)")