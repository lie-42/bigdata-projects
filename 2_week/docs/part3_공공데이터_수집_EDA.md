# Part 3: 공공데이터 수집 및 EDA

> **목표**: 공공데이터포털의 Open API를 활용하여 실제 데이터를 수집하고, 탐색적 자료분석(EDA)을 통해 데이터의 구조와 패턴을 파악하는 전 과정을 실습한다.

---

## 3-1. Open API를 활용한 공공데이터 수집

### 3-1-1. 공공데이터포털 소개

#### 공공데이터란?

공공데이터는 **정부, 지방자치단체, 공공기관**이 생성하거나 보유하고 있는 데이터를 말한다. 「공공데이터의 제공 및 이용 활성화에 관한 법률」에 따라 누구나 무료로 이용할 수 있다.

#### 공공데이터포털 (data.go.kr)

| 항목 | 내용 |
|------|------|
| 사이트 | https://www.data.go.kr |
| 제공 형태 | 파일 데이터(CSV, Excel, JSON), Open API |
| 데이터 수 | 약 80,000건 이상 (2025년 기준) |
| 주요 분야 | 교통, 환경, 보건, 식품, 문화, 기상, 부동산, 교육 등 |
| 비용 | 무료 (회원가입 필요) |

#### 왜 공공데이터를 사용하는가?

1. **무료**: 별도의 비용 없이 대규모 데이터를 확보할 수 있다
2. **신뢰성**: 공공기관이 수집한 데이터이므로 출처가 명확하다
3. **포트폴리오**: 프로젝트에 실제 데이터를 사용하면 결과물의 완성도가 높아진다
4. **실무 연습**: 실제 업무에서도 공공 API를 활용하는 경우가 많다

#### 공공데이터 외에 활용 가능한 데이터 소스

| 플랫폼 | URL | 특징 |
|--------|-----|------|
| Kaggle | https://www.kaggle.com/datasets | 전 세계 데이터셋, 경진대회, 커뮤니티 |
| 서울 열린데이터 광장 | https://data.seoul.go.kr | 서울시 특화 데이터 |
| 기상청 기상자료개방포털 | https://data.kma.go.kr | 기상/기후 데이터 |
| 국가통계포털(KOSIS) | https://kosis.kr | 국가 통계 데이터 |
| AI Hub | https://aihub.or.kr | AI 학습용 데이터셋 |

---

### 3-1-2. API 기본 개념

#### API (Application Programming Interface)란?

프로그램과 프로그램 사이의 **약속된 통신 방법**이다. 식당에 비유하면:

```
고객(프로그램) → 주문서(API 요청) → 주방(서버) → 음식(API 응답)
```

우리가 사용할 것은 **REST API**로, 웹 주소(URL)를 통해 데이터를 요청하고 받는 방식이다.

#### REST API 핵심 개념

| 용어 | 설명 | 예시 |
|------|------|------|
| **엔드포인트(Endpoint)** | 데이터를 요청할 서버 주소(URL) | `http://apis.data.go.kr/서비스명` |
| **파라미터(Parameter)** | 요청 시 전달하는 조건/설정값 | `?numOfRows=100&pageNo=1` |
| **API 키(Service Key)** | 사용자 인증을 위한 고유 키 | `serviceKey=abcd1234...` |
| **응답(Response)** | 서버가 반환하는 데이터 | JSON 또는 XML 형식 |
| **HTTP 메서드** | 요청 방식 | GET (조회), POST (생성) 등 |
| **상태 코드** | 요청 결과를 나타내는 숫자 | 200(성공), 401(인증실패), 404(없음), 500(서버오류) |

#### 응답 형식: JSON vs XML

**JSON** (JavaScript Object Notation) — 현재 가장 널리 사용되는 형식
```json
{
  "response": {
    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE"},
    "body": {
      "items": [
        {"stationName": "종로구", "pm10Value": "45", "pm25Value": "22"},
        {"stationName": "중구", "pm10Value": "52", "pm25Value": "28"}
      ],
      "totalCount": 2
    }
  }
}
```

- 사람이 읽기 쉽고, Python에서 딕셔너리로 바로 변환 가능
- `key: value` 구조
- 리스트(`[]`)와 객체(`{}`)를 중첩하여 복잡한 데이터 표현

**XML** (eXtensible Markup Language)
```xml
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <stationName>종로구</stationName>
        <pm10Value>45</pm10Value>
      </item>
    </items>
  </body>
</response>
```

- HTML과 유사한 태그 구조
- JSON보다 장황하지만, 일부 오래된 API에서 아직 사용

> **이 수업에서는 JSON 형식을 사용한다.** JSON은 Python 딕셔너리와 구조가 거의 동일하므로 다루기 쉽다.

#### API 요청의 전체 흐름

```
1. API 키 발급 (공공데이터포털 가입 후)
2. API 문서 확인 (엔드포인트, 파라미터, 응답 구조)
3. Python으로 HTTP 요청 (requests.get)
4. 응답 데이터 파싱 (response.json())
5. 필요한 데이터 추출 → DataFrame 변환
6. 파일 저장 (CSV)
```

---

### 3-1-3. API 키 발급 방법 안내

> 수업 시간에 바로 API 키를 발급받기에는 시간이 걸릴 수 있으므로, **사전에 안내하거나 수업 시작 전 발급을 완료해두는 것이 좋다.** API 키 승인까지 최대 1~2시간 소요될 수 있다.

#### 발급 절차

**Step 1: 공공데이터포털 회원가입**
1. https://www.data.go.kr 접속
2. 우측 상단 `회원가입` 클릭
3. 일반 회원으로 가입 (이메일 인증 필요)

**Step 2: 원하는 데이터 API 검색**
1. 상단 검색창에서 키워드 검색 (예: "대기오염", "미세먼지", "서울 인구")
2. 검색 결과에서 `오픈API` 탭 선택
3. 원하는 API 클릭하여 상세 페이지 진입

**Step 3: 활용 신청**
1. 상세 페이지에서 `활용신청` 버튼 클릭
2. 활용 목적 입력 (예: "수업 실습", "학습용 프로젝트")
3. 신청 후 승인 대기 (일반적으로 자동 승인 또는 1~2시간 소요)

**Step 4: API 키 확인**
1. `마이페이지` > `활용신청 현황` 메뉴 이동
2. 인증키는 **두 종류**가 제공된다:
   - **일반 인증키 (Encoding)**: URL 인코딩이 적용된 키 (특수문자가 `%2F`, `%3D` 등으로 변환됨)
   - **일반 인증키 (Decoding)**: 인코딩 전 원본 키 (`/`, `=`, `+` 등 특수문자 그대로)
