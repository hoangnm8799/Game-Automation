# Auto Craft Tool

Overlay QOL tool cho game, kiến trúc mở: mỗi feature 1 package trong
`features/`, tự đăng ký vào menu chính - thêm feature mới không phải sửa
code cũ.

## Cài đặt

```
pip install -r requirements.txt
```

**Windows:** nếu F6/F7/Space/F10 không nhận được lúc game đang focus, thử
chạy terminal/IDE với quyền **Administrator**. `pynput` hook phím ở mức
hệ thống, nhưng Windows (UIPI) chặn app quyền thấp hơn nhận phím khi cửa
sổ đang focus có quyền cao hơn (nhiều game/anti-cheat chạy elevated).

## Chạy

```
cd autocraft_tool
python main.py
```

Chạy vậy sẽ có cửa sổ cmd/terminal đứng bên cạnh - **cứ dùng cách này khi
nào còn nghi có lỗi**, vì traceback (nếu crash) chỉ hiện ra ở đây.

Muốn chạy hàng ngày **không hiện cửa sổ cmd**: double-click `main.pyw`
thay vì `main.py` (Windows tự chạy file `.pyw` bằng `pythonw.exe`, không
console). Cùng 1 app, cùng code - `main.pyw` chỉ gọi lại `run()` trong
`main.py`. Nhược điểm: nếu có lỗi thì cũng không thấy traceback ở đâu cả,
vì không có console để in ra.

**Menu chính tự ẩn khi mở 1 feature, tự hiện lại khi đóng cửa sổ feature
đó** (đóng bằng nút X trên cửa sổ feature) - hành vi này áp dụng chung
cho mọi feature, kể cả feature thêm sau này, không phải cấu hình gì
thêm.

## Hotkey (Auto Craft)

| Phím | Chức năng |
|------|-----------|
| F6 | Start |
| F7 | Stop |
| F10 | Pause / Resume |
| Space | Capture vị trí đang chờ (hover chuột tới vị trí trong game rồi bấm) |

Space dùng chung cho mọi ô vị trí (currency, target): bấm nút "Capture" ở
ô nào, ô đó "chờ" lần bấm Space tiếp theo.

**Lưu ý khi dùng Space làm capture hotkey:** đây là hotkey TOÀN CỤC (global)
- nó bắt luôn cả khi bạn gõ dấu cách vào bất kỳ ô nhập nào (kể cả ô nhập
regex/tên profile ngay trong tool này, hoặc chat trong game), và cả khi
Space đang được bind cho hành động khác trong game (nhảy, dùng vật
phẩm,...). Nếu thấy phiền, đổi `CAPTURE_HOTKEY` trong `core/capture.py`
sang phím khác ít dùng hơn (`<f9>`, `<f8>`, `<insert>`,...) - `ui/widgets.py`
tự lấy tên phím hiển thị trên nút từ hằng số này, không cần sửa thêm chỗ
nào khác.

Đưa chuột vào **góc màn hình** bất kỳ lúc nào để kích hoạt fail-safe của
pyautogui, dừng khẩn cấp ngay lập tức - độc lập với các hotkey trên.

## Nếu click không ăn trong game

Một số game (raw input / DirectInput) không nhận click giả lập kiểu
`SetCursorPos` mà `pyautogui` dùng. Nếu gặp tình trạng này: cài
`pip install pydirectinput`, rồi sửa `core/input_actions.py` - đây là
file DUY NHẤT gọi thẳng `pyautogui`, nên chỉ cần đổi import
`import pyautogui as ...` / các lệnh gọi ở đây sang `pydirectinput`
(cùng API: `moveTo`, `click`, `hotkey`), không phải đụng file nào khác.

## Thêm feature mới

1. Tạo thư mục `features/<ten_feature>/`
2. Viết `ui.py` bên trong: 1 class kế thừa `BaseFeature`
   (`features/base_feature.py`), decorate bằng `@register`
   (`features/registry.py`), nhận `AppContext` trong `open(self, ctx)`
   để dùng chung `ctx.hotkeys` / `ctx.capture`
3. Thêm 1 dòng import trong `features/__init__.py`

Không cần sửa `ui/main_menu.py` hay bất cứ feature nào khác.

## Đóng gói .exe + tự cập nhật qua GitHub (share công khai)

Không cần server riêng - dùng GitHub Releases làm nơi chứa bản build,
app tự gọi GitHub API để kiểm tra/tải bản mới. Repo **public**: ai cũng
xem/tải được trực tiếp từ trang Releases, không cần bạn gửi file tay,
không cần token gì cả (API GitHub cho phép gọi không cần đăng nhập với
repo public).

### Lần đầu setup (làm 1 lần)

1. **Tạo repo GitHub:** github.com → nút **New** → đặt tên → chọn
   **Public** → **Create repository**.

