import streamlit as st
import sys
from pathlib import Path
import torch
from PIL import Image
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.model import load_model, get_device, MODEL_PATH
from src.transforms import get_inference_transforms

st.title("😴 졸음 감지 서비스")

DEVICE      = get_device()
CLASS_NAMES = st.session_state.get("class_names", ["DROWSY", "NATURAL"])
DROWSY_KEY  = "DROWSY"


@st.cache_resource
def get_model(mtime: float):
    return load_model(num_classes=len(CLASS_NAMES), path=MODEL_PATH, device=DEVICE)


if not MODEL_PATH.exists():
    model = None
else:
    model = get_model(MODEL_PATH.stat().st_mtime)

if model is None:
    st.warning("⚠️ 학습된 모델이 없습니다. **모델 학습** 페이지에서 먼저 학습하세요.")
    st.stop()

transform = get_inference_transforms(img_size=224)


def predict(pil_img: Image.Image):
    img    = pil_img.convert("RGB")
    tensor = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits = model(tensor)
        probs  = torch.softmax(logits, dim=1)[0].cpu().numpy()
    pred_idx = int(np.argmax(probs))
    return CLASS_NAMES[pred_idx], {cls: float(p) for cls, p in zip(CLASS_NAMES, probs)}


def show_result(pred_class: str, probs: dict):
    drowsy_prob = probs.get(DROWSY_KEY, 0.0)
    if pred_class == DROWSY_KEY:
        st.error(f"## 😴 졸림 감지!  확률: {drowsy_prob*100:.1f}%")
    else:
        st.success(f"## 😀 정상  졸음 확률: {drowsy_prob*100:.1f}%")

    import pandas as pd
    st.bar_chart(pd.DataFrame({"확률": probs}))


# ── 탭 ──────────────────────────────────────────────────────
tab_upload, tab_cam, tab_video = st.tabs(["📁 이미지 업로드", "📷 웹캠 촬영", "🎬 영상 파일"])

# ── 탭 1: 이미지 업로드 ──────────────────────────────────────
with tab_upload:
    uploaded = st.file_uploader("이미지를 업로드하세요", type=["jpg", "jpeg", "png", "bmp"])
    if uploaded:
        img = Image.open(uploaded)
        col1, col2 = st.columns([1, 1])
        col1.image(img, caption="업로드된 이미지", use_container_width=True)
        with col2:
            with st.spinner("분석 중..."):
                pred_class, probs = predict(img)
            show_result(pred_class, probs)

# ── 탭 2: 웹캠 스냅샷 ────────────────────────────────────────
with tab_cam:
    st.info("사진을 찍으면 바로 졸음 여부를 판정합니다.")
    cam_img = st.camera_input("웹캠으로 촬영")
    if cam_img:
        img = Image.open(cam_img)
        col1, col2 = st.columns([1, 1])
        col1.image(img, caption="촬영된 이미지", use_container_width=True)
        with col2:
            with st.spinner("분석 중..."):
                pred_class, probs = predict(img)
            show_result(pred_class, probs)

# ── 탭 3: 영상 파일 ──────────────────────────────────────────
with tab_video:
    video_file = st.file_uploader("영상 파일 업로드", type=["mp4", "avi", "mov"], key="vid")
    frame_step = st.slider("몇 프레임마다 분석?", 5, 60, 15)

    if video_file:
        import cv2, tempfile, os, pandas as pd

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
            tmp.write(video_file.read())
            tmp_path = tmp.name

        cap          = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 30
        st.write(f"총 {total_frames}프레임 ({total_frames/fps:.1f}초) | {frame_step}프레임마다 분석")

        progress = st.progress(0, "영상 분석 중...")
        results, frame_no = [], 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_no % frame_step == 0:
                rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil  = Image.fromarray(rgb)
                pred_class, probs = predict(pil)
                results.append({"프레임": frame_no, "예측": pred_class, "졸음확률": probs.get(DROWSY_KEY, 0.0)})
                progress.progress(min(frame_no / max(total_frames, 1), 1.0))
            frame_no += 1

        cap.release()
        os.unlink(tmp_path)
        progress.empty()

        if results:
            df_res        = pd.DataFrame(results)
            drowsy_ratio  = (df_res["예측"] == DROWSY_KEY).mean()

            if drowsy_ratio > 0.5:
                st.error(f"## 😴 졸음 구간 **{drowsy_ratio*100:.1f}%**")
            else:
                st.success(f"## 😀 대부분 정상. 졸음 비율: {drowsy_ratio*100:.1f}%")

            st.line_chart(df_res.set_index("프레임")["졸음확률"])
            st.dataframe(df_res, use_container_width=True)