3. **반드시 `Decoding` 키를 복사**하여 사용한다 (아래 주의사항 참고)

> **주의**: API 키는 개인 고유 키이므로 GitHub 등에 공개하지 않도록 주의한다. `.env` 파일이나 환경 변수로 관리하는 것이 좋다.

> **⚠️ Encoding 키 vs Decoding 키 — 반드시 알아야 할 핵심 주의사항**
>
> 공공데이터포털에서 가장 흔하게 발생하는 오류가 바로 **인증키 이중 인코딩 문제**이다.
>
> **문제 상황:**
> - `requests` 라이브러리의 `params`에 값을 넣으면, 라이브러리가 **자동으로 URL 인코딩**을 수행한다
> - 그런데 **Encoding 키**는 이미 URL 인코딩이 되어 있는 상태이다
> - 따라서 Encoding 키를 `params`에 넣으면 **이중 인코딩**이 발생하여 서버가 키를 인식하지 못한다
> - 결과: `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` 오류 발생
>
> **예시:**
> ```
> Decoding 키 (원본):  abcd1234/XYZ+efgh==
> Encoding 키 (인코딩됨): abcd1234%2FXYZ%2Befgh%3D%3D
>
> params에 Encoding 키를 넣으면:
> → requests가 다시 인코딩 → abcd1234%252FXYZ%252Befgh%253D%253D (이중 인코딩!)
> → 서버: "이 키는 등록되지 않았습니다" 오류
> ```
>
> **해결 방법 (택 1):**
>
> ```python
> # ✅ 방법 1 (권장): Decoding 키를 params에 사용
> API_KEY = "abcd1234/XYZ+efgh=="  # Decoding 키
> params = {"serviceKey": API_KEY, ...}
> response = requests.get(url, params=params)
>
> # ✅ 방법 2: Encoding 키를 URL에 직접 포함
> API_KEY_ENCODED = "abcd1234%2FXYZ%2Befgh%3D%3D"  # Encoding 키
> full_url = f"{url}?serviceKey={API_KEY_ENCODED}"
> response = requests.get(full_url, params=other_params)  # serviceKey 제외한 나머지만
>
> # ❌ 잘못된 방법: Encoding 키를 params에 넣기
> API_KEY_ENCODED = "abcd1234%2FXYZ%2Befgh%3D%3D"
> params = {"serviceKey": API_KEY_ENCODED, ...}  # 이중 인코딩 발생!
> ```
>
> **결론: `params`를 사용할 때는 항상 `Decoding 키`를 사용하자.**

#### API 키 안전 관리 방법 (참고)

```bash
# .env 파일 생성 (프로젝트 루트에)
echo "API_KEY=발급받은키값" > .env
```

```python
# .env 파일에서 키 불러오기
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
```

```bash
# .gitignore에 .env 추가 (이미 되어 있어야 함)
echo ".env" >> .gitignore
```

> `python-dotenv` 패키지가 필요하다: `pip install python-dotenv`

---

### 3-1-4. 공공데이터 API 호출 실습

> 이 실습에서는 **한국환경공단 에어코리아 대기오염정보 API**를 예시로 사용한다.
> 학생들이 API 키 발급이 완료되지 않은 경우를 대비하여, **대체 실습 방안**(미리 준비한 CSV 파일 또는 키 없이 사용 가능한 API)도 함께 안내한다.

#### 실습 1: 기본 API 호출 — 대기오염 정보 수집

`data_collection.py` 파일 생성:

```python
import requests
import pandas as pd
import json

# ============================================================
# 1. API 설정
# ============================================================
# 공공데이터포털에서 발급받은 일반 인증키 (⚠️ 반드시 Decoding 키 사용!)
# Encoding 키를 params에 넣으면 이중 인코딩 오류 발생
API_KEY = "발급받은_Decoding_API_키"

# 에어코리아 대기오염정보 - 시도별 실시간 측정정보 조회
url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"

# ============================================================
# 2. 요청 파라미터 설정
# ============================================================
params = {
    "serviceKey": API_KEY,       # 인증키
    "returnType": "json",        # 응답 형식 (json 또는 xml)
    "numOfRows": "100",          # 한 페이지에 가져올 데이터 수
    "pageNo": "1",               # 페이지 번호
    "sidoName": "서울",           # 시도 이름 (서울, 부산, 대구, 인천 등)
    "ver": "1.0"                 # API 버전
}

# ============================================================
# 3. API 호출
# ============================================================
print("▶ API 호출 중...")
response = requests.get(url, params=params)

# 응답 상태 확인
print(f"▶ 응답 상태 코드: {response.status_code}")

if response.status_code == 200:
    print("▶ API 호출 성공!")
else:
    print(f"▶ API 호출 실패! 상태 코드: {response.status_code}")
    print(f"▶ 응답 내용: {response.text[:200]}")
    exit()

# ============================================================
# 4. JSON 응답 파싱
# ============================================================
data = response.json()

# 응답 구조 확인 (디버깅용)
print("\n▶ 응답 구조 확인 (최상위 키):")
print(json.dumps(list(data.keys()), ensure_ascii=False))

# 실제 데이터 추출
# 공공데이터 API의 일반적인 응답 구조:
# data["response"]["header"] → 결과 코드, 메시지
# data["response"]["body"]["items"] → 실제 데이터 리스트
try:
    header = data["response"]["header"]
    print(f"\n▶ 결과 코드: {header['resultCode']}")
    print(f"▶ 결과 메시지: {header['resultMsg']}")

    body = data["response"]["body"]
    total_count = body["totalCount"]
    print(f"▶ 전체 데이터 수: {total_count}")

    items = body["items"]

    # ⚠️ 응답 구조 주의: API마다 items의 형태가 다를 수 있다!
    # - 형태 A: items가 바로 리스트 → [{"key": "val"}, ...]
    # - 형태 B: items 안에 "item" 키가 있음 → {"item": [{"key": "val"}, ...]}
    # 실습 중 오류가 나면 아래처럼 type()으로 먼저 확인하자.
    print(f"▶ items의 타입: {type(items)}")

    if isinstance(items, dict):
        # 형태 B: items가 딕셔너리인 경우 → "item" 키 안에 실제 리스트
        items = items.get("item", items)
        print(f"▶ items['item']에서 데이터 추출 (형태 B)")

    if isinstance(items, list):
        print(f"▶ 가져온 데이터 수: {len(items)}")
    else:
        print(f"▶ 예상치 못한 items 타입: {type(items)}")
        print(f"▶ items 내용 미리보기: {str(items)[:300]}")
        exit()

except KeyError as e:
    print(f"▶ 응답 구조가 예상과 다릅니다. 키 오류: {e}")
    # 응답 구조를 먼저 확인하는 습관을 들이자
    print(f"▶ 전체 응답 구조 확인:")
    print(f"▶ 전체 응답:\n{json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    exit()

# ============================================================
# 5. DataFrame 변환
# ============================================================
df = pd.DataFrame(items)
print(f"\n▶ DataFrame 크기: {df.shape}")
print(f"▶ 컬럼 목록: {df.columns.tolist()}")
print("\n▶ 처음 5행:")
print(df.head())

# ============================================================
# 6. 필요한 컬럼만 선택하고 이름 변경
# ============================================================
# 대기오염 데이터의 주요 컬럼
columns_map = {
    "stationName": "측정소",
    "dataTime": "측정일시",
    "pm10Value": "미세먼지(PM10)",
    "pm25Value": "초미세먼지(PM2.5)",
    "o3Value": "오존(O3)",
    "no2Value": "이산화질소(NO2)",
    "coValue": "일산화탄소(CO)",
    "so2Value": "아황산가스(SO2)",
    "pm10Grade": "PM10등급",
    "pm25Grade": "PM25등급"
}

# 존재하는 컬럼만 선택
available_cols = {k: v for k, v in columns_map.items() if k in df.columns}
df_selected = df[list(available_cols.keys())].rename(columns=available_cols)

print(f"\n▶ 선택된 컬럼: {df_selected.columns.tolist()}")
print(df_selected.head(10))

# ============================================================
# 7. CSV 파일로 저장
# ============================================================
df_selected.to_csv("air_quality_seoul.csv", index=False, encoding="utf-8-sig")
print("\n▶ 'air_quality_seoul.csv' 파일로 저장 완료!")
```

