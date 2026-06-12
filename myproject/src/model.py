import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "model.pth"


def build_model(num_classes: int = 2, pretrained: bool = True) -> nn.Module:
    """MobileNetV2 전이학습 모델. 마지막 FC층만 num_classes로 교체."""
    weights = models.MobileNet_V2_Weights.DEFAULT if pretrained else None
    model = models.mobilenet_v2(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def save_model(model: nn.Module, path: Path = MODEL_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


def load_model(num_classes: int = 2, path: Path = MODEL_PATH, device: str = "cpu") -> nn.Module:
    model = build_model(num_classes=num_classes, pretrained=False)
    model.load_state_dict(torch.load(path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"
