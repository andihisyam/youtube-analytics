from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "public" / "data"

SUPERVISED_FILE = OUTPUT_DIR / "clean_comments_with_predictions.csv"
LEXICON_FILE = OUTPUT_DIR / "clean_comments_with_lexicon_predictions.csv"
MODEL_METRICS_FILE = OUTPUT_DIR / "sentiment_model_metrics.json"
LEXICON_METRICS_FILE = OUTPUT_DIR / "lexicon_sentiment_metrics.json"
DASHBOARD_FILE = DASHBOARD_DATA_DIR / "dashboard-data.json"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "for", "from", "had", "has", "have",
    "he", "her", "him", "his", "i", "if", "in", "is", "it", "its", "just", "like", "me", "my", "not", "of",
    "on", "or", "our", "she", "so", "that", "the", "their", "them", "there", "they", "this", "to", "too", "was",
    "we", "were", "what", "when", "who", "with", "you", "your", "yt", "nba", "com", "https", "www"
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def safe_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def distribution(series: pd.Series) -> list[dict[str, Any]]:
    counts = series.fillna("unclassified").astype(str).value_counts()
    return [{"label": str(label), "count": int(count)} for label, count in counts.items()]


def top_comments(df: pd.DataFrame, sentiment: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
    data = df.copy()
    if sentiment:
        data = data[data["predicted_sentiment"] == sentiment]
    data = data.sort_values(["like_count", "total_reply_count"], ascending=[False, False]).head(limit)
    rows = []
    for _, row in data.iterrows():
        rows.append({
            "author": str(row.get("author_display_name", "")),
            "text": str(row.get("text_original", ""))[:280],
            "sentiment": str(row.get("predicted_sentiment", "unclassified")),
            "likes": safe_int(row.get("like_count")),
            "replies": safe_int(row.get("total_reply_count")),
        })
    return rows


def length_by_sentiment(df: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = df.groupby("predicted_sentiment", dropna=False).agg(
        comments=("comment_thread_id", "count"),
        avg_length=("text_length", "mean"),
        avg_likes=("like_count", "mean"),
        avg_replies=("total_reply_count", "mean"),
    ).reset_index()
    result = []
    for _, row in grouped.iterrows():
        result.append({
            "label": str(row["predicted_sentiment"]),
            "comments": int(row["comments"]),
            "avgLength": round(float(row["avg_length"]), 2),
            "avgLikes": round(float(row["avg_likes"]), 2),
            "avgReplies": round(float(row["avg_replies"]), 2),
        })
    return result


def comments_over_time(df: pd.DataFrame) -> list[dict[str, Any]]:
    data = df.copy()
    data["published_at_parsed"] = pd.to_datetime(data["published_at"], errors="coerce")
    data = data.dropna(subset=["published_at_parsed"])
    if data.empty:
        return []
    data["date"] = data["published_at_parsed"].dt.strftime("%Y-%m-%d")
    pivot = data.pivot_table(
        index="date",
        columns="predicted_sentiment",
        values="comment_thread_id",
        aggfunc="count",
        fill_value=0,
    ).reset_index()
    rows = []
    for _, row in pivot.iterrows():
        rows.append({
            "date": row["date"],
            "positive": int(row.get("positive", 0)),
            "negative": int(row.get("negative", 0)),
            "neutral": int(row.get("neutral", 0)),
        })
    return rows


def keywords_by_sentiment(df: pd.DataFrame, limit: int = 18) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for sentiment in ["positive", "negative", "neutral"]:
        text = " ".join(df.loc[df["predicted_sentiment"] == sentiment, "cleaned_text"].fillna("").astype(str))
        tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
        tokens = [token for token in tokens if token not in STOPWORDS]
        output[sentiment] = [{"term": term, "count": count} for term, count in Counter(tokens).most_common(limit)]
    return output


def model_comparison(model_metrics: dict[str, Any], lexicon_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for model_name, metrics in model_metrics.get("metrics", {}).items():
        rows.append({
            "model": model_name.replace("_", " ").title(),
            "accuracy": float(metrics.get("accuracy", 0)),
            "macroF1": float(metrics.get("macro_f1", 0)),
            "weightedF1": float(metrics.get("weighted_f1", 0)),
            "type": "Supervised",
        })
    lex_eval = lexicon_metrics.get("evaluation", {})
    if lex_eval:
        rows.append({
            "model": "Lexicon Baseline",
            "accuracy": float(lex_eval.get("accuracy", 0)),
            "macroF1": float(lex_eval.get("macro_f1", 0)),
            "weightedF1": float(lex_eval.get("weighted_f1", 0)),
            "type": "Rule-based",
        })
    return sorted(rows, key=lambda item: item["macroF1"], reverse=True)


def main() -> None:
    if not SUPERVISED_FILE.exists():
        raise FileNotFoundError(f"Supervised prediction file not found: {SUPERVISED_FILE}")

    supervised = pd.read_csv(SUPERVISED_FILE)
    supervised["predicted_sentiment"] = supervised["predicted_sentiment"].fillna("unclassified").astype(str)
    supervised["cleaned_text"] = supervised["cleaned_text"].fillna("").astype(str)
    supervised["text_length"] = supervised["text_length"].apply(safe_int)
    supervised["like_count"] = supervised["like_count"].apply(safe_int)
    supervised["total_reply_count"] = supervised["total_reply_count"].apply(safe_int)

    lexicon = pd.read_csv(LEXICON_FILE) if LEXICON_FILE.exists() else pd.DataFrame()
    model_metrics = read_json(MODEL_METRICS_FILE)
    lexicon_metrics = read_json(LEXICON_METRICS_FILE)

    video_ids = sorted(supervised["video_id"].dropna().astype(str).unique().tolist())
    total_comments = int(len(supervised))
    low_information = int(supervised.get("is_low_information", pd.Series(dtype=bool)).astype(str).str.lower().eq("true").sum())

    payload = {
        "generatedAt": pd.Timestamp.utcnow().isoformat(),
        "overview": {
            "videoIds": video_ids,
            "totalComments": total_comments,
            "lowInformationComments": low_information,
            "usableComments": total_comments - low_information,
            "totalLikesOnComments": int(supervised["like_count"].sum()),
            "totalRepliesOnThreads": int(supervised["total_reply_count"].sum()),
            "avgCommentLength": round(float(supervised["text_length"].mean()), 2),
            "bestModel": model_metrics.get("best_model", "linear_svm").replace("_", " ").title(),
            "trainingRowsUsed": int(model_metrics.get("training_rows_used", 0)),
        },
        "sentimentDistribution": distribution(supervised["predicted_sentiment"]),
        "lexiconDistribution": distribution(lexicon["lexicon_predicted_label"]) if not lexicon.empty else [],
        "lengthBySentiment": length_by_sentiment(supervised),
        "commentsOverTime": comments_over_time(supervised),
        "keywordsBySentiment": keywords_by_sentiment(supervised),
        "topComments": {
            "overall": top_comments(supervised),
            "positive": top_comments(supervised, "positive"),
            "negative": top_comments(supervised, "negative"),
            "neutral": top_comments(supervised, "neutral"),
        },
        "modelComparison": model_comparison(model_metrics, lexicon_metrics),
        "modelMetrics": model_metrics,
        "lexiconMetrics": lexicon_metrics,
    }

    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Dashboard data exported to {DASHBOARD_FILE}")
    print(f"Comments exported: {total_comments}")
    print(f"Models compared: {len(payload['modelComparison'])}")


if __name__ == "__main__":
    main()
