TRUNCATE TABLE stg_comments, stg_videos, stg_playlist_videos, stg_channels;

WITH ranked_channels AS (
    SELECT
        channel_id,
        source_handle,
        fetched_at,
        payload,
        ROW_NUMBER() OVER (
            PARTITION BY channel_id
            ORDER BY fetched_at DESC, raw_channel_id DESC
        ) AS row_num
    FROM raw_channels
    WHERE channel_id IS NOT NULL
)
INSERT INTO stg_channels (
    channel_id,
    title,
    description,
    custom_url,
    country,
    published_at,
    uploads_playlist_id,
    view_count,
    subscriber_count,
    hidden_subscriber_count,
    video_count,
    thumbnail_default_url,
    thumbnail_medium_url,
    thumbnail_high_url,
    fetched_at
)
SELECT
    channel_id,
    payload->'snippet'->>'title' AS title,
    payload->'snippet'->>'description' AS description,
    payload->'snippet'->>'customUrl' AS custom_url,
    payload->'snippet'->>'country' AS country,
    (payload->'snippet'->>'publishedAt')::timestamp AS published_at,
    payload->'contentDetails'->'relatedPlaylists'->>'uploads' AS uploads_playlist_id,
    NULLIF(payload->'statistics'->>'viewCount', '')::bigint AS view_count,
    NULLIF(payload->'statistics'->>'subscriberCount', '')::bigint AS subscriber_count,
    CASE
        WHEN payload->'statistics'->>'hiddenSubscriberCount' = 'true' THEN TRUE
        WHEN payload->'statistics'->>'hiddenSubscriberCount' = 'false' THEN FALSE
        ELSE NULL
    END AS hidden_subscriber_count,
    NULLIF(payload->'statistics'->>'videoCount', '')::bigint AS video_count,
    payload->'snippet'->'thumbnails'->'default'->>'url' AS thumbnail_default_url,
    payload->'snippet'->'thumbnails'->'medium'->>'url' AS thumbnail_medium_url,
    payload->'snippet'->'thumbnails'->'high'->>'url' AS thumbnail_high_url,
    fetched_at
FROM ranked_channels
WHERE row_num = 1;

WITH ranked_playlist_items AS (
    SELECT
        playlist_item_id,
        playlist_id,
        channel_id,
        video_id,
        fetched_at,
        payload,
        ROW_NUMBER() OVER (
            PARTITION BY playlist_item_id
            ORDER BY fetched_at DESC, raw_playlist_item_id DESC
        ) AS row_num
    FROM raw_playlist_items
    WHERE playlist_item_id IS NOT NULL
)
INSERT INTO stg_playlist_videos (
    playlist_item_id,
    playlist_id,
    channel_id,
    channel_title,
    video_owner_channel_id,
    video_owner_channel_title,
    video_id,
    title,
    description,
    position,
    published_at,
    video_published_at,
    thumbnail_default_url,
    thumbnail_medium_url,
    thumbnail_high_url,
    thumbnail_standard_url,
    thumbnail_maxres_url,
    fetched_at
)
SELECT
    playlist_item_id,
    playlist_id,
    channel_id,
    payload->'snippet'->>'channelTitle' AS channel_title,
    payload->'snippet'->>'videoOwnerChannelId' AS video_owner_channel_id,
    payload->'snippet'->>'videoOwnerChannelTitle' AS video_owner_channel_title,
    COALESCE(
        payload->'contentDetails'->>'videoId',
        payload->'snippet'->'resourceId'->>'videoId'
    ) AS video_id,
    payload->'snippet'->>'title' AS title,
    payload->'snippet'->>'description' AS description,
    NULLIF(payload->'snippet'->>'position', '')::integer AS position,
    (payload->'snippet'->>'publishedAt')::timestamp AS published_at,
    (payload->'contentDetails'->>'videoPublishedAt')::timestamp AS video_published_at,
    payload->'snippet'->'thumbnails'->'default'->>'url' AS thumbnail_default_url,
    payload->'snippet'->'thumbnails'->'medium'->>'url' AS thumbnail_medium_url,
    payload->'snippet'->'thumbnails'->'high'->>'url' AS thumbnail_high_url,
    payload->'snippet'->'thumbnails'->'standard'->>'url' AS thumbnail_standard_url,
    payload->'snippet'->'thumbnails'->'maxres'->>'url' AS thumbnail_maxres_url,
    fetched_at
FROM ranked_playlist_items
WHERE row_num = 1;

