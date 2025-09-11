from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
from typing import Optional
import aiofiles
import mimetypes

from app.schemas.contract.file_upload import (
    FileUploadResponse,
    FileValidationError,
    FileType,
    UploadStatusResponse
)
from app.services.text_extractor import text_extractor

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB (프론트엔드와 동일)
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png'}

# 업로드 디렉토리 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """파일 유효성 검사"""
    if file.size and file.size > MAX_FILE_SIZE:
        return False, f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 허용됩니다."
    
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, None


def get_file_type(filename: str) -> FileType:
    """파일명으로부터 파일 타입 결정"""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        return FileType.PDF
    elif ext in ['.doc', '.docx']:
        return FileType.DOCX
    elif ext == '.txt':
        return FileType.TXT
    elif ext in ['.jpg', '.jpeg', '.png']:
        return FileType.IMAGE
    else:
        return FileType.UNKNOWN


async def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    """업로드된 파일을 저장하고 file_id와 file_path 반환"""
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1].lower()
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
    
    async with aiofiles.open(file_path, "wb") as f:
        while content := await file.read(1024):
            await f.write(content)
    
    return file_id, file_path


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="업로드할 파일"),
    description: Optional[str] = None
):
    """파일 업로드 및 텍스트 추출"""
    try:
        # 파일 유효성 검사
        is_valid, error_message = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # 파일 저장
        file_id, file_path = await save_uploaded_file(file)
        file_type = get_file_type(file.filename)
        file_size = os.path.getsize(file_path)
        
        # 텍스트 추출
        extracted_text = None
        try:
            extracted_text = await text_extractor.extract_text(file_path, file_type)
        except Exception as e:
            print(f"텍스트 추출 실패: {str(e)}")
            # 텍스트 추출 실패해도 업로드는 성공으로 처리
        
        return FileUploadResponse(
            success=True,
            message="파일이 성공적으로 업로드되었습니다.",
            file_id=file_id,
            file_name=file.filename,
            file_size=file_size,
            file_type=file_type,
            extracted_text=extracted_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}")


@router.get("/status/{file_id}", response_model=UploadStatusResponse)
async def get_upload_status(file_id: str):
    """업로드 상태 확인"""
    try:
        # 파일 존재 여부 확인
        file_exists = False
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_id):
                file_exists = True
                break
        
        if not file_exists:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        return UploadStatusResponse(
            file_id=file_id,
            status="uploaded",
            message="파일이 업로드되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 중 오류가 발생했습니다: {str(e)}")


@router.delete("/{file_id}")
async def delete_uploaded_file(file_id: str):
    """업로드된 파일 삭제"""
    try:
        deleted = False
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                os.remove(file_path)
                deleted = True
                break
        
        if not deleted:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        return {"success": True, "message": "파일이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}")
