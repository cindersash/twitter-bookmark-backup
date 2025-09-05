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

from runner.constants import HTML_TEMPLATE

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

    def _download_avatar_picture(self, username: str, profile_image_url: str):
        """Download and save a user's profile image if it doesn't exist.

        Args:
            username: The Twitter username (used for the filename)
            profile_image_url: URL of the profile image to download
        """
        if not profile_image_url:
            return

        # Create a clean filename from username (always use .jpg for consistency)
        safe_username = "".join(c if c.isalnum() else "_" for c in username.lower())
        avatar_filename = f"{safe_username}.jpg"
        avatar_path = self.backup_dir / "avatars" / avatar_filename

        # Don't re-download if we already have the file
        if avatar_path.exists():
            return

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
        except Exception as e:
            LOG.error(f"Failed to download profile image for {username}: {e}")

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
        template = Template(HTML_TEMPLATE)
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
                    self._download_avatar_picture(username, profile_image_url)
            
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
