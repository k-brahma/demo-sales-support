from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

RANK_SCORE = {"A": 18, "B": 10, "C": 4}
PHASE_SCORE = {"提案中": 12, "見積提出": 16, "稟議中": 18, "契約調整": 20, "保守": 4}


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["前回訪問日"] = pd.to_datetime(df["前回訪問日"], errors="coerce")
    for col in ["案件金額", "契約更新まで日数", "失注兆候", "役員商談予定", "重要顧客"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    ref = pd.Timestamp(reference_date).normalize() if reference_date is not None else pd.Timestamp.today().normalize()
    df = load_data(filepath).copy()
    df["未訪問日数"] = (ref - df["前回訪問日"]).dt.days.clip(lower=0)
    df["未訪問スコア"] = (df["未訪問日数"] / 2).clip(upper=18).round(1)
    df["更新接近スコア"] = df["契約更新まで日数"].apply(lambda d: 20 if d <= 30 else 14 if d <= 60 else 8 if d <= 90 else 2)
    df["失注兆候スコア"] = (df["失注兆候"] * 4).clip(upper=20)
    df["案件金額スコア"] = (df["案件金額"] / 1000000).clip(upper=18).round(1)
    df["役員商談スコア"] = df["役員商談予定"].apply(lambda v: 12 if v == 1 else 0)
    df["重要顧客スコア"] = df["重要顧客"].apply(lambda v: 10 if v == 1 else 0)
    df["ランクスコア"] = df["顧客ランク"].map(RANK_SCORE).fillna(4)
    df["フェーズスコア"] = df["案件フェーズ"].map(PHASE_SCORE).fillna(6)
    score_cols = [
        "未訪問スコア",
        "更新接近スコア",
        "失注兆候スコア",
        "案件金額スコア",
        "役員商談スコア",
        "重要顧客スコア",
        "ランクスコア",
        "フェーズスコア",
    ]
    df["優先スコア"] = df[score_cols].sum(axis=1).round(1)
    df["訪問優先度"] = df["優先スコア"].apply(lambda s: "今週必須" if s >= 78 else "優先" if s >= 58 else "候補")
    df["主な理由"] = df.apply(_build_reason, axis=1)
    df["推奨アクション"] = df.apply(_build_action, axis=1)
    return df.sort_values(["訪問優先度", "優先スコア"], ascending=[True, False]).reset_index(drop=True)


def _build_reason(row: pd.Series) -> str:
    reasons = []
    if row["契約更新まで日数"] <= 30:
        reasons.append("更新月が近い")
    if row["失注兆候"] >= 4:
        reasons.append("失注兆候が強い")
    if row["役員商談予定"] == 1:
        reasons.append("役員商談前")
    if row["未訪問日数"] >= 20:
        reasons.append("長期未訪問")
    if row["案件金額"] >= 8000000:
        reasons.append("大型案件")
    if not reasons:
        reasons.append("関係維持")
    return " / ".join(reasons[:3])


def _build_action(row: pd.Series) -> str:
    if row["訪問優先度"] == "今週必須":
        return "今週前半に訪問打診"
    if row["役員商談予定"] == 1:
        return "事前資料を持って訪問"
    if row["訪問優先度"] == "優先":
        return "今週中にアポ取得"
    return "電話フォロー後に調整"


def get_summary(df: pd.DataFrame) -> dict:
    return {
        "今週必須": int((df["訪問優先度"] == "今週必須").sum()),
        "優先": int((df["訪問優先度"] == "優先").sum()),
        "候補": int((df["訪問優先度"] == "候補").sum()),
        "平均スコア": float(round(df["優先スコア"].mean(), 1)) if len(df) else 0.0,
    }


def get_top_reason_breakdown(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    cols = ["未訪問スコア", "更新接近スコア", "失注兆候スコア", "案件金額スコア", "役員商談スコア"]
    top = df.head(top_n)[["企業名", *cols]].copy()
    return top.iloc[::-1].reset_index(drop=True)


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "weekly_visit_plan.csv"
    export = df.copy()
    export["前回訪問日"] = export["前回訪問日"].dt.strftime("%Y-%m-%d")
    export.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "visits.csv"
