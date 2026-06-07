# YouTube Analytics Pipeline

## Current Scope
This project extracts public YouTube data from:
- `channels.list`
- `playlistItems.list`
- `videos.list`
- `commentThreads.list`

The first implementation stores raw JSON files locally before loading them into PostgreSQL.

## Setup
1. Create and activate a virtual environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`
4. Fill in your real API key and channel settings

## Run
From the project root:

```bash
python src/extract_youtube.py
```

## Output
Raw files will be saved into:

```text
data/
└─ raw/
   ├─ channels/
   ├─ playlist_items/
   ├─ videos/
   ├─ comments/
   └─ manifest_*.json
```

## Recommended First Run
- `YOUTUBE_CHANNEL_HANDLE=NBA`
- `MAX_PLAYLIST_ITEMS=10`
- `MAX_COMMENT_VIDEOS=3`
- `MAX_COMMENTS_PER_VIDEO=20`

## Next Step
After raw extraction works, the next step is to build:
- raw-to-PostgreSQL loader
- SQL transformations into staging tables
- mart queries for reporting
