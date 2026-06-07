CREATE TABLE IF NOT EXISTS stg_channels (
    channel_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    custom_url TEXT,
    country TEXT,
    published_at TIMESTAMP,
    uploads_playlist_id TEXT,
    view_count BIGINT,
    subscriber_count BIGINT,
    hidden_subscriber_count BOOLEAN,
    video_count BIGINT,
    thumbnail_default_url TEXT,
    thumbnail_medium_url TEXT,
    thumbnail_high_url TEXT,
    fetched_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_playlist_videos (
    playlist_item_id TEXT PRIMARY KEY,
    playlist_id TEXT,
    channel_id TEXT,
    channel_title TEXT,
    video_owner_channel_id TEXT,
    video_owner_channel_title TEXT,
    video_id TEXT NOT NULL,
    title TEXT,
    description TEXT,
    position INTEGER,
    published_at TIMESTAMP,
    video_published_at TIMESTAMP,
    thumbnail_default_url TEXT,
    thumbnail_medium_url TEXT,
    thumbnail_high_url TEXT,
    thumbnail_standard_url TEXT,
    thumbnail_maxres_url TEXT,
    fetched_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT,
    channel_title TEXT,
    title TEXT,
    description TEXT,
    published_at TIMESTAMP,
    category_id INTEGER,
    live_broadcast_content TEXT,
    default_language TEXT,
    default_audio_language TEXT,
    tags JSONB,
    duration_iso TEXT,
    duration_seconds INTEGER,
    dimension TEXT,
    definition TEXT,
    caption_available BOOLEAN,
    licensed_content BOOLEAN,
    region_blocked JSONB,
    projection TEXT,
    view_count BIGINT,
    like_count BIGINT,
    favorite_count BIGINT,
    comment_count BIGINT,
    thumbnail_default_url TEXT,
    thumbnail_medium_url TEXT,
    thumbnail_high_url TEXT,
    thumbnail_standard_url TEXT,
    thumbnail_maxres_url TEXT,
    fetched_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_comments (
    comment_thread_id TEXT PRIMARY KEY,
    top_level_comment_id TEXT NOT NULL,
    channel_id TEXT,
    video_id TEXT,
    author_channel_id TEXT,
    author_display_name TEXT,
    author_channel_url TEXT,
    author_profile_image_url TEXT,
    text_original TEXT,
    text_display TEXT,
    like_count BIGINT,
    total_reply_count BIGINT,
    can_reply BOOLEAN,
    is_public BOOLEAN,
    viewer_rating TEXT,
    published_at TIMESTAMP,
    updated_at TIMESTAMP,
    fetched_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stg_playlist_videos_video_id
    ON stg_playlist_videos(video_id);

CREATE INDEX IF NOT EXISTS idx_stg_videos_channel_id
    ON stg_videos(channel_id);

CREATE INDEX IF NOT EXISTS idx_stg_comments_video_id
    ON stg_comments(video_id);

