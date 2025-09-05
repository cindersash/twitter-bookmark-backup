#!/usr/bin/env python3
"""
X (Twitter) Bookmark Backup Tool

This script automatically backs up your X (Twitter) bookmarks as individual HTML pages
that preserve the original tweet appearance with embedded media.
"""

import json
import logging
import sys
import argparse
from pathlib import Path

from .backup import TwitterBookmarkBackup

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


def _load_bookmarks_response_from_file(file_path: Path) -> list:
    """Load bookmarks from a local JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        LOG.error(f"Failed to load bookmarks from {file_path}: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Backup X (Twitter) bookmarks')
    parser.add_argument('--use-local', action='store_true', 
                       help='Use local get_bookmarks.json file instead of making API calls')
    args = parser.parse_args()

    try:
        backup_tool = TwitterBookmarkBackup()
        bookmarks = None

        # See if we should use a local file instead of making API calls
        if args.use_local:
            json_path = Path('api_responses/get_bookmarks.json')
            if not json_path.exists():
                LOG.error(f"Local bookmarks file not found at {json_path}")
                sys.exit(1)
                
            LOG.info(f"Using local bookmarks from {json_path}")
            api_response = _load_bookmarks_response_from_file(json_path)
            bookmarks = backup_tool.process_bookmarks_response(api_response)

        # Save the bookmarks to disk
        backup_tool.backup_all_bookmarks(bookmarks)
            
    except KeyboardInterrupt:
        LOG.info("Backup interrupted by user")
    except Exception as e:
        LOG.error(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
