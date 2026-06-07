from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
MODEL_DIR = PROJECT_ROOT / "models"

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


def ensure_directories() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return LABEL_MAP.get(text)


def load_labeled_data() -> pd.DataFrame:
    if not LABELED_FILE.exists():
        raise FileNotFoundError(f"Labeled file not found: {LABELED_FILE}")

    df = pd.read_csv(LABELED_FILE)
    df["cleaned_text"] = df["cleaned_text"].fillna("").astype(str)
    df["normalized_label"] = df["manual_label"].apply(normalize_label)
    df = df.dropna(subset=["normalized_label"])
    df = df[df["cleaned_text"].str.strip() != ""]

    if df.empty:
        raise ValueError("No labeled rows available after removing blank labels and empty text.")

    class_counts = df["normalized_label"].value_counts()
    if len(class_counts) < 2:
        raise ValueError("At least two sentiment classes are required for model training.")
    if (class_counts < 2).any():
        too_small = class_counts[class_counts < 2].to_dict()
        raise ValueError(
            "Each class needs at least 2 labeled rows for train/test split. "
            f"Too small: {too_small}"
        )

    return df


def build_models() -> dict[str, Pipeline]:
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2)
    return {
        "logistic_regression": Pipeline([
            ("tfidf", vectorizer),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]),
        "naive_bayes": Pipeline([
            ("tfidf", vectorizer),
            ("model", MultinomialNB()),
        ]),
        "linear_svm": Pipeline([
            ("tfidf", vectorizer),
            ("model", LinearSVC(class_weight="balanced")),
        ]),
    }


def evaluate_models(df: pd.DataFrame) -> tuple[dict[str, Any], str, Pipeline]:
    x = df["cleaned_text"].astype(str)
    y = df["normalized_label"].astype(str)
    ordered_labels = sorted(y.unique().tolist())

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    results: dict[str, Any] = {}
    best_model_name = ""
    best_model: Pipeline | None = None
    best_macro_f1 = -1.0

    for model_name, pipeline in build_models().items():
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)

        accuracy = accuracy_score(y_test, predictions)
        macro_f1 = f1_score(y_test, predictions, average="macro")
        weighted_f1 = f1_score(y_test, predictions, average="weighted")

        results[model_name] = {
            "accuracy": round(float(accuracy), 4),
            "macro_f1": round(float(macro_f1), 4),
            "weighted_f1": round(float(weighted_f1), 4),
            "labels": ordered_labels,
            "classification_report": classification_report(
                y_test,
                predictions,
                labels=ordered_labels,
                output_dict=True,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                y_test,
                predictions,
                labels=ordered_labels,
            ).tolist(),
        }

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_model_name = model_name
            best_model = pipeline

    if best_model is None:
        raise RuntimeError("No model was trained successfully")

    return results, best_model_name, best_model


def save_metrics(metrics: dict[str, Any], best_model_name: str, labeled_df: pd.DataFrame) -> None:
    payload = {
        "best_model": best_model_name,
        "training_rows_used": int(len(labeled_df)),
        "label_distribution": labeled_df["normalized_label"].value_counts().to_dict(),
        "metrics": metrics,
    }
    output_path = OUTPUT_DIR / "sentiment_model_metrics.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_best_model(best_model_name: str, best_model: Pipeline) -> None:
    model_path = MODEL_DIR / f"{best_model_name}.joblib"
    joblib.dump(best_model, model_path)


def flag_low_information(df: pd.DataFrame) -> pd.Series:
    text = df["cleaned_text"].fillna("").astype(str)
    return (
        (text.str.strip() == "")
        | (text.str.len() < 3)
        | (~text.str.contains(r"[a-zA-Z]", regex=True))
    )


def predict_full_dataset(best_model: Pipeline) -> None:
    if not FULL_FILE.exists():
        raise FileNotFoundError(f"Full dataset file not found: {FULL_FILE}")

    df = pd.read_csv(FULL_FILE)
    df = df.copy()
    df["cleaned_text"] = df["cleaned_text"].fillna("").astype(str)
    df["is_low_information"] = flag_low_information(df)

    eligible_mask = ~df["is_low_information"]
    df["predicted_sentiment"] = None
    if eligible_mask.any():
        df.loc[eligible_mask, "predicted_sentiment"] = best_model.predict(df.loc[eligible_mask, "cleaned_text"])

    output_csv = OUTPUT_DIR / "clean_comments_with_predictions.csv"
    output_json = OUTPUT_DIR / "clean_comments_with_predictions.json"

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    output_json.write_text(df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")


def save_labeled_training_data(df: pd.DataFrame) -> None:
    output_csv = OUTPUT_DIR / "labeled_comments_used_for_training.csv"
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")


def main() -> None:
    ensure_directories()
    labeled_df = load_labeled_data()
    metrics, best_model_name, best_model = evaluate_models(labeled_df)
    save_metrics(metrics, best_model_name, labeled_df)
    save_best_model(best_model_name, best_model)
    save_labeled_training_data(labeled_df)
    predict_full_dataset(best_model)

    print("Sentiment training completed.")
    print(f"Labeled rows used: {len(labeled_df)}")
    print("Label distribution:")
    for label, count in labeled_df["normalized_label"].value_counts().items():
        print(f"- {label}: {count}")
    print(f"Best model: {best_model_name}")
    for model_name, model_metrics in metrics.items():
        print(
            f"- {model_name}: accuracy={model_metrics['accuracy']}, "
            f"macro_f1={model_metrics['macro_f1']}, weighted_f1={model_metrics['weighted_f1']}"
        )


if __name__ == "__main__":
    main()
