import pandas as pd
from sklearn.preprocessing import LabelEncoder


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """결측치 처리 및 기본 정제."""
    df = df.copy()
    # TODO: 필요한 정제 로직을 추가하세요
    # 예) df = df.dropna(subset=["target"])
    # 예) df["col"] = df["col"].fillna(df["col"].median())
    return df


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    """파생 변수 생성."""
    df = df.copy()
    # TODO: 파생 변수 생성 로직을 추가하세요
    return df


def encode(df: pd.DataFrame, cat_cols: list[str]) -> pd.DataFrame:
    """범주형 변수를 레이블 인코딩."""
    df = df.copy()
    le = LabelEncoder()
    for col in cat_cols:
        df[col] = le.fit_transform(df[col].astype(str))
    return df


def get_X_y(df: pd.DataFrame, target: str):
    """feature 행렬과 타깃 시리즈를 분리해서 반환."""
    X = df.drop(columns=[target])
    y = df[target]
    return X, y
