# YouTube Analytics Pipeline

This project builds an end-to-end YouTube analytics workflow:

1. Extract public data from the YouTube Data API
2. Store raw JSON locally
3. Load raw data into PostgreSQL
4. Transform data into staging and mart tables with SQL
5. Run sentiment analysis with supervised and lexicon-based approaches
6. Export dashboard-ready JSON
7. Render the results in a React dashboard

## Data Sources

This project uses the following YouTube Data API endpoints:

- `channels.list`
- `playlistItems.list`
- `videos.list`
- `commentThreads.list`

## Project Structure

```text
youtube-analytics-pipeline/
├─ data/
│  └─ raw/
├─ dashboard/
├─ models/
├─ output/
├─ sql/
├─ src/
├─ .env
├─ .env.example
└─ requirements.txt
```

## 1. Python Setup

From the project root:

```powershell
cd D:\GitHub\youtube-analytics-pipeline
pip install -r requirements.txt
```

Create `.env` from `.env.example`, then fill in your real values.

Important fields:

- `YOUTUBE_API_KEY`
- `YOUTUBE_CHANNEL_HANDLE`
- `YOUTUBE_CHANNEL_ID`
- `YOUTUBE_UPLOADS_PLAYLIST_ID`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

Recommended initial configuration:

```env
YOUTUBE_CHANNEL_HANDLE=NBA
YOUTUBE_CHANNEL_ID=UCWJ2lWNubArHWmf3FIHbfcQ
YOUTUBE_UPLOADS_PLAYLIST_ID=UUWJ2lWNubArHWmf3FIHbfcQ
MAX_PLAYLIST_ITEMS=10
MAX_COMMENT_VIDEOS=1
MAX_COMMENTS_PER_VIDEO=0
TEST_VIDEO_ID=AL0AGaoJCWY
START_COMMENT_PAGE_TOKEN=
EXPORT_COMMENT_LIMIT=100000
```

## 2. Extract Raw Data from YouTube API

Run:

```powershell
python src\extract_youtube.py
```

This script:

- gets channel metadata
- gets video discovery data from the uploads playlist
- gets video details
- gets top-level comment threads
- saves raw JSON to `data/raw/`

Raw output will be saved into:

```text
data/
└─ raw/
   ├─ channels/
   ├─ playlist_items/
   ├─ videos/
   ├─ comments/
   └─ manifest_*.json
```

## 3. Create PostgreSQL Database and Tables

Open `pgAdmin 4` and create a database named:

```text
youtube_analytics
```

After the database is created, open `Query Tool` for that database and run these SQL files in this exact order:

1. `sql/01_raw_schema.sql`
2. `sql/02_staging_schema.sql`
3. `sql/03_mart_schema.sql`

What these files do:

- `01_raw_schema.sql` creates raw tables for JSON payload storage
- `02_staging_schema.sql` creates cleaned staging tables
- `03_mart_schema.sql` creates reporting-ready mart tables

## 4. Load Raw JSON into PostgreSQL

After the raw tables exist, run:

```powershell
python src\load_raw_postgres.py
```

This script reads the raw JSON files from `data/raw/` and inserts them into:

- `raw_channels`
- `raw_playlist_items`
- `raw_videos`
- `raw_comment_threads`

## 5. Run SQL Transformations in PostgreSQL

After raw data has been loaded, go back to `pgAdmin` and run these SQL files:

1. `sql/04_raw_to_staging.sql`
2. `sql/05_staging_to_mart.sql`

What these files do:

- `04_raw_to_staging.sql`
  - parses JSONB payloads
  - removes duplicates
  - casts fields into usable types
  - fills staging tables

- `05_staging_to_mart.sql`
  - creates reporting-ready outputs
  - builds summary tables for comments, videos, and sentiment-ready text

At this point, PostgreSQL already contains:

- raw layer
- staging layer
- mart layer

## 6. Export Clean Comments for Labeling

Run:

```powershell
python src\export_clean_comments.py
```

