@echo off
chcp 65001 >nul
echo MobiPics 개발 모드 실행...
echo.

REM 의존성 설치 확인
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo 의존성 설치 중...
    pip install -r requirements.txt
    echo.
)

REM 프로그램 실행 (UTF-8 환경 변수 설정)
set PYTHONIOENCODING=utf-8
python src/main.py

pause
