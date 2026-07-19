# Auto Craft Tool

Tool Windows hỗ trợ Auto Craft với các thao tác chuột và kiểm tra regex sau từng lần craft.

## Cài đặt và chạy local

```bash
pip install -r requirements.txt
python main.py
```

Khi dùng hằng ngày, có thể double-click `main.pyw` để chạy không hiện cửa sổ terminal. Dùng `main.py` khi cần xem lỗi.

## Cài đặt hotkey

Mở menu chính rồi bấm **Cài đặt hotkey**. Có thể đặt phím Start, Stop, Pause/Resume và Capture vị trí ngay trong app.

- Ví dụ hợp lệ: `F8`, `Space`, `Ctrl+F8`.
- Các hotkey phải khác nhau.
- Thay đổi được lưu tại `configs/app/hotkeys.json` cạnh ứng dụng và áp dụng ngay, kể cả khi cửa sổ Auto Craft đang mở.
- Đưa chuột vào bất kỳ góc màn hình nào để kích hoạt fail-safe của PyAutoGUI, dừng khẩn cấp.

## Độ chính xác và tốc độ craft

Thao tác click đã được rút ngắn để craft nhanh hơn. Sau mỗi lần áp currency, app vẫn xóa clipboard, copy lại text mới và chỉ kiểm regex trên text mới đó. Nếu game không trả text kịp thời, app dừng thay vì tiếp tục craft với kết quả check không chắc chắn.

## Build và chia sẻ bản `.exe`

Push một Git tag theo dạng `vMAJOR.MINOR.PATCH` để GitHub Actions tự build và tạo Release:

```bash
git tag v1.0.4
git push origin v1.0.4
```

Git tag tự quyết định version nhúng trong file `.exe`; không cần sửa `core/version.py`. Người dùng tải bản mới thủ công tại trang Releases của repo:

`https://github.com/hoangnm8799/Game-Automation/releases/latest`

App có thể kiểm tra, tải và khởi động lại bản mới từ GitHub Releases ngay trong menu chính.

## Lưu ý

Một số game có thể chặn input giả lập hoặc cấm macro/bot. Hãy tự kiểm tra quy định của game trước khi dùng.