> **코드 설명**
>
> | 코드 | 설명 |
> |------|------|
> | `requests.get(url, params=params)` | GET 방식으로 API 호출. `params` 딕셔너리를 자동으로 URL 쿼리 문자열로 변환 |
> | `response.status_code` | HTTP 응답 상태 코드. 200이면 정상 |
> | `response.json()` | JSON 형식의 응답을 Python 딕셔너리로 변환 |
> | `pd.DataFrame(items)` | 리스트(딕셔너리의 리스트)를 DataFrame으로 변환 |
> | `encoding="utf-8-sig"` | CSV 저장 시 한글이 엑셀에서도 깨지지 않도록 BOM 포함 인코딩 사용 |

---

#### 실습 2 (대체): API 키가 없는 경우 — 공개 API 사용

API 키 발급이 안 된 학생을 위해, **인증 키 없이 사용 가능한 공개 API**를 활용하는 대체 실습도 제공한다.

`data_collection_alt.py` 파일 생성:

```python
import requests
import pandas as pd

# ============================================================
# 서울 열린데이터 광장 API (인증키 없이 사용 가능한 예시)
# 서울시 자치구별 인구 통계 데이터
# ============================================================

# API URL (서울 열린데이터 광장은 키 없이도 일부 데이터 제공)
url = "http://openapi.seoul.go.kr:8088/sample/json/SPOP_LOCAL_RESD_JACHI/1/20/"

print("▶ API 호출 중...")
response = requests.get(url)
print(f"▶ 상태 코드: {response.status_code}")

if response.status_code == 200:
    data = response.json()

    # 데이터 추출 (서울 열린데이터의 응답 구조)
    key = list(data.keys())[0]  # 첫 번째 키가 데이터셋 이름
    items = data[key]["row"]

    df = pd.DataFrame(items)
    print(f"\n▶ DataFrame 크기: {df.shape}")
    print(f"▶ 컬럼 목록: {df.columns.tolist()}")
    print(df.head())

    df.to_csv("seoul_population.csv", index=False, encoding="utf-8-sig")
    print("\n▶ 'seoul_population.csv' 저장 완료!")
else:
    print("▶ API 호출 실패")
```

---

#### 실습 3 (대체): CSV 파일 직접 다운로드

API 호출이 어려운 상황을 대비하여, 공공데이터포털에서 **파일 데이터(CSV)를 직접 다운로드**하여 사용하는 방법도 안내한다.

1. https://www.data.go.kr 접속
2. 검색창에 원하는 키워드 입력 (예: "서울 미세먼지")
3. `파일데이터` 탭 선택
4. 원하는 데이터셋 클릭 → `다운로드` 버튼으로 CSV 파일 저장
5. 프로젝트 폴더에 파일 복사

```python
import pandas as pd

# 다운로드한 CSV 파일 로드
df = pd.read_csv("다운로드한_파일.csv", encoding="cp949")  # 또는 "utf-8", "euc-kr"
print(df.shape)
print(df.head())
```

> **인코딩 오류가 발생할 경우**: 한국의 공공데이터 CSV 파일은 `cp949`(Windows 한글), `euc-kr`, `utf-8`, `utf-8-sig` 등 다양한 인코딩으로 저장되어 있다. 오류 발생 시 다른 인코딩을 시도한다.
>
> ```python
> # 인코딩 자동 감지 (chardet 패키지 필요)
> import chardet
>
> with open("파일명.csv", "rb") as f:
>     result = chardet.detect(f.read())
>     print(result)  # {'encoding': 'EUC-KR', 'confidence': 0.99, ...}
> ```

---

#### requests 라이브러리 핵심 정리

| 코드 | 설명 |
|------|------|
| `requests.get(url)` | GET 요청 (데이터 조회) |
| `requests.get(url, params=dict)` | 쿼리 파라미터 포함 GET 요청 |
| `response.status_code` | HTTP 상태 코드 (200: 성공) |
| `response.text` | 응답 본문 (문자열) |
| `response.json()` | 응답 본문을 JSON → 딕셔너리로 변환 |
| `response.content` | 응답 본문 (바이트, 파일 다운로드 시 사용) |
| `response.headers` | 응답 헤더 정보 |
| `response.raise_for_status()` | 오류 시 예외 발생 (4xx, 5xx) |

#### API 호출 시 자주 발생하는 오류와 해결 방법

| 상태 코드 | 원인 | 해결 방법 |
|-----------|------|-----------|
| **401 Unauthorized** | API 키가 잘못됨 | 키를 다시 확인, URL 인코딩 확인 |
| **403 Forbidden** | 접근 권한 없음 | API 활용 신청 승인 여부 확인 |
| **404 Not Found** | 엔드포인트 URL 오류 | API 문서에서 URL 재확인 |
| **429 Too Many Requests** | 요청 횟수 초과 | 잠시 후 재시도, 호출 간격 조절 |
| **500 Internal Server Error** | 서버 내부 오류 | 시간을 두고 재시도 |
| **SERVICE_KEY_IS_NOT_REGISTERED_ERROR** | Encoding 키를 `params`에 넣어 이중 인코딩 발생 | **Decoding 키로 교체** (가장 흔한 원인, 위 3-1-3 참고) |
| **응답이 XML로 옴** | `returnType` 파라미터 누락 또는 오타 | `"returnType": "json"` 확인 |
| **items 파싱 오류** | API마다 응답 구조가 다름 | `type(items)` 출력 후 dict면 `items["item"]`으로 접근 |

