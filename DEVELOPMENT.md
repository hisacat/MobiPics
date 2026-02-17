# MobiPics 개발 가이드

## 프로젝트 구조

```
MobiPics/
├── src/                         # 소스 코드
│   ├── __init__.py              # 패키지 초기화 + 전역 상수 (버전, GitHub URL)
│   ├── main.py                  # 메인 진입점 + 단일 인스턴스 체크
│   ├── singleton.py             # 단일 인스턴스 보장 (PID 파일 기반)
│   ├── config.py                # 설정 관리 (JSON) + Windows 경로 감지
│   ├── utils.py                 # 유틸리티 (시작 프로그램 등록, 파일명 파싱)
│   ├── file_organizer.py        # 파일 정리 로직 + 중복 파일 해시 비교
│   ├── file_watcher.py          # 실시간 파일 모니터링 (watchdog)
│   ├── updater.py               # 업데이트 확인 (GitHub API)
│   └── tray_app.py              # 시스템 트레이 UI + 메뉴
├── assets/
│   └── icon.ico                 # 트레이 아이콘
├── requirements.txt             # Python 의존성
├── build.py                     # 빌드 스크립트 (버전별 exe 생성)
├── build.bat                    # 빌드 실행 배치 파일
├── run_dev.bat                  # 개발 모드 실행 배치 파일
├── README.md                    # 프로젝트 개요
├── DEVELOPMENT.md               # 개발자 가이드
└── LICENSE.txt                  # 라이센스
```

## 개발 환경 설정

### 1. 요구사항
- **Python 3.10 이상** (3.13에서 테스트됨)
- Windows 10/11

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

**설치되는 패키지:**
- `watchdog>=6.0.0` - 파일 시스템 모니터링
- `pystray>=0.19.5` - 시스템 트레이 UI
- `Pillow>=10.2.0` - 이미지 처리
- `pyinstaller>=6.3.0` - exe 빌드
- `psutil>=5.9.0` - 프로세스 관리
- `requests>=2.31.0` - HTTP 요청 (업데이트 확인)

### 3. 개발 모드 실행
```bash
# 배치 파일 실행
run_dev.bat

# 또는 Python 스크립트 직접 실행
python src/main.py
```

## 빌드 (배포용 EXE 생성)

### 간편 빌드
```bash
# 배치 파일 실행
build.bat

# 또는 Python 스크립트 직접 실행
python build.py
```

### 빌드 결과

```
dist/MobiPics_v{버전}.exe
```

### 빌드 옵션

자동으로 적용되는 PyInstaller 옵션:
- `--onefile`: 단일 exe 파일
- `--windowed`: 콘솔 창 숨김
- `--icon=assets/icon.ico`: 아이콘 설정
- `--add-data "assets;assets"`: assets 폴더 포함
- `--paths=src`: 소스 코드 경로
- `--clean`: 캐시 정리 후 빌드

### 버전 변경 방법

`src/__init__.py`에서 버전만 수정:
```python
__version__ = "1.0.0"  # 버전 변경
```

## 주요 모듈 설명

### 📦 src/__init__.py
**패키지 초기화 및 전역 상수**

```python
__version__ = "1.0.0"                              # 버전 (트레이 메뉴 + exe 파일명에 사용)
GITHUB_URL = "https://github.com/hisacat/MobiPics" # GitHub URL
MARKER_FILE_NAME = "MobiPics.txt"                  # 마커 파일명
```

### 🔐 src/singleton.py
**단일 인스턴스 보장 (PID 파일 기반)**

- **PID 파일 위치**: `%LOCALAPPDATA%\MobiPics\mobipics.lock`
- **동작 방식**:
  1. PID 파일 확인
  2. 해당 PID의 프로세스가 실행 중인지 `psutil`로 확인
  3. 실행 중이면 경고 메시지 표시 후 종료
  4. 죽은 프로세스면 stale lock 파일 자동 정리

### ⚙️ src/config.py
**설정 관리 및 Windows 경로 감지**

- **설정 파일**: `%LOCALAPPDATA%\MobiPics\config.json`
- **저장 내용**:
  ```json
  {
    "screenshot_path": "C:/Users/.../Mabinogi Mobile/screenshots",
    "auto_start": false
  }
  ```
