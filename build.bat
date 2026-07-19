@echo off
REM build.bat - dong goi thanh 1 file .exe duy nhat, khong hien console.
REM Chay lai file nay moi lan muon build ban moi (nho tang APP_VERSION
REM trong core/version.py TRUOC khi build).

pip install pyinstaller

pyinstaller --onefile --windowed --name AutoCraftTool ^
  --hidden-import pynput.keyboard._win32 ^
  --hidden-import pynput.mouse._win32 ^
  main.py

echo.
echo Xong - file exe nam o dist\AutoCraftTool.exe
echo (Neu Windows Defender/SmartScreen canh bao khi chay: binh thuong voi
echo  exe khong co chu ky so - bam "More info" roi "Run anyway".)
pause
