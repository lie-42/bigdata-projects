# 12주차 — 이미지 분류 프로젝트 (2) · 파인튜닝 · 성능평가 · 웹 앱 배포

## 실습 코드 목록

| 교시 | 파일명 | 내용 | 강의안 |
|------|--------|------|--------|
| 1교시 | `04_finetune_vit.ipynb` | ViT 헤드 교체 + 백본 동결 + `Trainer` 파인튜닝 + 혼동행렬 평가 + 모델 저장 | [1교시](../../12_week/plane/1교시_이미지_분류_모델_파인튜닝_및_성능평가.md) |
| 2교시 | `app.py` | Streamlit 이미지 분류 웹 앱 (파일 업로드 + 카메라 실시간) | [2교시](../../12_week/plane/2교시_Streamlit_이미지_분류_웹앱_구현.md) |
| 3교시 | — | 프로젝트 수업 (위 두 파일을 본인 주제에 적용) | |

## 사전 준비

### 1) 패키지 설치

```bash
pip install torch torchvision transformers accelerate datasets scikit-learn pillow matplotlib streamlit
```

> ⚠️ `Trainer`는 **`accelerate>=0.26.0`** 가 반드시 필요합니다(없으면 셀 [8]에서 ImportError).
> 강의실 환경: **GPU(8GB)**. CPU에서도 동작하지만 학습이 더 느립니다.
> GPU 가속을 위해 PyTorch는 CUDA 빌드로 설치하세요(없으면 자동 CPU 폴백).

### 2) JupyterLab 실행 (1교시)

```bash
jupyter lab
```
`BigDataAnalysis/12_week/04_finetune_vit.ipynb` 를 더블클릭 → 셀을 위에서부터 실행.

### 3) Streamlit 앱 실행 (2교시)

```bash
streamlit run app.py
```
브라우저에서 `http://localhost:8501` 자동 오픈.
> ⚠️ **순서 주의**: `app.py`는 1교시에서 만든 `vit-cifar10-finetuned/` 폴더가 있어야 동작합니다.
> 노트북 셀 [12]까지 실행해 모델을 먼저 저장하세요.

## 실습 흐름 (1·2교시 90분 + 3교시 프로젝트)

### 1교시 — 파인튜닝 및 성능 평가 (45분) · `04_finetune_vit.ipynb`

| 단계 | 셀 | 내용 | 시간 |
|------|-----|------|------|
| Step 1 | [0]·[1] | 환경 확인 + CIFAR-10 로드(소량) + 라벨 매핑 | 5분 |
| Step 2 | [2]·[3] | ViTImageProcessor 전처리 + 결과 확인 | 5분 |
| Step 3 | [4]·[5] | 헤드 10개로 교체 + 백본 동결(선형 탐침) | 10분 |
| Step 4 | [6]·[7]·[8] | collate/metrics + Trainer + 학습 | 15분 |
| Step 5 | [9]·[10]·[11] | 정확도·F1 + 혼동행렬 + 오분류 분석 | 8분 |
| Step 6 | [12] | 모델 저장 → 2교시 준비 | 2분 |

### 2교시 — Streamlit 웹 앱 (45분) · `app.py`

| 단계 | 내용 | 시간 |
|------|------|------|
| Step 1 | 모델 로드 + `@st.cache_resource` 캐싱 | 10분 |
| Step 2 | `st.file_uploader` 업로드 분류 ★ | 15분 |
| Step 3 | `st.camera_input` 실시간 카메라 분류 ★ | 10분 |
| Step 4 | Top-5 시각화 + (선택) 로컬 네트워크 공유 배포 | 10분 |

### 3교시 — 프로젝트 수업

오늘 만든 `04_finetune_vit.ipynb` + `app.py` 를 **본인 주제**에 적용:
주제·클래스 선정 → 데이터 수집 → 데이터 부분만 교체해 파인튜닝 → 앱 모델 경로 교체 → 발표 준비.

## 생성/사용 파일

| 파일 | 생성/사용 시점 | 용도 |
|------|-------------|------|
| `./vit-cifar10-ckpt/` | 1교시 학습 중 | Trainer 체크포인트(중간 저장, `save_total_limit=1`) |
| `./vit-cifar10-finetuned/` | 1교시 셀 [12] | **최종 모델 + 전처리** (2교시 `app.py`가 로드) |
| `~/.cache/huggingface/...` | 1교시 셀 [1]·[2] | CIFAR-10 / ViT 사전학습 가중치 캐시 |

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `ImportError: ... requires accelerate>=0.26.0` | `accelerate` 미설치 | `pip install 'accelerate>=0.26.0'` 후 커널 재시작 |
| `TypeError: ... eval_strategy` | 구버전 transformers | 노트북이 자동 호환 처리(셀 [7]) — 그래도 나면 업그레이드 |
| `KeyError: 'img'` | 데이터셋 컬럼명 다름 | `train_ds.column_names`로 확인 |
| `RuntimeError: CUDA out of memory` | 8GB 초과 | batch 16→8→4, `fp16` 유지, 백본 동결 확인 |
| 정확도가 ~10%에서 안 오름 | classifier까지 동결됨 / lr 과소 | 셀 [5] 동결 범위 확인, `learning_rate` ↑ |
| 앱이 모델을 못 찾음 | 노트북 셀 [12] 미실행 | 모델 저장 후 `streamlit run app.py` |
| 앱이 매번 느림 | 모델 매 실행마다 로드 | `@st.cache_resource` 확인 |
| 앱 실행 중 GPU OOM | 노트북이 GPU 점유 중 | 노트북 **커널 종료** 후 앱 실행 |
| 카메라가 안 켜짐 | 브라우저 권한/HTTPS | 권한 허용, 로컬은 `localhost`에서 실행 |

## 다음 주차(13주차) 미리보기

12주차까지 **데이터 → 파인튜닝 → 평가 → 배포**의 전체 파이프라인을 익혔습니다.
13·14주차는 이 템플릿으로 **자유 주제 프로젝트**를 수행하고, 15주차에 기말 발표를 합니다.
