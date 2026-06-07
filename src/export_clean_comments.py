from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_config() -> dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env")

    host = os.getenv("POSTGRES_HOST", "").strip()
    port = os.getenv("POSTGRES_PORT", "").strip()
    database = os.getenv("POSTGRES_DB", "").strip()
    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "").strip()
    test_video_id = os.getenv("TEST_VIDEO_ID", "").strip()
    export_limit = int(os.getenv("EXPORT_COMMENT_LIMIT", "100"))

    missing = [
        name
        for name, value in {
            "POSTGRES_HOST": host,
            "POSTGRES_PORT": port,
            "POSTGRES_DB": database,
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Missing PostgreSQL settings in .env: {', '.join(missing)}")

    return {
        "host": host,
        "port": int(port),
        "database": database,
        "user": user,
        "password": password,
        "test_video_id": test_video_id,
        "export_limit": export_limit,
    }


def connect_postgres(config: dict[str, Any]):
    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )


def fetch_clean_comments(connection, config: dict[str, Any]) -> list[dict[str, Any]]:
    query = """
        SELECT
            comment_thread_id,
            video_id,
            channel_id,
            published_at,
            author_display_name,
            text_original,
            cleaned_text,
            text_length,
            like_count,
            total_reply_count,
            last_refresh_at
        FROM mart_comment_sentiment_ready
    """

    params: list[Any] = []
    if config["test_video_id"]:
        query += " WHERE video_id = %s"
        params.append(config["test_video_id"])

    query += " ORDER BY published_at DESC LIMIT %s"
    params.append(config["export_limit"])

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict[str, Any]], path: Path) -> None:
    path.write_text(json.dumps(rows, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    ensure_output_dir()
    config = load_config()

    with connect_postgres(config) as connection:
        rows = fetch_clean_comments(connection, config)

    csv_path = OUTPUT_DIR / "clean_comments_sample.csv"
    json_path = OUTPUT_DIR / "clean_comments_sample.json"

    write_csv(rows, csv_path)
    write_json(rows, json_path)

    print("Comment export completed.")
    print(f"Rows exported: {len(rows)}")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