> **가장 흔한 실수 TOP 2:**
>
> **1위: 인증키 이중 인코딩** — `params`에 Encoding 키를 넣으면 `requests`가 다시 인코딩하여 서버가 키를 인식하지 못한다. **반드시 Decoding 키를 사용**하자. (상세 설명: 위 3-1-3 참고)
>
> **2위: JSON 응답 구조 오해** — `data["response"]["body"]["items"]`가 바로 리스트(`list`)인 API도 있고, `{"item": [...]}` 형태의 딕셔너리(`dict`)인 API도 있다. 항상 `type(items)`를 먼저 출력하여 확인하는 습관을 들이자.
>
> ```python
> # 안전한 items 추출 패턴 (어떤 구조든 대응 가능)
> items = body["items"]
> if isinstance(items, dict):
>     items = items.get("item", [])
> df = pd.DataFrame(items)
> ```

---

### 3-1-5. API 호출 시 에러 핸들링 Tip

#### HTTP 200인데 데이터가 안 오는 경우

공공데이터 API의 특이한 점은, **시스템 오류가 발생해도 HTTP 상태 코드는 200을 반환**하는 경우가 많다는 것이다. 실제 에러 메시지는 응답 본문(body) 안에 담겨 온다.

```
일반적인 API:
  요청 실패 → HTTP 401, 403, 500 등 상태 코드로 알려줌

공공데이터 API:
  요청 실패 → HTTP 200 (성공처럼 보임) + 본문에 에러 메시지 포함 😱
```

따라서 `status_code == 200`만 확인하면 **오류를 놓칠 수 있다.**

#### 에러 감지 방법

```python
response = requests.get(url, params=params)

# 1차 확인: HTTP 상태 코드
if response.status_code != 200:
    print(f"▶ HTTP 오류: {response.status_code}")
    exit()

# 2차 확인: 응답 본문에 에러 메시지가 포함되어 있는지
# 공공데이터 API는 에러 시 "cmmMsgHeader" 또는 "OpenAPI_ServiceResponse"를 반환
if "cmmMsgHeader" in response.text:
    print("▶ API 서비스 내부 오류 발생!")
    print(response.text)  # 에러 메시지 (인증 오류, 트래픽 초과 등)
    exit()

if "OpenAPI_ServiceResponse" in response.text:
    print("▶ API 서비스 에러 응답!")
    print(response.text)
    exit()

# 3차 확인: JSON 파싱 후 resultCode 확인
data = response.json()
result_code = data.get("response", {}).get("header", {}).get("resultCode", "")
if result_code != "00":
    result_msg = data["response"]["header"].get("resultMsg", "알 수 없는 오류")
    print(f"▶ API 오류 - 코드: {result_code}, 메시지: {result_msg}")
    exit()

print("▶ 데이터 정상 수신!")
```

#### 공공데이터 API 주요 resultCode 목록

| resultCode | 메시지 | 원인 | 해결 |
|------------|--------|------|------|
| **00** | NORMAL SERVICE | 정상 | - |
| **01** | APPLICATION ERROR | 서버 내부 오류 | 시간 후 재시도 |
| **04** | HTTP_ERROR | HTTP 통신 오류 | 네트워크 확인 |
| **10** | INVALID_REQUEST_PARAMETER_ERROR | 파라미터 오류 | API 문서에서 필수 파라미터 확인 |
| **12** | NO_OPENAPI_SERVICE_ERROR | 해당 API 서비스 없음 | 엔드포인트 URL 확인 |
| **20** | SERVICE_ACCESS_DENIED_ERROR | 접근 거부 | 활용 신청 승인 확인 |
| **22** | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | 일일 호출 횟수 초과 | 다음 날 재시도 |
| **30** | SERVICE_KEY_IS_NOT_REGISTERED_ERROR | 인증키 미등록 | **Decoding 키 사용** (3-1-3 참고) |
| **31** | DEADLINE_HAS_EXPIRED_ERROR | 활용 기간 만료 | 활용 연장 신청 |

> **실습 Tip**: 위의 에러 감지 코드를 `data_collection.py`의 3번(API 호출) 직후에 추가하면, 문제 발생 시 원인을 빠르게 파악할 수 있다.

**체크포인트:**
- [ ] `requests.get()`으로 API 호출이 성공한다 (status_code == 200)
- [ ] HTTP 200이어도 응답 본문의 에러 메시지를 확인하는 방법을 안다
- [ ] `response.json()`으로 JSON 데이터를 딕셔너리로 변환할 수 있다
- [ ] JSON 응답에서 필요한 데이터를 추출하여 DataFrame으로 변환했다
- [ ] CSV 파일로 저장이 완료되었다

---

## 3-2. 탐색적 자료분석(EDA) 실습

### 3-2-1. EDA(Exploratory Data Analysis)란?

#### EDA의 정의

**탐색적 자료분석(Exploratory Data Analysis, EDA)**은 데이터를 다양한 각도에서 살펴보며 **구조, 분포, 패턴, 이상치, 관계**를 파악하는 분석 과정이다.

> **존 튜키(John Tukey)**가 1977년 제안한 개념으로, "데이터가 우리에게 말하려는 것에 귀를 기울이자"는 철학에 기반한다.

#### EDA의 목적

| 목적 | 설명 | 예시 |
|------|------|------|
| **데이터 이해** | 데이터의 구조, 크기, 타입 파악 | "이 데이터는 몇 행 몇 열인가?" |
| **품질 확인** | 결측치, 이상치, 중복 등 문제 발견 | "빈 값이 얼마나 있는가?" |
| **분포 파악** | 각 변수의 값 분포 확인 | "정규분포인가? 편향되어 있는가?" |
| **관계 탐색** | 변수 간 상관관계, 패턴 발견 | "미세먼지와 오존 농도는 관계가 있는가?" |
| **가설 생성** | 분석/모델링 방향 설정 | "이 변수가 예측에 중요할 것 같다" |

#### EDA vs 통계 분석

| 항목 | EDA | 통계 분석(확인적 분석) |
|------|-----|----------------------|
| 목적 | 패턴 발견, 가설 생성 | 가설 검증 |
| 방법 | 시각화, 요약 통계 | 통계 검정 (t-test, ANOVA 등) |
| 결론 | "이런 패턴이 보인다" | "유의미하다 / 유의미하지 않다" |
| 순서 | **먼저** 수행 | EDA 이후 수행 |

