# 빅데이터분석프로젝트

동양미래대학교 인공지능소프트웨어학과 - 2026학년도 1학기

> 이 저장소는 **빅데이터분석프로젝트** 수업에서 다룬 내용과 실습 코드를 주차별로 정리한 저장소입니다.

## 개발 환경 설정

### 1. Python 설치

- [Python 3.12+](https://www.python.org/downloads/) 설치
- 설치 시 **"Add Python to PATH"** 반드시 체크

### 2. 프로젝트 클론

```bash
git clone <저장소 URL>
cd bigdata-project
```

### 3. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows PowerShell)
venv\Scripts\activate

# 활성화 (Git Bash)
source venv/Scripts/activate
```

### 4. 패키지 설치

```bash
pip install -r requirements.txt
```

### 5. Streamlit 앱 실행

```bash
python -m streamlit run app.py
```

> **참고**: 프로젝트 경로에 한글이 포함된 경우 `streamlit` 명령어가 동작하지 않을 수 있습니다. `python -m streamlit`으로 실행하세요.

## 주요 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| pandas | 데이터 분석/전처리 |
| scikit-learn | 머신러닝 모델 |
| matplotlib / seaborn | 데이터 시각화 |
| altair | 인터랙티브 시각화 |
| streamlit | 웹 대시보드/앱 |
| requests | API 데이터 수집 |
