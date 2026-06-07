from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"

LABELED_FILE = OUTPUT_DIR / "al0agaojcwY_comment_sample_200_for_labeling.csv"
FULL_FILE = OUTPUT_DIR / "clean_comments_sample.csv"

LABEL_MAP = {
    "positive": "positive",
    "positif": "positive",
    "negative": "negative",
    "negatif": "negative",
    "neutral": "neutral",
    "netral": "neutral",
}

NEGATIONS = {
    "not", "no", "never", "none", "hardly", "rarely", "cannot", "cant", "can't", "dont", "don't", "isnt", "isn't",
    "wasnt", "wasn't", "shouldnt", "shouldn't", "wouldnt", "wouldn't", "couldnt", "couldn't"
}

POSITIVE_WORDS = {
    "amazing", "awesome", "beautiful", "best", "brilliant", "calm", "clutch", "cold", "crazy", "elite", "enjoy",
    "excellent", "fire", "fun", "glad", "goat", "good", "great", "happy", "impressive", "incredible", "insane",
    "legend", "love", "nice", "perfect", "phenomenal", "proud", "respect", "solid", "strong", "support", "tough",
    "unreal", "valuable", "win", "winner", "winning", "wow", "favourite", "favorite", "cook", "cooked", "cooking",
    "smooth", "beautiful", "dominant", "killer", "special", "smart", "clean", "nasty", "hard", "tremendous"
}

NEGATIVE_WORDS = {
    "annoying", "awful", "bad", "boring", "brick", "bricked", "choke", "choked", "choking", "confusing", "crazybad",
    "dirty", "disappointing", "disaster", "dumb", "embarrassing", "flop", "flopping", "garbage", "hate", "horrible",
    "inconsistent", "lazy", "lost", "mess", "mid", "overrated", "pathetic", "poor", "problem", "rough", "sad",
    "slow", "stupid", "terrible", "trash", "ugly", "washed", "weak", "worse", "worst", "wrong", "injured", "injury",
    "soft", "bum", "bums", "fraud", "frauds"
}

POSITIVE_PHRASES = {
    "well done": 2,
    "good job": 2,
    "great job": 2,
    "love this": 2,
    "so good": 2,
    "too good": 2,
    "mvp": 2,
    "goat": 2,
    "lets go": 2,
    "let's go": 2,
    "what a pass": 2,
    "what a move": 2,
}

NEGATIVE_PHRASES = {
    "not good": -2,
    "so bad": -2,
    "too bad": -2,
    "hate this": -2,
    "what is this": -1,
    "fell off": -2,
    "ball hog": -2,
    "no defense": -2,
    "not clutch": -2,
    "not him": -2,
    "not it": -2,
}


TOKEN_PATTERN = re.compile(r"[a-zA-Z']+")


def normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return LABEL_MAP.get(text)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def score_text(text: str) -> int:
    lowered = text.lower()
    score = 0

    for phrase, value in POSITIVE_PHRASES.items():
        if phrase in lowered:
            score += value
    for phrase, value in NEGATIVE_PHRASES.items():
        if phrase in lowered:
            score += value

    tokens = tokenize(lowered)
    previous_tokens = [None] + tokens[:-1]

    for previous, token in zip(previous_tokens, tokens):
        token_score = 0
        if token in POSITIVE_WORDS:
            token_score = 1
        elif token in NEGATIVE_WORDS:
            token_score = -1

        if token_score != 0 and previous in NEGATIONS:
            token_score *= -1

        score += token_score

    return score


