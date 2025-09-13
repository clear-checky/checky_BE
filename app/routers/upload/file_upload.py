from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
import time
from typing import Optional
import aiofiles
import mimetypes
from datetime import datetime
from app.schemas.upload.file_upload import (
    FileUploadResponse,
    FileValidationError,
    FileType,
    UploadStatusResponse,
    AnalysisResult
)
from app.schemas.contract.types import AnalyzeRequest, AnalyzeResponse
from app.services.file.text_extractor import text_extractor
from app.services.file.file_cleaner import file_cleaner

router = APIRouter(prefix="/upload", tags=["upload"])

# 렌더 환경에 맞는 임시 디렉토리 사용
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB로 줄임 (렌더 메모리 제한 고려)
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.hwp', '.jpg', '.jpeg', '.png'}

# 렌더 환경에서 사용 가능한 디렉토리 찾기
UPLOAD_DIR = None
possible_dirs = [
    "/tmp",
    "/tmp/files", 
    os.path.join(os.getcwd(), "files"),
    os.path.join(os.path.expanduser("~"), "files")
]

for dir_path in possible_dirs:
    try:
        os.makedirs(dir_path, exist_ok=True)
        # 쓰기 권한 테스트
        test_file = os.path.join(dir_path, "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        UPLOAD_DIR = dir_path
        print(f"업로드 디렉토리 설정됨: {UPLOAD_DIR}")
        break
    except Exception as e:
        print(f"디렉토리 {dir_path} 사용 불가: {e}")
        continue

if UPLOAD_DIR is None:
    raise RuntimeError("사용 가능한 업로드 디렉토리를 찾을 수 없습니다.")

# 파일별 상태 저장 (실제로는 DB 사용)
file_statuses = {}

# 분석 결과 저장소 (실제로는 DB 사용 권장)
analysis_results = {}


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
    elif ext == '.hwp':
        return FileType.HWP
    elif ext in ['.jpg', '.jpeg', '.png']:
        return FileType.IMAGE
    else:
        return FileType.UNKNOWN


async def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    """업로드된 파일을 저장하고 task_id와 file_path 반환"""
    task_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1].lower()
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}{file_ext}")
    
    print(f"파일 저장 시도: {file_path}")
    
    # 파일 내용을 메모리에 먼저 읽기 (렌더 환경 고려)
    file_content = await file.read()
    print(f"파일 크기: {len(file_content)} bytes")
    
    try:
        # 동기 방식으로 파일 저장 (더 안정적)
        with open(file_path, "wb") as f:
            f.write(file_content)
        print(f"파일 저장 완료: {file_path}")
        return task_id, file_path
    except Exception as e:
        print(f"파일 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="업로드할 파일"),
    description: Optional[str] = None
):
    """파일 업로드 및 텍스트 추출"""
    try:
        print(f"파일 업로드 시작: {file.filename}, 크기: {file.size}")
        
        # 파일 유효성 검사
        is_valid, error_message = validate_file(file)
        if not is_valid:
            print(f"파일 유효성 검사 실패: {error_message}")
            raise HTTPException(status_code=400, detail=error_message)
        
        print("파일 유효성 검사 통과")
        
        # 파일 저장
        task_id, file_path = await save_uploaded_file(file)
        file_type = get_file_type(file.filename)
        file_size = os.path.getsize(file_path)
        
        print(f"파일 저장 완료 - task_id: {task_id}, file_path: {file_path}, file_type: {file_type}")
        
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
            task_id=task_id,
            file_name=file.filename,
            file_size=file_size,
            file_type=file_type,
            extracted_text=extracted_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}")


