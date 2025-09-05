#!/usr/bin/env python3
"""
X (Twitter) Bookmark Backup Tool

This script automatically backs up your X (Twitter) bookmarks as individual HTML pages
that preserve the original tweet appearance with embedded media.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .auth import TwitterAuth
from .html_generator import HTMLGenerator

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
        self.auth = TwitterAuth(config_file)
        self.client = self.auth.setup_client()
        self.backup_dir = Path("bookmark_backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.saved_bookmarks_file = self.backup_dir / "saved_bookmarks.json"
        self.html_generator = HTMLGenerator(self.backup_dir, self.saved_bookmarks_file)



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
                media_fields=['media_key', 'type', 'url', 'preview_image_url', 'variants'],
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
                            
                            # Handle different media types
                            if media_obj.type == 'video':
                                # For videos, try to get the best quality video URL from variants
                                video_url = None
                                if hasattr(media_obj, 'variants') and media_obj.variants:
                                    # Find the highest quality video variant
                                    video_variants = [v for v in media_obj.variants if v.get('content_type', '').startswith('video/')]
                                    if video_variants:
                                        # Sort by bitrate to get the highest quality
                                        video_variants.sort(key=lambda x: x.get('bit_rate', 0), reverse=True)
                                        video_url = video_variants[0].get('url')
                                
                                # Fallback to preview image if no video URL found
                                if not video_url:
                                    video_url = media_obj.preview_image_url
                                
                                bookmark_data['media'].append({
                                    'media_key': media_obj.media_key,
                                    'type': media_obj.type,
                                    'url': video_url
                                })
                            else:
                                # For photos and other media types, use the standard URL
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


    def backup_all_bookmarks(self):
        """Backup all bookmarks."""
        LOG.info("Starting bookmark backup...")

        bookmarks = self.get_bookmarks()
        if not bookmarks:
            LOG.warning("No bookmarks found or failed to fetch bookmarks")
            return

        saved_count = 0
        for bookmark in bookmarks:
            if self.html_generator.save_bookmark(bookmark):
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
