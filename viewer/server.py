#!/usr/bin/env python3
"""
Flask web server for viewing Twitter bookmarks.
"""

import logging
import re
from pathlib import Path

from flask import Flask, render_template, send_from_directory

LOG = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)

    # Get the bookmark backup directory
    bookmark_dir = Path("viewer/bookmarks")

    def get_bookmark_files():
        """Get all bookmark HTML files from the disk."""
        if not bookmark_dir.exists():
            return []

        bookmark_files = []
        for file_path in bookmark_dir.glob("bookmark_*.html"):
            if file_path.is_file():
                bookmark_files.append(file_path.name)

        # Sort by filename for consistent ordering
        bookmark_files.sort()
        bookmark_files.reverse()
        return bookmark_files

    def extract_tweet_content(html_content):
        """Extract just the tweet content from HTML, keeping all formatting and media."""
        try:
            # Find the tweet div and extract its content
            tweet_match = re.search(r'<div class="tweet">(.*?)</div>\s*<div class="backup-info">', html_content,
                                    re.DOTALL)
            if tweet_match:
                content = tweet_match.group(1)
            else:
                # Fallback: try to find any content between body tags
                body_match = re.search(r'<body>(.*?)</body>', html_content, re.DOTALL)
                if body_match:
                    content = body_match.group(1)
                else:
                    content = html_content

            return content
        except Exception as e:
            LOG.error(f"Failed to extract tweet content: {e}")
            return html_content

    @app.route('/')
    def index():
        """Main page showing all bookmarks."""
        bookmark_files = get_bookmark_files()

        if not bookmark_files:
            return render_template('index.html', bookmarks=[], message="No bookmarks found")

        # Extract content from each bookmark file
        bookmarks = []
        for filename in bookmark_files:
            try:
                file_path = bookmark_dir / filename
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                tweet_content = extract_tweet_content(html_content)
                bookmarks.append({
                    'filename': filename,
                    'content': tweet_content
                })

            except Exception as e:
                LOG.error(f"Failed to process {filename}: {e}")
                bookmarks.append({
                    'filename': filename,
                    'content': f"<div class='error'>Failed to load {filename}: {e}</div>"
                })

        return render_template('index.html', bookmarks=bookmarks)

    @app.route('/bookmark/<filename>')
    def serve_bookmark(filename):
        """Serve individual bookmark HTML files."""
        return send_from_directory(bookmark_dir, filename)

    @app.route('/media/<filename>')
    def serve_media(filename):
        """Serve media files."""
        media_dir = Path("bookmarks/media")
        return send_from_directory(media_dir, filename)

    return app


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask development server."""
    app = create_app()

    print(f"Starting Twitter Bookmark Viewer...")
    print(f"Open your browser and go to: http://{host}:{port}")
    print("Press Ctrl+C to stop the server")

    app.run(host=host, port=port, debug=debug)
