"""MobiPics 메인 진입점"""

import sys
import os
from tkinter import Tk, messagebox

# Windows 콘솔 UTF-8 출력 설정 (개발 모드에서만)
if sys.platform == "win32" and not getattr(sys, "frozen", False):
    # PyInstaller로 패키징된 exe가 아닌 경우에만 실행
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

from singleton import SingleInstance
from tray_app import TrayApp


def show_already_running_message():
    """이미 실행 중 메시지 표시"""
    root = Tk()
    root.withdraw()  # 메인 윈도우 숨기기
    root.attributes("-topmost", True)

    messagebox.showwarning("MobiPics", "MobiPics가 이미 실행 중입니다.\n\n" "시스템 트레이에서 아이콘을 확인하세요.")

    root.destroy()


def main():
    """메인 함수"""
    # 단일 인스턴스 체크
    with SingleInstance() as instance:
        if instance.is_already_running():
            print("[Main] 이미 MobiPics가 실행 중입니다.")
            show_already_running_message()
            sys.exit(0)

        # 정상 실행
        try:
            app = TrayApp()
            app.run()
        except KeyboardInterrupt:
            print("\n프로그램 종료")
            sys.exit(0)
        except Exception as e:
            print(f"오류 발생: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
