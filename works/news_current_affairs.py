"""
News & Current Affairs Aggregator
Combines Reddit and GNews for clean, LLM-friendly news feeds
"""

import requests
import html
import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Headers for API requests
REDDIT_HEADERS = {
    "User-Agent": "SelfAwareAgent/1.0 (News Aggregator)"
}

# GNews API Key (from environment)
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')


def is_english(text: str) -> bool:
    """Check if text is English (simple heuristic)"""
    if not text or len(text.strip()) < 10:
        return False
    
    # Simple check: English has more common English characters
    english_chars = sum(1 for c in text if c.isascii() and c.isalnum())
    total_chars = sum(1 for c in text if c.isalnum())
    
    if total_chars == 0:
        return False
    
    # If >80% are ASCII alphanumeric, likely English
    return (english_chars / total_chars) > 0.8


def clean_text(text: str, max_length: int = 220) -> str:
    """Clean and truncate text"""
    if not text:
        return ""
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + "..."
    
    return text.strip()


def fetch_reddit(subreddit: str = "technology", query: str = "", limit: int = 5, sort: str = "new") -> Dict:
    """
    Fetch posts from Reddit
    
    Args:
        subreddit: Subreddit name (without r/)
        query: Search query
        limit: Number of posts to fetch
        sort: Sort order (new, hot, top)
    
    Returns:
        dict: Cleaned Reddit posts
    """
    try:
        if query:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                "q": query,
                "sort": sort,
                "limit": min(limit, 25),  # Reddit max is 25
                "restrict_sr": 1
            }
        else:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
            params = {"limit": min(limit, 25)}
        
        response = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        items = []
        
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            
            # Combine title and text for language check
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            text_blob = f"{title} {selftext}"
            
            # Skip non-English posts
            if not is_english(text_blob):
                continue
            
            # Extract image URL if available
            image_url = ""
            if post.get("url_overridden_by_dest"):
                url_dest = post["url_overridden_by_dest"]
                if any(ext in url_dest.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    image_url = url_dest
            elif post.get("preview", {}).get("images"):
                try:
                    image_url = post["preview"]["images"][0]["source"]["url"]
                    # Clean Reddit image URL
                    image_url = image_url.replace("&amp;", "&")
                except:
                    pass
            
            # Create summary
            summary = clean_text(selftext) if selftext else clean_text(title)
            if not summary:
                summary = "No description provided."
            
            items.append({
                "id": post.get("id", ""),
                "title": clean_text(title, 120),
                "summary": summary,
                "subreddit": post.get("subreddit", subreddit),
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "url": f"https://www.reddit.com{post.get('permalink', '')}",
                "image_url": image_url,
                "created_utc": post.get("created_utc", 0)
            })
        
        return {
            "source": "reddit",
            "category": subreddit,
            "query": query,
            "items": items,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"⚠ Reddit fetch error: {str(e)}")
        return {
            "source": "reddit",
            "category": subreddit,
            "query": query,
            "items": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def fetch_gnews(topic: str = "technology", limit: int = 5, lang: str = "en") -> Dict:
    """
    Fetch news from GNews API
    
    Args:
        topic: News topic (technology, world, business, sports, etc.)
        limit: Number of articles
        lang: Language code
    
    Returns:
        dict: Cleaned GNews articles
    """
    if not GNEWS_API_KEY:
        return {
            "source": "gnews",
            "category": topic,
            "items": [],
            "error": "GNews API key not configured",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        url = "https://gnews.io/api/v4/top-headlines"
        params = {
            "topic": topic,
            "lang": lang,
            "max": min(limit, 10),  # GNews free tier limit
            "token": GNEWS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        items = []
        
        for article in data.get("articles", []):
            # Skip non-English
            title = article.get("title", "")
            description = article.get("description", "")
            if not is_english(f"{title} {description}"):
                continue
            
            items.append({
                "id": article.get("url", ""),
                "title": clean_text(title, 120),
                "summary": clean_text(description) or clean_text(title),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "image_url": article.get("image", ""),
                "published_at": article.get("publishedAt", "")
            })
        
        return {
            "source": "gnews",
            "category": topic,
            "items": items,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"⚠ GNews fetch error: {str(e)}")
        return {
            "source": "gnews",
            "category": topic,
            "items": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def get_world_snapshot(categories: Optional[List[str]] = None) -> Dict:
    """
    Get combined news snapshot from multiple sources
    
    Args:
        categories: List of categories to fetch. If None, fetches default set
    
    Returns:
        dict: Combined news snapshot
    """
    if categories is None:
        categories = ["tech", "programming", "world", "politics"]
    
    snapshot = {}
    
    # Reddit sources
    reddit_sources = {
        "tech": ("technology", "python OR AI OR programming OR tech"),
        "programming": ("programming", "python OR javascript OR coding"),
        "webdev": ("webdev", "react OR nextjs OR frontend"),
        "machinelearning": ("MachineLearning", "AI OR deep learning OR LLM")
    }
    
    # GNews sources
    gnews_sources = {
        "world": "world",
        "politics": "politics",
        "business": "business",
        "sports": "sports",
        "science": "science"
    }
    
    # Fetch Reddit posts
    for cat in categories:
        if cat in reddit_sources:
            subreddit, query = reddit_sources[cat]
            snapshot[cat] = fetch_reddit(subreddit, query, limit=5)
        elif cat in gnews_sources:
            topic = gnews_sources[cat]
            snapshot[cat] = fetch_gnews(topic, limit=5)
    
    return {
        "snapshot": snapshot,
        "fetched_at": datetime.utcnow().isoformat(),
        "total_categories": len(snapshot)
    }


def dig_deeper_topic(topic: str, max_results: int = 10) -> Dict:
    """
    Deep dive into a specific topic across multiple sources
    This is the main function for topic-based exploration
    
    Args:
        topic: Topic to search for (e.g., "Python", "AI", "Ukraine", "Elections")
        max_results: Maximum number of results per source
    
    Returns:
        dict: Comprehensive results from Reddit and GNews
    """
    results = {
        "topic": topic,
        "reddit_results": [],
        "gnews_results": [],
        "total_items": 0,
        "searched_at": datetime.utcnow().isoformat()
    }
    
    # Search Reddit across multiple relevant subreddits
    reddit_subreddits = [
        ("technology", topic),
        ("programming", topic),
        ("worldnews", topic),
        ("news", topic),
        ("science", topic)
    ]
    
    print(f"🔍 Searching Reddit for: {topic}")
    for subreddit, query in reddit_subreddits:
        try:
            data = fetch_reddit(subreddit, query, limit=max_results, sort="relevance")
            if data.get("items"):
                results["reddit_results"].extend(data["items"])
        except Exception as e:
            print(f"  ⚠ Error searching r/{subreddit}: {str(e)}")
    
    # Remove duplicates from Reddit results
    seen_ids = set()
    unique_reddit = []
    for item in results["reddit_results"]:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_reddit.append(item)
    results["reddit_results"] = unique_reddit[:max_results]
    
    # Search GNews
    print(f"🔍 Searching GNews for: {topic}")
    if GNEWS_API_KEY:
        try:
            # Try search endpoint if available, otherwise use topic-based
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": topic,
                "lang": "en",
                "max": max_results,
                "token": GNEWS_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    if is_english(f"{article.get('title', '')} {article.get('description', '')}"):
                        results["gnews_results"].append({
                            "id": article.get("url", ""),
                            "title": clean_text(article.get("title", ""), 120),
                            "summary": clean_text(article.get("description", "")),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "url": article.get("url", ""),
                            "image_url": article.get("image", ""),
                            "published_at": article.get("publishedAt", "")
                        })
        except Exception as e:
            print(f"  ⚠ GNews search error: {str(e)}")
            # Fallback to topic-based fetch
            try:
                data = fetch_gnews("general", limit=max_results)
                results["gnews_results"] = data.get("items", [])
            except:
                pass
    else:
        print("  ⚠ GNews API key not configured")
    
    results["total_items"] = len(results["reddit_results"]) + len(results["gnews_results"])
    
    return results


def get_trending_topics(limit: int = 10) -> List[Dict]:
    """
    Get trending topics from Reddit
    
    Args:
        limit: Number of trending topics
    
    Returns:
        list: Trending topics with metadata
    """
    try:
        # Get hot posts from multiple subreddits
        subreddits = ["technology", "programming", "worldnews", "science"]
        all_posts = []
        
        for subreddit in subreddits:
            data = fetch_reddit(subreddit, limit=5, sort="hot")
            all_posts.extend(data.get("items", []))
        
        # Sort by score and get top topics
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        topics = []
        seen_titles = set()
        
        for post in all_posts[:limit * 2]:  # Get more to filter duplicates
            title = post.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                topics.append({
                    "topic": title.split()[0] if title else "",  # First word as topic hint
                    "title": title,
                    "score": post.get("score", 0),
                    "subreddit": post.get("subreddit", ""),
                    "url": post.get("url", "")
                })
                if len(topics) >= limit:
                    break
        
        return topics
        
    except Exception as e:
        print(f"⚠ Error getting trending topics: {str(e)}")
        return []


# Main functions for easy access
def get_news_feed(category: str = "tech", limit: int = 5) -> Dict:
    """
    Simple function to get news feed for a category
    
    Args:
        category: Category name (tech, programming, world, politics, etc.)
        limit: Number of items
    
    Returns:
        dict: News feed
    """
    if category in ["tech", "programming", "webdev", "machinelearning"]:
        subreddit_map = {
            "tech": "technology",
            "programming": "programming",
            "webdev": "webdev",
            "machinelearning": "MachineLearning"
        }
        return fetch_reddit(subreddit_map.get(category, "technology"), limit=limit)
    else:
        return fetch_gnews(category, limit=limit)


# Example usage
if __name__ == "__main__":
    print("📰 News & Current Affairs Aggregator\n")
    
    # Example 1: Get world snapshot
    print("1️⃣ Getting world snapshot...")
    snapshot = get_world_snapshot(["tech", "world", "politics"])
    print(f"   ✓ Fetched {snapshot['total_categories']} categories\n")
    print("=" * 50)
    print(snapshot)
    print("=" * 50)
    # # Example 2: Deep dive into a topic
    print("2️⃣ Deep diving into topic: 'Python'...")
    python_news = dig_deeper_topic("Python", max_results=5)
    print(f"   ✓ Found {python_news['total_items']} items")
    print(f"   - Reddit: {len(python_news['reddit_results'])} posts")
    print(f"   - GNews: {len(python_news['gnews_results'])} articles\n")
    
    # Example 3: Get trending topics
    print("3️⃣ Getting trending topics...")
    trending = get_trending_topics(limit=5)
    print(f"   ✓ Found {len(trending)} trending topics\n")
    
    # Example 4: Simple category feed
    print("4️⃣ Getting tech feed...")
    tech_feed = get_news_feed("tech", limit=3)
    print(tech_feed)
    print(f"   ✓ Found {len(tech_feed.get('items', []))} items")

    news_current_affairs = fetch_gnews("world", limit=3)
    print("=" * 50)
    print(news_current_affairs)
    print("=" * 50)
    print(f"   ✓ Found {len(news_current_affairs.get('items', []))} items")
    print("\n✅ All examples completed!")
