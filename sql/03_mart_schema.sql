CREATE TABLE IF NOT EXISTS mart_channel_summary (
    channel_id TEXT PRIMARY KEY,
    channel_title TEXT,
    subscriber_count BIGINT,
    total_channel_views BIGINT,
    total_channel_videos BIGINT,
    tracked_videos_loaded BIGINT,
    tracked_comments_loaded BIGINT,
    last_video_published_at TIMESTAMP,
    last_refresh_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mart_video_metrics (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT,
    channel_title TEXT,
    title TEXT,
    published_at TIMESTAMP,
    duration_seconds INTEGER,
    definition TEXT,
    caption_available BOOLEAN,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
    engagement_score NUMERIC,
    engagement_rate NUMERIC,
    last_refresh_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mart_comment_summary (
    video_id TEXT PRIMARY KEY,
    total_comments_loaded BIGINT,
    total_comment_likes BIGINT,
    avg_comment_length NUMERIC,
    avg_reply_count NUMERIC,
    latest_comment_at TIMESTAMP,
    last_refresh_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mart_comment_sentiment_ready (
    comment_thread_id TEXT PRIMARY KEY,
    video_id TEXT,
    channel_id TEXT,
    published_at TIMESTAMP,
    author_display_name TEXT,
    text_original TEXT,
    cleaned_text TEXT,
    text_length INTEGER,
    like_count BIGINT,
    total_reply_count BIGINT,
    last_refresh_at TIMESTAMP
);
