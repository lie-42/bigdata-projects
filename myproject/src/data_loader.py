from pathlib import Path
from torch.utils.data import DataLoader
from torchvision import datasets

# 실제 데이터 경로 (변경 필요 시 이 두 줄만 수정)
DATA_DIR  = Path(__file__).resolve().parents[1] / "data" / "Drowsy_datset"
TRAIN_DIR = DATA_DIR / "train"
VAL_DIR   = DATA_DIR / "test"


def get_dataloaders(train_transforms, val_transforms, batch_size: int = 32):
    """
    data/Drowsy_datset/train/{DROWSY,NATURAL} 과
    data/Drowsy_datset/test/{DROWSY,NATURAL} 로부터 DataLoader 반환.
    """
    if not TRAIN_DIR.exists():
        raise FileNotFoundError(
            f"학습 데이터 폴더를 찾을 수 없습니다: {TRAIN_DIR}\n"
            f"아래 구조인지 확인하세요:\n"
            f"  data/Drowsy_datset/train/DROWSY/\n"
            f"  data/Drowsy_datset/train/NATURAL/"
        )

    train_ds = datasets.ImageFolder(str(TRAIN_DIR), transform=train_transforms)
    val_ds   = datasets.ImageFolder(str(VAL_DIR),   transform=val_transforms)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, val_loader, train_ds.classes