> EDA는 데이터 분석의 **첫 번째 단계**로, 이후 모델링이나 통계 분석에 앞서 반드시 수행해야 한다.

#### EDA 5단계 프로세스

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  ① 데이터    │ →  │  ② 기술     │ →  │  ③ 시각화   │ →  │  ④ 상관관계  │ →  │  ⑤ 인사이트 │
│  구조 확인   │    │  통계 분석   │    │              │    │  분석        │    │  도출        │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
  shape, info()      describe()         히스토그램         corr()               패턴 요약
  dtypes, head()     value_counts()     박스플롯           히트맵               가설 설정
  isnull().sum()                        산점도                                  전처리 방향 결정
```

| 단계 | 핵심 질문 | 주요 도구 |
|------|-----------|-----------|
| ① 데이터 구조 확인 | 행과 열은 몇 개? 타입은? 결측치는? | `shape`, `info()`, `dtypes`, `isnull().sum()` |
| ② 기술통계 분석 | 평균, 중앙값, 분포는 어떤가? | `describe()`, `value_counts()`, `nunique()` |
| ③ 시각화 | 데이터는 어떤 분포/패턴을 보이는가? | 히스토그램, 박스플롯, 막대그래프, 산점도 |
| ④ 상관관계 분석 | 변수 간에 어떤 관계가 있는가? | `corr()`, 히트맵, 산점도 행렬 |
| ⑤ 인사이트 도출 | 어떤 패턴/문제점을 발견했는가? | 분석 결과 종합, 가설 수립 |

---

### 3-2-2. 시각화 라이브러리 소개

이 실습에서는 **matplotlib**과 **seaborn**을 사용한다.

#### matplotlib

- Python의 **가장 기본적인** 시각화 라이브러리
- 세밀한 커스터마이징 가능
- 문법이 다소 장황하지만, 모든 차트를 그릴 수 있음

#### seaborn

- matplotlib 위에 구축된 **고수준(high-level) 시각화** 라이브러리
- 더 적은 코드로 **통계적으로 의미 있는 시각화** 가능
- 기본 스타일이 깔끔

| 차트 종류 | matplotlib | seaborn | 용도 |
|-----------|-----------|---------|------|
| 히스토그램 | `plt.hist()` | `sns.histplot()` | 수치형 변수 분포 |
| 박스플롯 | `plt.boxplot()` | `sns.boxplot()` | 분포 + 이상치 확인 |
| 산점도 | `plt.scatter()` | `sns.scatterplot()` | 두 변수 관계 |
| 막대그래프 | `plt.bar()` | `sns.barplot()` | 범주별 비교 |
| 히트맵 | - | `sns.heatmap()` | 상관관계, 결측치 |
| 파이차트 | `plt.pie()` | - | 비율/구성 |

#### 한글 폰트 설정 (필수)

matplotlib은 기본적으로 한글을 지원하지 않으므로, 반드시 폰트 설정이 필요하다.

```python
import matplotlib.pyplot as plt

# Windows의 경우
plt.rcParams["font.family"] = "Malgun Gothic"    # 맑은 고딕
plt.rcParams["axes.unicode_minus"] = False        # 마이너스 기호 깨짐 방지

# macOS의 경우
# plt.rcParams["font.family"] = "AppleGothic"

