from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

# 파일 정리 서비스
from app.services.file.file_cleaner import file_cleaner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시
    asyncio.create_task(file_cleaner.start_cleaner())
    yield
    # 서버 종료 시
    await file_cleaner.stop_cleaner()

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Checky API",
    description="AI 계약서 독소조항 분석기 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
from app.routers.upload.file_upload import router as file_upload_router
app.include_router(file_upload_router)

# 기본 라우트
@app.get("/")
async def root():
    return {"message": "Checky API 서버가 정상적으로 실행 중입니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


from app.routers.contract import analyze
app.include_router(analyze.router)
