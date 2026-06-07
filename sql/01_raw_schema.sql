CREATE TABLE IF NOT EXISTS raw_channels (
    raw_channel_id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    source_handle TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_playlist_items (
    raw_playlist_item_id BIGSERIAL PRIMARY KEY,
    playlist_item_id TEXT NOT NULL,
    playlist_id TEXT NOT NULL,
    channel_id TEXT,
    video_id TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_videos (
    raw_video_id BIGSERIAL PRIMARY KEY,
    video_id TEXT NOT NULL,
    channel_id TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_comment_threads (
    raw_comment_thread_id BIGSERIAL PRIMARY KEY,
    comment_thread_id TEXT NOT NULL,
    channel_id TEXT,
    video_id TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_channels_channel_id
    ON raw_channels(channel_id);

CREATE INDEX IF NOT EXISTS idx_raw_playlist_items_playlist_id
    ON raw_playlist_items(playlist_id);

CREATE INDEX IF NOT EXISTS idx_raw_playlist_items_video_id
    ON raw_playlist_items(video_id);

CREATE INDEX IF NOT EXISTS idx_raw_videos_video_id
    ON raw_videos(video_id);

CREATE INDEX IF NOT EXISTS idx_raw_comment_threads_video_id
    ON raw_comment_threads(video_id);

