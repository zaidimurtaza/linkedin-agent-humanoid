"""
Step 5: Save post to database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from db.connection import run_query
from db.model import LinkedinPost
from datetime import datetime
from main import LinkedInBot

def save_post_to_db(bot: LinkedInBot, post_urn: str, decision: dict, news_content: dict):
    """
    Save created post to database
    
    Args:
        bot: LinkedInBot instance
        post_urn: URN of created post
        decision: LLM decision dict
        news_content: News content used for post
    """
    db_name = "student"
    collection_name = "linkedin_posts"
    
    # Get user info if not already set
    if not bot.person_urn:
        user_info = bot.get_user_info()
    else:
        user_info = {"name": "User", "email": ""}
    
    # Prepare post data
    # Ensure post_type is always set (default to "text" if missing)
    post_type = decision.get("post_type", "text")
    if post_type not in ["text", "url", "image"]:
        post_type = "text"  # Fallback to text if invalid
    
    post_data = {
        "post_urn": post_urn,
        "author_urn": bot.person_urn or "",
        "author_name": user_info.get("name", ""),
        "author_title": "",
        "author_profile_url": "",
        "post_text": decision.get("text", ""),
        "post_type": post_type,  # Store post type (text, url, or image)
        "created_at": datetime.now(),
        "image_url": None,
        "url": None,
        "title": None,
        "description": None
    }
    
    # Add type-specific fields based on post_type
    if post_type == "image":
        # Use Supabase public URL if available, otherwise fallback to local path
        post_data["image_url"] = decision.get("image_url") or "generated_image.png"
        post_data["title"] = decision.get("title")
        post_data["description"] = decision.get("description")
    
    elif post_type == "url":
        post_data["url"] = decision.get("url")
        post_data["title"] = decision.get("title")
        post_data["description"] = decision.get("description")
    
    # For "text" posts, no additional fields needed
    
    print(f"💾 Saving {post_type} post to database...")
    
    # Convert to dict (Pydantic model handles datetime serialization)
    try:
        post_model = LinkedinPost(**post_data)
        post_dict = post_model.dict()
        post_dict["created_at"] = post_data["created_at"]  # Keep datetime for MongoDB
    except Exception as e:
        print(f"⚠️ Error creating model: {e}, using dict directly")
        post_dict = post_data
    
    # Insert to database
    try:
        result = run_query(db_name, collection_name, "insert", data=post_dict)
        print(f"✅ Post saved to database: {result}")
        return result
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    print("Step 5: Save post to database")
