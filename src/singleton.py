"""단일 인스턴스 보장 모듈 (PID 파일 기반)"""

import os
import psutil
from pathlib import Path


class SingleInstance:
    """
    PID 파일 기반 단일 인스턴스 보장

    Mutex보다 안전함:
    - 프로세스 강제 종료/크래시 시에도 다음 실행 때 자동 복구
    - PID 파일로 실제 프로세스 존재 여부 확인
    """

    def __init__(self, lock_dir=None):
        """
        단일 인스턴스 체크

        Args:
            lock_dir: PID 파일을 저장할 디렉토리 (None이면 AppData\\Local\\MobiPics)
        """
        if lock_dir is None:
            lock_dir = Path.home() / "AppData" / "Local" / "MobiPics"

        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        self.lock_file = self.lock_dir / "mobipics.lock"
        self.already_running = False

        # 기존 PID 파일 확인
        if self.lock_file.exists():
            try:
                # 기존 PID 읽기
                with open(self.lock_file, "r") as f:
                    old_pid = int(f.read().strip())

                # 해당 PID의 프로세스가 실제로 존재하는지 확인
                if self._is_process_running(old_pid):
                    # 실제로 실행 중!
                    self.already_running = True
                    print(f"[SingleInstance] 이미 MobiPics가 실행 중입니다! (PID: {old_pid})")
                else:
                    # 프로세스가 죽었으면 stale lock 파일 삭제
                    print(f"[SingleInstance] 이전 프로세스(PID: {old_pid})가 종료됨. Lock 파일 정리 중...")
                    self.lock_file.unlink()
                    self._write_pid()
            except Exception as e:
                # 파일 읽기 실패 시 새로 생성
                print(f"[SingleInstance] Lock 파일 확인 실패: {e}. 새로 생성합니다.")
                self.lock_file.unlink(missing_ok=True)
                self._write_pid()
        else:
            # Lock 파일 없음 - 첫 실행
            self._write_pid()

    def _is_process_running(self, pid: int) -> bool:
        """
        PID로 프로세스가 실행 중인지 확인

        Args:
            pid: 확인할 프로세스 ID

        Returns:
            True: 실행 중, False: 종료됨
        """
        try:
            process = psutil.Process(pid)

            # 프로세스 이름 확인 (python.exe 또는 MobiPics.exe)
            name = process.name().lower()
            if "python" in name or "mobipics" in name:
                return True
            else:
                # 다른 프로그램이 같은 PID를 재사용한 경우
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    def _write_pid(self):
        """현재 프로세스 PID를 파일에 기록"""
        try:
            current_pid = os.getpid()
            with open(self.lock_file, "w") as f:
                f.write(str(current_pid))
            print(f"[SingleInstance] Lock 파일 생성: PID {current_pid}")
        except Exception as e:
            print(f"[SingleInstance] Lock 파일 생성 실패: {e}")

    def is_already_running(self) -> bool:
        """
        이미 실행 중인지 확인

        Returns:
            True: 이미 실행 중, False: 첫 실행
        """
        return self.already_running

    def release(self):
        """Lock 파일 삭제 (정상 종료 시)"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                print("[SingleInstance] Lock 파일 삭제 완료")
        except Exception as e:
            print(f"[SingleInstance] Lock 파일 삭제 실패: {e}")

    def __del__(self):
        """소멸자: Lock 파일 삭제"""
        self.release()

    def __enter__(self):
        """Context manager: with 문 지원"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: 종료 시 Lock 파일 삭제"""
        self.release()
