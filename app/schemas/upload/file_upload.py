from pydantic import BaseModel
from enum import Enum
from typing import Optional, List


class FileType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    HWP = "HWP"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"


class FileValidationError(str, Enum):
    FILE_TOO_LARGE = "파일 크기가 너무 큽니다."
    UNSUPPORTED_FORMAT = "지원하지 않는 파일 형식입니다."
    UPLOAD_FAILED = "파일 업로드에 실패했습니다."


class FileUploadResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    file_name: str
    file_size: int
    file_type: FileType
    extracted_text: Optional[str] = None


class RiskLevel(str, Enum):
    DANGER = "danger"
    WARNING = "warning"
    SAFE = "safe"


class Sentence(BaseModel):
    id: str
    text: str
    risk: RiskLevel
    why: Optional[str] = None
    fix: Optional[str] = None


class Article(BaseModel):
    id: int
    title: str
    sentences: List[Sentence]


class AnalysisResult(BaseModel):
    id: str
    title: str
    articles: List[Article]


class UploadStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str
