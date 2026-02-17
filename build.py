"""빌드 스크립트 - 버전 정보를 포함하여 exe 생성"""

import sys
import os
import subprocess
import shutil
import re
from pathlib import Path


def get_version():
    """
    src/__init__.py에서 버전 정보 추출
    * Import 시에는 모듈의 모든 코드가 실행되어 의존성 문제가 발생할 수 있음으로,
      대신 정규식을 사용하여 해당 값만 추출합니다.
    """
    try:
        init_file = Path("src/__init__.py")
        content = init_file.read_text(encoding="utf-8")

        # __version__ = "1.0.0" 형태 찾기
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            version = match.group(1)
            print(f"버전: {version}")
            return version
        else:
            raise ValueError("__version__을 찾을 수 없음")
    except Exception as e:
        print(f"버전 정보를 가져올 수 없어 기본값 사용: {e}")
        return "1.0.0"


# 버전 정보 가져오기
__version__ = get_version()


def remove_existing_exe():
    """동일한 이름의 기존 exe 파일 삭제"""
    print("\n[1/3] 기존 exe 파일 확인 중...")

    exe_name = f"MobiPics_v{__version__}.exe"
    exe_path = Path("dist") / exe_name

    if exe_path.exists():
        try:
            exe_path.unlink()
            print(f"  - {exe_name} 삭제")
        except Exception as e:
            print(f"  - {exe_name} 삭제 실패: {e}")
            print(f"  ⚠ 파일이 실행 중일 수 있습니다. 종료 후 다시 시도하세요.")
            sys.exit(1)
    else:
        print(f"  - 기존 파일 없음")


def install_dependencies():
    """의존성 설치"""
    print("\n[2/3] 의존성 확인 및 설치 중...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)


def build_exe():
    """PyInstaller로 exe 빌드"""
    print("\n[3/3] 실행 파일 빌드 중...")

    # 파일명에 버전 포함
    exe_name = f"MobiPics_v{__version__}"

    cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", f"--icon=assets/icon.ico", "--add-data", "assets;assets", "--paths=src", f"--name={exe_name}", "src/main.py", "--clean"]

    print(f"실행 파일명: {exe_name}.exe")
    subprocess.run(cmd, check=True)


def main():
    """메인 빌드 프로세스"""
    print("=" * 60)
    print("MobiPics 빌드 시작")
    print("=" * 60)

    try:
        remove_existing_exe()
        install_dependencies()
        build_exe()

        print("\n" + "=" * 60)
        print("✓ 빌드 완료!")
        print(f"실행 파일 위치: dist/MobiPics_v{__version__}.exe")
        print("=" * 60)

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 빌드 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
