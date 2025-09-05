HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Twitter Bookmark - {{ tweet.id }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            color: #e7e9ea;
            background-color: #000000;
            line-height: 1.4;
        }
        .tweet {
            background-color: #16181c;
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 20px;
        }
        .tweet-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            margin-right: 12px;
        }
        .user-info {
            flex: 1;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 5px;
        }
        .username {
            font-weight: bold;
            color: #e7e9ea;
            text-decoration: none;
            margin-right: 5px;
        }
        .handle, .timestamp {
            color: #71767b;
            font-size: 0.9em;
        }
        .tweet-content {
            font-size: 1.1em;
            margin-bottom: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
            margin-left: 60px; /* Match avatar width + margin */
        }
        .tweet-media {
            margin: 12px 0 12px 60px; /* Match avatar width + margin */
        }
        .tweet-media img,
        .tweet-media video {
            max-width: 100%;
            border-radius: 16px;
            margin-top: 10px;
        }
        .tweet-stats {
            display: flex;
            gap: 20px;
            color: #71767b;
            font-size: 0.9em;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #2f3336;
            margin-left: 60px; /* Match avatar width + margin */
        }
        .backup-info {
            font-size: 0.8em;
            color: #71767b;
            text-align: center;
            margin-top: 20px;
        }
        .backup-info a {
            color: #1d9bf0;
            text-decoration: none;
        }
        .backup-info a:hover {
            text-decoration: underline;
        }
        .metadata {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .separator {
            color: #71767b;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="tweet">
        <div class="tweet-header">
            {% set author = tweet.author %}
            {% set username = author.username if author is mapping else author.username %}
            {% set display_name = author.name if author is mapping else author.name %}
            {% set safe_username = username|lower|replace('@', '')|replace(' ', '_')|replace('.', '_') }}
            {% set avatar_src = 'avatars/' ~ safe_username ~ '.jpg' %}
            {% set original_avatar_url = tweet.author.profile_image_url if author is mapping else author.profile_image_url %}

            <img src="{{ avatar_src }}" 
                 alt="Profile" 
                 class="avatar" 
                 data-original-src="{{ original_avatar_url }}"
                 onerror="this.src={{ {{ original_avatar_url }}">
            <div class="user-info">
                <a href="https://x.com/{{ username }}" class="username">
                    {{ display_name }}
                </a>
                <span class="handle">@{{ username }}</span>
                <span class="separator">·</span>
                <span class="timestamp">{{ tweet.created_at }}</span>
            </div>
            {% else %}
            <div class="user-info">
                <span class="username">Unknown User</span>
                <span class="separator">·</span>
                <span class="timestamp">{{ tweet.created_at }}</span>
            </div>
            {% endif %}
        </div>

        <div class="tweet-content">
            {{ tweet.text | safe }}
        </div>

        {% if tweet.media %}
        <div class="tweet-media">
            {% for media in tweet.media %}
                {% if media.type == 'photo' %}
                    <img src="{{ media.url }}" alt="Tweet image">
                {% elif media.type == 'video' %}
                    <video controls>
                        <source src="{{ media.url }}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                {% endif %}
            {% endfor %}
        </div>
        {% endif %}

        <div class="tweet-stats">
            <span>❤️ {{ tweet.public_metrics.like_count if tweet.public_metrics else 0 }}</span>
            <span>🔄 {{ tweet.public_metrics.retweet_count if tweet.public_metrics else 0 }}</span>
            <span>💬 {{ tweet.public_metrics.reply_count if tweet.public_metrics else 0 }}</span>
        </div>
    </div>

    <div class="backup-info">
        Bookmark backed up on {{ backup_date }} | 
        Original: <a href="https://twitter.com/{{ tweet.author.username if tweet.author else 'unknown' }}/status/{{ tweet.id }}" target="_blank">View on X</a>
    </div>
</body>
</html>
        """
