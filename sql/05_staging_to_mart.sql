TRUNCATE TABLE mart_comment_sentiment_ready, mart_comment_summary, mart_video_metrics, mart_channel_summary;

INSERT INTO mart_channel_summary (
    channel_id,
    channel_title,
    subscriber_count,
    total_channel_views,
    total_channel_videos,
    tracked_videos_loaded,
    tracked_comments_loaded,
    last_video_published_at,
    last_refresh_at
)
SELECT
    c.channel_id,
    c.title AS channel_title,
    c.subscriber_count,
    c.view_count AS total_channel_views,
    c.video_count AS total_channel_videos,
    COUNT(DISTINCT v.video_id) AS tracked_videos_loaded,
    COUNT(DISTINCT cm.comment_thread_id) AS tracked_comments_loaded,
    MAX(v.published_at) AS last_video_published_at,
    CURRENT_TIMESTAMP AS last_refresh_at
FROM stg_channels c
LEFT JOIN stg_videos v
    ON c.channel_id = v.channel_id
LEFT JOIN stg_comments cm
    ON c.channel_id = cm.channel_id
GROUP BY
    c.channel_id,
    c.title,
    c.subscriber_count,
    c.view_count,
    c.video_count;

INSERT INTO mart_video_metrics (
    video_id,
    channel_id,
    channel_title,
    title,
    published_at,
    duration_seconds,
    definition,
    caption_available,
    view_count,
    like_count,
    comment_count,
    engagement_score,
    engagement_rate,
    last_refresh_at
)
SELECT
    video_id,
    channel_id,
    channel_title,
    title,
    published_at,
    duration_seconds,
    definition,
    caption_available,
    view_count,
    like_count,
    comment_count,
    COALESCE(like_count, 0) + COALESCE(comment_count, 0) AS engagement_score,
    CASE
        WHEN COALESCE(view_count, 0) = 0 THEN NULL
        ELSE ROUND(
            ((COALESCE(like_count, 0) + COALESCE(comment_count, 0))::numeric / view_count::numeric),
            6
        )
    END AS engagement_rate,
    CURRENT_TIMESTAMP AS last_refresh_at
FROM stg_videos;

INSERT INTO mart_comment_summary (
    video_id,
    total_comments_loaded,
    total_comment_likes,
    avg_comment_length,
    avg_reply_count,
    latest_comment_at,
    last_refresh_at
)
SELECT
    video_id,
    COUNT(*) AS total_comments_loaded,
    COALESCE(SUM(like_count), 0) AS total_comment_likes,
    ROUND(AVG(LENGTH(COALESCE(text_original, ''))), 2) AS avg_comment_length,
    ROUND(AVG(COALESCE(total_reply_count, 0)), 2) AS avg_reply_count,
    MAX(published_at) AS latest_comment_at,
    CURRENT_TIMESTAMP AS last_refresh_at
FROM stg_comments
GROUP BY video_id;

INSERT INTO mart_comment_sentiment_ready (
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
)
SELECT
    comment_thread_id,
    video_id,
    channel_id,
    published_at,
    author_display_name,
    text_original,
    LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(COALESCE(text_original, ''), 'https?://\\S+', '', 'g'),
            '\\s+',
            ' ',
            'g'
        )
    ) AS cleaned_text,
    LENGTH(COALESCE(text_original, '')) AS text_length,
    like_count,
    total_reply_count,
    CURRENT_TIMESTAMP AS last_refresh_at
FROM stg_comments;
