# -*- coding: utf-8 -*-
"""12주차 2교시 — 이미지 분류 Streamlit 웹 앱
1교시에서 저장한 모델(./vit-cifar10-finetuned)로 이미지를 분류한다.
실행:  streamlit run app.py
"""
import os

import pandas as pd
import streamlit as st
import torch
from PIL import Image
from transformers import pipeline

MODEL_DIR = "./vit-cifar10-finetuned"

# CIFAR-10 영문 라벨 → 한글 (사용자 친화적 표시용)
KO = {
    "airplane": "비행기", "automobile": "자동차", "bird": "새",
    "cat": "고양이", "deer": "사슴", "dog": "개", "frog": "개구리",
    "horse": "말", "ship": "배", "truck": "트럭",
}

st.set_page_config(page_title="이미지 분류기", page_icon="🖼️")


@st.cache_resource  # ★ 모델은 단 한 번만 로드하고 메모리에 보관
def load_classifier():
    device = 0 if torch.cuda.is_available() else -1  # GPU(8GB)면 0번, 없으면 CPU
    return pipeline(
        task="image-classification",
        model=MODEL_DIR,
        device=device,
    )


def classify_and_render(pil_image):
    """이미지 1장을 분류하고 결과(예측 + Top-5 그래프/표)를 화면에 표시."""
    st.image(pil_image, caption="입력 이미지", use_container_width=True)

    with st.spinner("분류하는 중..."):
        results = classifier(pil_image, top_k=5)

    top = results[0]
    st.success(f"예측: **{KO.get(top['label'], top['label'])}**  (확신도 {top['score'] * 100:.1f}%)")
    if top["score"] < 0.5:
        st.warning("1위 확신도가 낮습니다 — 모델이 헷갈려 합니다. Top-5를 함께 보세요.")

    df = pd.DataFrame(results)
    df["클래스"] = df["label"].map(lambda x: KO.get(x, x))
    df["확률(%)"] = (df["score"] * 100).round(2)

    st.subheader("Top-5 분류 결과")
    st.bar_chart(df.set_index("클래스")["확률(%)"])
    st.dataframe(df[["클래스", "확률(%)"]], use_container_width=True, hide_index=True)


# ── 화면 ──────────────────────────────────────────────────────────────
st.title("🖼️ 나만의 이미지 분류기")
st.write("1교시에 파인튜닝한 ViT로 CIFAR-10 10개 클래스를 분류합니다.")
st.caption("클래스: 비행기·자동차·새·고양이·사슴·개·개구리·말·배·트럭")

# 모델 폴더가 없으면 친절하게 안내하고 중단
if not os.path.isdir(MODEL_DIR):
    st.error(
        f"모델 폴더 `{MODEL_DIR}` 를 찾을 수 없습니다.\n\n"
        "먼저 1교시 노트북 `04_finetune_vit.ipynb` 의 셀 [12]까지 실행해 "
        "모델을 저장한 뒤 다시 실행하세요."
    )
    st.stop()

classifier = load_classifier()

tab_upload, tab_camera = st.tabs(["📁 파일 업로드", "📷 카메라 촬영"])

with tab_upload:
    up = st.file_uploader("이미지를 올려주세요", type=["jpg", "jpeg", "png"])
    if up is not None:
        classify_and_render(Image.open(up).convert("RGB"))

with tab_camera:
    cam = st.camera_input("카메라로 촬영")
    if cam is not None:
        classify_and_render(Image.open(cam).convert("RGB"))
