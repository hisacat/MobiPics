"""업데이트 확인 모듈"""

import requests
from packaging import version
from __init__ import __version__, GITHUB_URL


def parse_github_repo_from_url(url: str) -> tuple:
    """
    GitHub URL에서 owner와 repo 추출

    Args:
        url: GitHub URL

    Returns:
        (owner, repo) 튜플
    """
    # https://github.com/hisacat/MobiPics → hisacat, MobiPics
    url = url.rstrip("/")
    parts = url.split("/")

    if len(parts) >= 2:
        return parts[-2], parts[-1]

    raise ValueError(f"잘못된 GitHub URL: {url}")


def get_latest_version_info() -> dict:
    """
    GitHub API에서 최신 릴리스 정보 가져오기

    Returns:
        {
            'version': 'v1.0.1',
            'download_url': 'https://github.com/.../releases/latest',
            'available': True/False
        }
    """
    try:
        owner, repo = parse_github_repo_from_url(GITHUB_URL)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

        print(f"[Updater] 업데이트 확인 중: {api_url}")

        response = requests.get(api_url, timeout=5)

        if response.status_code == 404:
            # 릴리스가 아직 없음
            print("[Updater] 릴리스가 존재하지 않습니다.")
            return {"version": None, "download_url": f"{GITHUB_URL}/releases", "available": False, "error": "no_release"}

        response.raise_for_status()
        data = response.json()

        latest_version = data["tag_name"]  # "v1.0.1" 또는 "1.0.1"
        download_url = data["html_url"]  # Release 페이지 URL

        # 'v' 접두사 제거
        latest_version_clean = latest_version.lstrip("v")
        current_version_clean = __version__.lstrip("v")

        # 버전 비교
        is_newer = version.parse(latest_version_clean) > version.parse(current_version_clean)

        print(f"[Updater] 현재 버전: v{current_version_clean}")
        print(f"[Updater] 최신 버전: v{latest_version_clean}")
        print(f"[Updater] 업데이트 필요: {is_newer}")

        return {"version": f"v{latest_version_clean}", "download_url": download_url, "available": is_newer, "error": None}

    except requests.exceptions.RequestException as e:
        print(f"[Updater] 네트워크 오류: {e}")
        return {"version": None, "download_url": f"{GITHUB_URL}/releases", "available": False, "error": "network"}
    except Exception as e:
        print(f"[Updater] 업데이트 확인 실패: {e}")
        return {"version": None, "download_url": f"{GITHUB_URL}/releases", "available": False, "error": str(e)}


def check_for_updates_on_startup() -> dict:
    """
    프로그램 시작 시 업데이트 확인 (백그라운드)
    실패해도 프로그램 실행은 계속됨

    Returns:
        get_latest_version_info()와 동일
    """
    try:
        return get_latest_version_info()
    except Exception as e:
        print(f"[Updater] 시작 시 업데이트 확인 실패 (무시): {e}")
        return {"version": None, "download_url": f"{GITHUB_URL}/releases", "available": False, "error": "startup_check_failed"}
