import numpy as np
import pandas as pd

def normalize_features(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Normalizes numerical features using z-score normalization."""
    df_norm = df.copy()
    for col in feature_cols:
        mean = df_norm[col].mean()
        std = df_norm[col].std()
        if std > 0:
            df_norm[col] = (df_norm[col] - mean) / std
    return df_norm
