import streamlit as st
import sys
from pathlib import Path
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import random
from scipy import ndimage

matplotlib.rc("font", family="Malgun Gothic")
matplotlib.rcParams["axes.unicode_minus"] = False

sys.path.append(str(Path(__file__).resolve().parents[1]))

st.title("📊 데이터 시각화")

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "Drowsy_datset"
RESIZE = (128, 128)

if not DATA_ROOT.exists():
    st.error(f"데이터 경로를 찾을 수 없습니다: `{DATA_ROOT}`")
    st.stop()


def load_gray(fp, size=None):
    return np.array(Image.open(fp).convert("L").resize(size or RESIZE), dtype=np.float32)


@st.cache_data
def collect_files():
    result = {}
    for split in ["train", "test"]:
        split_path = DATA_ROOT / split
        if not split_path.exists():
            continue
        result[split] = {}
        for cls_dir in sorted(split_path.iterdir()):
            if cls_dir.is_dir():
                files = list(cls_dir.glob("*.png")) + list(cls_dir.glob("*.jpg"))
                result[split][cls_dir.name] = files
    return result


@st.cache_data
def compute_brightness(sample_n):
    result = {}
    for split, cls_dict in splits.items():
        for cls_name, file_list in cls_dict.items():
            key = f"{split}/{cls_name}"
            sampled = random.sample(file_list, min(sample_n, len(file_list)))
            result[key] = [load_gray(fp).mean() for fp in sampled]
    return result


@st.cache_data
def compute_mean_images(sample_n):
    means = {}
    for split, cls_dict in splits.items():
        for cls_name, file_list in cls_dict.items():
            key = f"{split}/{cls_name}"
            sampled = random.sample(file_list, min(sample_n, len(file_list)))
            arrays = np.stack([load_gray(fp) for fp in sampled])
            means[key] = arrays.mean(axis=0)
    return means


@st.cache_data
def compute_row_profile(sample_n):
    result = {}
    for split, cls_dict in splits.items():
        for cls_name, file_list in cls_dict.items():
            key = f"{split}/{cls_name}"
            sampled = random.sample(file_list, min(sample_n, len(file_list)))
            arrays = np.stack([load_gray(fp) for fp in sampled])
            result[key] = arrays.mean(axis=(0, 2))
    return result


def _canny(gray, low=50, high=150):
    blurred = ndimage.gaussian_filter(gray.astype(float), sigma=1.5)
    gx = ndimage.sobel(blurred, axis=1)
    gy = ndimage.sobel(blurred, axis=0)
    mag = np.hypot(gx, gy)
    if mag.max() > 0:
        mag = mag / mag.max() * 255
    edges = np.zeros_like(mag, dtype=np.uint8)
    edges[mag > high] = 255
    edges[(mag >= low) & (mag <= high)] = 128
    return edges


