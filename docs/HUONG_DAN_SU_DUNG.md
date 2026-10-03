# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG TRAFFICVISION
**Hệ thống Thị giác máy tính nhận dạng biển báo giao thông Việt Nam bằng Trí tuệ nhân tạo (AI)**

> 🌐 **Sổ tay Hướng dẫn sử dụng:** [Bản HTML trực quan](huong_dan_su_dung.html) | [Bản PDF](huong_dan_su_dung.pdf)  
> 📊 **Slide Thuyết trình Bảo vệ:** [Bản Slide HTML](slide_bao_ve_du_an.html) | [Bản PDF 14 trang](slide_bao_ve_du_an.pdf)  
> 🔬 **Tài liệu Kỹ thuật Huấn luyện Chuyên sâu:** [Bản HTML](tai_lieu_huan_luyen_chuyen_sau.html) | [Bản PDF](tai_lieu_huan_luyen_chuyen_sau.pdf)  
> 🎓 **Cẩm nang Câu hỏi & Trả lời Bảo vệ (Q&A 4 thành viên):** [Bản HTML](cau_hoi_bao_ve_du_an.html) | [Bản PDF](cau_hoi_bao_ve_du_an.pdf)

---

## MỤC LỤC
1. [Giới thiệu tổng quan hệ thống](#1-giới-thiệu-tổng-quan-hệ-thống)
2. [Yêu cầu hệ thống & Môi trường](#2-yêu-cầu-hệ-thống--môi-trường)
3. [Cài đặt & Khởi động nhanh (Quick Start)](#3-cài-đặt--khởi-động-nhanh-quick-start)
   - [3.1. Cài đặt môi trường](#31-cài-đặt-môi-trường)
   - [3.2. Khởi tạo mô hình ban đầu (Bootstrap)](#32-khởi-tạo-mô-hình-ban-đầu-bootstrap)
   - [3.3. Khởi chạy ứng dụng Web (1-Click)](#33-khởi-chạy-ứng-dụng-web-1-click)
4. [Hướng dẫn sử dụng Giao diện Web Dashboard](#4-hướng-dẫn-sử-dụng-giao-diện-web-dashboard)
   - [4.1. Không gian "Phân tích" (Nhận dạng Ảnh & Video)](#41-không-gian-phân-tích-nhận-dạng-ảnh--video)
   - [4.2. Không gian "Lịch sử" (Tra cứu dữ liệu phiên)](#42-không-gian-lịch-sử-tra-cứu-dữ-liệu-phiên)
   - [4.3. Không gian "Thống kê" (Báo cáo & Phân bố biển báo)](#43-không-gian-thống-kê-báo-cáo--phân-bố-biển-báo)
   - [4.4. Không gian "Huấn luyện AI" (Quy trình 4 bước Phase 2)](#44-không-gian-huấn-luyện-ai-quy-trình-4-bước-phase-2)
   - [4.5. Không gian "Thông tin mô hình" (Model Registry & Rollback)](#45-không-gian-thông-tin-mô-hình-model-registry--rollback)
   - [4.6. Không gian "Thiết lập" (Cấu hình ngưỡng Conf & IoU)](#46-không-gian-thiết-lập-cấu-hình-ngưỡng-conf--iou)
5. [Hướng dẫn công cụ dòng lệnh (CLI Scripts)](#5-hướng-dẫn-công-cụ-dòng-lệnh-cli-scripts)
6. [Cấu trúc thư mục dữ liệu & Lưu trữ (Artifacts)](#6-cấu-trúc-thư-mục-dữ-liệu--lưu-trữ-artifacts)
7. [Xử lý sự cố thường gặp (Troubleshooting)](#7-xử-lý-sự-cố-thường-gặp-troubleshooting)

---

## 1. Giới thiệu tổng quan hệ thống

**TrafficVision** là giải pháp phần mềm thị giác máy tính thông minh được thiết kế chuyên biệt để phát hiện, định vị và phân loại biển báo giao thông đường bộ Việt Nam.

```
       [ Ảnh / Video Đầu vào ]
                  │
                  ▼
       ┌────────────────────────┐
       │   Tiền xử lý & Resize  │ (640x640 letterbox)
       └──────────┬─────────────┘
                  │
                  ▼
       ┌────────────────────────┐
       │  ONNX Runtime CPU / GPU│ (Tối ưu hóa đa luồng)
       └──────────┬─────────────┘
                  │
                  ▼
       ┌────────────────────────┐
       │ Hậu xử lý NMS (Conf/IoU│ (Lọc nhiễu & trùng lặp)
       └──────────┬─────────────┘
                  │
                  ▼
       [ Trực quan hóa & Xuất CSV ]
```

### Các ưu điểm nổi bật:
* **Tối ưu suy luận:** Hỗ trợ mô hình dạng ONNX siêu nhẹ, chạy mượt mà trực tiếp trên vi xử lý CPU (macOS Apple Silicon/Intel, Windows PC) mà không bắt buộc phải có card đồ họa rời (GPU).
* **Danh mục chuẩn hóa 82 lớp:** Nhận dạng chính xác 82 loại biển báo giao thông Việt Nam theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT (Biển báo cấm, Biển hiệu lệnh, Biển cảnh báo/nguy hiểm, Biển chỉ dẫn).
* **Xử lý đa phương tiện:** Hỗ trợ tải lên ảnh tĩnh (JPG, PNG, WEBP) và video chuyển động (MP4, AVI, MOV) kèm thanh tiến trình trực quan theo thời gian thực.
* **Quy trình MLOps khép kín:** Tích hợp sẵn phòng thí nghiệm Huấn luyện AI 4 bước: Thu nạp dữ liệu $\rightarrow$ Cổng kiểm định chất lượng (Quality Gate) & EDA $\rightarrow$ Huấn luyện ngầm độc lập $\rightarrow$ Đóng gói & Thăng cấp an toàn với tính năng Rollback 1-click.

---

## 2. Yêu cầu hệ thống & Môi trường

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
| :--- | :--- | :--- |
| **Hệ điều hành** | macOS 12+ (Intel hoặc Apple Silicon M1/M2/M3) hoặc Windows 10/11 64-bit | macOS (Apple Silicon M-series) hoặc Windows 11 |
| **Python** | Python 3.11 | Python 3.11 hoặc 3.12 |
| **Bộ nhớ RAM** | Tối thiểu 4 GB RAM | 8 GB – 16 GB RAM trở lên |
| **Ổ đĩa trống** | 2 GB dung lượng trống | 10 GB trở lên (đặc biệt khi huấn luyện dữ liệu lớn) |
| **Bộ tăng tốc phần cứng** | CPU đa nhân (hỗ trợ AVX2) | GPU NVIDIA hỗ trợ CUDA (nếu có nhu cầu huấn luyện mô hình nhanh) |

---

## 3. Cài đặt & Khởi động nhanh (Quick Start)

### 3.1. Cài đặt môi trường

Mở Terminal (trên macOS/Linux) hoặc PowerShell/CMD (trên Windows), chuyển đến thư mục gốc của dự án `Traffic_Vision`:

#### Trên macOS / Linux:
```bash
# 1. Tạo môi trường ảo Python
python3 -m venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Nâng cấp công cụ cài đặt pip và cài đặt gói dự án
pip install --upgrade pip
pip install -e ".[dev]"
```

#### Trên Windows:
```powershell
# 1. Tạo môi trường ảo Python
python -m venv .venv

# 2. Kích hoạt môi trường ảo
.venv\Scripts\Activate.ps1

# 3. Nâng cấp pip và cài đặt dự án
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3.2. Khởi tạo mô hình ban đầu (Bootstrap)
Trước khi chạy giao diện lần đầu, hệ thống cần thiết lập mô hình nền ban đầu (Baseline Model). Hãy chạy lệnh sau:
```bash
python scripts/bootstrap_baseline.py
```
> [!NOTE]
> Tập lệnh này sẽ tải trọng số `yolo11n.pt`, xuất định dạng chuẩn hóa sang ONNX tĩnh (`640x640`, batch 1, CPU) và lưu trữ bất biến tại thư mục `artifacts/baseline/`, đồng thời kích hoạt làm mô hình Production ban đầu tại `artifacts/production/`.

### 3.3. Khởi chạy ứng dụng Web (1-Click)

Dự án cung cấp các kịch bản tiện ích giúp khởi chạy ứng dụng tức thì:

* **Trên macOS:**
  * **Cách 1 (Chuột):** Nhấp đúp chuột vào file `run.command`. Cửa sổ Terminal sẽ bật lên kèm menu tương tác.
  * **Cách 2 (Terminal):** Chạy `./run_app.sh` (hoặc `./run.sh`).
* **Trên Windows:**
  * **Cách 1 (Chuột):** Nhấp đúp chuột vào file `run_app.bat` (hoặc `run.bat`).
  * **Cách 2 (CMD):** Gõ `run_app.bat`.
* **Khởi chạy trực tiếp bằng lệnh Streamlit:**
  ```bash
  streamlit run app.py
  ```

Sau khi khởi chạy thành công, giao diện quản trị Web sẽ tự động mở trên trình duyệt tại địa chỉ:
👉 **`http://localhost:8501`**

---

## 4. Hướng dẫn sử dụng Giao diện Web Dashboard

Giao diện TrafficVision được phân chia thành **Thanh điều hướng bên trái (Sidebar)** và **Khu vực hiển thị nội dung chính bên phải**.

Thanh Sidebar luôn hiển thị trạng thái thẻ mô hình đang vận hành (Model Card):
* **Đèn xanh lá (Production):** Mô hình đã được huấn luyện với tập 82 lớp biển báo Việt Nam.
* **Đèn vàng hổ phách (Baseline):** Mô hình khởi đầu sơ bộ (Chưa fine-tune).

---

### 4.1. Không gian "Phân tích" (Nhận dạng Ảnh & Video)

Đây là chức năng chính giúp người dùng tải lên dữ liệu phương tiện giao thông và kiểm tra kết quả phát hiện biển báo.

```
┌───────────────────────────────────────────────┬──────────────────────────────┐
│             KHUNG TRỰC QUAN (TRÁI)            │      BẢNG TÓM TẮT (PHẢI)     │
│ ┌──────────────────────┬────────────────────┐ │ ┌──────────────────────────┐ │
│ │  📷 Tab Hình ảnh     │  🎥 Tab Video      │ │ │ Biển báo: 3              │ │
│ └──────────────────────┴────────────────────┘ │ │ Độ tin cậy cao: 94.2%    │ │
│ [ Vùng kéo thả tệp tải lên (JPG/PNG/MP4) ]   │ │ Thời gian: 45.8 ms         │ │
│                                               │ │ Số lớp hỗ trợ: 82        │ │
│ [ Nút 🚀 Bắt đầu phân tích ]                  │ ├──────────────────────────┤ │
│ [ Hiển thị ảnh/video có bounding box ]        │ │ Danh sách biển phát hiện │ │
│                                               │ ├──────────────────────────┤ │
│                                               │ │ [ Tải tệp chú thích ]    │ │
│                                               │ │ [ Tải bảng CSV dữ liệu ] │ │
└───────────────────────────────────────────────┴──────────────────────────────┘
```

#### A. Phân tích Hình ảnh:
1. Nhấp chọn tab **📷 Hình ảnh**.
2. Kéo thả hoặc nhấn nút **Browse files** để chọn ảnh chụp giao thông (định dạng hỗ trợ: `.jpg`, `.jpeg`, `.png`, `.webp`).
3. Xem trước ảnh gốc được hiển thị trên màn hình.
4. Bấm nút **🚀 Bắt đầu phân tích ảnh**.
5. **Kết quả trả về:**
   * Ảnh đã qua xử lý được vẽ các khung bao màu (Bounding box) quanh biển báo kèm tên biển báo và chỉ số tin cậy (Confidence).
   * Bảng tóm tắt bên phải hiển thị: Tổng số biển báo phát hiện, biển báo có độ tin cậy cao nhất, thời gian suy luận (miligiây).
   * Bảng phân loại chi tiết các biển báo kèm số lượng phát hiện.
   * Cung cấp 2 nút tải về:
     - 📥 **Tải ảnh đã chú thích**: Lưu trữ hình ảnh kèm khung bao về máy.
     - 📊 **Tải kết quả CSV**: Xuất bảng kê chi tiết (Tọa độ $x_1, y_1, x_2, y_2$, Class ID, Tên biển báo, Điểm tin cậy).

#### B. Phân tích Video:
1. Nhấp chọn tab **🎥 Video**.
2. Chọn tệp video quay cảnh giao thông (định dạng hỗ trợ: `.mp4`, `.avi`, `.mov`).
3. Bấm nút **🚀 Bắt đầu phân tích video**.
4. Hệ thống hiển thị thanh tiến trình xử lý theo thời gian thực (Progress bar) cho biết khung hình đang đọc và tỷ lệ hoàn thành (%).
5. **Kết quả trả về:**
   * Trình phát video tích hợp sẵn cho phép xem lại toàn bộ đoạn phim đã được đóng khung biển báo mượt mà.
   * Hỗ trợ tải video kết quả `.mp4` và tệp thống kê tổng hợp `.csv`.

---

### 4.2. Không gian "Lịch sử" (Tra cứu dữ liệu phiên)

Toàn bộ các lần thực hiện phân tích ảnh hoặc video đều được ghi nhận tự động vào cơ sở dữ liệu SQLite cục bộ (`artifacts/state/trafficvision.db`).

* **Tính năng:**
  * Hiển thị bảng tổng hợp tối đa 100 phiên phân tích gần nhất.
  * Các cột dữ liệu chi tiết: **Thời gian thực hiện**, **Tên tệp gốc**, **Loại tệp (IMAGE/VIDEO)**, **Mã mô hình**, **Số đối tượng phát hiện**, **Thời gian xử lý (ms)**, **Ngưỡng Conf** và **Ngưỡng IoU** được áp dụng tại thời điểm đó.
* **Mục đích:** Giúp kiểm tra lại lịch sử vận hành, đối soát dữ liệu và phân tích tốc độ phản hồi của hệ thống.

---

### 4.3. Không gian "Thống kê" (Báo cáo & Phân bố biển báo)

Cung cấp bức tranh toàn cảnh về hiệu suất hoạt động và các dạng biển báo xuất hiện phổ biến nhất:

1. **Bộ 3 chỉ số đo lường hiệu quả (KPI):**
   * **Tổng số phiên phân tích:** Số lượng lượt ảnh và video đã chạy qua hệ thống.
   * **Tổng số biển báo phát hiện:** Tổng tích lũy tất cả các biển báo nhận dạng được.
   * **Thời gian trung bình (ms):** Tốc độ phản hồi trung bình của mô hình trên mỗi yêu cầu.
2. **Biểu đồ phân bố:** Hiển thị trực quan tần suất xuất hiện của từng loại biển báo, giúp nhận diện các biển báo thường gặp (như Giới hạn tốc độ, Cấm đỗ xe, Cấm đi ngược chiều,...) trên các cung đường được khảo sát.

---

### 4.4. Không gian "Huấn luyện AI" (Quy trình 4 bước Phase 2)

Khu vực **AI Experiment Lab** cho phép huấn luyện mô hình nhận dạng chuyên sâu cho biển báo Việt Nam thông qua quy trình MLOps tiêu chuẩn:

#### Bước 1: Tiếp nhận dữ liệu (Dataset Ingestion)
* **Nguồn dữ liệu:** Nạp tập dữ liệu YOLO chuẩn vào thư mục `artifacts/staging/` gồm 3 tập con: `train/`, `val/`, `test/` (mỗi tập chứa cặp thư mục `images/` và `labels/`).
* **Thử nghiệm nhanh:** Nếu chưa tải bộ dữ liệu lớn, bạn có thể bấm nút **Tạo dữ liệu thử nghiệm (Synthetic Fixture)** để tự động sinh 100 mẫu ảnh/nhãn mô phỏng.
* Bấm nút **Quét và nạp dữ liệu** để hệ thống kiểm đếm số lượng tệp ảnh và nhãn.

#### Bước 2: Cổng kiểm định chất lượng (Quality Gate) & Báo cáo EDA
* Nhấn nút **Chạy kiểm định Quality Gate & EDA**.
* Hệ thống tiến hành rà soát tự động 5 quy tắc chặn:
  1. `CORRUPT_IMAGE`: Kiểm tra ảnh có bị hỏng hoặc 0 byte không.
  2. `MALFORMED_YOLO_LINE`: Kiểm tra cấu trúc dòng nhãn (phải đủ 5 giá trị số).
  3. `CLASS_ID_OUT_OF_RANGE`: Đảm bảo Class ID nằm chuẩn xác trong khoảng từ `0` đến `81`.
  4. `INVALID_COORDINATES`: Kiểm tra tọa độ hộp bao trong khoảng `[0, 1]`.
  5. `DATA_LEAKAGE`: Phát hiện trùng lặp ảnh giữa tập Train và tập Val/Test thông qua mã băm SHA-256.
* Nếu dữ liệu vượt qua cổng kiểm định, hệ thống sẽ tạo một **Dataset Snapshot** bất biến lưu tại `artifacts/snapshots/<snapshot_id>/` kèm tệp `data.yaml` hợp thức và xuất báo cáo phân tích khám phá dữ liệu (EDA Report).

#### Bước 3: Huấn luyện nền (Background Training)
* Tùy chỉnh các tham số huấn luyện:
  * **Số Epoch:** Mặc định `50` (hoặc điều chỉnh từ 1 – 300).
  * **Batch Size:** Kích thước mini-batch (2, 4, 8, 16,...).
  * **Độ phân giải ảnh (Image Size):** Mặc định `640` px.
  * **Kiên nhẫn dừng sớm (Early Stopping Patience):** Dừng nếu mô hình không cải thiện sau $N$ epoch liên tiếp.
  * **Thiết bị (Device):** Tự động nhận diện `cuda` (nếu có GPU) hoặc `cpu` / `mps` (trên Mac).
* Bấm nút **Khởi động huấn luyện**.
* **Ưu điểm vượt trội:** Tiến trình huấn luyện chạy ngầm trong background process độc lập. Người dùng có thể tự do chuyển sang tab khác mà không làm gián đoạn quá trình train. Cửa sổ nhật ký (Realtime Log) cho phép xem quá trình học theo từng epoch và có nút **Dừng an toàn (Abort)** bất cứ khi nào cần.

#### Bước 4: Đóng gói Ứng viên & Thăng cấp (Candidate & Promotion)
* Khi hoàn thành phiên train, mô hình được tự động đánh giá:
  * Đo đạc chỉ số chất lượng: **mAP50**, **Precision**, **Recall**.
  * Xuất sang định dạng **ONNX** chuẩn hóa cho CPU.
  * Kiểm tra sai số số học giữa PyTorch và ONNX (`max_abs_diff <= 1e-3`).
  * Đo tốc độ FPS và thời gian trễ trung bình trên CPU.
* **Thăng cấp lên Production:** Người dùng kiểm tra thông số của Candidate, sau đó nhấn nút **Thăng cấp lên Production**.
* **Cơ chế sao lưu an toàn (Safe Atomic Swap):** Trước khi mô hình mới tiếp quản hệ thống, hệ thống sẽ tự động sao lưu toàn bộ mô hình cũ vào thư mục `artifacts/backups/<backup_id>/`.

---

### 4.5. Không gian "Thông tin mô hình" (Model Registry & Rollback)

Trang này dành cho quản trị viên và kỹ sư vận hành kiểm soát mô hình đang chạy:

1. **Thông tin định danh mô hình hiện tại:**
   * Mã mô hình (Model ID) & Trạng thái phân cấp (Baseline hoặc Production).
   * Backend tính toán (`ONNX`), độ phân giải ảnh (`640x640`).
   * Mã băm bảo mật SHA-256 kiểm tra tính toàn vẹn của tệp trọng số.
   * Danh sách đầy đủ 82 lớp biển báo (Xem bảng ID và tên tiếng Việt tương ứng).
2. **Lịch sử sao lưu & Phục hồi khẩn cấp (Rollback):**
   * Hiển thị danh sách các bản sao lưu đã được tạo khi thăng cấp.
   * **Cách Rollback:** Chọn bản sao lưu mong muốn trong danh sách thả xuống $\rightarrow$ Bấm nút **⏪ Phục hồi mô hình (Rollback)**. Toàn bộ hệ thống sẽ quay trở về phiên bản mô hình trước đó ngay lập tức mà không cần khởi động lại ứng dụng.

---

### 4.6. Không gian "Thiết lập" (Cấu hình ngưỡng Conf & IoU)

Cung cấp khả năng tùy chỉnh linh hoạt các siêu tham số suy luận theo điều kiện môi trường thực tế:

* **Ngưỡng tin cậy (Confidence Threshold):**
  * *Khoảng giá trị:* `0.05` đến `0.95` (Mặc định: `0.25`).
  * *Ý nghĩa:* Tăng ngưỡng này khi bạn muốn loại bỏ tối đa các phát hiện nhầm lẫn (False Positives); giảm ngưỡng này khi cần tìm tất cả các biển báo mờ, ở xa hoặc bị che khuất một phần.
* **Ngưỡng lọc trùng (IoU / NMS Threshold):**
  * *Khoảng giá trị:* `0.10` đến `0.95` (Mặc định: `0.45`).
  * *Ý nghĩa:* Dùng trong thuật toán Non-Maximum Suppression (NMS) để loại bỏ các hộp bao trùng lặp cùng phát hiện vào một biển báo.
* **Giới hạn kích thước tệp tải lên:**
  * Giới hạn dung lượng tối đa cho ảnh (MB) và video (MB).
* Bấm nút **💾 Lưu thiết lập**: Các giá trị mới sẽ có hiệu lực ngay lập tức trong tất cả các phiên phân tích kế tiếp.

---

## 5. Hướng dẫn công cụ dòng lệnh (CLI Scripts)

Dành cho các kỹ sư dữ liệu, quản trị viên hệ thống hoặc chạy tích hợp CI/CD tự động:

### 1. Khởi tạo baseline (`scripts/bootstrap_baseline.py`)
```bash
python scripts/bootstrap_baseline.py --project-root .
```

### 2. Kiểm thử nhanh qua dòng lệnh (`scripts/smoke_test.py`)
```bash
# Kiểm tra suy luận trên một tệp ảnh bất kỳ
python scripts/smoke_test.py --image path/to/bien_bao.jpg

# Hoặc chạy kiểm thử tự động với ảnh mẫu mặc định
python scripts/smoke_test.py
```

### 3. Kiểm định tập dữ liệu & EDA (`scripts/validate_dataset.py`)
```bash
python scripts/validate_dataset.py \
  --data-dir artifacts/staging \
  --output-dir artifacts/eda \
  --create-snapshot
```

### 4. Huấn luyện mô hình từ dòng lệnh (`scripts/train.py`)
```bash
python scripts/train.py \
  --data-yaml artifacts/snapshots/<snapshot_id>/data.yaml \
  --epochs 50 \
  --batch 4 \
  --imgsz 640 \
  --device cpu
```

### 5. Thăng cấp hoặc Hoàn tác mô hình (`scripts/promote_model.py`)
```bash
# Thăng cấp Candidate lên Production
python scripts/promote_model.py --candidate-dir artifacts/runs/<run_id>/candidate

# Xem danh sách các bản backup đã lưu
python scripts/promote_model.py --list-backups

# Hoàn tác về bản backup gần nhất
python scripts/promote_model.py --rollback

# Hoàn tác về một bản backup cụ thể theo ID
python scripts/promote_model.py --rollback --backup-id <backup_id>
```

---

## 6. Cấu trúc thư mục dữ liệu & Lưu trữ (Artifacts)

Hệ thống quản lý dữ liệu và mô hình tách bạch, minh bạch theo cấu trúc thư mục chuẩn:

```text
Traffic_Vision/
├── artifacts/
│   ├── baseline/       # Trọng số gốc YOLO11n + manifest.json bất biến
│   ├── production/     # Mô hình ONNX đang trực tiếp phục vụ suy luận
│   ├── backups/        # Các bản sao lưu an toàn tự động trước mỗi lần thăng cấp
│   ├── runs/           # Nhật ký huấn luyện (train.log), trọng số và Candidate đóng gói
│   ├── snapshots/      # Bản chụp dữ liệu bất biến + data.yaml chuẩn hóa
│   ├── staging/        # Thư mục chứa dữ liệu YOLO mới đưa vào
│   ├── outputs/        # Lưu trữ ảnh/video đã gắn nhãn và bảng CSV xuất ra
│   └── state/          # Cơ sở dữ liệu SQLite (trafficvision.db) và tệp settings.json
├── configs/            # Tệp cấu hình mặc định của hệ thống
├── docs/               # Toàn bộ tài liệu kỹ thuật, báo cáo và hướng dẫn sử dụng
├── scripts/            # Các công cụ script dòng lệnh thực thi
├── src/trafficvision/  # Mã nguồn lõi ứng dụng và giao diện Streamlit
└── tests/              # Bộ kiểm thử tự động (Unit test, Integration test)
```

---

## 7. Xử lý sự cố thường gặp (Troubleshooting)

### Q1: Giao diện hiển thị cảnh báo "Chưa cài đặt mô hình" hoặc "Chưa có Production"?
* **Nguyên nhân:** Lần đầu khởi chạy, thư mục `artifacts/production/` chưa có tệp `model.onnx`.
* **Cách khắc phục:** Chạy lệnh:
  ```bash
  python scripts/bootstrap_baseline.py
  ```
  Sau đó tải lại (F5) trang trình duyệt.

### Q2: Mô hình phát hiện nhầm các vật thể không phải biển báo?
* **Nguyên nhân:**
  1. Hệ thống đang sử dụng mô hình khởi đầu (Baseline COCO 80 lớp) chưa được thăng cấp lên mô hình biển báo chuyên dụng 82 lớp.
  2. Ngưỡng tin cậy (Confidence) đặt quá thấp (ví dụ: `0.10`).
* **Cách khắc phục:**
  1. Kiểm tra thẻ mô hình ở Sidebar. Nếu hiển thị nhãn `BASELINE`, hãy thực hiện quy trình tại trang **Huấn luyện AI** để huấn luyện và thăng cấp mô hình 82 lớp.
  2. Vào mục **Thiết lập**, tăng thanh trượt **Ngưỡng tin cậy** lên mức từ `0.35` đến `0.50` rồi bấm **Lưu thiết lập**.

### Q3: Video xử lý lâu hoặc báo lỗi khi tải lên?
* **Khuyến nghị:**
  * Video giao thông nên có độ dài vừa phải (từ 5 đến 60 giây) cho các bài kiểm tra thực tế trên CPU.
  * Nếu video có độ phân giải quá cao (4K), hãy cân nhắc nén xuống Full HD (1080p) hoặc HD (720p) trước khi tải lên để tối ưu tốc độ xử lý từng khung hình.

### Q4: Quá trình huấn luyện bị gián đoạn hoặc muốn dừng lại?
* Trong tab **Huấn luyện AI** $\rightarrow$ **Bước 3: Huấn luyện nền**, bạn có thể bấm nút **Dừng huấn luyện** bất cứ lúc nào. Tiến trình nền sẽ gửi tín hiệu ngắt an toàn (`SIGINT`) và lưu trữ trạng thái dở dang vào tệp log mà không làm treo hệ điều hành.

---
*Chúc bạn có trải nghiệm phân tích thị giác giao thông hiệu quả và chính xác cùng TrafficVision!*
