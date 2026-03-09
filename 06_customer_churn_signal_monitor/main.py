from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["最終受注日"] = pd.to_datetime(df["最終受注日"], errors="coerce")
    for col in ["利用頻度増減率", "問い合わせ件数", "契約金額"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    ref = pd.Timestamp(reference_date).normalize() if reference_date is not None else pd.Timestamp.today().normalize()
    df = load_data(filepath).copy()
    df["経過日数"] = (ref - df["最終受注日"]).dt.days.clip(lower=0)
    df["リスクスコア"] = (
        (df["経過日数"] / 7).clip(lower=0)
        + (-df["利用頻度増減率"]).clip(lower=0) * 0.8
        + (df["クレーム有無"] == 1).astype(int) * 18
        + (3 - df["問い合わせ件数"]).clip(lower=0) * 4
    ).round(1)
    df["判定"] = df["リスクスコア"].apply(lambda s: "高" if s >= 35 else "中" if s >= 20 else "低")
    return df.sort_values(["判定", "リスクスコア", "契約金額"], ascending=[True, False, False]).reset_index(drop=True)


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "churn_alerts.csv"
    export = df.copy()
    export["最終受注日"] = export["最終受注日"].dt.strftime("%Y-%m-%d")
    export.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "customers.csv"
