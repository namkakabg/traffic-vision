#!/usr/bin/env bash
set -e

# Xác định thư mục gốc dự án
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "=============================================================="
echo "          TRAFFICVISION - HỆ THỐNG KIỂM THỬ & KHỞI CHẠY (macOS)"
echo "=============================================================="
echo ""

# 1. Tìm kiếm môi trường Python
PYTHON_CMD=""
if [ -f "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$REPO_ROOT/.venv/bin/python"
    echo "[*] Sử dụng môi trường ảo: .venv"
elif [ -f "$REPO_ROOT/venv/bin/python" ]; then
    PYTHON_CMD="$REPO_ROOT/venv/bin/python"
    echo "[*] Sử dụng môi trường ảo: venv"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo "[*] Sử dụng python3 hệ thống"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
    echo "[*] Sử dụng python hệ thống"
else
    echo "[!] Lỗi: Không tìm thấy Python trên hệ thống!"
    echo "    Vui lòng cài đặt Python 3.11+ hoặc khởi tạo môi trường .venv"
    exit 1
fi

# 2. Tự động kiểm tra baseline model
if [ ! -f "$REPO_ROOT/artifacts/production/model.onnx" ]; then
    echo ""
    echo "[*] Phát hiện baseline model chưa được khởi tạo!"
    echo "[*] Đang tự động chạy scripts/bootstrap_baseline.py..."
    "$PYTHON_CMD" scripts/bootstrap_baseline.py
    echo "[+] Khởi tạo baseline model thành công!"
    echo ""
fi

# 3. Xử lý tham số dòng lệnh nếu có (app / test / smoke)
TARGET_ACTION="${1:-}"

run_dashboard() {
    echo ""
    echo "[*] Đang khởi chạy Streamlit Web Dashboard..."
    echo "[*] Trình duyệt sẽ tự động mở tại: http://localhost:8501"
    echo "[*] Nhấn Ctrl+C tại Terminal để dừng ứng dụng."
    echo ""
    exec "$PYTHON_CMD" -m streamlit run app.py
}

run_tests() {
    echo ""
    echo "[*] Đang chạy toàn bộ bộ kiểm thử tự động (pytest)..."
    echo ""
    "$PYTHON_CMD" -m pytest -v
}

run_smoke() {
    echo ""
    echo "[*] Đang chạy Smoke Test với pipeline nội bộ..."
    echo ""
    "$PYTHON_CMD" scripts/smoke_test.py
}

case "$TARGET_ACTION" in
    app)
        run_dashboard
        ;;
    test)
        run_tests
        exit 0
        ;;
    smoke)
        run_smoke
        exit 0
        ;;
esac

# 4. Hiển thị menu nếu không truyền tham số
while true; do
    echo ""
    echo "=============================================================="
    echo "                      LỰA CHỌN HOẠT ĐỘNG"
    echo "=============================================================="
    echo " [1] Khởi chạy ứng dụng Web Dashboard (Streamlit)"
    echo " [2] Chạy toàn bộ test kiểm thử tự động (Pytest)"
    echo " [3] Chạy Smoke Test nhanh (Kiểm thử model & pipeline)"
    echo " [4] Thoát"
    echo "=============================================================="
    read -r -p "Nhập lựa chọn [1/2/3/4] (Mặc định là 1): " CHOICE
    CHOICE="${CHOICE:-1}"

    case "$CHOICE" in
        1)
            run_dashboard
            ;;
        2)
            run_tests
            ;;
        3)
            run_smoke
            ;;
        4)
            echo "[*] Tạm biệt!"
            exit 0
            ;;
        *)
            echo "[!] Lựa chọn không hợp lệ, vui lòng thử lại."
            ;;
    esac
done