# Linux의 경우
# plt.rcParams["font.family"] = "NanumGothic"
```

> `axes.unicode_minus = False`를 설정하지 않으면, 음수 부호(`-`)가 네모(□)로 표시될 수 있다.

---

### 3-2-3. EDA 실습 — 전체 코드

앞서 수집한 대기오염 데이터(또는 준비된 샘플 데이터)를 활용하여 EDA를 수행한다.

`eda_practice.py` 파일 생성:

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================
# 0. 기본 설정
# ============================================================
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ============================================================
# 1단계: 데이터 로드 및 구조 확인
# ============================================================
print("=" * 60)
print("1단계: 데이터 구조 확인")
print("=" * 60)

# 앞서 저장한 CSV 파일 로드
df = pd.read_csv("air_quality_seoul.csv")

# 기본 정보 출력
print(f"\n▶ 데이터 크기: {df.shape[0]}행 × {df.shape[1]}열")
print(f"\n▶ 컬럼 목록:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i}. {col}")

print(f"\n▶ 데이터 타입:")
print(df.dtypes)

print(f"\n▶ 처음 5행:")
print(df.head())

print(f"\n▶ 마지막 5행:")
print(df.tail())

# 결측치 확인
print(f"\n▶ 컬럼별 결측치 수:")
missing = df.isnull().sum()
missing_pct = (df.isnull().sum() / len(df) * 100).round(1)
missing_df = pd.DataFrame({"결측치 수": missing, "비율(%)": missing_pct})
print(missing_df[missing_df["결측치 수"] > 0])  # 결측치가 있는 컬럼만 출력

# ============================================================
# 2단계: 기술통계 분석
# ============================================================
print("\n" + "=" * 60)
print("2단계: 기술통계 분석")
print("=" * 60)

# 수치형 컬럼 자동 감지
# 대기오염 데이터의 수치값이 문자열로 저장되어 있을 수 있으므로 변환
numeric_candidates = ["미세먼지(PM10)", "초미세먼지(PM2.5)", "오존(O3)",
                      "이산화질소(NO2)", "일산화탄소(CO)", "아황산가스(SO2)"]

for col in numeric_candidates:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")  # 변환 실패 시 NaN

# 기술통계
print(f"\n▶ 기술통계:")
print(df.describe().round(2))

# 범주형 컬럼 빈도 분석
if "측정소" in df.columns:
    print(f"\n▶ 측정소별 데이터 수:")
    print(df["측정소"].value_counts().head(10))

if "PM10등급" in df.columns:
    print(f"\n▶ PM10 등급 분포:")
    grade_map = {"1": "좋음", "2": "보통", "3": "나쁨", "4": "매우나쁨"}
    df["PM10등급_텍스트"] = df["PM10등급"].astype(str).map(grade_map)
    print(df["PM10등급_텍스트"].value_counts())

# ============================================================
# 3단계: 시각화
# ============================================================
print("\n" + "=" * 60)
print("3단계: 시각화")
print("=" * 60)

# --- 3-1. 결측치 히트맵 ---
plt.figure(figsize=(12, 5))
sns.heatmap(df.isnull(), cbar=True, yticklabels=False, cmap="YlOrRd")
plt.title("결측치 히트맵", fontsize=14, fontweight="bold")
plt.xlabel("컬럼")
plt.ylabel("행")
plt.tight_layout()
plt.savefig("01_missing_heatmap.png", dpi=150)
plt.show()
print("▶ '01_missing_heatmap.png' 저장 완료")

# --- 3-2. 수치형 변수 분포 (히스토그램 + KDE) ---
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

if len(numeric_cols) > 0:
    # 서브플롯으로 한 번에 표시
    n_cols = min(3, len(numeric_cols))
    n_rows = (len(numeric_cols) + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 4 * n_rows))
    if n_rows * n_cols == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for i, col in enumerate(numeric_cols):
        sns.histplot(df[col].dropna(), kde=True, ax=axes[i], color="steelblue")
        axes[i].set_title(f"{col} 분포", fontsize=12)
        axes[i].set_xlabel(col)
        axes[i].set_ylabel("빈도")

    # 빈 서브플롯 숨기기
    for j in range(len(numeric_cols), len(axes)):
        axes[j].set_visible(False)

    plt.suptitle("수치형 변수 분포", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig("02_distributions.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("▶ '02_distributions.png' 저장 완료")

# --- 3-3. 박스플롯 (이상치 확인) ---
if len(numeric_cols) > 0:
    fig, axes = plt.subplots(1, min(4, len(numeric_cols)),
                              figsize=(5 * min(4, len(numeric_cols)), 5))
    if min(4, len(numeric_cols)) == 1:
        axes = [axes]

    for i, col in enumerate(numeric_cols[:4]):
        sns.boxplot(y=df[col].dropna(), ax=axes[i], color="lightcoral")
        axes[i].set_title(f"{col}", fontsize=12)

    plt.suptitle("박스플롯 — 이상치 확인", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig("03_boxplots.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("▶ '03_boxplots.png' 저장 완료")

# --- 3-4. 막대그래프 (범주형 변수) ---
if "PM10등급_텍스트" in df.columns:
    plt.figure(figsize=(8, 5))
    grade_order = ["좋음", "보통", "나쁨", "매우나쁨"]
    available_grades = [g for g in grade_order if g in df["PM10등급_텍스트"].values]

    colors = {"좋음": "#2196F3", "보통": "#4CAF50", "나쁨": "#FF9800", "매우나쁨": "#F44336"}
    grade_counts = df["PM10등급_텍스트"].value_counts()

    bars = plt.bar(
        [g for g in available_grades if g in grade_counts.index],
        [grade_counts[g] for g in available_grades if g in grade_counts.index],
        color=[colors.get(g, "gray") for g in available_grades if g in grade_counts.index]
    )
    plt.title("PM10 등급별 측정소 수", fontsize=14, fontweight="bold")
    plt.xlabel("등급")
    plt.ylabel("측정소 수")

    # 막대 위에 값 표시
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f"{int(height)}", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plt.savefig("04_pm10_grade_bar.png", dpi=150)
    plt.show()
    print("▶ '04_pm10_grade_bar.png' 저장 완료")

# ============================================================
# 4단계: 상관관계 분석
# ============================================================
print("\n" + "=" * 60)
print("4단계: 상관관계 분석")
print("=" * 60)

if len(numeric_cols) >= 2:
    # 상관계수 행렬 계산
    corr_matrix = df[numeric_cols].corr().round(2)
    print("\n▶ 상관계수 행렬:")
    print(corr_matrix)

    # 히트맵 시각화
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,           # 셀 안에 숫자 표시
        cmap="coolwarm",      # 색상: 파란색(-1) ~ 빨간색(+1)
        center=0,             # 0을 기준으로 색상 대칭
        vmin=-1, vmax=1,      # 범위 고정
        square=True,          # 정사각형 셀
        linewidths=0.5,       # 셀 경계선
        fmt=".2f"             # 소수점 2자리
    )
    plt.title("변수 간 상관관계 히트맵", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig("05_correlation_heatmap.png", dpi=150)
    plt.show()
    print("▶ '05_correlation_heatmap.png' 저장 완료")

    # 강한 상관관계 쌍 출력
    print("\n▶ 강한 상관관계 (|r| ≥ 0.5):")
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            r = corr_matrix.iloc[i, j]
            if abs(r) >= 0.5:
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                direction = "양의 상관" if r > 0 else "음의 상관"
                print(f"   {col1} ↔ {col2}: r = {r} ({direction})")

# ============================================================
# 5단계: 인사이트 도출 (요약)
# ============================================================
print("\n" + "=" * 60)
print("5단계: EDA 인사이트 요약")
print("=" * 60)

print(f"""
[데이터 개요]
- 전체 데이터: {df.shape[0]}행 × {df.shape[1]}열
- 수치형 변수: {len(numeric_cols)}개
- 결측치가 있는 컬럼: {(df.isnull().sum() > 0).sum()}개

[발견한 내용]
- 결측치 현황을 확인하고, 전처리 방향을 결정할 수 있다
- 각 변수의 분포를 히스토그램과 박스플롯으로 확인했다
- 상관관계 분석을 통해 변수 간 관계를 파악했다

[다음 단계]
- 결측치 처리 (Part 2에서 배운 방법 적용)
- 필요한 특성 엔지니어링 수행
- 모델 학습 또는 대시보드 시각화로 연결
""")
```

---

### 3-2-4. 시각화 해석 가이드

각 시각화에서 **무엇을 봐야 하는지** 정리한다.

#### 히스토그램 (Histogram)

```
빈도
 │  ▓▓
 │  ▓▓▓▓
 │  ▓▓▓▓▓▓▓▓
 │  ▓▓▓▓▓▓▓▓▓▓▓▓
 │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 └──────────────────── 값
       (정규분포 형태)
```

| 확인 포인트 | 해석 |
|-------------|------|
| **좌우 대칭** | 정규분포에 가까움 → 평균/표준편차 사용 가능 |
| **한쪽으로 쏠림** (왼쪽 또는 오른쪽) | 편향된 분포 → 중앙값 사용 권장, 로그 변환 고려 |
| **봉우리가 2개** | 이봉분포 → 두 그룹이 섞여 있을 수 있음 |
| **극단값 존재** | 이상치 → 박스플롯으로 추가 확인 |

#### 박스플롯 (Box Plot)

```
              ○  ← 이상치 (Q3 + 1.5×IQR 초과)
              │
         ┌────┤  ← Q3 (75%)
         │    │
         │  ──│  ← 중앙값 (50%)
         │    │
         └────┤  ← Q1 (25%)
              │
              ○  ← 이상치 (Q1 - 1.5×IQR 미만)
```

