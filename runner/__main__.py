#!/usr/bin/env python3
"""
X (Twitter) Bookmark Backup Tool

This script automatically backs up your X (Twitter) bookmarks as individual HTML pages
that preserve the original tweet appearance with embedded media.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from jinja2 import Template
from tweepy import Client, OAuth2UserHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bookmark_backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
LOG = logging.getLogger(__name__)
MAX_RESULTS = 100


class TwitterBookmarkBackup:
    """Main class for backing up Twitter bookmarks."""

    def __init__(self, config_file: str = "config.json"):
        """Initialize the backup tool with configuration."""
        self.config_file = config_file
        self.config = self._load_config()
        self.client = self._setup_client()
        self.backup_dir = Path("bookmark_backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.saved_bookmarks_file = self.backup_dir / "saved_bookmarks.json"
        self.saved_bookmarks = self._load_saved_bookmarks()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_file):
            self._create_default_config()

        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            "client_id": "your_client_id_here",
            "client_secret": "your_client_secret_here",
            "redirect_uri": "http://localhost:8080/callback"
        }

        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        LOG.info(f"Created default config file: {self.config_file}")
        LOG.info("Please update the config file with your OAuth 2.0 credentials")
        sys.exit(1)

    def _get_oauth2_token(self) -> str:
        """Get OAuth 2.0 access token using authorization code flow."""
        try:
            # Check if we already have a valid token stored
            token_file = Path("oauth2_token.json")
            if token_file.exists():
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                    # Check if token is still valid (basic check)
                    if 'access_token' in token_data:
                        LOG.info("Using existing OAuth 2.0 token")
                        return token_data['access_token']

            # Start OAuth 2.0 flow
            LOG.info("Starting OAuth 2.0 authorization flow...")

            # Create OAuth2UserHandler with HTTPS redirect URI
            oauth2_handler = OAuth2UserHandler(
                client_id=self.config["client_id"],
                client_secret=self.config["client_secret"],
                redirect_uri="https://localhost:8080/callback",  # Use HTTPS
                scope=["bookmark.read", "tweet.read", "users.read"]
            )

            # Get authorization URL
            auth_url = oauth2_handler.get_authorization_url()
            LOG.info(f"Please visit this URL to authorize the application: {auth_url}")
            LOG.info("After authorization, you will be redirected to a page that may show an error.")
            LOG.info("This is normal - please copy the 'code' parameter from the URL and paste it below.")

            # Get authorization code from user input
            auth_code = input("Please enter the authorization code from the callback URL: ").strip()

            if not auth_code:
                LOG.error("No authorization code provided")
                sys.exit(1)

            # Get access token
            access_token = oauth2_handler.fetch_token(auth_code)

            # Save token for future use
            with open(token_file, 'w') as f:
                json.dump(access_token, f, indent=2)

            LOG.info("OAuth 2.0 authorization successful!")
            return access_token['access_token']

        except Exception as e:
            LOG.error(f"Failed to get OAuth 2.0 token: {e}")
            sys.exit(1)

    def _setup_client(self) -> Client:
        """Set up Twitter API v2 client for bookmarks."""
        try:
            access_token = self._get_oauth2_token()
            client = Client(
                bearer_token=access_token,
                wait_on_rate_limit=True
            )
            return client
        except Exception as e:
            LOG.error(f"Failed to setup Twitter API v2 client: {e}")
            sys.exit(1)

    def _load_saved_bookmarks(self) -> set:
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

    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """Fetch bookmarks from Twitter API v2."""
        try:
            LOG.info("Fetching bookmarks...")

            # Fetch bookmarks using Twitter API v2
            bookmarks_response = self.client.get_bookmarks(
                max_results=MAX_RESULTS,  # API limit is 100 per request
                tweet_fields=[
                    'id', 'text', 'created_at', 'author_id', 'public_metrics',
                    'attachments', 'entities', 'context_annotations'
                ],
                user_fields=['id', 'name', 'username', 'profile_image_url'],
                media_fields=['media_key', 'type', 'url', 'preview_image_url'],
                expansions=['author_id', 'attachments.media_keys']
            )

            if not bookmarks_response.data:
                LOG.info("No bookmarks found")
                return []

            # Process the response to create a more usable format
            bookmarks = []
            users = {user.id: user for user in bookmarks_response.includes.get('users', [])}
            media = {media.media_key: media for media in bookmarks_response.includes.get('media', [])}

            for tweet in bookmarks_response.data:
                bookmark_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'author': users.get(tweet.author_id, {}),
                    'public_metrics': tweet.public_metrics,
                    'media': []
                }

                # Add media if present
                if tweet.attachments and 'media_keys' in tweet.attachments:
                    for media_key in tweet.attachments['media_keys']:
                        if media_key in media:
                            media_obj = media[media_key]
                            bookmark_data['media'].append({
                                'media_key': media_obj.media_key,
                                'type': media_obj.type,
                                'url': media_obj.url or media_obj.preview_image_url
                            })

                bookmarks.append(bookmark_data)

            LOG.info(f"Found {len(bookmarks)} bookmarks")
            return bookmarks

        except Exception as e:
            LOG.error(f"Failed to fetch bookmarks: {e}")
            LOG.error("Make sure your app has 'bookmarks:read' permission")
            return []

    def download_media(self, media_url: str, filename: str) -> Optional[str]:
        """Download media file and return local path."""
        try:
            response = requests.get(media_url, stream=True)
            response.raise_for_status()

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
                        local_path = self.download_media(media['url'], f"{tweet_id}_{media['media_key']}")
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

    def backup_all_bookmarks(self):
        """Backup all bookmarks."""
        LOG.info("Starting bookmark backup...")

        bookmarks = self.get_bookmarks()
        if not bookmarks:
            LOG.warning("No bookmarks found or failed to fetch bookmarks")
            return

        saved_count = 0
        for bookmark in bookmarks:
            if self.save_bookmark(bookmark):
                saved_count += 1

        LOG.info(f"Backup complete! Saved {saved_count} new bookmarks")


def main():
    """Main entry point."""
    try:
        backup_tool = TwitterBookmarkBackup()
        backup_tool.backup_all_bookmarks()
    except KeyboardInterrupt:
        LOG.info("Backup interrupted by user")
    except Exception as e:
        LOG.error(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