@router.get("/status/{task_id}", response_model=UploadStatusResponse)
async def get_upload_status(task_id: str):
    """업로드 상태 확인 (Mock 상태 전환)"""
    try:
        # 파일 존재 여부 확인
        file_exists = False
        file_path = None
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(task_id):
                file_exists = True
                file_path = os.path.join(UPLOAD_DIR, filename)
                break
        
        if not file_exists:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 파일 만료 확인
        if file_path and file_cleaner.is_file_expired(file_path):
            # 만료된 파일 삭제
            await file_cleaner.clean_file_now(file_path)
            raise HTTPException(status_code=410, detail="파일이 만료되어 삭제되었습니다. (24시간 TTL)")
        
        # Mock 상태 전환 로직
        if task_id not in file_statuses:
            file_statuses[task_id] = {
                "status": "uploaded",
                "created_at": time.time()
            }
        
        current_time = time.time()
        created_at = file_statuses[task_id]["created_at"]
        elapsed_time = current_time - created_at
        
        # 5초 후 processing, 10초 후 completed
        if elapsed_time < 5:
            status = "uploaded"
            message = "파일이 업로드되었습니다."
        elif elapsed_time < 10:
            status = "processing"
            message = "분석 중입니다..."
        else:
            status = "completed"
            message = "분석이 완료되었습니다."
        
        file_statuses[task_id]["status"] = status
        
        return UploadStatusResponse(
            task_id=task_id,
            status=status,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 중 오류가 발생했습니다: {str(e)}")


@router.get("/analysis/{task_id}", response_model=AnalysisResult)
async def get_analysis_result(task_id: str):
    """분석 결과 조회 (Mock 데이터)"""
    try:
        # 파일 존재 여부 확인
        file_exists = False
        file_path = None
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(task_id):
                file_exists = True
                file_path = os.path.join(UPLOAD_DIR, filename)
                break
        
        if not file_exists:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 파일 만료 확인
        if file_path and file_cleaner.is_file_expired(file_path):
            # 만료된 파일 삭제
            await file_cleaner.clean_file_now(file_path)
            raise HTTPException(status_code=410, detail="파일이 만료되어 삭제되었습니다. (24시간 TTL)")
        
        # 실제 분석 결과가 있으면 반환, 없으면 Mock 데이터 반환
        if task_id in analysis_results:
            return analysis_results[task_id]
        
        # AI가 추출한 제목 사용 (실제로는 analyze_contract에서 처리됨)
        # 여기서는 기본값만 사용
        title = "계약서 분석 결과"
        
        # Mock 분석 결과 데이터
        return AnalysisResult(
            id=task_id,
            title=title,
            articles=[
                {
                    "id": 1,
                    "title": "제1조 (근로계약 기간)",
                    "sentences": [
                        {
                            "id": "s1-1",
                            "text": "근로계약 기간은 2025년 1월 1일부터 2025년 12월 31일까지로 한다.",
                            "risk": "safe",
                            "why": "표준 계약 조건을 따르고 있습니다.",
                            "fix": "추가 조치 불필요"
                        },
                        {
                            "id": "s1-2",
                            "text": "계약 기간 만료 후 상호 협의에 따라 갱신할 수 있다.",
                            "risk": "safe",
                            "why": "갱신 조건이 명확하게 명시되어 있습니다.",
                            "fix": "추가 조치 불필요"
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "제2조 (근무 장소 및 업무)",
                    "sentences": [
                        {
                            "id": "s2-1",
                            "text": "근무 장소는 회사가 정한 사업장으로 한다.",
                            "risk": "safe",
                            "why": "근무 장소가 명확하게 지정되어 있습니다.",
                            "fix": "추가 조치 불필요"
                        },
                        {
                            "id": "s2-2",
                            "text": "근로자의 주요 업무는 고객 응대 및 매장 관리로 한다.",
                            "risk": "safe",
                            "why": "업무 내용이 구체적으로 명시되어 있습니다.",
                            "fix": "추가 조치 불필요"
                        }
                    ]
                },
                {
                    "id": 3,
                    "title": "제3조 (근로시간 및 휴게)",
                    "sentences": [
                        {
                            "id": "s3-1",
                            "text": "근로시간은 1일 8시간, 주 40시간을 원칙으로 한다.",
                            "risk": "safe",
                            "why": "법정 근로시간을 준수하고 있습니다.",
                            "fix": "추가 조치 불필요"
                        },
                        {
                            "id": "s3-2",
                            "text": "근로자는 근로시간 중 1시간의 휴게시간을 가진다.",
                            "risk": "safe",
                            "why": "휴게시간이 적절하게 보장되고 있습니다.",
                            "fix": "추가 조치 불필요"
                        },
                        {
                            "id": "s3-3",
                            "text": "휴게시간 중에도 상급자 지시에 즉시 응해야 하며, 이 시간은 근로시간으로 보지 않는다.",
                            "risk": "danger",
                            "why": "대기·콜 대기 등 사용자의 지휘감독 하에 있으면 실질적 휴게가 아니며 근로시간으로 볼 여지 큼.",
                            "fix": "휴게시간 동안 지휘감독을 배제하여 자유로운 이용을 보장하고, 불가피한 대기·지시가 있는 경우 해당 시간은 근로시간으로 본다."
                        }
                    ]
                }
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/save-analysis/{task_id}")
async def save_analysis_result(task_id: str, analysis_data: AnalyzeResponse, file_name: Optional[str] = None):
    """분석 결과 저장 (프론트엔드에서 호출)"""
    try:
        # AI가 추출한 제목 사용 (analyze_contract에서 이미 처리됨)
        # 여기서는 기본값만 사용
        title = "계약서 분석 결과"
        
        # 분석 결과를 저장
        analysis_results[task_id] = AnalysisResult(
            id=task_id,
            title=title,
            articles=analysis_data.articles
        )
        
        return {"success": True, "message": "분석 결과가 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 결과 저장 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{task_id}")
async def delete_uploaded_file(task_id: str):
    """업로드된 파일 삭제"""
    try:
        deleted = False
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(task_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                os.remove(file_path)
                deleted = True
                break
        
        if not deleted:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 상태 정보도 삭제
        if task_id in file_statuses:
            del file_statuses[task_id]
        
        return {"success": True, "message": "파일이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}")
