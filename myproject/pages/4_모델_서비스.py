import streamlit as st
import sys
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import models
from PIL import Image
import numpy as np
import cv2

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.model import load_model, get_device, MODEL_PATH
from src.transforms import get_inference_transforms

st.title("😴 졸음 감지 서비스")

DEVICE      = get_device()
CLASS_NAMES = st.session_state.get("class_names", ["DROWSY", "NATURAL"])
VIT_PATH    = Path(__file__).resolve().parents[1] / "models" / "vit_model.pth"

# ── MediaPipe (ImportError 외 TypeError 등 모든 예외 처리) ────
try:
    import mediapipe as mp
    _mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=0.45,
    )
    MEDIAPIPE_OK = True
except Exception:
    MEDIAPIPE_OK = False

_LEFT_EYE  = [362, 385, 387, 263, 373, 380]
_RIGHT_EYE = [33,  160, 158, 133, 153, 144]
EAR_CLOSED = 0.18
EAR_OPEN   = 0.28


# ── 모델 로드 ─────────────────────────────────────────────────

@st.cache_resource
def get_cnn_model(mtime: float):
    return load_model(num_classes=len(CLASS_NAMES), path=MODEL_PATH, device=DEVICE)

@st.cache_resource
def get_vit_model(mtime: float):
    vit = models.vit_b_16(weights=None)
    vit.heads.head = nn.Linear(vit.heads.head.in_features, len(CLASS_NAMES))
    vit.load_state_dict(torch.load(VIT_PATH, map_location=DEVICE))
    vit = vit.to(DEVICE).eval()
    return vit

cnn_model = get_cnn_model(MODEL_PATH.stat().st_mtime) if MODEL_PATH.exists() else None
vit_model = get_vit_model(VIT_PATH.stat().st_mtime)   if VIT_PATH.exists()   else None

if cnn_model is None and vit_model is None:
    st.warning("⚠️ 학습된 모델이 없습니다. **모델 학습** 페이지에서 먼저 학습하세요.")
    st.stop()

transform = get_inference_transforms(img_size=224)


# ── EAR 계산 (MediaPipe용) ────────────────────────────────────

def _calc_ear(landmarks, idxs, w, h):
    pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idxs], dtype=np.float32)
    A = np.linalg.norm(pts[1] - pts[5])
    B = np.linalg.norm(pts[2] - pts[4])
    C = np.linalg.norm(pts[0] - pts[3])
    return float((A + B) / (2.0 * C + 1e-6))

def ear_to_drowsy(ear: float) -> float:
    """EAR → 졸음 점수 (0~1, 높을수록 졸음)."""
    if ear <= EAR_CLOSED: return 1.0
    if ear >= EAR_OPEN:   return 0.0
    return (EAR_OPEN - ear) / (EAR_OPEN - EAR_CLOSED)


# ── 얼굴·눈 검출 캐스케이드 ───────────────────────────────────

@st.cache_resource
def _get_face_cascade():
    return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

@st.cache_resource
def _get_eye_cascade():
    return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


# ── 통합 얼굴 분석 ────────────────────────────────────────────

