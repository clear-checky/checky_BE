# Checky Backend

AI 계약서 독소조항 분석기 백엔드 API

## 🚀 빠른 시작

### 1. 개발 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp env.example .env

# 서버 실행
uvicorn app.main:app --reload
```

### 2. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 프로젝트 구조

```
checky_BE/
├── app/                    # 메인 애플리케이션
│   ├── main.py            # FastAPI 앱 진입점
│   ├── routers/           # API 엔드포인트들
│   │   ├── contract/      # 계약서 관련 API
│   │   └── chat/          # 챗봇 관련 API
│   ├── models/            # 데이터베이스 모델들
│   └── schemas/           # API 요청/응답 스키마들
│       ├── contract/      # 계약서 관련 스키마
│       └── chat/          # 챗봇 관련 스키마
├── uploads/               # 파일 업로드 저장소
├── tests/                 # 테스트 코드
└── requirements.txt       # Python 의존성
```

## 🛠 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.8+
- **Database**: SQLite (개발용)
- **File Upload**: python-multipart
- **Validation**: Pydantic

## 📋 주요 기능

### 계약서 관련

- [ ] 계약서 파일 업로드
- [ ] AI 계약서 분석
- [ ] 분석 결과 조회
- [ ] 분석 리포트 다운로드

### 챗봇 관련

- [ ] 계약서 기반 챗봇 (특정 계약서에 대해 질문)
- [ ] 일반 챗봇 (계약서와 관련 없는 일반적인 질문)

## 📚 개발 가이드

자세한 개발 가이드는 [DEVELOPMENT.md](./DEVELOPMENT.md)를 참고하세요.

## 🤝 기여하기

1. 이슈 생성 또는 기존 이슈 확인
2. 기능 브랜치 생성 (`git checkout -b feature/새기능`)
3. 변경사항 커밋 (`git commit -m 'feat: 새기능 추가'`)
4. 브랜치에 푸시 (`git push origin feature/새기능`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.