def predict_label(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return "neutral"

    score = score_text(cleaned)
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def evaluate_against_manual() -> dict[str, Any]:
    if not LABELED_FILE.exists():
        raise FileNotFoundError(f"Labeled file not found: {LABELED_FILE}")

    df = pd.read_csv(LABELED_FILE)
    df["cleaned_text"] = df["cleaned_text"].fillna("").astype(str)
    df["manual_label_normalized"] = df["manual_label"].apply(normalize_label)
    df = df.dropna(subset=["manual_label_normalized"])
    df = df[df["cleaned_text"].str.strip() != ""]

    df["lexicon_predicted_label"] = df["cleaned_text"].apply(predict_label)

    labels = ["negative", "neutral", "positive"]
    accuracy = accuracy_score(df["manual_label_normalized"], df["lexicon_predicted_label"])
    macro_f1 = f1_score(df["manual_label_normalized"], df["lexicon_predicted_label"], average="macro")
    weighted_f1 = f1_score(df["manual_label_normalized"], df["lexicon_predicted_label"], average="weighted")
    matrix = confusion_matrix(df["manual_label_normalized"], df["lexicon_predicted_label"], labels=labels)

    comparison_csv = OUTPUT_DIR / "lexicon_vs_manual_labeled_sample.csv"
    df.to_csv(comparison_csv, index=False, encoding="utf-8-sig")

    return {
        "rows_evaluated": int(len(df)),
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "labels": labels,
        "classification_report": classification_report(
            df["manual_label_normalized"],
            df["lexicon_predicted_label"],
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": matrix.tolist(),
        "label_distribution_manual": df["manual_label_normalized"].value_counts().to_dict(),
        "label_distribution_lexicon": df["lexicon_predicted_label"].value_counts().to_dict(),
    }


def predict_full_dataset() -> pd.DataFrame:
    if not FULL_FILE.exists():
        raise FileNotFoundError(f"Full dataset file not found: {FULL_FILE}")

    df = pd.read_csv(FULL_FILE)
    df = df.copy()
    df["cleaned_text"] = df["cleaned_text"].fillna("").astype(str)
    df["lexicon_score"] = df["cleaned_text"].apply(score_text)
    df["lexicon_predicted_label"] = df["cleaned_text"].apply(predict_label)

    csv_path = OUTPUT_DIR / "clean_comments_with_lexicon_predictions.csv"
    json_path = OUTPUT_DIR / "clean_comments_with_lexicon_predictions.json"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
    return df


def save_metrics(metrics: dict[str, Any], full_df: pd.DataFrame) -> None:
    payload = {
        "lexicon_method": "rule_based_custom_english_sports_lexicon",
        "evaluation": metrics,
        "full_prediction_distribution": full_df["lexicon_predicted_label"].value_counts().to_dict(),
    }
    metrics_path = OUTPUT_DIR / "lexicon_sentiment_metrics.json"
    metrics_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def print_confusion_matrix(labels: list[str], matrix: list[list[int]]) -> None:
    print("Confusion Matrix - lexicon")
    header = "actual\\pred".ljust(14) + " ".join(label.rjust(10) for label in labels)
    print(header)
    for label, row in zip(labels, matrix):
        row_text = " ".join(str(value).rjust(10) for value in row)
        print(label.ljust(14) + row_text)


def main() -> None:
    evaluation = evaluate_against_manual()
    full_df = predict_full_dataset()
    save_metrics(evaluation, full_df)

    print("Lexicon sentiment labeling completed.")
    print(f"Rows evaluated against manual labels: {evaluation['rows_evaluated']}")
    print(
        f"Accuracy={evaluation['accuracy']}, "
        f"macro_f1={evaluation['macro_f1']}, "
        f"weighted_f1={evaluation['weighted_f1']}"
    )
    print("Manual label distribution:")
    for label, count in evaluation["label_distribution_manual"].items():
        print(f"- {label}: {count}")
    print("Lexicon prediction distribution on labeled sample:")
    for label, count in evaluation["label_distribution_lexicon"].items():
        print(f"- {label}: {count}")
    print_confusion_matrix(evaluation["labels"], evaluation["confusion_matrix"])
    print("Full dataset lexicon prediction distribution:")
    for label, count in full_df["lexicon_predicted_label"].value_counts().items():
        print(f"- {label}: {count}")


if __name__ == "__main__":
    main()
