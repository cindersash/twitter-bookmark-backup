# X (Twitter) Bookmark Backup Tool

A Python script to automatically back up your X (Twitter) bookmarks as individual HTML pages that preserve the original tweet appearance with embedded media.

## Features

- 🔐 Secure authentication using Twitter API v2
- 📱 Generates HTML pages that match X's current design
- 🖼️ Downloads and embeds images and videos
- 🔄 Prevents duplicate backups
- 📊 Preserves engagement metrics (likes, retweets, replies)
- 📝 Comprehensive logging

## Quick Start

### 1. Install Everything

```bash
python install.py
```

This will install dependencies, create directories, and set up the environment.

### 2. Get Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. Generate API keys and access tokens
4. **Important**: Make sure your app has the following permissions:
   - `bookmarks:read` - Essential for accessing bookmarks
   - `tweets:read` - For reading tweet content
   - `users:read` - For user information

### 3. Configure the Tool

1. Update `config.json` with your actual API credentials:
   ```json
   {
     "api_key": "your_actual_api_key",
     "api_secret": "your_actual_api_secret", 
     "access_token": "your_actual_access_token",
     "access_token_secret": "your_actual_access_token_secret",
     "bearer_token": "your_actual_bearer_token"
   }
   ```

### 4. Test Your Setup

```bash
python test_setup.py
```

This will verify your configuration and API connection.

## Usage

### Run the Backup

```bash
python -m __main__
```

### What It Does

1. **Authentication**: Connects to Twitter API using your credentials
2. **Fetch Bookmarks**: Retrieves your bookmarked tweets
3. **Check Duplicates**: Skips bookmarks that have already been backed up
4. **Download Media**: Downloads images and videos to local storage
5. **Generate HTML**: Creates individual HTML pages for each bookmark
6. **Save Files**: Stores everything in the `bookmark_backups/` directory

### Output Structure

```
bookmark_backups/
├── bookmark_1234567890.html
├── bookmark_1234567891.html
├── media/
│   ├── 1234567890_abc123.jpg
│   └── 1234567891_def456.mp4
└── saved_bookmarks.json
```

## HTML Output

Each bookmark is saved as a standalone HTML file that:
- Matches X's current dark theme design
- Includes the original tweet content and formatting
- Embeds downloaded media (images/videos)
- Shows engagement metrics
- Provides a link back to the original tweet
- Displays backup timestamp

## Configuration Options

You can modify the following in the script:
- `max_results`: Maximum number of bookmarks to fetch (default: 100)
- Backup directory location
- HTML template styling
- Media download settings

## Important Notes

⚠️ **API Limitations**: This tool requires Twitter API v2 with bookmarks access. The bookmarks endpoint may have rate limits and access restrictions.

⚠️ **Authentication**: Keep your API credentials secure and never commit them to version control.

⚠️ **Media Storage**: Downloaded media files are stored locally and may take up significant disk space.

## Troubleshooting

### Common Issues

1. **Authentication Failed**: 
   - Verify your API credentials in `config.json`
   - Ensure all tokens are correct and not expired
   - Check that your app has the required permissions

2. **"No bookmarks found" or "Could not fetch bookmarks"**:
   - This is the most common issue - the bookmarks endpoint requires special access
   - Your Twitter app must have `bookmarks:read` permission
   - This permission is not available to all developers - you may need to request access
   - Try the test script first: `python test_setup.py`

3. **Rate Limited**: 
   - The script includes automatic rate limiting
   - Wait a few minutes and try again
   - Consider reducing the `max_results` parameter

4. **Media Download Failed**: 
   - Check your internet connection
   - Ensure you have enough disk space
   - Some media URLs may be temporary and expire

5. **"Invalid or expired token"**:
   - Regenerate your access tokens in the Twitter Developer Portal
   - Make sure you're using the correct tokens for your app

### Getting Bookmarks Access

The bookmarks endpoint requires special permission that's not automatically granted:

1. Go to your Twitter Developer Portal
2. Navigate to your app's settings
3. Look for "App permissions" or "Scopes"
4. Request access to `bookmarks:read` if not already available
5. You may need to provide justification for why you need this access

### Logs

The tool creates detailed logs in `bookmark_backup.log` for troubleshooting. Check this file if you encounter issues.

## License

This project is for personal use only. Please respect Twitter's Terms of Service and API usage policies.