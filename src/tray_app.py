"""시스템 트레이 애플리케이션 모듈"""

import os
import sys
import webbrowser
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from pathlib import Path
from tkinter import Tk, filedialog, messagebox
from config import Config
from utils import add_to_startup, remove_from_startup, is_in_startup, open_folder
from file_organizer import FileOrganizer
from file_watcher import FileWatcher
from updater import check_for_updates_on_startup, get_latest_version_info
from __init__ import GITHUB_URL, MARKER_FILE_NAME, __version__


class TrayApp:
    """시스템 트레이 애플리케이션"""

    def __init__(self):
        print("[TrayApp] 초기화 시작...")
        self.config = Config()
        print(f"[TrayApp] 설정 로드 완료: {self.config.screenshot_path}")

        self.organizer = FileOrganizer(self.config.screenshot_path)
        print("[TrayApp] 파일 정리기 생성 완료")

        self.watcher = FileWatcher(self.config.screenshot_path, self.organizer)
        print("[TrayApp] 파일 감시자 생성 완료")

        self.icon = None

        # 프로그램 시작 시 기존 파일 정리 (매 실행마다)
        print("[TrayApp] 기존 파일 정리 중...")
        self.organizer.organize_existing_files()
        print("[TrayApp] 기존 파일 정리 완료")

        # 마커 파일 생성
        self.create_marker_file(self.config.screenshot_path)

        # 백그라운드에서 업데이트 확인 (프로그램 시작 지연 방지)
        threading.Thread(target=self._check_updates_on_startup, daemon=True).start()

        print("[TrayApp] 초기화 완료")

    def create_marker_file(self, folder_path: str):
        """
        대상 폴더에 MobiPics.txt 마커 파일 생성

        Args:
            folder_path: 마커 파일을 생성할 폴더 경로
        """
        try:
            folder = Path(folder_path)
            folder.mkdir(parents=True, exist_ok=True)

            marker_file = folder / MARKER_FILE_NAME
            marker_content = f"""이 디렉토리는 MobiPics에서 관리되고 있습니다.
{GITHUB_URL}
"""

            with open(marker_file, "w", encoding="utf-8") as f:
                f.write(marker_content)

            print(f"[TrayApp] 마커 파일 생성: {marker_file}")
        except Exception as e:
            print(f"[TrayApp] 마커 파일 생성 실패: {e}")

    def remove_marker_file(self, folder_path: str):
        """
        대상 폴더의 MobiPics.txt 마커 파일 삭제

        Args:
            folder_path: 마커 파일을 삭제할 폴더 경로
        """
        try:
            marker_file = Path(folder_path) / MARKER_FILE_NAME
            if marker_file.exists():
                marker_file.unlink()
                print(f"[TrayApp] 마커 파일 삭제: {marker_file}")
        except Exception as e:
            print(f"[TrayApp] 마커 파일 삭제 실패: {e}")

    def load_icon_image(self):
        """트레이 아이콘 이미지 로드"""
        try:
            # 실행 파일 위치 기준으로 assets 폴더 찾기
            if getattr(sys, "frozen", False):
                # PyInstaller로 패키징된 경우 - _MEIPASS 사용 (임시 추출 폴더)
                base_path = Path(sys._MEIPASS)
            else:
                # 일반 Python 스크립트로 실행된 경우
                base_path = Path(__file__).parent.parent

            icon_path = base_path / "assets" / "icon.ico"

            if icon_path.exists():
                print(f"[TrayApp] 아이콘 로드: {icon_path}")
                return Image.open(icon_path)
            else:
                print(f"[TrayApp] 아이콘 파일을 찾을 수 없음: {icon_path}")
                print(f"[TrayApp] base_path: {base_path}")
                return self._create_fallback_icon()
        except Exception as e:
            print(f"[TrayApp] 아이콘 로드 실패: {e}")
            return self._create_fallback_icon()

    def _create_fallback_icon(self):
        """폴백 아이콘 생성 (icon.ico를 못 찾을 경우)"""
        width = 64
        height = 64
        image = Image.new("RGB", (width, height), "white")
        dc = ImageDraw.Draw(image)

        # 파란색 원 그리기
        dc.ellipse([10, 10, width - 10, height - 10], fill="#4A90E2", outline="#2E5C8A")

        # 가운데 'M' 글자 (흰색)
        dc.text((20, 15), "M", fill="white")

        return image

    def on_auto_start_toggle(self, icon, item):
        """자동 시작 토글"""
        current = is_in_startup()

        if current:
            if remove_from_startup():
                self.config.auto_start = False
                print("시작 프로그램에서 제거됨")
        else:
            if add_to_startup():
                self.config.auto_start = True
                print("시작 프로그램에 등록됨")

        # 아이콘 메뉴 업데이트
        icon.update_menu()

    def on_open_folder(self):
        """스크린샷 폴더 열기 (더블클릭 시에도 동작)"""
        print("[TrayApp] 스크린샷 폴더 열기")
        open_folder(self.config.screenshot_path)

    def on_change_folder(self):
        """스크린샷 폴더 변경"""
        # Tkinter 루트 윈도우 숨기기
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        # 폴더 선택 다이얼로그
        folder_path = filedialog.askdirectory(title="스크린샷 폴더 선택", initialdir=self.config.screenshot_path)

        root.destroy()

        if folder_path:
            print(f"[TrayApp] 스크린샷 폴더 변경: {folder_path}")

            # 기존 폴더의 마커 파일 삭제
            old_path = self.config.screenshot_path
            self.remove_marker_file(old_path)

            # 설정 업데이트
            self.config.screenshot_path = folder_path

            # 정리기 및 감시자 경로 업데이트
            self.organizer.update_base_path(folder_path)
            self.watcher.update_watch_path(folder_path)

            # 변경된 폴더의 기존 파일 즉시 정리
            print("[TrayApp] 변경된 폴더의 기존 파일 정리 중...")
            self.organizer.organize_existing_files()
            print("[TrayApp] 기존 파일 정리 완료")

            # 새 폴더에 마커 파일 생성
            self.create_marker_file(folder_path)

    def on_reset_folder(self):
        """스크린샷 폴더를 기본값으로 되돌리기"""
        from config import get_windows_pictures_folder
        from pathlib import Path

        # 기본 경로 계산
        default_path = str(Path(get_windows_pictures_folder()) / "Mabinogi Mobile" / "screenshots")

        # 이미 기본값이면 메시지 표시
        if self.config.screenshot_path == default_path:
            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            from tkinter import messagebox

            messagebox.showinfo("MobiPics", "이미 기본 경로를 사용 중입니다.")
            root.destroy()
            return

        print(f"[TrayApp] 스크린샷 폴더를 기본값으로 되돌림: {default_path}")

        # 기존 폴더의 마커 파일 삭제
        old_path = self.config.screenshot_path
        self.remove_marker_file(old_path)

        # 설정 업데이트
        self.config.screenshot_path = default_path

        # 정리기 및 감시자 경로 업데이트
        self.organizer.update_base_path(default_path)
        self.watcher.update_watch_path(default_path)

        # 기본 폴더의 기존 파일 즉시 정리
        print("[TrayApp] 기본 폴더의 기존 파일 정리 중...")
        self.organizer.organize_existing_files()
        print("[TrayApp] 기존 파일 정리 완료")

        # 기본 폴더에 마커 파일 생성
        self.create_marker_file(default_path)

    def on_open_github(self):
        """GitHub 페이지를 브라우저로 열기"""
        try:
            webbrowser.open(GITHUB_URL)
            print(f"[TrayApp] GitHub 페이지 열기: {GITHUB_URL}")
        except Exception as e:
            print(f"[TrayApp] GitHub 페이지 열기 실패: {e}")

    def _check_updates_on_startup(self):
        """프로그램 시작 시 업데이트 확인 (백그라운드 스레드)"""
        update_info = check_for_updates_on_startup()

        if update_info["available"]:
            self._show_update_available_dialog(update_info, is_manual=False)

    def _show_update_available_dialog(self, update_info: dict, is_manual: bool = True):
        """
        업데이트 가능 메시지 표시

        Args:
            update_info: 업데이트 정보 dict
            is_manual: 수동 확인 여부 (메뉴에서 클릭)
        """
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        latest_version = update_info["version"]

        response = messagebox.askyesno(
            "MobiPics 업데이트", f"신규 버전 ({latest_version})이 있습니다.\n\n" f"현재 버전: v{__version__}\n" f"최신 버전: {latest_version}\n\n" f"다운로드 페이지로 이동할까요?", icon="info"
        )

        root.destroy()

        if response:
            webbrowser.open(update_info["download_url"])
            print(f"[Updater] 다운로드 페이지 열기: {update_info['download_url']}")

    def on_check_updates(self):
        """업데이트 확인 (메뉴에서 수동 실행)"""
        print("[Updater] 업데이트 확인 시작 (수동)")

        update_info = get_latest_version_info()

        if update_info["available"]:
            # 업데이트 있음
            self._show_update_available_dialog(update_info, is_manual=True)
        else:
            # 최신 버전 또는 오류
            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            if update_info["error"] == "no_release":
                messagebox.showinfo("MobiPics 업데이트", "릴리스 정보를 찾을 수 없습니다.\n\n" f"현재 버전: v{__version__}")
            elif update_info["error"] == "network":
                messagebox.showerror("MobiPics 업데이트", "네트워크 연결을 확인할 수 없습니다.\n\n" "인터넷 연결을 확인하고 다시 시도해주세요.")
            elif update_info["error"]:
                messagebox.showerror("MobiPics 업데이트", f"업데이트 확인 중 오류가 발생했습니다.\n\n{update_info['error']}")
            else:
                messagebox.showinfo("MobiPics 업데이트", f"현재 최신 버전입니다. (v{__version__})")

            root.destroy()

    def on_quit(self, icon):
        """프로그램 종료"""
        print("프로그램 종료 중...")
        self.watcher.stop()
        icon.stop()

    def create_menu(self):
        """트레이 메뉴 생성"""
        return pystray.Menu(
            item(f"MobiPics v{__version__}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("시스템 시작 시 자동 실행", self.on_auto_start_toggle, checked=lambda item: is_in_startup()),
            pystray.Menu.SEPARATOR,
            item("스크린샷 폴더 열기", lambda: self.on_open_folder(), default=True),  # 더블클릭 기본 동작
            item("스크린샷 대상 폴더 변경", lambda: self.on_change_folder()),
            item("스크린샷 대상 폴더 기본값으로 되돌리기", lambda: self.on_reset_folder()),
            pystray.Menu.SEPARATOR,
            item("업데이트 확인", lambda: self.on_check_updates()),
            item("GitHub 페이지로 이동", lambda: self.on_open_github()),
            pystray.Menu.SEPARATOR,
            item("종료", self.on_quit),
        )

    def run(self):
        """애플리케이션 실행"""
        print("[TrayApp] 애플리케이션 실행 시작...")

        # 파일 감시 시작
        print("[TrayApp] 파일 감시 시작 중...")
        self.watcher.start()
        print("[TrayApp] 파일 감시 시작 완료")

        # 트레이 아이콘 생성 및 실행
        print("[TrayApp] 트레이 아이콘 생성 중...")
        icon_image = self.load_icon_image()
        self.icon = pystray.Icon("MobiPics", icon_image, "MobiPics - 모비노기 스크린샷 자동 정리", menu=self.create_menu())

        print("[TrayApp] 시스템 트레이 애플리케이션 시작")
        print(f"[TrayApp] 감시 경로: {self.config.screenshot_path}")
        print("[TrayApp] 트레이 아이콘을 확인하세요! (작업 표시줄 우측 하단)")
        print("[TrayApp] 종료하려면 트레이 아이콘 우클릭 -> 종료")

        # 블로킹 모드로 실행
        self.icon.run()
