"""파일 정리 로직 모듈"""

import shutil
import hashlib
from pathlib import Path
from utils import parse_filename_date


class FileOrganizer:
    """스크린샷 파일 자동 정리"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        파일의 SHA256 해시 계산
        
        Args:
            file_path: 해시를 계산할 파일 경로
            
        Returns:
            SHA256 해시 문자열
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # 큰 파일을 위해 청크 단위로 읽기
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"해시 계산 실패: {file_path}, {e}")
            return ""
    
    def _get_unique_filename(self, target_folder: Path, filename: str) -> Path:
        """
        중복되지 않는 파일명 생성
        
        Args:
            target_folder: 대상 폴더
            filename: 원본 파일명
            
        Returns:
            고유한 파일 경로
        """
        name_stem = Path(filename).stem  # 확장자 제외
        ext = Path(filename).suffix       # 확장자
        
        counter = 1
        while True:
            new_name = f"{name_stem}_{counter}{ext}"
            new_path = target_folder / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # 안전장치: 1000개 이상은 비정상
            if counter > 1000:
                raise RuntimeError(f"중복 파일이 너무 많음: {filename}")

    def organize_file(self, file_path: str) -> bool:
        """
        파일을 년-월 폴더로 정리

        Args:
            file_path: 정리할 파일의 전체 경로

        Returns:
            성공 여부
        """
        try:
            file_path = Path(file_path)

            # 파일이 존재하는지 확인
            if not file_path.exists():
                print(f"파일이 존재하지 않음: {file_path}")
                return False

            # 파일명에서 날짜 추출
            filename = file_path.name
            date_info = parse_filename_date(filename)

            if not date_info:
                print(f"날짜 파싱 실패: {filename}")
                return False

            year, month = date_info
            folder_name = f"{year}-{month}"

            # 대상 폴더 생성
            target_folder = self.base_path / folder_name
            target_folder.mkdir(parents=True, exist_ok=True)

            # 대상 파일 경로
            target_path = target_folder / filename

            # 파일이 이미 존재하는 경우 해시 비교
            if target_path.exists():
                print(f"파일이 이미 존재함: {target_path}")
                
                # 해시 비교
                source_hash = self._calculate_file_hash(file_path)
                target_hash = self._calculate_file_hash(target_path)
                
                if source_hash and target_hash and source_hash == target_hash:
                    # 동일한 파일 - 원본 삭제
                    print(f"  → 동일한 파일 확인됨 (해시 일치). 원본 삭제")
                    file_path.unlink()
                    return True
                else:
                    # 다른 파일 - 고유한 이름으로 저장
                    print(f"  → 다른 파일 감지됨 (해시 불일치). 파일명 변경하여 보존")
                    target_path = self._get_unique_filename(target_folder, filename)
                    print(f"  → 새 파일명: {target_path.name}")
                    shutil.move(str(file_path), str(target_path))
                    print(f"파일 이동 완료: {filename} -> {folder_name}/{target_path.name}")
                    return True
            
            # 파일이 없으면 그냥 이동
            shutil.move(str(file_path), str(target_path))
            print(f"파일 이동 완료: {filename} -> {folder_name}/")
            return True

        except Exception as e:
            print(f"파일 정리 실패: {file_path}, {e}")
            return False

    def organize_existing_files(self):
        """
        기존 파일들을 모두 정리
        프로그램 시작 시 한 번 실행
        """
        try:
            if not self.base_path.exists():
                print(f"폴더가 존재하지 않음: {self.base_path}")
                return

            # MabinogiMobile_로 시작하는 png 파일만 찾기
            files = [f for f in self.base_path.glob("MabinogiMobile_*.png")]

            if not files:
                print("정리할 파일이 없습니다.")
                return

            success_count = 0
            for file_path in files:
                if self.organize_file(str(file_path)):
                    success_count += 1

            print(f"기존 파일 정리 완료: {success_count}/{len(files)}")

        except Exception as e:
            print(f"기존 파일 정리 중 오류: {e}")

    def update_base_path(self, new_path: str):
        """기본 경로 업데이트"""
        self.base_path = Path(new_path)