def analyze_face(pil_img: Image.Image):
    """
    Returns
    -------
    cropped        : PIL.Image       얼굴 크롭 (실패 시 원본)
    aux_score      : float | None    졸음 보조 점수 0~1 (높을수록 졸음)
    aux_label      : str             UI 표시용 설명
    method         : str             'mediapipe' | 'haar' | 'none'
    face_found     : bool
    """
    # ── MediaPipe 경로 ────────────────────────────────────────
    if MEDIAPIPE_OK:
        rgb = np.array(pil_img.convert("RGB"))
        h, w = rgb.shape[:2]
        result = _mp_face_mesh.process(rgb)
        if result.multi_face_landmarks:
            lms = result.multi_face_landmarks[0].landmark
            xs  = [lm.x for lm in lms]
            ys  = [lm.y for lm in lms]
            mg  = 0.15
            cropped = pil_img.crop((
                int(max(0.0, min(xs) - mg) * w), int(max(0.0, min(ys) - mg) * h),
                int(min(1.0, max(xs) + mg) * w), int(min(1.0, max(ys) + mg) * h),
            ))
            ear   = (_calc_ear(lms, _LEFT_EYE, w, h) + _calc_ear(lms, _RIGHT_EYE, w, h)) / 2
            score = ear_to_drowsy(ear)
            label = f"EAR = {ear:.3f}  (기준: ≤{EAR_CLOSED} 졸음 / ≥{EAR_OPEN} 정상)"
            return cropped, score, label, "mediapipe", True

    # ── Haarcascade 경로 (MediaPipe 없거나 검출 실패) ─────────
    gray  = np.array(pil_img.convert("L"))
    faces = _get_face_cascade().detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

    if len(faces) == 0:
        return pil_img, None, "얼굴 미검출", "none", False

    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    W, H = pil_img.size
    mg   = 0.20
    mx, my = int(fw * mg), int(fh * mg)
    x1, y1 = max(0, x - mx), max(0, y - my)
    x2, y2 = min(W, x + fw + mx), min(H, y + fh + my)
    face_crop = pil_img.crop((x1, y1, x2, y2))
    face_gray = gray[y1:y2, x1:x2]

    # 얼굴 상단 절반에서 눈 검출 (눈썹·코 아래 영역 제외)
    top_half = face_gray[:face_gray.shape[0] // 2, :]
    eyes = _get_eye_cascade().detectMultiScale(top_half, 1.05, 3, minSize=(15, 15))
    n = min(len(eyes), 2)

    # 눈 검출 수 → 졸음 점수 (열린 눈 많을수록 정상)
    score_map = {0: 0.85, 1: 0.50, 2: 0.15}
    score = score_map[n]
    label = f"눈 검출: {n}개  (0개=졸음 가능성 높음 / 2개=정상)"
    return face_crop, score, label, "haar", True


# ── 모델 추론 ─────────────────────────────────────────────────

def _probs(model, pil_img):
    tensor = transform(pil_img.convert("RGB")).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        return torch.softmax(model(tensor), dim=1)[0].cpu().numpy()

def predict_with(model, pil_img):
    p   = _probs(model, pil_img)
    idx = int(np.argmax(p))
    return CLASS_NAMES[idx], {c: float(v) for c, v in zip(CLASS_NAMES, p)}

def ensemble_predict(pil_img):
    preds = []
    if cnn_model: preds.append(_probs(cnn_model, pil_img))
    if vit_model: preds.append(_probs(vit_model, pil_img))
    avg = np.mean(preds, axis=0)
    return CLASS_NAMES[int(np.argmax(avg))], {c: float(v) for c, v in zip(CLASS_NAMES, avg)}


# ── 종합 판정 ─────────────────────────────────────────────────

def combined_score(model_prob: float, aux_score):
    """모델 확률 + 보조 점수 가중 결합."""
    if aux_score is None:
        return model_prob, "모델 확률만 사용 (얼굴/눈 미검출)"
    # 보조 점수가 명확할수록 aux에 더 많이 의존
    if aux_score >= 0.75 or aux_score <= 0.25:
        w_aux, w_model = 0.65, 0.35
    else:
        w_aux, w_model = 0.50, 0.50
    score = w_model * model_prob + w_aux * aux_score
    basis = (f"모델 {model_prob*100:.1f}% × {w_model:.0%}  +  "
             f"눈/EAR {aux_score*100:.1f}% × {w_aux:.0%}")
    return score, basis


# ── UI 헬퍼 ──────────────────────────────────────────────────

def _show_model_col(title, fn):
    pred, probs = fn()
    dp = probs.get("DROWSY", 0.0)
    st.markdown(f"**{title}**")
    if dp >= 0.5:
        st.error(f"😴 졸림 | {dp*100:.1f}%")
    else:
        st.success(f"😀 정상 | {dp*100:.1f}%")
    import pandas as pd
    st.bar_chart(pd.DataFrame({"확률": probs}), height=150)
    return dp

def _show_aux(aux_score, aux_label, method):
    if aux_score is None:
        return
    tag = "👁️ EAR (Eye Aspect Ratio)" if method == "mediapipe" else "👁️ 눈 검출 결과"
    st.markdown(f"**{tag}**")
    c1, c2 = st.columns(2)
    c1.metric("졸음 점수", f"{aux_score*100:.1f}%")
    c2.caption(aux_label)
    if aux_score >= 0.70:
        st.error("눈이 거의 감겨 있거나 졸음 징후 감지")
    elif aux_score >= 0.40:
        st.warning("눈 상태 불확실 — 주의")
    else:
        st.success("눈이 잘 떠 있음 — 정상")

def _show_final(score, basis):
    st.divider()
    st.markdown("### 종합 판정")
    if score >= 0.55:
        st.error(f"## 😴 졸음 감지  ({score*100:.1f}%)")
    elif score >= 0.40:
        st.warning(f"## ⚠️ 경계 상태  ({score*100:.1f}%)")
    else:
        st.success(f"## 😀 정상  ({score*100:.1f}%)")
    st.caption(basis)


# ── 메인 분석 흐름 ────────────────────────────────────────────

def show_all_results(pil_img: Image.Image):
    cropped, aux_score, aux_label, method, face_found = analyze_face(pil_img)

    if face_found:
        method_name = {"mediapipe": "MediaPipe", "haar": "Haarcascade"}.get(method, "")
        st.success(f"✅ 얼굴 검출 완료 ({method_name})")
        c1, c2 = st.columns(2)
        c1.image(pil_img, caption="원본",       use_container_width=True)
        c2.image(cropped, caption="검출된 얼굴", use_container_width=True)
    else:
        st.warning("⚠️ 얼굴을 찾지 못했습니다 — 전체 이미지로 예측합니다.")
        cropped = pil_img

    target = cropped
    st.divider()

    available = []
    if cnn_model: available.append(("🧠 CNN (MobileNetV2)", lambda t=target: predict_with(cnn_model, t)))
    if vit_model: available.append(("🤖 ViT-B/16",          lambda t=target: predict_with(vit_model, t)))
    if cnn_model and vit_model:
        available.append(("⚖️ 앙상블", lambda t=target: ensemble_predict(t)))

    cols = st.columns(len(available))
    model_prob = None
    for col, (title, fn) in zip(cols, available):
        with col:
            dp = _show_model_col(title, fn)
            if "앙상블" in title or len(available) == 1:
                model_prob = dp

    st.divider()
    _show_aux(aux_score, aux_label, method)

    if model_prob is not None:
        score, basis = combined_score(model_prob, aux_score)
        _show_final(score, basis)


# ── 탭 ───────────────────────────────────────────────────────

if not MEDIAPIPE_OK:
    st.info("ℹ️ MediaPipe 비활성 — Haarcascade 눈 검출 모드로 동작합니다.")

tab_upload, tab_cam, tab_video = st.tabs(["📁 이미지 업로드", "📷 웹캠 촬영", "🎬 영상 파일"])

with tab_upload:
    uploaded = st.file_uploader("이미지를 업로드하세요", type=["jpg", "jpeg", "png", "bmp"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="업로드된 이미지", width=300)
        st.divider()
        with st.spinner("분석 중..."):
            show_all_results(img)

with tab_cam:
    st.info("사진을 찍으면 바로 졸음 여부를 판정합니다.")
    cam_img = st.camera_input("웹캠으로 촬영")
    if cam_img:
        img = Image.open(cam_img)
        st.divider()
        with st.spinner("분석 중..."):
            show_all_results(img)

with tab_video:
    video_file   = st.file_uploader("영상 파일 업로드", type=["mp4", "avi", "mov"], key="vid")
    frame_step   = st.slider("몇 프레임마다 분석?", 5, 60, 15)
    model_choice = st.radio("영상 분석 모델", ["CNN", "ViT", "앙상블"], horizontal=True)

    if video_file:
        import tempfile, os, pandas as pd

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
            tmp.write(video_file.read())
            tmp_path = tmp.name

        cap          = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 30
        st.write(f"총 {total_frames}프레임 ({total_frames/fps:.1f}초) | {frame_step}프레임마다 분석")

        def _video_predict(pil_img):
            if model_choice == "CNN" and cnn_model:
                return predict_with(cnn_model, pil_img)
            if model_choice == "ViT" and vit_model:
                return predict_with(vit_model, pil_img)
            return ensemble_predict(pil_img)

        progress = st.progress(0, "영상 분석 중...")
        results, frame_no = [], 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_no % frame_step == 0:
                pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                cropped, aux_score, _, _, _ = analyze_face(pil)
                pred_class, probs = _video_predict(cropped)
                model_dp = probs.get("DROWSY", 0.0)
                final, _  = combined_score(model_dp, aux_score)
                results.append({
                    "프레임":   frame_no,
                    "모델예측": pred_class,
                    "모델졸음%": round(model_dp * 100, 1),
                    "눈점수%":  round(aux_score * 100, 1) if aux_score is not None else None,
                    "종합졸음%": round(final * 100, 1),
                })
                progress.progress(min(frame_no / max(total_frames, 1), 1.0))
            frame_no += 1

        cap.release()
        os.unlink(tmp_path)
        progress.empty()

        if results:
            df_res       = pd.DataFrame(results)
            drowsy_ratio = (df_res["종합졸음%"] >= 55).mean()

            if drowsy_ratio > 0.5:
                st.error(f"## 😴 졸음 구간 **{drowsy_ratio*100:.1f}%**")
            else:
                st.success(f"## 😀 대부분 정상. 졸음 비율: {drowsy_ratio*100:.1f}%")

            st.line_chart(df_res.set_index("프레임")["종합졸음%"])
            st.dataframe(df_res, use_container_width=True)
