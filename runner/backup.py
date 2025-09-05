#!/usr/bin/env python3
"""
Twitter Bookmark Backup Class

This module contains the main TwitterBookmarkBackup class for backing up
X (Twitter) bookmarks as individual HTML pages.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .auth import TwitterAuth
from .html_generator import HTMLGenerator

LOG = logging.getLogger(__name__)
MAX_RESULTS = 100


class TwitterBookmarkBackup:
    """Main class for backing up Twitter bookmarks."""

    def __init__(self, config_file: str = "config.json"):
        """Initialize the backup tool with configuration."""
        self.config_file = config_file
        self.auth = TwitterAuth(config_file)
        self.client = self.auth.setup_client()
        self.backup_dir = Path("viewer/bookmarks")
        self.backup_dir.mkdir(exist_ok=True)
        self.html_generator = HTMLGenerator(self.backup_dir)

    @staticmethod
    def save_bookmarks_response_to_disk(data: List[Dict[str, Any]]) -> Path:
        """Save bookmarks data to a JSON file.
        
        Args:
            data: The bookmarks data to save
            
        Returns:
            Path to the saved file
        """
        backup_dir = Path('api_responses')
        backup_dir.mkdir(exist_ok=True)
        
        file_path = backup_dir / 'get_bookmarks.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
        LOG.info(f"Saved bookmarks to {file_path}")
        return file_path

    @staticmethod
    def process_bookmarks_response(bookmarks_response) -> List[Dict[str, Any]]:
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
                                video_variants = [v for v in media_obj.variants if
                                                  v.get('content_type', '').startswith('video/')]
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

    def get_bookmarks(self, save_to_disk: bool = True) -> List[Dict[str, Any]]:
        """Fetch bookmarks from Twitter API v2.
        
        Args:
            save_to_disk: If True, saves the raw bookmarks data to a JSON file
            
        Returns:
            List of bookmarks with their details
        """
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

            # Save the API response so we can do easier testing going forward
            if save_to_disk:
                self.save_bookmarks_response_to_disk(bookmarks_response.data)

            return self.process_bookmarks_response(bookmarks_response)

        except Exception as e:
            LOG.error(f"Failed to fetch bookmarks: {e}")
            LOG.error("Make sure your app has 'bookmarks:read' permission")
            return []

    def backup_all_bookmarks(self, bookmarks = None):
        """Backup all bookmarks."""
        LOG.info("Starting bookmark backup...")

        if not bookmarks:
            bookmarks = self.get_bookmarks()

        saved_count = 0
        for bookmark in bookmarks:
            if self.html_generator.save_bookmark(bookmark):
                saved_count += 1

        LOG.info(f"Backup complete! Saved {saved_count} new bookmarks")