- **Windows 사진 폴더 감지**:
  - 레지스트리 `HKEY_CURRENT_USER\...\User Shell Folders\My Pictures` 읽기
  - 환경 변수 자동 확장 (`%USERPROFILE%` 등)

### 📁 src/file_organizer.py
**파일 정리 로직**

- **파일명 파싱**: `MabinogiMobile_2025081212213272.png` → `2025-08`
- **폴더 생성**: 년-월 폴더 자동 생성
- **파일 이동**: `shutil.move()` 사용 (같은 폴더 내 하위 폴더로 이동)
- **중복 파일 처리**:
  - 동일 파일명 존재 시 SHA256 해시 비교
  - 해시 일치 (같은 파일): 원본 삭제
  - 해시 불일치 (다른 파일): `파일명_1.png`, `파일명_2.png` 형태로 보존
- **대량 정리**: 프로그램 시작 시 기존 파일 일괄 정리

### 👁️ src/file_watcher.py
**실시간 파일 시스템 모니터링**

- **라이브러리**: `watchdog>=6.0.0` (Python 3.13 호환)
- **감지 이벤트**: `FileCreatedEvent`
- **필터링**: `MabinogiMobile_*.png` 파일만 처리
- **안전성**: 파일 쓰기 완료 뒤에 이동
  - 파일 열기 시도 (Windows 배타적 잠금 활용)
  - 0.1초 간격으로 재시도, 최대 5초 대기 (타임아웃)
- **경로 변경**: 런타임에 감시 경로 변경 가능

### 🖥️ src/tray_app.py
**시스템 트레이 애플리케이션**

- **아이콘**: `assets/Icon.ico` 로드 (개발/배포 모드 자동 감지)
- **트레이 메뉴**: 버전, 스크린샷 폴더 열기/변경, 업데이트 확인 등의 메뉴 제공
- **마커 파일 관리**:
  - 감시 폴더에 `MobiPics.txt` 생성
  - 폴더 변경 시 기존 마커 삭제 후 새 폴더에 생성
  - 내용: "이 디렉토리는 MobiPics에서 관리되고 있습니다. {GitHub URL}"
- **업데이트 확인**:
  - 프로그램 시작 시 자동 확인
  - 새 버전 있으면 다이얼로그 표시

### 🛠️ src/utils.py
**유틸리티 함수**

- `get_exe_path()`: 실행 파일 경로 (개발/배포 모드 자동 감지)
- `add_to_startup()`: Windows 시작 프로그램 등록
- `remove_from_startup()`: 시작 프로그램 제거
- `is_in_startup()`: 등록 여부 확인
- `open_folder()`: 탐색기로 폴더 열기
- `parse_filename_date()`: 파일명에서 날짜 추출

### 🔄 src/updater.py
**업데이트 확인 (GitHub Releases API)**

- **GitHub API**: `https://api.github.com/repos/{owner}/{repo}/releases/latest`
- **동작 방식**:
  1. 프로그램 시작 백그라운드에서 자동 확인
  2. 새 버전 있으면: 신규 버전 안내 다이얼로그 표시
  3. Yes 선택 시 Release 페이지 열기
- **수동 확인**: 트레이 메뉴 "업데이트 확인" 클릭

## 문제 해결

### 개발 모드 실행 오류

**ImportError: attempted relative import**
- 원인: `src/` 폴더 내에서 직접 실행
- 해결: 프로젝트 루트에서 `python src/main.py` 실행

**ModuleNotFoundError**
- 원인: 의존성 미설치
- 해결: `pip install -r requirements.txt`

**한글 깨짐 (콘솔)**
- 원인: Windows 콘솔 인코딩
- 해결: `run_dev.bat` 사용 (자동으로 UTF-8 설정)

### 실행 관련

**파일이 이동되지 않음**
- 확인 사항:
  - 파일명이 `MabinogiMobile_`로 시작하는지
  - 확장자가 `.png`인지
  - 날짜 부분이 최소 8자리(YYYYMMDD)인지
- 개발 모드 실행하여 콘솔 로그 확인

**"이미 실행 중" 메시지가 계속 뜸**
- 원인: Lock 파일이 남아있음
- 해결: `%LOCALAPPDATA%\MobiPics\mobipics.lock` 수동 삭제
