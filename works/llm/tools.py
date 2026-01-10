# LinkedIn API tools
linkedin_tools = [
    {
        "type": "function",
        "function": {
            "name": "create_text_post",
            "description": "Create a simple text post on LinkedIn",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text content of the post"
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["PUBLIC", "CONNECTIONS"],
                        "description": "Post visibility - PUBLIC (visible to everyone) or CONNECTIONS (only connections)",
                        "default": "PUBLIC"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_url_post",
            "description": "Create a LinkedIn post with a URL/article link",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The commentary text for the post"
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL to share"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title for the URL preview"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the URL preview"
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["PUBLIC", "CONNECTIONS"],
                        "description": "Post visibility - PUBLIC or CONNECTIONS",
                        "default": "PUBLIC"
                    }
                },
                "required": ["text", "url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_image_post",
            "description": "Create a LinkedIn post with an image",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The commentary text for the post"
                    },
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file (e.g., 'generated_image.png')"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title for the image"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the image"
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["PUBLIC", "CONNECTIONS"],
                        "description": "Post visibility - PUBLIC or CONNECTIONS",
                        "default": "PUBLIC"
                    }
                },
                "required": ["text", "image_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_video_post",
            "description": "Create a LinkedIn post with a video",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The commentary text for the post"
                    },
                    "video_path": {
                        "type": "string",
                        "description": "Path to the video file (e.g., 'video.mp4')"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title for the video"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the video"
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["PUBLIC", "CONNECTIONS"],
                        "description": "Post visibility - PUBLIC or CONNECTIONS",
                        "default": "PUBLIC"
                    }
                },
                "required": ["text", "video_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "like_post",
            "description": "Like a LinkedIn post",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_urn": {
                        "type": "string",
                        "description": "The URN of the post to like (e.g., 'urn:li:share:123456789' or 'urn:li:ugcPost:123456789')"
                    }
                },
                "required": ["post_urn"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "react_to_post",
            "description": "React to a LinkedIn post with different reaction types (LIKE, PRAISE, APPRECIATION, EMPATHY, INTEREST, ENTERTAINMENT)",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_urn": {
                        "type": "string",
                        "description": "The URN of the post to react to (e.g., 'urn:li:share:123456789')"
                    },
                    "reaction_type": {
                        "type": "string",
                        "enum": ["LIKE", "PRAISE", "APPRECIATION", "EMPATHY", "INTEREST", "ENTERTAINMENT"],
                        "description": "Type of reaction - LIKE (👍), PRAISE (🙌), APPRECIATION (❤️), EMPATHY (🤗), INTEREST (💡), ENTERTAINMENT (😂)",
                        "default": "LIKE"
                    }
                },
                "required": ["post_urn"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "comment_on_post",
            "description": "Comment on a LinkedIn post",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_urn": {
                        "type": "string",
                        "description": "The URN of the post to comment on (e.g., 'urn:li:share:123456789')"
                    },
                    "comment_text": {
                        "type": "string",
                        "description": "The text of the comment"
                    }
                },
                "required": ["post_urn", "comment_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get the authenticated user's profile information including name, email, and person URN. This also sets the person_urn which is required for creating posts.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# News and Current Affairs tools
news_tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_reddit",
            "description": "Fetch posts from Reddit subreddit with optional search query",
            "parameters": {
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Subreddit name without r/ prefix (e.g., 'technology', 'programming', 'worldnews')",
                        "default": "technology"
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional search query to filter posts"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to fetch (max 25)",
                        "default": 5
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["new", "hot", "top", "relevance"],
                        "description": "Sort order for posts",
                        "default": "new"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_gnews",
            "description": "Fetch news articles from GNews API by topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "News topic (technology, world, business, sports, science, politics, general)",
                        "default": "technology"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to fetch (max 10 for free tier)",
                        "default": 5
                    },
                    "lang": {
                        "type": "string",
                        "description": "Language code (e.g., 'en' for English)",
                        "default": "en"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_world_snapshot",
            "description": "Get combined news snapshot from multiple sources and categories",
            "parameters": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of categories to fetch (e.g., ['tech', 'programming', 'world', 'politics', 'business', 'science']). If not provided, defaults to ['tech', 'programming', 'world', 'politics']"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dig_deeper_topic",
            "description": "Deep dive into a specific topic across multiple Reddit subreddits and GNews sources",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to search for (e.g., 'Python', 'AI', 'Ukraine', 'Elections', 'Machine Learning')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results per source",
                        "default": 10
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_topics",
            "description": "Get trending topics from Reddit across multiple subreddits",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of trending topics to return",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_feed",
            "description": "Get a simple news feed for a specific category from Reddit or GNews",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category name: 'tech', 'programming', 'webdev', 'machinelearning' (Reddit) or 'world', 'politics', 'business', 'sports', 'science' (GNews)",
                        "default": "tech"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of items to fetch",
                        "default": 5
                    }
                },
                "required": []
            }
        }
    }
]

# Image generation tools
image_generation_tools = [
    {
        "type": "function",
        "function": {
            "name": "chat_with_image_model",
            "description": "Generates an image from a text prompt for LinkedIn post",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt to generate the image from"
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]