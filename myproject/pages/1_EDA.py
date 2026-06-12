import streamlit as st
import sys
from pathlib import Path
import random
from PIL import Image
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from collections import Counter

matplotlib.rc("font", family="Malgun Gothic")
matplotlib.rcParams["axes.unicode_minus"] = False

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATA_DIR  = Path(__file__).resolve().parents[1] / "data" / "Drowsy_datset"
TRAIN_DIR = DATA_DIR / "train"
TEST_DIR  = DATA_DIR / "test"
IMG_EXTS  = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

st.title("🔍 데이터 탐색 (EDA)")

if not TRAIN_DIR.exists():
    st.error(f"**{TRAIN_DIR}** 폴더가 없습니다.")
    st.stop()


def collect(base_dir: Path) -> dict:
    result = {}
    for cls_dir in sorted(base_dir.iterdir()):
        if cls_dir.is_dir():
            imgs = [p for p in cls_dir.iterdir() if p.suffix.lower() in IMG_EXTS]
            result[cls_dir.name] = imgs
    return result


train_imgs = collect(TRAIN_DIR)
test_imgs  = collect(TEST_DIR) if TEST_DIR.exists() else {}
all_classes = sorted(train_imgs.keys())

train_total = sum(len(v) for v in train_imgs.values())
test_total  = sum(len(v) for v in test_imgs.values())

# ── 데이터셋 소개 ─────────────────────────────────────────────
st.subheader("데이터셋 소개")
st.markdown(
    "운전 중 졸음을 감지하기 위한 얼굴 이미지 데이터셋입니다. "
    "두 클래스로 구성되며, CNN 기반 이진 분류 모델을 학습하는 데 사용됩니다."
)
col_intro1, col_intro2 = st.columns(2)
col_intro1.info(
    "**😴 DROWSY (졸린 상태)**\n\n"
    "눈이 감기거나 반쯤 감긴 상태, 하품, 고개 숙임 등 졸음 징후가 있는 얼굴"
)
col_intro2.success(
    "**😀 NATURAL (정상 상태)**\n\n"
    "눈을 뜨고 정상적으로 깨어있는 얼굴, 시선이 전방을 향한 상태"
)

# ── 데이터셋 요약 ─────────────────────────────────────────────
st.subheader("데이터셋 요약")
c0, c1, c2, c3 = st.columns(4)
c0.metric("전체 이미지", f"{train_total + test_total:,}")
c1.metric("학습(Train)", f"{train_total:,}")
c2.metric("테스트(Test)", f"{test_total:,}")
c3.metric("클래스 수", len(all_classes))

