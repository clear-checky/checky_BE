# Checky 백엔드 개발 가이드

## 📋 프로젝트 개요

- **프레임워크**: FastAPI
- **언어**: Python 3.8+
- **데이터베이스**: SQLite (개발용) → PostgreSQL (운영용)
- **목적**: AI 계약서 독소조항 분석기 API

## 🚀 개발 환경 설정

### 1. Python 설치 확인

```bash
python3 --version
# Python 3.8 이상이어야 함
```

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성 (macOS/Linux)
python3 -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 3. 의존성 패키지 설치

```bash
# pip 업그레이드 (선택 사항)
pip3 install --upgrade pip

# 패키지 설치
pip3 install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
# env.example을 복사해서 .env 파일 생성
cp env.example .env

# .env 파일을 열어서 실제 값들로 수정
# (개발용이므로 기본값 그대로 사용해도 됨)
```

### 5. 서버 실행

```bash
# 가상환경이 활성화되어 있는지 확인 (프롬프트 앞에 (venv)가 있어야 함)
# 만약 (venv)가 없다면 다시 활성화:
source venv/bin/activate

# 서버 실행
uvicorn app.main:app --reload
```

서버가 실행되면:

- **API 문서**: http://localhost:8000/docs
- **서버 상태**: http://localhost:8000/health

## 📁 프로젝트 구조

```
checky_BE/
├── app/                    # 메인 애플리케이션
│   ├── __init__.py
│   ├── main.py            # FastAPI 앱 진입점
│   ├── routers/           # API 엔드포인트들
│   │   └── contract/      # 계약서 관련 API
│   ├── models/            # 데이터베이스 모델들
│   └── schemas/           # API 요청/응답 스키마들
│       └── contract/      # 계약서 관련 스키마
├── uploads/               # 파일 업로드 저장소
├── tests/                 # 테스트 코드
├── requirements.txt       # Python 의존성
├── env.example           # 환경변수 예시
└── README.md
```

## 🔧 개발 가이드

### API 개발 순서

1. **스키마 정의** (`app/schemas/contract/`)
   - 요청/응답 데이터 구조 정의
2. **모델 생성** (`app/models/`)
   - 데이터베이스 테이블 구조 정의
3. **라우터 구현** (`app/routers/contract/`)
   - API 엔드포인트 구현
4. **메인 앱에 등록** (`app/main.py`)
   - 라우터를 메인 앱에 연결

### 기능별 개발 가이드

#### 계약서 관련 기능 (`app/routers/contract/`, `app/schemas/contract/`)

- 계약서 파일 업로드
- AI 계약서 분석
- 분석 결과 조회
- 분석 리포트 다운로드
- 챗봇

### 파일 명명 규칙

- **파일명**: 소문자 + 언더스코어 (`contract_upload.py`)
- **클래스명**: 파스칼 케이스 (`ContractUpload`)
- **함수명**: 소문자 + 언더스코어 (`upload_contract`)

### Git 커밋 규칙

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
```

## 🚨 주의사항

### 1. 환경 변수

- `.env` 파일은 **절대 Git에 올리지 마세요**
- 민감한 정보(API 키, 비밀번호)는 환경 변수로 관리

### 2. 파일 업로드

- `uploads/` 폴더에 업로드된 파일들은 **24시간 후 자동 삭제**
- 파일 크기 제한: 20MB

### 3. 데이터베이스

- 개발용: SQLite (파일 기반)
- 운영용: PostgreSQL (나중에 변경 예정)

## 📚 학습 자료

### FastAPI 공식 문서

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [FastAPI 튜토리얼](https://fastapi.tiangolo.com/tutorial/)

### Python 관련

- [Python 공식 문서](https://docs.python.org/ko/3/)
- [Pydantic 문서](https://pydantic-docs.helpmanual.io/)

## 🆘 문제 해결

### 자주 발생하는 문제들

1. **포트 충돌**

   ```bash
   # 다른 포트로 실행
   uvicorn app.main:app --reload --port 8001
   ```

2. **패키지 설치 실패**

   ```bash
   # pip 업그레이드
   pip3 install --upgrade pip
   ```

3. **가상환경 활성화 실패**
   ```bash
   # 가상환경 재생성
   rm -rf venv
   python -m venv venv
   ```

## 📞 도움 요청

문제가 발생하면:

1. 에러 메시지 전체 복사
2. 어떤 작업을 하다가 발생했는지 설명
3. 팀 채널에 공유

---

**Happy Coding! 🎉**