@st.cache_data
def compute_embeddings(sample_n):
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE

    X, y_labels = [], []
    for split, cls_dict in splits.items():
        for cls_name, file_list in cls_dict.items():
            key = f"{split}/{cls_name}"
            sampled = random.sample(file_list, min(sample_n, len(file_list)))
            for fp in sampled:
                X.append(load_gray(fp, size=(32, 32)).flatten() / 255.0)
                y_labels.append(key)

    X = np.array(X)
    pca_full = PCA(n_components=min(50, X.shape[0] - 1, X.shape[1]))
    X_pca50 = pca_full.fit_transform(X)

    pca2 = PCA(n_components=2)
    X_pca2 = pca2.fit_transform(X)

    perp = min(30, max(5, len(X) // 4))
    try:
        tsne = TSNE(n_components=2, random_state=42, perplexity=perp, max_iter=500)
    except TypeError:
        tsne = TSNE(n_components=2, random_state=42, perplexity=perp, n_iter=500)
    X_tsne = tsne.fit_transform(X_pca50)

    return X_pca2, X_tsne, y_labels, pca2.explained_variance_ratio_


splits = collect_files()
all_classes = sorted({cls for s in splits.values() for cls in s})
SAMPLE_N = st.sidebar.slider("분석 샘플 수 (클래스당)", 30, 200, 80)

# ── 1. 데이터 분포 ───────────────────────────────────────────
st.subheader("1. 데이터 분포")

counts = {split: {cls: len(files) for cls, files in cls_dict.items()}
          for split, cls_dict in splits.items()}
total_per_split = {split: sum(c.values()) for split, c in counts.items()}
total_all = sum(total_per_split.values())

metric_cols = st.columns(len(total_per_split) + 1)
metric_cols[0].metric("전체 이미지", total_all)
for col, (split, cnt) in zip(metric_cols[1:], total_per_split.items()):
    col.metric(split, cnt, f"{cnt/total_all*100:.1f}%")

col1, col2 = st.columns(2)
with col1:
    fig, ax = plt.subplots(figsize=(5, 3.5))
    x = np.arange(len(all_classes))
    width = 0.35
    for i, (split, color) in enumerate(zip(splits.keys(), ["steelblue", "salmon"])):
        vals = [counts[split].get(cls, 0) for cls in all_classes]
        bars = ax.bar(x + i * width, vals, width, label=split, color=color)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                    str(v), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(all_classes)
    ax.set_ylabel("이미지 수")
    ax.set_title("클래스별 이미지 수")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

with col2:
    fig, axes = plt.subplots(1, len(splits), figsize=(6, 3.5))
    if len(splits) == 1:
        axes = [axes]
    for ax, (split, cls_dict) in zip(axes, splits.items()):
        labels_pie = list(cls_dict.keys())
        sizes = [len(v) for v in cls_dict.values()]
        wedges, _, autotexts = ax.pie(
            sizes, labels=None, autopct="%1.1f%%", startangle=90,
            colors=["#ff9999", "#66b3ff"], pctdistance=0.75,
        )
        ax.legend(wedges, labels_pie, loc="lower center",
                  bbox_to_anchor=(0.5, -0.2), fontsize=8)
        ax.set_title(split)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ── 2. 픽셀 밝기 분포 ───────────────────────────────────────
st.subheader("3. 픽셀 밝기 분포")
st.caption("각 이미지의 평균 밝기를 클래스별로 비교합니다. 두 분포가 겹치면 밝기만으로는 구분이 어렵다는 의미입니다.")

brightness = compute_brightness(SAMPLE_N)
fig, ax = plt.subplots(figsize=(7, 3.5))
for label, vals in brightness.items():
    sns.kdeplot(vals, ax=ax, label=label, fill=True, alpha=0.3)
ax.set_xlabel("평균 밝기 (0~255)")
ax.set_ylabel("밀도")
ax.set_title("클래스별 픽셀 밝기 분포")
ax.legend()
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ── 3. 평균 이미지 & 차이 이미지 ────────────────────────────
st.subheader("3. 평균 이미지 & 차이 이미지 (DROWSY − NATURAL)")
st.caption(
    "평균 이미지: 클래스 이미지들을 픽셀 단위로 평균 → 공통 얼굴 패턴 확인.\n"
    "차이 이미지: 빨간 영역 = 졸음 상태에서 더 밝음, 파란 영역 = 정상 상태에서 더 밝음."
)
st.caption(" ")
st.caption(
    "평상시 얼굴은 겹쳤을때 비슷한모양을 하고있습니다. 반면 졸린 얼굴은 겹쳤을때 공통된부분이 없어서 형체를 알아보기 어렵습니다." 
)
st.caption(
    "졸릴때 제대로된 자세가 아니거나 얼굴에 손을 데는 현상이 많다는걸 의미 합니다." 
)


mean_images = compute_mean_images(SAMPLE_N)
train_keys = [k for k in mean_images if k.startswith("train")]
drowsy_key  = next((k for k in train_keys if "DROWSY"  in k), None)
natural_key = next((k for k in train_keys if "NATURAL" in k), None)

n_cols = len(mean_images) + (1 if drowsy_key and natural_key else 0)
fig, axes = plt.subplots(1, n_cols, figsize=(4 * n_cols, 4))
if n_cols == 1:
    axes = [axes]

for ax, (key, img) in zip(axes, mean_images.items()):
    ax.imshow(img, cmap="gray", vmin=0, vmax=255)
    ax.set_title(f"평균: {key}")
    ax.axis("off")

if drowsy_key and natural_key:
    diff = mean_images[drowsy_key].astype(float) - mean_images[natural_key].astype(float)
    ax = axes[len(mean_images)]
    im = ax.imshow(diff, cmap="RdBu_r", vmin=-60, vmax=60)
    ax.set_title("차이 (DROWSY − NATURAL)")
    ax.axis("off")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)



# ── 4. 행별 밝기 프로파일 ───────────────────────────────────
st.subheader("4. 행별 밝기 프로파일 (눈·입 위치 분석)")
st.caption(
    "이미지 세로 위치별 평균 밝기를 클래스별로 비교합니다.\n"
    "눈 영역(상단 30~50%)에서 두 클래스 간 차이가 크면 눈 개폐가 핵심 특징임을 확인할 수 있습니다."
)

row_profiles = compute_row_profile(SAMPLE_N)
y_pct = np.linspace(0, 100, RESIZE[1])

fig, ax = plt.subplots(figsize=(7, 4))
for label, profile in row_profiles.items():
    ax.plot(y_pct, profile, label=label)
ax.axvspan(30, 50, alpha=0.12, color="yellow",  label="눈 예상 영역 (30~50%)")
ax.axvspan(70, 90, alpha=0.12, color="orange",  label="입 예상 영역 (70~90%)")
ax.set_xlabel("세로 위치 (%, 0=상단 · 100=하단)")
ax.set_ylabel("평균 밝기")
ax.set_title("행별 평균 밝기 프로파일")
ax.legend(fontsize=8)
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ── 5. 에지 맵 ──────────────────────────────────────────────
st.subheader("5. 에지 맵")
st.caption("눈이 열려있으면 홍채·눈꺼풀 경계선(에지)이 많고, 감기면 줄어듭니다. 클래스별 샘플로 직접 비교합니다.")

split_edge = "train" if "train" in splits else list(splits.keys())[0]
edge_cols = st.columns(len(splits[split_edge]))
for col, (cls_name, file_list) in zip(edge_cols, splits[split_edge].items()):
    fp = random.choice(file_list)
    gray = np.array(Image.open(fp).convert("L").resize(RESIZE), dtype=np.float32)
    edges = _canny(gray)
    fig, axs = plt.subplots(1, 2, figsize=(4, 2.2))
    axs[0].imshow(gray, cmap="gray"); axs[0].set_title("원본"); axs[0].axis("off")
    axs[1].imshow(edges, cmap="gray"); axs[1].set_title("에지"); axs[1].axis("off")
    fig.suptitle(cls_name, fontsize=10)
    plt.tight_layout()
    col.pyplot(fig)
    plt.close(fig)



