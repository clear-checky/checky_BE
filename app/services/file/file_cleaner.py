import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)

class FileCleaner:
    """파일 자동 삭제 서비스"""
    
    def __init__(self, upload_dir: str = "files", ttl_hours: int = 24):
        self.upload_dir = Path(upload_dir)
        self.ttl_hours = ttl_hours
        self.is_running = False
        
    async def start_cleaner(self):
        """파일 정리 서비스 시작"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info(f"파일 정리 서비스 시작 (TTL: {self.ttl_hours}시간)")
        
        while self.is_running:
            try:
                await self.clean_old_files()
                # 1시간마다 실행
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"파일 정리 중 오류: {e}")
                await asyncio.sleep(300)  # 5분 후 재시도
    
    async def stop_cleaner(self):
        """파일 정리 서비스 중지"""
        self.is_running = False
        logger.info("파일 정리 서비스 중지")
    
    async def clean_old_files(self):
        """오래된 파일들을 삭제합니다"""
        if not self.upload_dir.exists():
            return
            
        current_time = datetime.now()
        deleted_count = 0
        total_size = 0
        
        try:
            # files 디렉토리의 모든 파일 확인
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    # 파일 생성 시간 확인
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    file_age = current_time - file_mtime
                    
                    # TTL 초과 시 삭제
                    if file_age > timedelta(hours=self.ttl_hours):
                        file_size = file_path.stat().st_size
                        file_path.unlink()  # 파일 삭제
                        deleted_count += 1
                        total_size += file_size
                        logger.info(f"파일 삭제: {file_path.name} (크기: {file_size} bytes)")
            
            if deleted_count > 0:
                logger.info(f"파일 정리 완료: {deleted_count}개 파일 삭제, {total_size} bytes 절약")
                
        except Exception as e:
            logger.error(f"파일 정리 중 오류: {e}")
    
    async def clean_file_now(self, file_path: str):
        """특정 파일을 즉시 삭제합니다"""
        try:
            path = Path(file_path)
            if path.exists():
                file_size = path.stat().st_size
                path.unlink()
                logger.info(f"파일 즉시 삭제: {path.name} (크기: {file_size} bytes)")
                return True
        except Exception as e:
            logger.error(f"파일 삭제 실패: {e}")
        return False
    
    def get_file_age(self, file_path: str) -> timedelta:
        """파일의 나이를 반환합니다"""
        try:
            path = Path(file_path)
            if path.exists():
                file_mtime = datetime.fromtimestamp(path.stat().st_mtime)
                return datetime.now() - file_mtime
        except Exception as e:
            logger.error(f"파일 나이 확인 실패: {e}")
        return timedelta(0)
    
    def is_file_expired(self, file_path: str) -> bool:
        """파일이 만료되었는지 확인합니다"""
        age = self.get_file_age(file_path)
        return age > timedelta(hours=self.ttl_hours)

# 전역 파일 정리 서비스 인스턴스
file_cleaner = FileCleaner()