This script exports cleaned comments from PostgreSQL into the `output/` folder.

For manual sentiment labeling, use the sample file:

```text
output/al0agaojcwY_comment_sample_200_for_labeling.csv
```

That sample is used to manually assign:

- `positive`
- `negative`
- `neutral`

Important:

- `export_clean_comments.py` prepares the clean comment export
- `al0agaojcwY_comment_sample_200_for_labeling.csv` is the manual labeling sample used in this project
- `export_dashboard_data.py` is only for preparing React dashboard data after the sentiment outputs are ready

## 7. Train Supervised Sentiment Model

After manual labels are ready, run:

```powershell
python src\train_sentiment_models.py
```

This script:

- reads the manually labeled sample
- removes rows with blank labels
- trains:
  - Logistic Regression
  - Naive Bayes
  - Linear SVM
- compares the models
- picks the best model
- predicts the full cleaned dataset

The best-performing model is saved here:

```text
models/linear_svm.joblib
```

That `.joblib` file is not handwritten. It is generated automatically by `src/train_sentiment_models.py` after training completes.

The script also creates:

- `output/sentiment_model_metrics.json`
- `output/clean_comments_with_predictions.csv`
- `output/clean_comments_with_predictions.json`

## 8. Run Lexicon Baseline

To generate lexicon-based sentiment predictions for comparison, run:

```powershell
python src\label_sentiment_lexicon.py
```

This creates:

- `output/lexicon_sentiment_metrics.json`
- `output/clean_comments_with_lexicon_predictions.csv`
- `output/clean_comments_with_lexicon_predictions.json`

## 9. Export Dashboard Data

After supervised and lexicon results are ready, run:

```powershell
python src\export_dashboard_data.py
```

This script combines the project outputs into one dashboard-ready file:

```text
dashboard/public/data/dashboard-data.json
```

That JSON is what the React dashboard reads.

## 10. Run the React Dashboard

Move into the dashboard folder:

```powershell
cd D:\GitHub\youtube-analytics-pipeline\dashboard
```

Install frontend dependencies:

```powershell
npm install
```

Start the dashboard:

```powershell
npm run dev
```

Vite will print a local URL such as:

```text
http://127.0.0.1:5176/
```

Open that URL in the browser.

Important:

- do not open `dashboard/index.html` directly by double-clicking
- always run the dashboard through `npm run dev`

## Full End-to-End Run Order

If you want to run the whole project from beginning to end, the order is:

1. `pip install -r requirements.txt`
2. Fill `.env`
3. `python src\extract_youtube.py`
4. Create PostgreSQL database `youtube_analytics`
5. Run:
   - `sql/01_raw_schema.sql`
   - `sql/02_staging_schema.sql`
   - `sql/03_mart_schema.sql`
6. `python src\load_raw_postgres.py`
7. Run:
   - `sql/04_raw_to_staging.sql`
   - `sql/05_staging_to_mart.sql`
8. `python src\export_clean_comments.py`
9. Complete manual labeling
10. `python src\train_sentiment_models.py`
11. `python src\label_sentiment_lexicon.py`
12. `python src\export_dashboard_data.py`
13. `cd dashboard`
14. `npm install`
15. `npm run dev`

## If You Only Want to Run the Dashboard

If the JSON file already exists:

```text
dashboard/public/data/dashboard-data.json
```

then you only need:

```powershell
cd D:\GitHub\youtube-analytics-pipeline\dashboard
npm install
npm run dev
```

## Core Scripts

- `src/extract_youtube.py`
  - fetch raw data from YouTube API

- `src/load_raw_postgres.py`
  - load raw JSON files into PostgreSQL raw tables

- `src/export_clean_comments.py`
  - export cleaned comments from PostgreSQL

- `src/train_sentiment_models.py`
  - train and evaluate supervised sentiment models

- `src/label_sentiment_lexicon.py`
  - run rule-based sentiment baseline

- `src/export_dashboard_data.py`
  - prepare one JSON file for the React dashboard
