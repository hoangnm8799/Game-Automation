@echo off
REM build.bat - dong goi thanh 1 file .exe duy nhat, khong hien console.
REM Dung: build.bat 1.2.3
REM Neu khong truyen version, ban build local se la 0.0.0-dev.

set "APP_VERSION=%~1"
if "%APP_VERSION%"=="" set "APP_VERSION=0.0.0-dev"
> core\_build_version.py echo APP_VERSION = "%APP_VERSION%"

pip install -r requirements.txt pyinstaller

pyinstaller --onefile --windowed --name AutoCraftTool ^
  --collect-data certifi ^
  --hidden-import pynput.keyboard._win32 ^
  --hidden-import pynput.mouse._win32 ^
  main.py

del core\_build_version.py 2>NUL

echo.
echo Xong - file exe nam o dist\AutoCraftTool.exe
echo (Neu Windows Defender/SmartScreen canh bao khi chay: binh thuong voi
echo  exe khong co chu ky so - bam "More info" roi "Run anyway".)
pause
