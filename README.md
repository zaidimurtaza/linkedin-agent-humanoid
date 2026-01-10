# LinkedIn Bot 🤖

A powerful Python bot for automating LinkedIn interactions using the official LinkedIn API. Create posts (text, URL, image, video), react to content, and engage with your network programmatically.

## Features ✨

- **Create Posts**
  - Simple text posts
  - URL/Article posts with preview
  - Image posts
  - Video posts
  
- **Engage with Content**
  - Like posts
  - React with different emotions (Like, Praise, Appreciation, Empathy, Interest, Entertainment)
  - Comment on posts
  
- **User Management**
  - Get authenticated user information
  - Delete posts

## Prerequisites 📋

1. **LinkedIn Developer Account**: Create an app at [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. **OAuth 2.0 Access Token** with the following scopes:
   - `w_member_social` - Required to create posts and interact with content
   - `openid` - For authentication
   - `profile` - To access profile information
   - `email` - To access email address

## Installation 🚀

1. Clone this repository:
```bash
git clone <repository-url>
cd linkedin-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your access token in the script or use environment variables

## Usage 💻

### Basic Setup

```python
from main import LinkedInBot

# Initialize the bot with your access token
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"
bot = LinkedInBot(ACCESS_TOKEN)

# Get user info (automatically sets person URN)
user_info = bot.get_user_info()
print(f"Authenticated as: {user_info['localizedFirstName']} {user_info['localizedLastName']}")
```

### Creating Posts

#### 1. Text Post

```python
post_id = bot.create_text_post(
    text="Hello LinkedIn! 🚀 Excited to share my journey!",
    visibility="PUBLIC"  # or "CONNECTIONS"
)
```

#### 2. URL/Article Post

```python
post_id = bot.create_url_post(
    text="Great insights on AI! 🤖 #AI #Technology",
    url="https://blog.linkedin.com/",
    title="Official LinkedIn Blog",
    description="Your source for insights and information about LinkedIn.",
    visibility="PUBLIC"
)
```

#### 3. Image Post

```python
post_id = bot.create_image_post(
    text="Check out this amazing view! 🌄 #Photography",
    image_path="/path/to/your/image.jpg",
    title="Beautiful Landscape",
    description="Captured during my morning hike",
    visibility="PUBLIC"
)
```

#### 4. Video Post

```python
post_id = bot.create_video_post(
    text="My latest video tutorial! 🎥 #Tutorial",
    video_path="/path/to/your/video.mp4",
    title="How to Build a LinkedIn Bot",
    description="Step-by-step guide",
    visibility="PUBLIC"
)
```

### Engaging with Content

#### Like a Post

```python
bot.like_post(post_urn="urn:li:share:1234567890")
```

#### React to a Post

Available reaction types:
- `LIKE` 👍
- `PRAISE` 🙌
- `APPRECIATION` ❤️
- `EMPATHY` 🤗
- `INTEREST` 💡
- `ENTERTAINMENT` 😂

```python
bot.react_to_post(
    post_urn="urn:li:share:1234567890",
    reaction_type="PRAISE"
)
```

#### Comment on a Post

```python
bot.comment_on_post(
    post_urn="urn:li:share:1234567890",
    comment_text="Great post! Thanks for sharing this valuable insight. 💡"
)
```

#### Delete a Post

```python
bot.delete_post(post_urn="urn:li:ugcPost:1234567890")
```

## API Reference 📚

### LinkedInBot Class

#### `__init__(access_token: str)`
Initialize the bot with an OAuth 2.0 access token.

#### `get_user_info() -> Dict[str, Any]`
Get the authenticated user's profile information and set the person URN.

#### `create_text_post(text: str, visibility: str = "PUBLIC") -> str`
Create a simple text post.

#### `create_url_post(text: str, url: str, title: Optional[str] = None, description: Optional[str] = None, visibility: str = "PUBLIC") -> str`
Create a post with a URL/article link.

#### `create_image_post(text: str, image_path: str, title: Optional[str] = None, description: Optional[str] = None, visibility: str = "PUBLIC") -> str`
Create a post with an image.

#### `create_video_post(text: str, video_path: str, title: Optional[str] = None, description: Optional[str] = None, visibility: str = "PUBLIC") -> str`
Create a post with a video.

#### `like_post(post_urn: str) -> bool`
Like a LinkedIn post.

#### `react_to_post(post_urn: str, reaction_type: str = "LIKE") -> bool`
React to a post with different reaction types.

#### `comment_on_post(post_urn: str, comment_text: str) -> str`
Comment on a LinkedIn post.

#### `delete_post(post_urn: str) -> bool`
Delete a LinkedIn post.

## Rate Limits ⚠️

LinkedIn API has the following rate limits:

- **Per Member**: 150 requests per day (UTC)
- **Per Application**: 100,000 requests per day (UTC)

Make sure to implement appropriate rate limiting in your application to avoid hitting these limits.

## Getting Post URNs 🔍

To interact with posts (like, react, comment), you need the post URN. There are several ways to get this:

1. **From the API Response**: When you create a post, the post ID is returned in the `X-RestLi-Id` header
2. **From LinkedIn URLs**: Extract from the post URL (e.g., `https://www.linkedin.com/feed/update/urn:li:share:1234567890`)
3. **Using LinkedIn API**: Fetch your recent posts using the UGC Posts API

## Error Handling 🛠️

All methods raise exceptions with descriptive error messages. Wrap your calls in try-except blocks:

```python
try:
    post_id = bot.create_text_post("Hello LinkedIn!")
    print(f"Post created: {post_id}")
except Exception as e:
    print(f"Error: {e}")
```

## Security Best Practices 🔒

1. **Never commit access tokens** to version control
2. Use environment variables for sensitive data:
   ```python
   import os
   ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
   ```
3. Rotate access tokens regularly
4. Use the principle of least privilege - only request necessary scopes

## Example Script 📝

Check out the `main.py` file for a complete example with all features demonstrated.

## Troubleshooting 🔧

### Common Issues

1. **401 Unauthorized**: Check that your access token is valid and has the required scopes
2. **403 Forbidden**: Ensure your app has the "Share on LinkedIn" product enabled in the Developer Portal
3. **429 Too Many Requests**: You've hit the rate limit - implement exponential backoff
4. **Media Upload Fails**: Ensure the file path is correct and the file format is supported

### Supported Media Formats

- **Images**: JPEG, PNG, GIF
- **Videos**: MP4, MOV (check LinkedIn's current specifications for size limits)

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is open source and available under the MIT License.

## Disclaimer ⚖️

This bot is for educational purposes. Make sure to comply with LinkedIn's Terms of Service and API Terms of Use when using this bot. Automated posting should be done responsibly and ethically.

## Support 💬

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Happy Automating! 🚀**
