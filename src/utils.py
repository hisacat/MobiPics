"""유틸리티 함수 모듈"""

import os
import winreg
import sys
from pathlib import Path


def get_exe_path() -> str:
    """실행 파일 경로 반환 (PyInstaller 호환)"""
    if getattr(sys, "frozen", False):
        # PyInstaller로 패키징된 경우
        return sys.executable
    else:
        # 일반 Python 스크립트로 실행된 경우
        return os.path.abspath(sys.argv[0])


def add_to_startup(app_name: str = "MobiPics") -> bool:
    """시작 프로그램에 등록"""
    try:
        exe_path = get_exe_path()
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        return True
    except Exception as e:
        print(f"시작 프로그램 등록 실패: {e}")
        return False


def remove_from_startup(app_name: str = "MobiPics") -> bool:
    """시작 프로그램에서 제거"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass  # 이미 없는 경우
        return True
    except Exception as e:
        print(f"시작 프로그램 제거 실패: {e}")
        return False


def is_in_startup(app_name: str = "MobiPics") -> bool:
    """시작 프로그램에 등록되어 있는지 확인"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            try:
                winreg.QueryValueEx(key, app_name)
                return True
            except FileNotFoundError:
                return False
    except Exception as e:
        print(f"시작 프로그램 확인 실패: {e}")
        return False


def open_folder(folder_path: str):
    """탐색기로 폴더 열기"""
    try:
        os.startfile(folder_path)
    except Exception as e:
        print(f"폴더 열기 실패: {e}")


def parse_filename_date(filename: str) -> tuple:
    """
    파일명에서 날짜 추출
    예: MabinogiMobile_2025081212213272.png -> (2025, 08)
    """
    try:
        # MabinogiMobile_ 제거
        if not filename.startswith("MabinogiMobile_"):
            return None

        date_part = filename.replace("MabinogiMobile_", "").split(".")[0]

        # 최소 8자리 (YYYYMMDD)
        if len(date_part) < 8:
            return None

        year = date_part[:4]
        month = date_part[4:6]

        return (year, month)
    except Exception as e:
        print(f"파일명 파싱 실패: {filename}, {e}")
        return None
