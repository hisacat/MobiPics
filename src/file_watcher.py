"""파일 시스템 모니터링 모듈"""

import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# 파일 쓰기 완료 대기 설정
FILE_WRITE_CHECK_INTERVAL = 0.1  # 파일 크기 체크 간격 (초)
FILE_WRITE_MAX_WAIT = 5.0  # 최대 대기 시간 (초)


class ScreenshotEventHandler(FileSystemEventHandler):
    """스크린샷 파일 생성 이벤트 핸들러"""

    def __init__(self, organizer):
        super().__init__()
        self.organizer = organizer

    def _wait_for_file_write_complete(self, file_path: str) -> bool:
        """
        파일 쓰기가 완료될 때까지 대기

        Args:
            file_path: 확인할 파일 경로

        Returns:
            True: 쓰기 완료, False: 타임아웃
        """
        file_path = Path(file_path)
        elapsed_time = 0.0

        while elapsed_time < FILE_WRITE_MAX_WAIT:
            try:
                # 파일이 존재하는지 확인
                if not file_path.exists():
                    time.sleep(FILE_WRITE_CHECK_INTERVAL)
                    elapsed_time += FILE_WRITE_CHECK_INTERVAL
                    continue

                # 파일을 읽기 모드로 열어보기 (쓰기 중이면 실패)
                with open(file_path, "rb") as f:
                    # 파일을 열 수 있으면 쓰기 완료!
                    return True

            except (IOError, PermissionError, OSError):
                # 파일이 아직 쓰기 중이거나 접근 불가
                time.sleep(FILE_WRITE_CHECK_INTERVAL)
                elapsed_time += FILE_WRITE_CHECK_INTERVAL
            except Exception as e:
                print(f"파일 쓰기 완료 대기 중 예상치 못한 오류: {e}")
                time.sleep(FILE_WRITE_CHECK_INTERVAL)
                elapsed_time += FILE_WRITE_CHECK_INTERVAL

        # 타임아웃
        print(f"파일 쓰기 완료 대기 타임아웃 ({FILE_WRITE_MAX_WAIT}초): {file_path}")
        return False

    def on_created(self, event: FileCreatedEvent):
        """파일 생성 이벤트 처리"""
        if event.is_directory:
            return

        file_path = event.src_path
        filename = Path(file_path).name

        # MabinogiMobile_로 시작하고 .png로 끝나는 파일만 처리
        if filename.startswith("MabinogiMobile_") and filename.endswith(".png"):
            print(f"새 스크린샷 감지: {filename}")

            # 파일 쓰기가 완료될 때까지 대기
            if self._wait_for_file_write_complete(file_path):
                # 파일 정리
                self.organizer.organize_file(file_path)
            else:
                print(f"파일 쓰기 완료 대기 실패: {filename}")


class FileWatcher:
    """파일 시스템 감시자"""

    def __init__(self, watch_path: str, organizer):
        self.watch_path = watch_path
        self.organizer = organizer
        self.observer = None
        self.event_handler = ScreenshotEventHandler(organizer)

    def start(self):
        """감시 시작"""
        try:
            # 경로가 존재하는지 확인
            watch_path = Path(self.watch_path)
            if not watch_path.exists():
                print(f"감시 경로 생성: {self.watch_path}")
                watch_path.mkdir(parents=True, exist_ok=True)

            # Observer 생성 및 시작
            self.observer = Observer()
            self.observer.schedule(self.event_handler, self.watch_path, recursive=False)
            self.observer.start()

            print(f"파일 감시 시작: {self.watch_path}")

        except Exception as e:
            import traceback

            print(f"파일 감시 시작 실패: {e}")
            traceback.print_exc()

    def stop(self):
        """감시 중지"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)  # 최대 5초 대기
            print("파일 감시 중지")

    def update_watch_path(self, new_path: str):
        """감시 경로 변경"""
        self.stop()
        self.watch_path = new_path
        self.start()
