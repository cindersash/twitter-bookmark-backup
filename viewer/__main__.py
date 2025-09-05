#!/usr/bin/env python3
"""
Twitter Bookmark Viewer - Main Entry Point

Run this to start the web server for viewing bookmarks.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from runner
sys.path.insert(0, str(Path(__file__).parent.parent))

from viewer.server import run_server

def main():
    """Main entry point for the viewer."""
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
