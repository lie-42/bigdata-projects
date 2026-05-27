"""
실습 11 (자율 실습): Streamlit 웹 공격 탐지 대시보드 — 스타터 코드
=================================================================
이 파일을 dashboard.py로 복사한 뒤 # TODO 주석이 달린 부분을 채우면
1·2교시에서 만든 3가지 분류기(IQR / RandomForest / LLM)를 통합한
대시보드가 완성됩니다.

실행:
    cp dashboard_starter.py dashboard.py
    streamlit run dashboard.py

사전 조건:
    - classification_results.pkl  (1교시 마지막 셀에서 생성)
    - ../7_week/processed_data.pkl (7주차 feature_engineering.py 결과)
    - Ollama 서버 실행 중 + gemma3:4b 모델 다운로드됨

힌트는 3교시 강의안: 10_week/plane/3교시_Streamlit_대시보드_자율실습.md
"""

import json
import math
import os
import re
import time
import pickle
from urllib.parse import unquote, urlparse, parse_qs

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Ollama는 사용 시점에 import (없을 수도 있음)


# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="웹 공격 탐지 대시보드",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# Step 1: 모델 로드 함수 (캐싱)
# ============================================================
@st.cache_resource
def load_models():
    """1교시에서 만든 모델과 데이터 로드.

    Returns:
        dict: {
            "rf":          학습된 RandomForest 모델,
            "xgb":         학습된 XGBoost 모델,
            "iqr_bounds":  [(lower, upper), ...] 23개 특성의 IQR 경계,
            "feature_cols": 23개 특성명 리스트,
            "scaler":      7주차 StandardScaler (특성 스케일링용),
            "iqr_threshold": 공격 판정 임계값 (정수),
        }
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1-A: classification_results.pkl 읽기 (1교시 마지막 셀에서 생성)
    cls_path = os.path.join(base_dir, "classification_results.pkl")
    with open(cls_path, "rb") as f:
        results = pickle.load(f)

    # 모델과 IQR 경계가 '스케일링된 특성' 기준으로 학습되었으므로
    # 7주차 processed_data.pkl 의 StandardScaler 도 함께 로드해야 한다.
    proc_path = os.path.join(base_dir, "..", "7_week", "processed_data.pkl")
    with open(proc_path, "rb") as f:
        processed = pickle.load(f)

    # 1-B: 반환 dict 구성
    return {
        "rf": results["rf_model"],
        "xgb": results["xgb_model"],
        "iqr_bounds": results["iqr_bounds"],
        "feature_cols": results["feature_cols"],
        "scaler": processed["scaler"],
        "iqr_threshold": 2,
    }


# ============================================================
# Step 3: 특성 추출 함수 (HTTP 텍스트 → 23차원 벡터)
# ============================================================
# 7주차 preprocessing.py 와 동일한 키워드 목록을 사용해야
# 학습한 모델이 같은 의미로 특성을 해석합니다.
SQL_KEYWORDS = ["select", "union", "drop", "insert", "delete",
                "update", "' or", "1=1", "1'='1", "--", "/*"]
XSS_KEYWORDS = ["<script", "alert(", "onerror", "<iframe",
                "<img", "javascript:", "onfocus", "onload"]
CMD_PATTERNS = ["; ", "| ", "&&", "/bin/", "/etc/", "exec"]


def _calculate_entropy(text: str) -> float:
    """섀넌 엔트로피 (7주차 preprocessing.py 와 동일)."""
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def extract_features(http_text: str, feature_cols: list) -> np.ndarray:
    """사용자가 입력한 HTTP 텍스트에서 23개 숫자 특성을 추출.

    7주차 preprocessing.py와 동일한 순서/계산 방식이어야
    1교시에서 학습한 모델이 올바른 결과를 줍니다.

    Args:
        http_text: 'GET /path?q=1 HTTP/1.1\\nHost: ...\\nBody: ...' 형태
        feature_cols: 7주차에서 추출한 특성명 리스트 (23개)

    Returns:
        shape (1, 23)의 numpy 배열 (스케일링 전 원시값)
    """
    # 3-A: HTTP 첫 줄에서 method 와 url 분리
    lines = http_text.strip().splitlines()
    first = lines[0] if lines else ""
    parts = first.split()
    url = parts[1] if len(parts) > 1 else ""

    # 3-B: body 부분 추출 ('Body:' 접두어 또는 빈 줄 뒤)
    body = ""
    body_mode = False
    for ln in lines[1:]:
        if ln.lower().startswith("body:"):
            body = ln[5:].strip()
            break
        if body_mode:
            body += ("\n" if body else "") + ln
        elif ln.strip() == "":
            body_mode = True

    # 3-C: URL / Body 디코딩 + 결합 (7주차와 동일하게 latin-1)
    url_decoded = unquote(url, encoding="latin-1")
    body_decoded = unquote(body, encoding="latin-1")
    full_text = url_decoded + " " + body_decoded
    full_lower = full_text.lower()

    # 3-D: 23개 특성 추출 (preprocessing.py 와 동일한 로직)
    feats = {}

    # 길이
    feats["url_length"] = len(url_decoded)
    feats["body_length"] = len(body_decoded)
    feats["total_length"] = feats["url_length"] + feats["body_length"]

    # URL 구조
    try:
        parsed = urlparse(url_decoded)
        params = parse_qs(parsed.query)
        feats["num_params"] = len(params)
        feats["path_depth"] = parsed.path.count("/")
        feats["has_query"] = 1 if parsed.query else 0
        feats["query_length"] = len(parsed.query)
    except Exception:
        feats["num_params"] = 0
        feats["path_depth"] = 0
        feats["has_query"] = 0
        feats["query_length"] = 0
    feats["body_num_params"] = (
        len(body_decoded.split("&")) if body_decoded and "=" in body_decoded else 0
    )

    # 공격 키워드
    feats["has_sql"] = int(any(kw in full_lower for kw in SQL_KEYWORDS))
    feats["sql_keyword_count"] = sum(1 for kw in SQL_KEYWORDS if kw in full_lower)
    feats["has_xss"] = int(any(kw in full_lower for kw in XSS_KEYWORDS))
    feats["has_traversal"] = int("../" in full_text or "..\\" in full_text)
    feats["traversal_count"] = full_text.count("../") + full_text.count("..\\")
    feats["has_cmd_injection"] = int(any(p in full_lower for p in CMD_PATTERNS))
    feats["has_crlf"] = int("%0d" in full_lower or "%0a" in full_lower)

    # 특수문자/공백
    feats["num_special_chars"] = len(re.findall(r"['\";|<>&`\\]", full_text))
    feats["special_char_ratio"] = feats["num_special_chars"] / max(len(full_text), 1)
    feats["num_dots"] = full_text.count(".")
    feats["num_slashes"] = full_text.count("/")
    feats["num_spaces"] = (
        full_text.count(" ") + full_text.count("%20") + full_text.count("+")
    )

    # 통계
    feats["url_entropy"] = _calculate_entropy(url_decoded)
    feats["digit_ratio"] = sum(c.isdigit() for c in full_text) / max(len(full_text), 1)
    feats["upper_ratio"] = sum(c.isupper() for c in full_text) / max(len(full_text), 1)

    # 3-E: feature_cols 순서대로 배열 생성
    row = [feats.get(c, 0) for c in feature_cols]
    return np.array(row, dtype=float).reshape(1, -1)


# ============================================================
# Step 4: 3가지 분류 함수
# ============================================================
def classify_iqr(features: np.ndarray, iqr_bounds: list, threshold: int = 2) -> dict:
    """IQR 이상치 점수 기반 분류.

    features 는 학습 때와 동일하게 **스케일링된 값**이어야 합니다.
    """
    start = time.perf_counter()

    # 4-A: 23개 특성 중 IQR 경계 밖에 있는 개수 카운트
    score = 0
    for i, bounds in enumerate(iqr_bounds):
        if bounds is None:
            continue
        lower, upper = bounds
        if lower is None or upper is None:
            continue
        val = features[0, i]
        if val < lower or val > upper:
            score += 1

    # 4-B: 점수가 임계값 이상이면 공격
    label = "Anomalous" if score >= threshold else "Normal"

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "label": label,
        "score": score,
        "max_score": len(iqr_bounds),
        "elapsed_ms": elapsed,
    }


def classify_ml(model, features: np.ndarray, name: str = "RF") -> dict:
    """RandomForest 또는 XGBoost로 분류 + 신뢰도."""
    start = time.perf_counter()

    # 4-C: 예측 + 예측한 클래스의 확률(신뢰도)
    pred = int(model.predict(features)[0])
    try:
        proba = model.predict_proba(features)[0]
        confidence = float(proba[pred])
    except Exception:
        confidence = 1.0
    label = "Anomalous" if pred == 1 else "Normal"

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "label": label,
        "confidence": confidence,
        "elapsed_ms": elapsed,
        "model_name": name,
    }


PROMPT_TEMPLATE = (
    "You are a web security expert. Classify the following HTTP request "
    "as \"Normal\" or \"Anomalous\" and provide a brief reason.\n\n"
    "Examples:\n"
    "Request: GET /index.jsp HTTP/1.1\n"
    "Output: {{\"label\": \"Normal\", \"reason\": \"Standard page request\"}}\n\n"
    "Request: GET /search?q=' OR '1'='1 HTTP/1.1\n"
    "Output: {{\"label\": \"Anomalous\", \"reason\": \"SQL Injection pattern\"}}\n\n"
    "Now classify:\n"
    "Request: {http_text}\n"
    "Output:"
)


def classify_llm(http_text: str, model_name: str = "gemma3:4b") -> dict:
    """Ollama LLM으로 HTTP 요청 직접 분류."""
    start = time.perf_counter()

    try:
        import ollama
    except ImportError:
        return {"label": "Unknown", "reason": "ollama 패키지 미설치",
                "elapsed_ms": 0}

    # 4-D: 프롬프트 생성 + ollama.chat 호출
    prompt = PROMPT_TEMPLATE.format(http_text=http_text)
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0},
        )
        text = response["message"]["content"]
    except Exception as e:
        return {
            "label": "Unknown",
            "reason": f"Ollama 오류: {e}",
            "elapsed_ms": (time.perf_counter() - start) * 1000,
        }

    # 4-E: JSON 응답 파싱
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not match:
        return {
            "label": "Unknown",
            "reason": text[:80],
            "elapsed_ms": (time.perf_counter() - start) * 1000,
        }
    try:
        parsed = json.loads(match.group())
        label = parsed.get("label", "Unknown")
        reason = parsed.get("reason", "")
    except json.JSONDecodeError:
        label, reason = "Unknown", text[:80]

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "label": label,
        "reason": reason,
        "elapsed_ms": elapsed,
    }


# ============================================================
# 사이드바 — 모델/데이터 정보
# ============================================================
with st.sidebar:
    st.header("ℹ️ 모델 정보")
    # 7-A: 사용 모델 정보 표시
    st.markdown("- **IQR**: 23개 특성 이상치 점수")
    st.markdown("- **RandomForest**: 100 trees, balanced")
    st.markdown("- **XGBoost**: GBT, max_depth=6")
    st.markdown("- **LLM**: Ollama gemma3:4b")

    st.markdown("---")
    st.subheader("📦 데이터셋")
    st.markdown("- CSIC 2010 (스페인 정보보호기관)")
    st.markdown("- 학습 8,000건 / 테스트 2,000건")
    st.metric("입력 특성 수", "23개")
    st.metric("판정 임계값 (IQR)", "2 / 23")

    st.markdown("---")
    # 7-B: 학번/이름 입력
    student_name = st.text_input("학번/이름", value="20XX-XXXXX 홍길동")
    st.caption("👆 보고서 제출 시 이 이름이 화면에 표시됩니다.")


# ============================================================
# 메인 영역 — Step 2: 입력 폼
# ============================================================
st.title("🛡️ 웹 공격 탐지 대시보드")
st.markdown(f"학생: **{student_name}**")
st.markdown(
    "HTTP 요청 텍스트를 입력하면 **3가지 모델**이 동시에 분류합니다. "
    "각 모델의 결과·신뢰도·처리 시간을 비교해 보세요."
)

# 예시 선택 — 학생들이 다양한 케이스를 빠르게 시도해 볼 수 있도록
EXAMPLES = {
    "(직접 입력)": "",
    "정상 페이지 요청": "GET /tienda1/index.jsp HTTP/1.1\nHost: localhost:8080",
    "SQL Injection (URL)": "GET /tienda1/publico/anadir.jsp?id=2'+OR+'1'='1 HTTP/1.1\nHost: localhost:8080",
    "XSS (Body)": "POST /tienda1/publico/comentar.jsp HTTP/1.1\nHost: localhost:8080\nBody: comentario=<script>alert('xss')</script>",
    "Path Traversal": "GET /tienda1/imagenes/../../../etc/passwd HTTP/1.1\nHost: localhost:8080",
}

example_name = st.selectbox("예시 선택", list(EXAMPLES.keys()))
default_text = EXAMPLES[example_name] or EXAMPLES["SQL Injection (URL)"]

# TODO 2-A: HTTP 요청 입력 박스
http_input = st.text_area(
    "HTTP 요청",
    value=default_text,
    height=140,
    placeholder="GET /index.jsp HTTP/1.1\nHost: localhost:8080",
)

# TODO 2-B: 분류 버튼
classify_button = st.button("🔍 분류 실행", type="primary", use_container_width=True)


# ============================================================
# Step 5: 분류 실행 + 3개 컬럼에 결과 표시
# ============================================================
if classify_button:
    if not http_input.strip():
        st.warning("HTTP 요청을 입력하세요.")
        st.stop()

    models = load_models()
    if models is None:
        st.error("⚠️ load_models() 함수의 TODO를 먼저 구현하세요.")
        st.stop()

    # 원시 23차원 특성 추출 → 학습 때 사용한 StandardScaler 로 동일하게 스케일링
    raw_features = extract_features(http_input, models["feature_cols"])
    features = models["scaler"].transform(raw_features)

    # 3개 분류기 동시 실행 (모두 스케일링된 특성을 사용)
    iqr_result = classify_iqr(features, models["iqr_bounds"], models["iqr_threshold"])
    rf_result  = classify_ml(models["rf"],  features, "RandomForest")
    xgb_result = classify_ml(models["xgb"], features, "XGBoost")

    with st.spinner("🤖 LLM 추론 중... (1~5초 소요)"):
        llm_result = classify_llm(http_input)

    # ─── 결과 카드 4개 ────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 분류 결과")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("##### 📊 IQR (통계)")
        # TODO 5-A: IQR 결과 표시
        is_attack = iqr_result["label"] == "Anomalous"
        if is_attack:
            st.error(f"🚨 공격")
        else:
            st.success(f"✅ 정상")
        st.metric("이상치 점수",
                  f"{iqr_result['score']}/{iqr_result['max_score']}")
        st.caption(f"⏱ {iqr_result['elapsed_ms']:.1f}ms")

    with col2:
        st.markdown("##### 🌲 RandomForest")
        # TODO 5-B: RF 결과 표시 (st.progress로 신뢰도 막대)
        is_attack = rf_result["label"] == "Anomalous"
        if is_attack:
            st.error(f"🚨 공격")
        else:
            st.success(f"✅ 정상")
        st.progress(rf_result["confidence"])
        st.metric("신뢰도", f"{rf_result['confidence']*100:.1f}%")
        st.caption(f"⏱ {rf_result['elapsed_ms']:.1f}ms")

    with col3:
        st.markdown("##### 🚀 XGBoost")
        is_attack = xgb_result["label"] == "Anomalous"
        if is_attack:
            st.error(f"🚨 공격")
        else:
            st.success(f"✅ 정상")
        st.progress(xgb_result["confidence"])
        st.metric("신뢰도", f"{xgb_result['confidence']*100:.1f}%")
        st.caption(f"⏱ {xgb_result['elapsed_ms']:.1f}ms")

    with col4:
        st.markdown("##### 🤖 LLM (Ollama)")
        # TODO 5-C: LLM 결과 표시 (자연어 근거 포함)
        label = llm_result.get("label", "Unknown")
        if label == "Anomalous":
            st.error(f"🚨 공격")
        elif label == "Normal":
            st.success(f"✅ 정상")
        else:
            st.warning(f"❓ {label}")
        st.info(f"💬 {llm_result.get('reason', '(근거 없음)')}")
        st.caption(f"⏱ {llm_result['elapsed_ms']:.0f}ms")

    # ─── Step 6: 비교 차트 ───────────────────────────────────
    st.markdown("---")
    st.subheader("📈 모델 비교")

    # TODO 6-A: 비교용 DataFrame 만들기
    comparison_df = pd.DataFrame([
        {"모델": "IQR", "라벨": iqr_result["label"],
         "신뢰도(%)": iqr_result["score"] / iqr_result["max_score"] * 100,
         "처리 시간(ms)": iqr_result["elapsed_ms"]},
        {"모델": "RF", "라벨": rf_result["label"],
         "신뢰도(%)": rf_result["confidence"] * 100,
         "처리 시간(ms)": rf_result["elapsed_ms"]},
        {"모델": "XGB", "라벨": xgb_result["label"],
         "신뢰도(%)": xgb_result["confidence"] * 100,
         "처리 시간(ms)": xgb_result["elapsed_ms"]},
        {"모델": "LLM", "라벨": llm_result.get("label", "Unknown"),
         "신뢰도(%)": 100 if llm_result.get("label") in ("Normal", "Anomalous") else 50,
         "처리 시간(ms)": llm_result["elapsed_ms"]},
    ])

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # TODO 6-B: 신뢰도 막대 차트
        fig1 = px.bar(
            comparison_df, x="모델", y="신뢰도(%)", color="라벨",
            title="모델별 신뢰도",
            color_discrete_map={"Normal": "#22d3ee", "Anomalous": "#ef4444",
                                "Unknown": "#888"},
            text_auto=".1f",
        )
        fig1.update_yaxes(range=[0, 100])
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        # TODO 6-C: 처리 시간 막대 (로그 스케일)
        fig2 = px.bar(
            comparison_df, x="모델", y="처리 시간(ms)",
            title="처리 시간 비교 (Y축 로그)",
            log_y=True,
            color="모델",
            text_auto=".1f",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ─── 다수결 최종 판정 (도전 과제 3) ──────────────────────
    st.markdown("---")
    st.subheader("🗳️ 다수결 최종 판정")

    all_results = [iqr_result, rf_result, xgb_result, llm_result]
    attack_votes = sum(1 for r in all_results if r.get("label") == "Anomalous")
    normal_votes = sum(1 for r in all_results if r.get("label") == "Normal")
    total = len(all_results)

    vote_col1, vote_col2 = st.columns([2, 1])
    with vote_col1:
        if attack_votes >= 2:
            st.error(f"⚠️ 최종 판정: **공격(Anomalous)** — 찬성 {attack_votes}/{total}")
        elif normal_votes >= 2:
            st.success(f"✅ 최종 판정: **정상(Normal)** — 찬성 {normal_votes}/{total}")
        else:
            st.warning(f"❓ 의견이 갈렸습니다 (공격 {attack_votes} · 정상 {normal_votes} · 기타 {total - attack_votes - normal_votes})")

    with vote_col2:
        st.metric("공격 표", f"{attack_votes}/{total}")
        st.metric("정상 표", f"{normal_votes}/{total}")

else:
    st.info("👆 위 입력 박스에 HTTP 요청을 작성한 뒤 [🔍 분류 실행] 버튼을 누르세요.")