WITH ranked_videos AS (
    SELECT
        video_id,
        channel_id,
        fetched_at,
        payload,
        ROW_NUMBER() OVER (
            PARTITION BY video_id
            ORDER BY fetched_at DESC, raw_video_id DESC
        ) AS row_num
    FROM raw_videos
    WHERE video_id IS NOT NULL
)
INSERT INTO stg_videos (
    video_id,
    channel_id,
    channel_title,
    title,
    description,
    published_at,
    category_id,
    live_broadcast_content,
    default_language,
    default_audio_language,
    tags,
    duration_iso,
    duration_seconds,
    dimension,
    definition,
    caption_available,
    licensed_content,
    region_blocked,
    projection,
    view_count,
    like_count,
    favorite_count,
    comment_count,
    thumbnail_default_url,
    thumbnail_medium_url,
    thumbnail_high_url,
    thumbnail_standard_url,
    thumbnail_maxres_url,
    fetched_at
)
SELECT
    video_id,
    channel_id,
    payload->'snippet'->>'channelTitle' AS channel_title,
    payload->'snippet'->>'title' AS title,
    payload->'snippet'->>'description' AS description,
    (payload->'snippet'->>'publishedAt')::timestamp AS published_at,
    NULLIF(payload->'snippet'->>'categoryId', '')::integer AS category_id,
    payload->'snippet'->>'liveBroadcastContent' AS live_broadcast_content,
    payload->'snippet'->>'defaultLanguage' AS default_language,
    payload->'snippet'->>'defaultAudioLanguage' AS default_audio_language,
    payload->'snippet'->'tags' AS tags,
    payload->'contentDetails'->>'duration' AS duration_iso,
    (
        COALESCE(NULLIF(SUBSTRING(payload->'contentDetails'->>'duration' FROM 'PT([0-9]+)H'), ''), '0')::integer * 3600
        + COALESCE(NULLIF(SUBSTRING(payload->'contentDetails'->>'duration' FROM '([0-9]+)M'), ''), '0')::integer * 60
        + COALESCE(NULLIF(SUBSTRING(payload->'contentDetails'->>'duration' FROM '([0-9]+)S'), ''), '0')::integer
    ) AS duration_seconds,
    payload->'contentDetails'->>'dimension' AS dimension,
    payload->'contentDetails'->>'definition' AS definition,
    CASE
        WHEN payload->'contentDetails'->>'caption' = 'true' THEN TRUE
        WHEN payload->'contentDetails'->>'caption' = 'false' THEN FALSE
        ELSE NULL
    END AS caption_available,
    CASE
        WHEN payload->'contentDetails'->>'licensedContent' = 'true' THEN TRUE
        WHEN payload->'contentDetails'->>'licensedContent' = 'false' THEN FALSE
        ELSE NULL
    END AS licensed_content,
    payload->'contentDetails'->'regionRestriction'->'blocked' AS region_blocked,
    payload->'contentDetails'->>'projection' AS projection,
    NULLIF(payload->'statistics'->>'viewCount', '')::bigint AS view_count,
    NULLIF(payload->'statistics'->>'likeCount', '')::bigint AS like_count,
    NULLIF(payload->'statistics'->>'favoriteCount', '')::bigint AS favorite_count,
    NULLIF(payload->'statistics'->>'commentCount', '')::bigint AS comment_count,
    payload->'snippet'->'thumbnails'->'default'->>'url' AS thumbnail_default_url,
    payload->'snippet'->'thumbnails'->'medium'->>'url' AS thumbnail_medium_url,
    payload->'snippet'->'thumbnails'->'high'->>'url' AS thumbnail_high_url,
    payload->'snippet'->'thumbnails'->'standard'->>'url' AS thumbnail_standard_url,
    payload->'snippet'->'thumbnails'->'maxres'->>'url' AS thumbnail_maxres_url,
    fetched_at
FROM ranked_videos
WHERE row_num = 1;

WITH ranked_comments AS (
    SELECT
        comment_thread_id,
        channel_id,
        video_id,
        fetched_at,
        payload,
        ROW_NUMBER() OVER (
            PARTITION BY comment_thread_id
            ORDER BY fetched_at DESC, raw_comment_thread_id DESC
        ) AS row_num
    FROM raw_comment_threads
    WHERE comment_thread_id IS NOT NULL
)
INSERT INTO stg_comments (
    comment_thread_id,
    top_level_comment_id,
    channel_id,
    video_id,
    author_channel_id,
    author_display_name,
    author_channel_url,
    author_profile_image_url,
    text_original,
    text_display,
    like_count,
    total_reply_count,
    can_reply,
    is_public,
    viewer_rating,
    published_at,
    updated_at,
    fetched_at
)
SELECT
    comment_thread_id,
    payload->'snippet'->'topLevelComment'->>'id' AS top_level_comment_id,
    channel_id,
    video_id,
    payload->'snippet'->'topLevelComment'->'snippet'->'authorChannelId'->>'value' AS author_channel_id,
    payload->'snippet'->'topLevelComment'->'snippet'->>'authorDisplayName' AS author_display_name,
    payload->'snippet'->'topLevelComment'->'snippet'->>'authorChannelUrl' AS author_channel_url,
    payload->'snippet'->'topLevelComment'->'snippet'->>'authorProfileImageUrl' AS author_profile_image_url,
    payload->'snippet'->'topLevelComment'->'snippet'->>'textOriginal' AS text_original,
    payload->'snippet'->'topLevelComment'->'snippet'->>'textDisplay' AS text_display,
    NULLIF(payload->'snippet'->'topLevelComment'->'snippet'->>'likeCount', '')::bigint AS like_count,
    NULLIF(payload->'snippet'->>'totalReplyCount', '')::bigint AS total_reply_count,
    CASE
        WHEN payload->'snippet'->>'canReply' = 'true' THEN TRUE
        WHEN payload->'snippet'->>'canReply' = 'false' THEN FALSE
        ELSE NULL
    END AS can_reply,
    CASE
        WHEN payload->'snippet'->>'isPublic' = 'true' THEN TRUE
        WHEN payload->'snippet'->>'isPublic' = 'false' THEN FALSE
        ELSE NULL
    END AS is_public,
    payload->'snippet'->'topLevelComment'->'snippet'->>'viewerRating' AS viewer_rating,
    (payload->'snippet'->'topLevelComment'->'snippet'->>'publishedAt')::timestamp AS published_at,
    (payload->'snippet'->'topLevelComment'->'snippet'->>'updatedAt')::timestamp AS updated_at,
    fetched_at
FROM ranked_comments
WHERE row_num = 1;