| 확인 포인트 | 해석 |
|-------------|------|
| **상자의 크기** | IQR (Q3-Q1), 값이 클수록 데이터가 퍼져 있음 |
| **중앙값의 위치** | 상자 중앙이면 대칭, 한쪽이면 편향 |
| **수염(whisker) 길이** | 길수록 꼬리가 긴 분포 |
| **동그라미(○)** | 이상치, 데이터의 오류인지 실제 값인지 확인 필요 |

#### 상관관계 히트맵

| 상관계수 | 해석 | 색상 (coolwarm) |
|----------|------|-----------------|
| +0.7 ~ +1.0 | 강한 양의 상관 | 진한 빨강 |
| +0.4 ~ +0.7 | 중간 양의 상관 | 연한 빨강 |
| -0.4 ~ +0.4 | 약한 상관 (거의 무관) | 흰색 |
| -0.7 ~ -0.4 | 중간 음의 상관 | 연한 파랑 |
| -1.0 ~ -0.7 | 강한 음의 상관 | 진한 파랑 |

> **주의**: 상관관계가 높다고 해서 반드시 인과관계가 있는 것은 아니다.
> 예: "아이스크림 판매량"과 "익사 사고 수"는 높은 양의 상관관계를 보이지만, 원인은 "여름 (기온)"이라는 제3의 변수 때문이다.

---

### 3-2-5. EDA 체크리스트

실제 프로젝트에서 EDA 수행 시 아래 체크리스트를 활용한다:

```
□ 데이터 크기 확인 (shape)
□ 컬럼명과 데이터 타입 확인 (info, dtypes)
□ 결측치 현황 파악 (isnull().sum())
□ 기술통계 확인 (describe)
□ 범주형 변수 빈도 확인 (value_counts)
□ 수치형 변수 분포 시각화 (히스토그램)
□ 이상치 확인 (박스플롯, IQR)
□ 변수 간 상관관계 분석 (corr, 히트맵)
□ 인사이트 정리 및 다음 단계 계획
```

---

### 3-2-6. "데이터가 말하게 하라" — 비즈니스 관점의 EDA

EDA는 단순히 `describe()`를 출력하고 그래프를 그리는 기술적 작업이 아니다. **"왜 이 지표를 보는가?"**, **"이 패턴이 현실에서 무엇을 의미하는가?"**라는 질문을 던지는 것이 핵심이다.

#### 기술적 EDA vs 비즈니스 관점 EDA

| 기술적 EDA (How) | 비즈니스 관점 EDA (Why) |
|------------------|----------------------|
| "결측치가 15개 있다" | **"왜 이 측정소에서만 결측치가 많을까? 장비 고장인가, 통신 장애인가?"** |
| "PM10과 O3의 상관계수가 -0.6이다" | **"미세먼지가 높을 때 오존 농도는 왜 낮아질까?"** (광화학 반응: 미세먼지가 햇빛을 차단 → 오존 생성 감소) |
| "가격 컬럼에 이상치 3개 발견" | **"이 수치는 단순 입력 오류인가, 아니면 실제로 일어난 이벤트인가?"** |
| "판매량의 표준편차가 크다" | **"어떤 요인이 판매량 변동을 만드는가? 계절? 프로모션? 경쟁사?"** |

#### 대기오염 데이터 EDA 시 던져볼 질문들

```
[결측치 분석]
Q. 특정 측정소에서만 결측이 집중되어 있지 않은가?
   → 해당 측정소의 장비 교체/점검 일정과 관련이 있을 수 있다
   → 무작위 결측 vs 체계적 결측에 따라 처리 방법이 달라진다

[분포 분석]
Q. 미세먼지 농도가 정규분포를 따르는가, 한쪽으로 치우쳐 있는가?
   → 오른쪽으로 치우친 분포(양의 편향) → 대부분 "좋음"이지만 가끔 극단적으로 나쁜 날이 있다
   → 이런 경우 평균보다 중앙값이 더 대표성 있는 지표이다

[이상치 분석]
Q. PM10이 300을 넘은 날이 있다면, 그날 무슨 일이 있었는가?
   → 황사, 산불, 공장 사고 등 실제 사건과 연결 가능
   → "이상치 = 무조건 제거"가 아니라, 원인을 파악한 후 판단해야 한다

[상관관계 분석]
Q. 미세먼지(PM10)와 초미세먼지(PM2.5)의 상관관계가 높다면?
   → 같은 오염원에서 발생하므로 당연한 결과 → 모델에 둘 다 넣으면 다중공선성 문제
   → 하나만 선택하거나 주성분분석(PCA) 등으로 차원 축소 고려
```

> **핵심**: 숫자와 그래프 뒤에 있는 **"이야기"를 찾는 것**이 EDA의 진짜 목적이다.
> 프로젝트 보고서에서도 "히트맵을 그렸습니다"가 아니라 "히트맵을 통해 ~한 패턴을 발견했고, 이는 ~를 의미합니다"로 작성해야 좋은 점수를 받을 수 있다.

---

### 3-2-7. 시각적 보조 자료 — 핵심 개념 다이어그램

수업 중 아래 다이어그램을 활용하면 학생들이 전체 흐름과 개념을 더 직관적으로 이해할 수 있다.

#### (1) API 요청-응답 흐름도

```
  ┌──────────┐                                    ┌──────────────┐
  │  클라이언트  │                                    │   API 서버    │
  │ (Python)  │                                    │ (data.go.kr) │
  └─────┬────┘                                    └──────┬───────┘
        │                                                │
        │  ① HTTP GET 요청                               │
        │  ┌─────────────────────────────────┐           │
        │  │ URL: http://apis.data.go.kr/... │           │
        │  │ params:                         │           │
        │  │   serviceKey = "Decoding키"     │──────────→│
        │  │   returnType = "json"           │           │
        │  │   sidoName   = "서울"            │           │
        │  │   numOfRows  = "100"            │           │
        │  └─────────────────────────────────┘           │
        │                                                │
        │                                    ② 인증 확인  │
        │                                    ③ 데이터 조회 │
        │                                                │
        │            ④ JSON 응답                          │
        │  ┌─────────────────────────────────┐           │
        │  │ {                               │           │
        │  │   "response": {                 │           │
        │←─│     "header": {resultCode:"00"},│───────────│
        │  │     "body": {                   │           │
        │  │       "items": [{...}, ...]     │           │
        │  │     }                           │           │
        │  │   }                             │           │
        │  │ }                               │           │
        │  └─────────────────────────────────┘           │
        │                                                │
        │  ⑤ response.json() → dict                     │
        │  ⑥ pd.DataFrame(items)                        │
        │  ⑦ df.to_csv("data.csv")                      │
        ▼                                                ▼
```

