from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


class LoaderError(RuntimeError):
    pass


def load_config() -> dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env")

    host = os.getenv("POSTGRES_HOST", "").strip()
    port = os.getenv("POSTGRES_PORT", "").strip()
    database = os.getenv("POSTGRES_DB", "").strip()
    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "").strip()

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
    }


def connect_postgres(config: dict[str, Any]):
    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
    )


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def list_json_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(folder.glob("*.json"))


def insert_raw_channel(cursor, payload: dict[str, Any]) -> int:
    rows = 0
    for item in payload.get("items", []):
        cursor.execute(
            """
            INSERT INTO raw_channels (channel_id, source_handle, payload)
            VALUES (%s, %s, %s)
            """,
            (
                item.get("id"),
                item.get("snippet", {}).get("customUrl"),
                Json(item),
            ),
        )
        rows += 1
    return rows


def insert_raw_playlist_items(cursor, payload: dict[str, Any]) -> int:
    rows = 0
    for item in payload.get("items", []):
        cursor.execute(
            """
            INSERT INTO raw_playlist_items (playlist_item_id, playlist_id, channel_id, video_id, payload)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                item.get("id"),
                item.get("snippet", {}).get("playlistId"),
                item.get("snippet", {}).get("channelId"),
                item.get("contentDetails", {}).get("videoId"),
                Json(item),
            ),
        )
        rows += 1
    return rows


def insert_raw_videos(cursor, payload: dict[str, Any]) -> int:
    rows = 0
    for item in payload.get("items", []):
        cursor.execute(
            """
            INSERT INTO raw_videos (video_id, channel_id, payload)
            VALUES (%s, %s, %s)
            """,
            (
                item.get("id"),
                item.get("snippet", {}).get("channelId"),
                Json(item),
            ),
        )
        rows += 1
    return rows


def insert_raw_comment_threads(cursor, payload: dict[str, Any]) -> int:
    rows = 0
    for item in payload.get("items", []):
        cursor.execute(
            """
            INSERT INTO raw_comment_threads (comment_thread_id, channel_id, video_id, payload)
            VALUES (%s, %s, %s, %s)
            """,
            (
                item.get("id"),
                item.get("snippet", {}).get("channelId"),
                item.get("snippet", {}).get("videoId"),
                Json(item),
            ),
        )
        rows += 1
    return rows


def process_folder(cursor, folder: Path, insert_fn) -> dict[str, int]:
    file_count = 0
    row_count = 0
    for json_file in list_json_files(folder):
        payload = load_json_file(json_file)
        inserted = insert_fn(cursor, payload)
        file_count += 1
        row_count += inserted
    return {"files": file_count, "rows": row_count}


def main() -> None:
    if not RAW_DIR.exists():
        raise LoaderError(f"Raw data folder not found: {RAW_DIR}")

    config = load_config()
    summary: dict[str, dict[str, int]] = {}

    with connect_postgres(config) as connection:
        with connection.cursor() as cursor:
            summary["channels"] = process_folder(
                cursor,
                RAW_DIR / "channels",
                insert_raw_channel,
            )
            summary["playlist_items"] = process_folder(
                cursor,
                RAW_DIR / "playlist_items",
                insert_raw_playlist_items,
            )
            summary["videos"] = process_folder(
                cursor,
                RAW_DIR / "videos",
                insert_raw_videos,
            )
            summary["comments"] = process_folder(
                cursor,
                RAW_DIR / "comments",
                insert_raw_comment_threads,
            )
        connection.commit()

    print("Raw PostgreSQL load completed.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
