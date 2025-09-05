#!/usr/bin/env python3
"""
Authentication module for Twitter Bookmark Backup Tool.

This module handles OAuth 2.0 authentication with Twitter API v2.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from tweepy import Client, OAuth2UserHandler

LOG = logging.getLogger(__name__)


class TwitterAuth:
    """Handles Twitter OAuth 2.0 authentication."""

    def __init__(self, config_file: str = "config.json"):
        """Initialize the authentication handler with configuration."""
        self.config_file = config_file
        self.config = self._load_config()

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

    def get_oauth2_token(self) -> str:
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

    def setup_client(self) -> Client:
        """Set up Twitter API v2 client for bookmarks."""
        try:
            access_token = self.get_oauth2_token()
            client = Client(
                bearer_token=access_token,
                wait_on_rate_limit=True
            )
            return client
        except Exception as e:
            LOG.error(f"Failed to setup Twitter API v2 client: {e}")
            sys.exit(1)
