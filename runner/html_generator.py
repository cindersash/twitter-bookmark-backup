#!/usr/bin/env python3
"""
HTML generation module for Twitter Bookmark Backup Tool.

This module handles HTML generation and saving of Twitter bookmarks.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from jinja2 import Template

LOG = logging.getLogger(__name__)


class HTMLGenerator:
    """Handles HTML generation and saving of Twitter bookmarks."""

    def __init__(self, backup_dir: Path):
        """Initialize the HTML generator with backup directory."""
        self.backup_dir = backup_dir
        # Create avatars directory if it doesn't exist
        (self.backup_dir / "avatars").mkdir(exist_ok=True)

    def _html_file_exists(self, tweet_id: str) -> bool:
        """Check if HTML file for a tweet already exists."""
        html_file = self.backup_dir / f"bookmark_{tweet_id}.html"
        return html_file.exists()

    def _get_avatar_path(self, username: str, profile_image_url: str) -> Optional[str]:
        """Download and save a user's profile image if it doesn't exist.

        Args:
            username: The Twitter username (used for the filename)
            profile_image_url: URL of the profile image to download

        Returns:
            The filename of the avatar (without path) if successful, None otherwise
        """
        if not profile_image_url:
            return None

        # Create a clean filename from username (always use .jpg for consistency)
        safe_username = "".join(c if c.isalnum() else "_" for c in username.lower())
        avatar_filename = f"{safe_username}.jpg"
        avatar_path = self.backup_dir / "avatars" / avatar_filename

        # Return filename if file already exists
        if avatar_path.exists():
            return avatar_filename

        # Create avatars directory if it doesn't exist
        avatar_path.parent.mkdir(exist_ok=True)

        # Download the avatar if it doesn't exist
        try:
            response = requests.get(profile_image_url, stream=True)
            response.raise_for_status()

            with open(avatar_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            LOG.debug(f"Downloaded profile image for {username} to {avatar_path}")
            return avatar_filename
            
        except Exception as e:
            LOG.error(f"Failed to download profile image for {username}: {e}")
            return None

    def _media_file_exists(self, tweet_id: str, media_key: str, media_type: str) -> bool:
        """Check if media file for a tweet already exists."""
        # Determine file extension based on media type
        if media_type == 'video':
            extension = '.mp4'
        elif media_type == 'photo':
            extension = '.jpg'
        else:
            extension = ''

        # Check for common extensions if the specific one doesn't exist
        extensions_to_check = [extension] if extension else ['.jpg', '.png', '.gif', '.mp4', '.webm', '.mov']

        for ext in extensions_to_check:
            media_file = self.backup_dir / "media" / f"{tweet_id}_{media_key}{ext}"
            if media_file.exists():
                return True
        return False

    def _find_existing_media_file(self, tweet_id: str, media_key: str, media_type: str) -> Optional[Path]:
        """Find the existing media file for a tweet."""
        # Determine file extension based on media type
        if media_type == 'video':
            extension = '.mp4'
        elif media_type == 'photo':
            extension = '.jpg'
        else:
            extension = ''

        # Check for common extensions if the specific one doesn't exist
        extensions_to_check = [extension] if extension else ['.jpg', '.png', '.gif', '.mp4', '.webm', '.mov']

        for ext in extensions_to_check:
            media_file = self.backup_dir / "media" / f"{tweet_id}_{media_key}{ext}"
            if media_file.exists():
                return media_file
        return None

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
            
            <img src="{{ avatar_src }}" alt="Profile" class="avatar" onerror="this.src='data:image/svg+xml;charset=UTF-8,<svg%20width%3D\'48\'%20height%3D\'48\'%20viewBox%3D\'0%200%2048%2048\'%20xmlns%3D\'http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg\'><rect%20width%3D\'48\'%20height%3D\'48\'%20fill%3D\'%23e7e9ea\'%2F><text%20x%3D\'50%\'%20y%3D\'60%\'%20font-size%3D\'24\'%20text-anchor%3D\'middle\'%20fill%3D\'%2371767b\'>{{ display_name|first|upper }}<\/text><\/svg>'">
            <div class="user-info">
                <a href="https://twitter.com/{{ username }}" class="username">
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

        template = Template(template_str)
        return template.render(
            tweet=tweet,
            backup_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def save_bookmark(self, tweet: Dict[str, Any]) -> bool:
        """Save a single bookmark as HTML."""
        try:
            tweet_id = tweet['id']

            # Check if HTML file already exists
            if self._html_file_exists(tweet_id):
                LOG.info(f"Bookmark {tweet_id} HTML file already exists, skipping")
                return False

            # Download profile image if author exists and has a profile image
            author = tweet.get('author')
            if author:
                # Get username safely regardless of whether author is a dict or object
                username = (
                    author.get('username')
                    if isinstance(author, dict)
                    else getattr(author, 'username', 'unknown')
                )
                
                # Get profile image URL safely
                profile_image_url = (
                    author.get('profile_image_url')
                    if isinstance(author, dict)
                    else getattr(author, 'profile_image_url', None)
                )
                
                if profile_image_url:
                    self._get_avatar_path(username, profile_image_url)
            
            # Download media if present and not already downloaded
            if 'media' in tweet:
                for media in tweet['media']:
                    if media['type'] in ['photo', 'video']:
                        # Check if media file already exists
                        if self._media_file_exists(tweet_id, media['media_key'], media['type']):
                            LOG.info(
                                f"Media file for {tweet_id}_{media['media_key']} already exists, skipping download")
                            # Update the media URL to point to the local file
                            # We need to find the actual file with the correct extension
                            media_file = self._find_existing_media_file(tweet_id, media['media_key'], media['type'])
                            if media_file:
                                media['url'] = str(media_file.relative_to(self.backup_dir))
                        else:
                            # Download the media
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

            LOG.info(f"Saved bookmark {tweet_id} to {html_file}")
            return True

        except Exception as e:
            LOG.error(f"Failed to save bookmark {tweet.get('id', 'unknown')}: {e}")
            return False