2. **Đẩy code lên** (chạy trong thư mục `autocraft_tool/`):
   ```
   git init
   git add .
   git commit -m "First version"
   git branch -M main
   git remote add origin https://github.com/<username>/<ten-repo>.git
   git push -u origin main
   ```
   `.gitignore` đã loại sẵn `configs/`, `dist/`, `build/` - không lo đẩy
   nhầm profile cá nhân hay file build lên. `core/updater.py` không có bí
   mật gì trong đó (không token) nên đẩy source lên public thoải mái.

3. **Điền vào `core/updater.py`:**
   ```python
   GITHUB_OWNER = "<username>"
   GITHUB_REPO = "<ten-repo>"
   ```
   (`GITHUB_TOKEN` để nguyên chuỗi rỗng - repo public không cần.)

4. **Build file exe** - 2 cách, chọn 1:

   **Cách A - build tay trên máy (đơn giản, khuyên dùng cho lần đầu):**
   double-click `build.bat` → ra file `dist\AutoCraftTool.exe` → vào repo
   trên GitHub → **Releases** → **Create a new release** → **Tag**: gõ
   `v1.0.0` (khớp `core/version.py`) → kéo thả file exe vào ô đính kèm →
   **Publish release**.

   **Cách B - để GitHub tự build (workflow có sẵn ở
   `.github/workflows/build-release.yml`):** không cần cài gì trên máy
   bạn, GitHub tự cài Python + PyInstaller + build trên server của họ.
   Chỉ cần:
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Đợi 1-2 phút, vào tab **Actions** trên repo xem tiến trình, xong tự
   động có Release kèm file exe - không phải tự tạo Release tay. Public
   repo thì phút chạy Actions này **miễn phí không giới hạn**.

   Cách A ít bước hơn để bắt đầu, thấy chắc chắn build chạy được trên máy
   mình trước. Cách B tiện hơn về lâu dài (gõ 2 dòng lệnh là xong, không
   cần mở GitHub tạo release tay mỗi lần) nhưng phải tin tưởng workflow
   chạy đúng - có thể dùng cả 2 (build tay cho chắc, xác nhận ổn rồi
   chuyển hẳn sang B).

5. **Xong, gửi ai đó cần cài lần đầu link:**
   `https://github.com/<username>/<ten-repo>/releases/latest` - ai vào
   cũng tải trực tiếp được, không cần bạn gửi file, không cần tài khoản
   GitHub.

### Từ lần sau (mỗi khi có bản mới)

1. Sửa code.
2. Tăng số trong `core/version.py`, ví dụ `"1.0.0"` → `"1.1.0"` (bắt buộc
   - đây là version app tự so sánh, không phải git tag; quên bước này
   thì app luôn nghĩ vẫn có update dù đã tải bản mới nhất rồi).
3. Build lại bằng cách A hoặc B ở trên, tag/release tăng theo, ví dụ
   `v1.1.0`.
4. Mọi người mở app, bấm **"Kiểm tra update"** ở cuối menu chính, app tự
   tải và tự khởi động lại bản mới.

## Cấu trúc

```
core/                    # dùng chung cho MỌI feature
  position.py             # Position(x, y) + to_dict/from_dict
  input_actions.py         # nơi DUY NHẤT gọi pyautogui/pyperclip
  regex_rules.py            # SingleRule/GroupRule/RuleSet - engine AND/OR
  hotkeys.py                 # HotkeyManager (pynput global hotkey)
  capture.py                  # CaptureController - hover+hotkey capture, thread-safe
  app_context.py                # bundle root+hotkeys+capture, truyền cho feature
  config_store.py                # save/load/list/delete profile JSON - biết cả path khi đóng gói .exe
  version.py                      # APP_VERSION - tăng trước mỗi lần build release mới
  updater.py                       # check/tải/tự thay bản mới từ GitHub Releases

features/
  base_feature.py          # abstract class mọi feature phải theo
  registry.py                # @register + all_features()
  auto_craft/
    config.py                 # CraftStep, CraftTarget, CraftConfig
    engine.py                  # vòng lặp craft, chạy background thread
    ui.py                       # Tkinter UI, đăng ký vào registry

ui/
  main_menu.py              # cửa sổ chính - đọc registry, tạo AppContext, ẩn/hiện khi mở feature, nút update
  widgets.py                  # PositionRow - widget vị trí dùng chung

main.py                    # entry point CÓ console (dùng lúc cần xem lỗi)
main.pyw                    # entry point KHÔNG console (double-click dùng hàng ngày)
build.bat                    # đóng gói thành dist\AutoCraftTool.exe (build tay - cách A)
.gitignore                    # loại configs/, dist/, build/ khỏi git
.github/workflows/
  build-release.yml            # GitHub tự build + tạo release khi push tag v* (cách B)
configs/                     # nơi lưu profile JSON, tự tạo khi bấm Lưu profile
```

## Lưu ý

Tool này tự động click chuột theo vòng lặp và tự đọc clipboard để quyết
định khi nào dừng - nếu dùng cho game có luật riêng về macro/bot (ví dụ
kiểu game currency-craft dạng Path of Exile), tự kiểm tra quy định của
game trước khi chạy full-auto lâu dài.
