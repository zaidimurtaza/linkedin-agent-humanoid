"""
Step 2: Fetch existing posts from database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from db.connection import run_query

def get_existing_posts(limit: int = 10):
    """
    Fetch recent posts from database
    
    Returns:
        list: Recent LinkedIn posts
    """
    db_name = "student"
    collection_name = "linkedin_posts"
    
    # Fetch recent posts (you may want to add sorting by created_at)
    posts = run_query(db_name, collection_name, "find", query={})
    
    # Sort by created_at if available, limit results
    if posts and isinstance(posts, list):
        try:
            posts = sorted(posts, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
        except:
            posts = posts[:limit]
    
    print(f"📋 Fetched {len(posts)} existing posts from database")
    return posts

if __name__ == "__main__":
    posts = get_existing_posts()
    print(f"Found {len(posts)} posts")
