#!/usr/bin/env python3
"""
HTML generation module for Twitter Bookmark Backup Tool.

This module handles HTML generation and saving of Twitter bookmarks.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Set

import requests
from jinja2 import Template

LOG = logging.getLogger(__name__)


class HTMLGenerator:
    """Handles HTML generation and saving of Twitter bookmarks."""

    def __init__(self, backup_dir: Path, saved_bookmarks_file: Path):
        """Initialize the HTML generator with backup directory and saved bookmarks file."""
        self.backup_dir = backup_dir
        self.saved_bookmarks_file = saved_bookmarks_file
        self.saved_bookmarks = self._load_saved_bookmarks()

    def _load_saved_bookmarks(self) -> Set[str]:
        """Load list of already saved bookmarks."""
        if self.saved_bookmarks_file.exists():
            with open(self.saved_bookmarks_file, 'r') as f:
                return set(json.load(f))
        return set()

    def _save_bookmark_id(self, bookmark_id: str):
        """Save a bookmark ID to the saved bookmarks list."""
        self.saved_bookmarks.add(bookmark_id)
        with open(self.saved_bookmarks_file, 'w') as f:
            json.dump(list(self.saved_bookmarks), f)

    def download_media(self, media_url: str, filename: str, media_type: str = None) -> Optional[str]:
        """Download media file and return local path."""
        try:
            response = requests.get(media_url, stream=True)
            response.raise_for_status()

            # Determine file extension based on content type or media type
            content_type = response.headers.get('content-type', '').lower()
            if 'video/' in content_type:
                if 'mp4' in content_type:
                    extension = '.mp4'
                elif 'webm' in content_type:
                    extension = '.webm'
                elif 'quicktime' in content_type:
                    extension = '.mov'
                else:
                    extension = '.mp4'  # Default for video
            elif 'image/' in content_type:
                if 'jpeg' in content_type or 'jpg' in content_type:
                    extension = '.jpg'
                elif 'png' in content_type:
                    extension = '.png'
                elif 'gif' in content_type:
                    extension = '.gif'
                else:
                    extension = '.jpg'  # Default for image
            elif media_type == 'video':
                extension = '.mp4'  # Default for video
            elif media_type == 'photo':
                extension = '.jpg'  # Default for photo
            else:
                extension = ''  # No extension if we can't determine

            # Add extension to filename if not already present
            if extension and not filename.endswith(extension):
                filename += extension

            media_path = self.backup_dir / "media" / filename
            media_path.parent.mkdir(exist_ok=True)

            with open(media_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return str(media_path.relative_to(self.backup_dir))

        except Exception as e:
            LOG.error(f"Failed to download media {media_url}: {e}")
            return None

    @staticmethod
    def generate_html(tweet: Dict[str, Any]) -> str:
        """Generate HTML for a single bookmark."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bookmark - @{{ tweet.author.username }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #000;
            color: #fff;
        }
        .tweet {
            border: 1px solid #2f3336;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #16181c;
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
        }
        .username {
            font-weight: bold;
            color: #fff;
            text-decoration: none;
        }
        .handle {
            color: #71767b;
            margin-left: 4px;
        }
        .timestamp {
            color: #71767b;
            font-size: 14px;
        }
        .tweet-content {
            font-size: 20px;
            line-height: 1.4;
            margin-bottom: 12px;
        }
        .tweet-media {
            margin: 12px 0;
        }
        .tweet-media img, .tweet-media video {
            max-width: 100%;
            border-radius: 12px;
        }
        .tweet-stats {
            display: flex;
            gap: 20px;
            margin-top: 12px;
            color: #71767b;
            font-size: 14px;
        }
        .backup-info {
            font-size: 12px;
            color: #71767b;
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #2f3336;
        }
    </style>
</head>
<body>
    <div class="tweet">
        <div class="tweet-header">
            {% if tweet.author %}
            <img src="{{ tweet.author.profile_image_url }}" alt="Profile" class="avatar">
            <div class="user-info">
                <a href="https://twitter.com/{{ tweet.author.username }}" class="username">
                    {{ tweet.author.name }}
                </a>
                <span class="handle">@{{ tweet.author.username }}</span>
                <div class="timestamp">{{ tweet.created_at }}</div>
            </div>
            {% else %}
            <div class="user-info">
                <span class="username">Unknown User</span>
                <div class="timestamp">{{ tweet.created_at }}</div>
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

        template = Template(template_str)
        return template.render(
            tweet=tweet,
            backup_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def save_bookmark(self, tweet: Dict[str, Any]) -> bool:
        """Save a single bookmark as HTML."""
        try:
            tweet_id = tweet['id']

            # Check if already saved
            if tweet_id in self.saved_bookmarks:
                LOG.info(f"Bookmark {tweet_id} already saved, skipping")
                return False

            # Download media if present
            if 'media' in tweet:
                for media in tweet['media']:
                    if media['type'] in ['photo', 'video']:
                        local_path = self.download_media(media['url'], f"{tweet_id}_{media['media_key']}",
                                                         media['type'])
                        if local_path:
                            media['url'] = local_path

            # Generate HTML
            html_content = self.generate_html(tweet)

            # Save HTML file
            html_file = self.backup_dir / f"bookmark_{tweet_id}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Mark as saved
            self._save_bookmark_id(tweet_id)

            LOG.info(f"Saved bookmark {tweet_id} to {html_file}")
            return True

        except Exception as e:
            LOG.error(f"Failed to save bookmark {tweet.get('id', 'unknown')}: {e}")
            return False
