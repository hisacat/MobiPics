"""설정 관리 모듈"""

import os
import json
import winreg
from pathlib import Path


def get_windows_pictures_folder() -> str:
    """
    Windows의 실제 사진 폴더 경로 가져오기
    (사용자가 사진 폴더를 이동했을 경우도 정확하게 감지)
    레지스트리에서 User Shell Folders의 My Pictures 값을 읽음
    """
    try:
        # Windows 레지스트리에서 사진 폴더 경로 읽기
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            # "My Pictures" 값 읽기
            pictures_path, _ = winreg.QueryValueEx(key, "My Pictures")

            # 환경 변수 확장 (예: %USERPROFILE% -> C:\Users\Username)
            pictures_path = os.path.expandvars(pictures_path)

            # 경로가 존재하는지 확인
            if os.path.exists(pictures_path):
                return pictures_path
            else:
                # 경로가 존재하지 않으면 기본 경로 사용
                return str(Path.home() / "Pictures")

    except Exception as e:
        print(f"레지스트리에서 사진 폴더 가져오기 실패: {e}")
        # 폴백: 기본 경로 사용
        return str(Path.home() / "Pictures")


class Config:
    """애플리케이션 설정 관리"""

    CONFIG_DIR = Path.home() / "AppData" / "Local" / "MobiPics"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self):
        self.config_dir = self.CONFIG_DIR
        self.config_file = self.CONFIG_FILE
        self.config = self._load_config()

    def _get_default_screenshot_path(self) -> str:
        """기본 스크린샷 경로 반환 (Windows 실제 사진 폴더 기반)"""
        pictures_folder = Path(get_windows_pictures_folder())
        return str(pictures_folder / "Mabinogi Mobile" / "screenshots")

    def _load_config(self) -> dict:
        """설정 파일 로드"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 실패: {e}")
                return self._default_config()
        else:
            return self._default_config()

    def _default_config(self) -> dict:
        """기본 설정 반환"""
        return {"screenshot_path": self._get_default_screenshot_path(), "auto_start": False, "first_run": True}

    def save(self):
        """설정을 파일에 저장"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")

    @property
    def screenshot_path(self) -> str:
        """스크린샷 경로"""
        return self.config.get("screenshot_path", self._get_default_screenshot_path())

    @screenshot_path.setter
    def screenshot_path(self, value: str):
        self.config["screenshot_path"] = value
        self.save()

    @property
    def auto_start(self) -> bool:
        """자동 시작 여부"""
        return self.config.get("auto_start", False)

    @auto_start.setter
    def auto_start(self, value: bool):
        self.config["auto_start"] = value
        self.save()

    @property
    def first_run(self) -> bool:
        """첫 실행 여부"""
        return self.config.get("first_run", True)

    @first_run.setter
    def first_run(self, value: bool):
        self.config["first_run"] = value
        self.save()