# ── 클래스 요약 테이블 ────────────────────────────────────────
st.subheader("클래스 요약 테이블")
rows = []
for cls in all_classes:
    train_n = len(train_imgs.get(cls, []))
    test_n  = len(test_imgs.get(cls, []))
    rows.append({
        "클래스":     cls,
        "Train 수":   train_n,
        "Train 비율": f"{train_n / train_total * 100:.1f}%" if train_total else "-",
        "Test 수":    test_n,
        "Test 비율":  f"{test_n / test_total * 100:.1f}%" if test_total else "-",
        "합계":       train_n + test_n,
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# 클래스 불균형 경고
train_counts = [len(v) for v in train_imgs.values()]
if max(train_counts) / max(min(train_counts), 1) > 1.5:
    st.warning("클래스 불균형 감지: 학습 시 class_weight 적용을 고려하세요.")
else:
    st.success("클래스 균형: 두 클래스의 이미지 수가 비슷합니다.")

# ── 클래스 분포 차트 ──────────────────────────────────────────
st.subheader("클래스 분포")
import plotly.express as px
dist_data = {
    "클래스":    list(train_imgs.keys()) + list(test_imgs.keys()),
    "이미지 수": [len(v) for v in train_imgs.values()] + [len(v) for v in test_imgs.values()],
    "분류":      ["train"] * len(train_imgs) + ["test"] * len(test_imgs),
}
fig = px.bar(pd.DataFrame(dist_data), x="클래스", y="이미지 수", color="분류",
             barmode="group", color_discrete_map={"train": "#4C9BE8", "test": "#F4845F"})
st.plotly_chart(fig, use_container_width=True)

# ── 이미지 해상도 정보 ────────────────────────────────────────
st.subheader("이미지 해상도 정보")
st.caption("모델 입력 크기를 결정할 때 원본 해상도를 확인하는 것이 중요합니다.")

@st.cache_data
def sample_sizes(n_per_class=60):
    rows = []
    for split_name, cls_dict in [("train", train_imgs), ("test", test_imgs)]:
        for cls, imgs in cls_dict.items():
            for fp in random.sample(imgs, min(n_per_class, len(imgs))):
                w, h = Image.open(fp).size
                rows.append({"split": split_name, "클래스": cls, "너비": w, "높이": h})
    return pd.DataFrame(rows)

size_df = sample_sizes()

col_s1, col_s2 = st.columns(2)
with col_s1:
    st.markdown("**클래스별 평균 해상도**")
    summary = (
        size_df.groupby("클래스")[["너비", "높이"]]
        .agg(["mean", "min", "max"])
        .round(0)
        .astype(int)
    )
    summary.columns = ["너비 평균", "너비 최소", "너비 최대", "높이 평균", "높이 최소", "높이 최대"]
    st.dataframe(summary, use_container_width=True)

with col_s2:
    st.markdown("**가장 많은 해상도 (Top 5)**")
    top_sizes = (
        size_df.assign(해상도=size_df["너비"].astype(str) + "×" + size_df["높이"].astype(str))
        ["해상도"].value_counts().head(5).reset_index()
    )
    top_sizes.columns = ["해상도", "개수"]
    st.dataframe(top_sizes, hide_index=True, use_container_width=True)

# ── 이미지 채널 확인 ──────────────────────────────────────────
st.subheader("이미지 채널 확인")
st.caption("RGB(컬러) / L(흑백) / RGBA(투명도 포함) 여부를 확인합니다. 모델 전처리 방식 결정에 영향을 줍니다.")

@st.cache_data
def check_channels(n_per_class=80):
    result = {}
    for cls, imgs in train_imgs.items():
        modes = [Image.open(fp).mode for fp in random.sample(imgs, min(n_per_class, len(imgs)))]
        result[cls] = dict(Counter(modes))
    return result

channel_info = check_channels()

ch_rows = []
for cls, mode_counts in channel_info.items():
    dominant = max(mode_counts, key=mode_counts.get)
    label = {"L": "흑백(Grayscale)", "RGB": "컬러(RGB)", "RGBA": "컬러+투명(RGBA)"}.get(dominant, dominant)
    ch_rows.append({"클래스": cls, "주요 모드": dominant, "설명": label, **mode_counts})
ch_df = pd.DataFrame(ch_rows).fillna(0)
st.dataframe(ch_df, hide_index=True, use_container_width=True)

# ── 파일 무결성 체크 ──────────────────────────────────────────
st.subheader("파일 무결성 체크")
st.caption("이미지를 열 수 없거나 손상된 파일이 있는지 확인합니다.")

if st.button("🔍 무결성 검사 실행 (전체 파일)"):
    all_files = [
        (cls, fp)
        for cls, imgs in {**train_imgs, **{f"test_{k}": v for k, v in test_imgs.items()}}.items()
        for fp in imgs
    ]
    broken = []
    prog = st.progress(0, "검사 중...")
    for i, (cls, fp) in enumerate(all_files):
        try:
            with Image.open(fp) as img:
                img.verify()
        except Exception as e:
            broken.append({"클래스": cls, "파일": fp.name, "오류": str(e)})
        prog.progress((i + 1) / len(all_files))
    prog.empty()

    if broken:
        st.error(f"손상된 파일 {len(broken)}개 발견")
        st.dataframe(pd.DataFrame(broken), use_container_width=True)
    else:
        st.success(f"전체 {len(all_files):,}개 파일 이상 없음 ✅")

# ── 샘플 이미지 ───────────────────────────────────────────────
st.subheader("샘플 이미지")
CLASS_LABEL = {"DROWSY": "😴 DROWSY (졸린 얼굴)", "NATURAL": "😀 NATURAL (보통 얼굴)"}
n_sample = st.slider("클래스당 표시 개수", 2, 10, 6)

for cls, imgs in train_imgs.items():
    st.markdown(f"**{CLASS_LABEL.get(cls, cls)}**")
    samples = random.sample(imgs, min(n_sample, len(imgs)))
    img_cols = st.columns(len(samples))
    for col, img_path in zip(img_cols, samples):
        col.image(Image.open(img_path).convert("RGB"),
                  use_container_width=True, caption=img_path.name)
