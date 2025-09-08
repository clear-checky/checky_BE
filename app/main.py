from fastapi import FastAPI

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Checky API",
    description="AI 계약서 독소조항 분석기 API",
    version="1.0.0"
)

# 기본 라우트
@app.get("/")
async def root():
    return {"message": "Checky API 서버가 정상적으로 실행 중입니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