> 핵심 포인트: `params`에 담긴 값들이 URL 쿼리 문자열로 변환되어 서버에 전달되고, 서버는 JSON 형태로 데이터를 돌려준다.

#### (2) 박스플롯 해부도 — 통계적 의미

```
                    값의 축 (예: 미세먼지 농도)

    ○ 200 ········· 이상치 (Q3 + 1.5×IQR 초과)
    │               → "이 값은 정상 범위를 벗어남"
    │               → 입력 오류? 실제 이벤트? 확인 필요
    │
    ┤ 150 ········· 상한 수염 (Whisker) = min(최댓값, Q3 + 1.5×IQR)
    │               → "이상치를 제외한 최댓값"
    │
    ┌────┐
    │    │ 130 ···· Q3 (75번째 백분위수)
    │    │          → "전체 데이터의 75%가 이 값 이하"
    │    │
    │────│ 85 ····· 중앙값 (Median, 50번째 백분위수)
    │    │          → "데이터를 반으로 나누는 값"
    │    │          → 이상치에 강건한 대표값
    │    │
    │    │ 45 ····· Q1 (25번째 백분위수)
    └────┘          → "전체 데이터의 25%가 이 값 이하"
    │
    │               IQR = Q3 - Q1 = 130 - 45 = 85
    │               → "데이터의 중간 50%가 퍼진 범위"
    │
    ┤ 10 ·········· 하한 수염 (Whisker) = max(최솟값, Q1 - 1.5×IQR)
    │
    ○ -20 ········· 이상치 (Q1 - 1.5×IQR 미만)
```

| 구성 요소 | 통계적 의미 | EDA에서 확인할 점 |
|-----------|------------|------------------|
| **상자 (Box)** | IQR, 데이터의 중간 50% 분포 | 상자가 넓으면 → 데이터 산포가 큼 |
| **중앙선** | 중앙값 (Median) | 상자 내 위치로 편향 방향 판단 |
| **수염 (Whisker)** | 이상치를 제외한 데이터 범위 | 비대칭이면 분포가 한쪽으로 치우침 |
| **점 (○)** | 이상치 | 개수와 값을 확인 → 원인 조사 |

#### (3) 상관관계 히트맵 읽는 법

```
              PM10    PM2.5    O3     NO2     CO
  PM10    │  1.00  │  0.85  │ -0.62 │  0.45 │  0.38 │
  PM2.5   │  0.85  │  1.00  │ -0.58 │  0.52 │  0.41 │
  O3      │ -0.62  │ -0.58  │  1.00 │ -0.71 │ -0.35 │
  NO2     │  0.45  │  0.52  │ -0.71 │  1.00 │  0.67 │
  CO      │  0.38  │  0.41  │ -0.35 │  0.67 │  1.00 │
            진한빨강   연한빨강   진한파랑   연한빨강   흰색
```

**읽는 순서:**

```
① 대각선은 항상 1.0 (자기 자신과의 상관) → 무시
② 절댓값이 0.7 이상인 셀 찾기 → 강한 상관관계
   예: PM10-PM2.5 (0.85) → "같은 오염원, 함께 증가"
   예: O3-NO2 (-0.71) → "오존↑이면 이산화질소↓ (광화학 반응)"
③ 0.4~0.7 범위 → 중간 상관 → 추가 분석 가치 있음
④ 0.4 미만 → 약한 상관 → 독립적인 변수일 가능성
```

> **실무 팁**: 상관계수가 0.9 이상인 변수 쌍이 있다면, 머신러닝 모델에 둘 다 넣으면 **다중공선성(Multicollinearity)** 문제가 발생할 수 있다. 이 경우 하나를 제거하거나 PCA로 차원을 축소한다. (7주차 이후 프로젝트에서 다시 다룸)

---

### 3-2-8. EDA 체크리스트

실제 프로젝트에서 EDA 수행 시 아래 체크리스트를 활용한다:

```
[기술적 확인]
□ 데이터 크기 확인 (shape)
□ 컬럼명과 데이터 타입 확인 (info, dtypes)
□ 결측치 현황 파악 (isnull().sum())
□ 기술통계 확인 (describe)
□ 범주형 변수 빈도 확인 (value_counts)
□ 수치형 변수 분포 시각화 (히스토그램)
□ 이상치 확인 (박스플롯, IQR)
□ 변수 간 상관관계 분석 (corr, 히트맵)

[비즈니스 관점 확인]
□ 결측치가 특정 조건에서 집중되지 않는가? (무작위 vs 체계적)
□ 이상치가 실제 현상을 반영하는가, 오류인가?
□ 발견한 패턴이 도메인 지식과 일치하는가?
□ 인사이트 정리 및 다음 단계 계획
```

---

## 핵심 정리

### 이번 파트에서 배운 것

| 주제 | 핵심 내용 |
|------|-----------|
| **공공데이터** | data.go.kr에서 API 키를 발급받아 Python으로 데이터 수집 |
| **REST API** | 엔드포인트 + 파라미터 → requests.get() → JSON 응답 파싱 |
| **requests** | `requests.get(url, params)` → `response.json()` → `pd.DataFrame()` |
| **EDA** | 데이터 구조 → 기술통계 → 시각화 → 상관관계 → 인사이트 도출 |
| **시각화** | matplotlib + seaborn으로 히스토그램, 박스플롯, 히트맵 작성 |

### 프로젝트에서의 활용

```
데이터 수집 (Part 3) → 전처리 (Part 2) → EDA (Part 3) → 모델링 (7주차~) → 대시보드 (3~4주차)
```

이번에 배운 데이터 수집과 EDA는 이번 학기 모든 프로젝트의 **시작점**이 된다.
- **7주차**: 웹 공격 분류 프로젝트 → 데이터 수집/전처리/EDA 수행
- **11~12주차**: 이미지 분류 프로젝트 → 데이터 수집/전처리/EDA 수행
- **13~14주차**: 자유 주제 프로젝트 → 데이터 수집/전처리/EDA 수행

---

## 체크포인트 (최종)

- [ ] 공공데이터포털의 API 키를 발급받았다 (또는 대체 API를 사용했다)
- [ ] `requests.get()`으로 API를 호출하고 JSON 데이터를 받았다
- [ ] JSON 데이터를 DataFrame으로 변환하고 CSV로 저장했다
- [ ] EDA 5단계 프로세스를 이해했다
- [ ] 결측치 히트맵, 히스토그램, 박스플롯, 상관관계 히트맵을 생성했다
- [ ] 시각화 결과를 해석할 수 있다 (분포, 이상치, 상관관계)
- [ ] (도전) 수집한 데이터와 EDA 결과를 Streamlit으로 표시해보기
