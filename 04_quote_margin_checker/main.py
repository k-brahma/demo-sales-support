from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["原価", "定価", "値引率"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path) -> pd.DataFrame:
    df = load_data(filepath).copy()
    df["提示価格"] = (df["定価"] * (1 - df["値引率"] / 100)).round(0)
    df["粗利額"] = df["提示価格"] - df["原価"]
    df["粗利率"] = (df["粗利額"] / df["提示価格"] * 100).round(1).fillna(0)
    df["承認判定"] = df.apply(lambda r: "要承認" if r["粗利率"] < 25 or r["値引率"] > 20 else "注意" if r["粗利率"] < 30 else "OK", axis=1)
    return df.sort_values(["承認判定", "粗利率"], ascending=[True, True]).reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict:
    return {
        "要承認": int((df["承認判定"] == "要承認").sum()),
        "注意": int((df["承認判定"] == "注意").sum()),
        "平均粗利率": float(round(df["粗利率"].mean(), 1)),
    }


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "quote_margin_report.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "quotes.csv"
