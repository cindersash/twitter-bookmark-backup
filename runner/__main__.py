#!/usr/bin/env python3
"""
X (Twitter) Bookmark Backup Tool

This script automatically backs up your X (Twitter) bookmarks as individual HTML pages
that preserve the original tweet appearance with embedded media.
"""

import logging
import sys

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
