# eda_08_bao_cao.py
# Mục đích: gom các biểu đồ và phát hiện của cột mốc 1-7 thành 1 tệp HTML duy nhất (bao_cao_eda.html).
# Ảnh được nhúng thẳng vào HTML nên chỉ cần gửi 1 tệp.

import base64
import html
import os

import pandas as pd

from common import FIG_DIR, OUT_DIR, load

OUT_FILE = "bao_cao_eda.html"
thieu_anh = []  # ghi lại các ảnh không tìm thấy để báo ở cuối


def anh(ten_file, chu_thich):
    """Đọc 1 ảnh PNG trong figures/ và nhúng vào HTML (base64). Thiếu ảnh thì bỏ qua và ghi nhớ."""
    path = os.path.join(FIG_DIR, ten_file)
    if not os.path.exists(path):
        thieu_anh.append(ten_file)
        return f"<p><i>(thiếu ảnh {ten_file})</i></p>"
    with open(path, "rb") as f:
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
pre { background: #f6f6f6; padding: 10px; overflow-x: auto; font-size: 0.8em; }
.luu-y { background: #fff8e1; border-left: 4px solid #f0b400; padding: 8px 14px; }
"""

# ---------- Bảng tổng quan: tính trực tiếp từ 5 tệp CSV ----------
files = ["nodes", "streets", "segments", "segment_status", "train"]
rows_html = ""
for name in files:
    df = load(name)
    thieu = df.isnull().sum()
    thieu = thieu[thieu > 0]
    thieu_text = ", ".join(f"{c} ({n:,})" for c, n in thieu.items()) or "không có"
    rows_html += f"<tr><td>{name}.csv</td><td>{len(df):,}</td><td>{df.shape[1]}</td><td>{thieu_text}</td></tr>"
bang_tong_quan = (
    "<table><tr><th>Tệp</th><th>Số dòng</th><th>Số cột</th><th>Cột có ô thiếu (số ô)</th></tr>"
    + rows_html + "</table>"
)

# Nhật ký kiểm tra chi tiết của cột mốc 1 (nếu có) để gập trong báo cáo
log_path = os.path.join(OUT_DIR, "01_kiem_tra_du_lieu.txt")
if os.path.exists(log_path):
    with open(log_path, encoding="utf-8") as f:
        log_html = ("<details><summary>Xem nhật ký kiểm tra dữ liệu chi tiết</summary><pre>"
                    + html.escape(f.read()) + "</pre></details>")
else:
    log_html = ""

# ---------- Ghép các phần của báo cáo ----------
p = []
p.append("<h1>Báo cáo EDA: dữ liệu giao thông</h1>")
p.append('<p class="luu-y">Các phát hiện dưới đây rút ra từ dữ liệu. Những điểm đánh dấu '
         "<b>(cần xác nhận)</b> là suy đoán, chưa có tài liệu mô tả dữ liệu để kiểm chứng.</p>")

p.append("<h2>1. Tổng quan và chất lượng dữ liệu</h2>")
p.append(bang_tong_quan)
p.append(danh_sach([
    "Không có dòng trùng lặp; cột <code>_id</code> của mọi bảng là duy nhất; mọi khoá nối giữa các bảng khớp 100%.",
    "<code>train</code> là bản sao thông tin đường từ <code>segments</code> và <code>nodes</code> (khớp 100%), "
    "cộng thêm 4 cột riêng: <code>date</code>, <code>weekday</code>, <code>period</code>, <code>LOS</code>.",
    "<code>max_velocity</code> thiếu 82–88% (streets 82,2%; segments 88,3%; train 85,2%).",
    "154 đoạn đường (khoảng 0,18%) có <code>length</code> = 0 (57 dòng trong train).",
    "<code>period</code> chỉ có 46/48 khung (thiếu <code>period_20_30</code> và <code>period_21_00</code>). "
    "Nhãn LOS không mâu thuẫn; <code>weekday</code> khớp 100% với <code>date</code>.",
]))
p.append(log_html)

p.append("<h2>2. Phân bố từng biến</h2>")
p.append(anh("02_los.png", "Phân bố LOS (train)"))
p.append(anh("02_street_type.png", "Tỉ lệ theo loại đường: toàn mạng lưới và các đoạn có trong train"))
p.append(anh("02_street_level.png", "Tỉ lệ theo cấp đường"))
p.append(anh("02_length.png", "Phân bố độ dài đoạn đường"))
p.append(anh("02_max_velocity.png", "Giới hạn tốc độ của các đoạn trong train"))
p.append(anh("02_velocity.png", "Phân bố vận tốc trong segment_status"))
p.append(danh_sach([
    "LOS lệch về mức A (39,7%); các mức B–F mỗi mức khoảng 11–14%.",
    "<code>train</code> nghiêng về đường lớn: <code>primary</code> chiếm 27,1% (toàn mạng lưới 10,2%), "
    "<code>unclassified</code> chỉ 4,7% (toàn mạng lưới 22,2%); cấp đường 2 chiếm 27,1% (so với 10,2%).",
    "<code>length</code> lệch phải, trung vị 30 trong train và 27 toàn mạng lưới. Đơn vị chưa xác nhận.",
    "85,2% đoạn trong train (8.547/10.027) thiếu <code>max_velocity</code>; giá trị phổ biến là 60, 50, 40.",
    "Vận tốc: trung vị 17; 99% giá trị không quá 79; 151 dòng vượt 100; chỉ 3 dòng bằng 200; "
    "giá trị 1 chiếm 23,4% số dòng.",
]))

p.append("<h2>3. Thời gian trong train (giờ UTC)</h2>")
p.append(anh("03_ngay.png", "Số dòng train theo ngày"))
p.append(anh("03_period.png", "Số dòng theo khung giờ (tách 2 ngày đột biến)"))
p.append(anh("03_los_theo_thu.png", "Tỉ lệ LOS theo thứ (thứ tính theo ngày UTC)"))
p.append(danh_sach([
    "Hai ngày 02/08/2020 và 03/08/2020 chiếm 21,7% số dòng train (3.651 và 3.610 dòng), mỗi ngày gồm khoảng 3.600 đoạn: "
    "giống một đợt thu thập hàng loạt. Chúng tạo ra 7.218/8.379 dòng của hai khung 0:00 và 23:30.",
    "Phân bố LOS của hai ngày này khác hẳn: mức A chỉ 2,4% (các ngày còn lại 50,0%). "
    "<b>(cần xác nhận nguyên nhân)</b>",
    "Dữ liệu dàn không đều: tháng 12/2020 chiếm khoảng 45% (15.105 dòng); tháng 10/2020 chỉ 13 dòng; tháng 2/2021 chỉ 1 dòng.",
    "Sau khi bỏ hai ngày đột biến, Chủ Nhật và Thứ Bảy thoáng nhất; Thứ Sáu nhiều mức F nhất "
    "nhưng chỉ có 2.011 dòng nên cần thận trọng.",
]))

p.append("<h2>4. Vị trí trên bản đồ</h2>")
p.append(anh("04_ban_do_nodes.png", "Các nút giao (nodes.csv)"))
p.append(anh("04_ban_do_pham_vi.png", "Phạm vi phủ của train so với toàn mạng lưới"))
p.append(anh("04_ban_do_los.png", "LOS trung bình theo đoạn đường (bỏ 2 ngày đột biến)"))
p.append(danh_sach([
    "<code>train</code> chỉ phủ 10.027/84.633 đoạn (11,8%), tập trung ở khu trung tâm và các trục đường lớn.",
    "Sau khi bỏ hai ngày đột biến còn 7.105 đoạn, trung bình 3,7 dòng mỗi đoạn, 25% đoạn chỉ có 1 dòng; "
    "chỉ 2.458 đoạn có từ 3 dòng trở lên nên màu của từng đoạn riêng lẻ chưa đáng tin.",
    "Xu hướng chung: vùng trung tâm nghiêng về mức D–F, các trục ngoại vi nghiêng về mức A–B.",
]))

p.append("<h2>5. Bảng segment_status</h2>")
p.append(anh("05_ban_ghi_theo_ngay.png", "Số bản ghi theo ngày (giờ VN, trục y dạng log)"))
p.append(anh("05_ban_ghi_theo_gio.png", "Số bản ghi theo giờ: UTC và giờ Việt Nam"))
p.append(anh("05_van_toc_theo_duong.png", "Vận tốc theo cấp đường và loại đường"))
p.append(anh("05_van_toc_so_voi_gioi_han.png", "Vận tốc so với giới hạn tốc độ"))
p.append(danh_sach([
    "Ngày 03/08/2020 (giờ VN) có 36.096 bản ghi (39,7% cả bảng) của 3.612 đoạn, dồn trong khoảng 6h–7h sáng giờ VN; "
    "trùng với hai ngày đột biến của train.",
    "Số bản ghi mỗi đoạn rất không đều: trung vị 5, tối đa 2.150, 25% đoạn chỉ có 1 bản ghi.",
    "Cấp 1 và <code>trunk</code> nhanh nhất (trung vị 48). Trung vị của <code>tertiary</code> (3) và cấp 4 (4) rất thấp "
    "vì có nhiều giá trị 1.",
    "549/6.996 dòng (7,8%) có vận tốc vượt <code>max_velocity</code>.",
    "Khoảng 0h–5h sáng giờ VN gần như không có bản ghi (309/90.938 dòng).",
]))

p.append("<h2>6. Mối liên hệ giữa các bảng và LOS</h2>")
p.append(anh("06_khop_mui_gio.png", "Độ lệch giờ giữa updated_at và train.period"))
p.append(anh("06_van_toc_theo_los.png", "Vận tốc trung bình và số bản ghi của khung theo LOS"))
p.append(anh("07_velocity_bang_1_theo_los.png", "Tỉ lệ velocity = 1 theo LOS và theo số bản ghi trong khung"))
p.append(danh_sach([
    "<code>train.date</code> và <code>train.period</code> là <b>giờ UTC</b>: dịch 0 giờ cho độ khớp 100%, "
    "mọi độ lệch khác dưới 10%. Muốn ra giờ Việt Nam phải cộng 7 giờ.",
    "<code>train</code> chính là <code>segment_status</code> gộp theo (đoạn, ngày, khung 30 phút UTC): "
    "90.938 dòng gộp thành đúng 33.441 khóa, khớp 100% hai chiều.",
    "LOS gắn rất chặt với vận tốc trung bình của khung: trung vị của A..F lần lượt là 49, 34, 26,5, 21, 16, 6; "
    "chỉ dùng vận tốc trung bình và ngưỡng đơn giản đã đoán đúng 84,1% (hầu hết lỗi là nhầm mức kề bên). "
    "LOS có vẻ được tính từ vận tốc <b>(cần xác nhận công thức)</b>.",
    "94,6% số dòng velocity = 1 nằm trong khung LOS F, và 91,8% dòng thuộc các khung có hơn 50 bản ghi là giá trị 1: "
    "giá trị 1 có thể là mã \"đứng yên/kẹt\" lặp lại nhiều lần <b>(cần xác nhận)</b>. "
    "Vì vậy thống kê trên bản ghi thô bị chi phối bởi các khung có rất nhiều bản ghi.",
    "Các khung A và B thường chỉ có 1 bản ghi với vận tốc quanh 49–50 (A) và 33–34 (B): có thể là giá trị gần như cố định, "
    "chưa chắc là đo thật <b>(cần xác nhận)</b>.",
]))

p.append("<h2>7. LOS theo đặc điểm đường và theo giờ Việt Nam</h2>")
p.append(anh("07_los_theo_duong.png", "LOS theo cấp đường, loại đường và độ dài đoạn (bỏ 2 ngày đột biến)"))
p.append(anh("07_los_theo_gio_vn.png", "Tỉ lệ LOS theo giờ Việt Nam"))
p.append(anh("07_los_trung_binh_thu_gio_vn.png", "LOS trung bình theo thứ và giờ Việt Nam"))
p.append(danh_sach([
    "Đường lớn thông thoáng hơn: cấp 1 có 71,4% mức A và 7,8% mức F; cấp 4 có 56,7% mức A và 16,7% mức F. "
    "Đường <code>primary</code> (cấp 2) có tỉ lệ mức B cao bất thường (32,3%).",
    "<code>street_level</code> và <code>street_type</code> gần như trùng thông tin: <code>primary</code> tương ứng cấp 2 "
    "(9.920 và 9.918 dòng, tỉ lệ LOS giống hệt), <code>trunk</code> tương ứng cấp 1.",
    "Đoạn ngắn có xu hướng ùn hơn: LOS trung bình 1,79 ở nhóm 0–10 và 0,55 ở nhóm trên 200 (nhóm này chỉ có 629 dòng). "
    "Đây là mối liên hệ, chưa phải quan hệ nhân quả.",
    "Theo giờ Việt Nam: gần như không có dữ liệu từ 0h đến 4h (dưới 30 dòng mỗi giờ); có hai khoảng cao điểm là 7h–9h (mức A còn khoảng 34% lúc 7h và 18% lúc 8h) "
    "và 16h–19h; khoảng 12h–15h thông thoáng nhất. Cuối tuần thoáng hơn ngày thường.",
]))

p.append("<h2>8. Lưu ý khi làm mô hình</h2>")
p.append(danh_sach([
    "LOS mất cân bằng (mức A khoảng 40%): nên dùng thêm độ đo như macro-F1, không chỉ accuracy.",
    "<b>Rò rỉ nhãn:</b> vận tốc của chính khung đó gần như quyết định LOS, nên không dùng làm đặc trưng nếu mục tiêu là dự đoán LOS.",
    "Hai ngày đột biến (02–03/08/2020) có phân bố LOS khác hẳn: nên đánh dấu hoặc xử lý riêng.",
    "Giờ trong <code>train</code> là UTC: khi tạo đặc trưng giờ và thứ, cộng 7 giờ trước.",
    "<code>train</code> chỉ phủ 11,8% đoạn đường và nghiêng về đường lớn: khó khái quát cho đường nhỏ.",
    "Dữ liệu lệch theo thời gian và mỗi đoạn có rất ít dòng: cần cân nhắc cách chia tập huấn luyện/kiểm tra.",
    "<code>max_velocity</code> thiếu khoảng 85%; <code>street_level</code> và <code>street_type</code> gần như trùng thông tin.",
    "Cần xác nhận với nguồn dữ liệu: đơn vị của <code>velocity</code> và <code>length</code>, ý nghĩa của giá trị 1, công thức tính LOS.",
]))

html_doc = (
    '<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">'
    "<title>Báo cáo EDA giao thông</title>"
    f"<style>{CSS}</style></head><body>"
    + "\n".join(p)
    + "</body></html>"
)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_doc)

print(f"Đã tạo {OUT_FILE} ({os.path.getsize(OUT_FILE) / 1024:.0f} KB)")
if thieu_anh:
    print("CHÚ Ý, thiếu các ảnh sau trong figures/:", thieu_anh)
else:
    print("Đã nhúng đủ ảnh.")