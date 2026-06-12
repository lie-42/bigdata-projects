import streamlit as st
import sys
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.data_loader import get_dataloaders
from src.transforms import get_train_transforms, get_val_transforms
from src.model import build_model, save_model, get_device, MODEL_PATH

st.title("🏋️ 모델 학습")

import torch as _torch
_device_info = f"PyTorch {_torch.__version__} | {'✅ CUDA ' + _torch.cuda.get_device_name(0) if _torch.cuda.is_available() else '⚠️ CPU (GPU 미감지)'}"
st.caption(_device_info)

# ── 사이드바 하이퍼파라미터 ──────────────────────────────────
st.sidebar.header("학습 설정")
epochs     = st.sidebar.slider("Epochs",      5, 50, 10)
batch_size = st.sidebar.selectbox("Batch Size", [8, 16, 32, 64, 128], index=2)
lr         = st.sidebar.select_slider("Learning Rate", [0.0001, 0.0005, 0.001, 0.005], value=0.001)
img_size   = st.sidebar.selectbox("Image Size", [128, 224], index=1)
freeze     = st.sidebar.checkbox("Backbone 고정 (전이학습 권장)", value=True)

# ── 학습 버튼 ────────────────────────────────────────────────
if st.button("🚀 학습 시작", type="primary"):
    device = get_device()
    st.info(f"사용 장치: **{device.upper()}**")

    # 데이터 로드
    try:
        train_loader, val_loader, class_names = get_dataloaders(
            get_train_transforms(img_size),
            get_val_transforms(img_size),
            batch_size=batch_size,
        )
    except FileNotFoundError as e:
        st.error(str(e)); st.stop()

    st.write(f"클래스: {class_names} | 학습 배치 수: {len(train_loader)} | 검증 배치 수: {len(val_loader)}")

    # 모델
    model = build_model(num_classes=len(class_names), pretrained=True).to(device)
    if freeze:
        for name, param in model.named_parameters():
            if "classifier" not in name:
                param.requires_grad = False

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    # 학습 루프
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    progress_bar = st.progress(0, text="학습 중...")
    chart_placeholder = st.empty()

    for epoch in range(epochs):
        # train
        model.train()
        t_loss, t_correct, t_total = 0.0, 0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            t_loss += loss.item() * imgs.size(0)
            t_correct += (outputs.argmax(1) == labels).sum().item()
            t_total += imgs.size(0)

        # validation
        model.eval()
        v_loss, v_correct, v_total = 0.0, 0, 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                v_loss += loss.item() * imgs.size(0)
                v_correct += (outputs.argmax(1) == labels).sum().item()
                v_total += imgs.size(0)

        scheduler.step()

        history["train_loss"].append(t_loss / t_total)
        history["train_acc"].append(t_correct / t_total)
        history["val_loss"].append(v_loss / v_total)
        history["val_acc"].append(v_correct / v_total)

        progress_bar.progress((epoch + 1) / epochs, text=f"Epoch {epoch+1}/{epochs} | val_acc: {v_correct/v_total:.3f}")

        # 실시간 차트
        import pandas as pd
        df_hist = pd.DataFrame(history)
        df_hist.index += 1
        with chart_placeholder.container():
            c1, c2 = st.columns(2)
            c1.line_chart(df_hist[["train_loss", "val_loss"]], use_container_width=True)
            c2.line_chart(df_hist[["train_acc",  "val_acc"]],  use_container_width=True)

    save_model(model, MODEL_PATH)
    st.session_state["class_names"] = class_names
    st.success(f"✅ 학습 완료! 최종 val_acc: **{history['val_acc'][-1]:.4f}** — models/model.pth 저장됨")

    # Confusion Matrix
    st.subheader("Confusion Matrix")
    from sklearn.metrics import confusion_matrix, classification_report
    import seaborn as sns, matplotlib.pyplot as plt

    all_preds, all_labels = [], []
    model.eval()
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs = imgs.to(device)
            preds = model(imgs).argmax(1).cpu().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.tolist())

    cm = confusion_matrix(all_labels, all_preds)
    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=class_names, yticklabels=class_names, ax=ax, cmap="Blues")
    ax.set_xlabel("예측"); ax.set_ylabel("실제")
    st.pyplot(fig)
    st.text(classification_report(all_labels, all_preds, target_names=class_names))

elif MODEL_PATH.exists():
    st.info(f"저장된 모델이 있습니다: `{MODEL_PATH}`  \n학습을 다시 하려면 위 버튼을 누르세요.")
else:
    st.info("사이드바에서 설정을 조정한 뒤 **학습 시작** 버튼을 누르세요.")
