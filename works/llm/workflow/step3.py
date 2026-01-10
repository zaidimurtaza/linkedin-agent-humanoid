"""
Step 3: LLM decides post type based on news content and existing posts
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from works.llm.chat import chat_with_meta_llama
import json
import re

def decide_post_type(news_content: dict, existing_posts: list):
    """
    LLM decides what type of post to create (text, url, image)
    
    Returns:
        dict: Decision with post_type, text, and other parameters
    """
    # Format news content for LLM
    news_summary = f"""
News Items Found: {len(news_content.get('all_items', []))}
Top Items:
"""
    for i, item in enumerate(news_content.get('all_items', [])[:5], 1):
        news_summary += f"{i}. {item.get('title', 'N/A')}\n"
        if item.get('summary'):
            news_summary += f"   {item.get('summary', '')[:100]}...\n"
        if item.get('url'):
            news_summary += f"   URL: {item.get('url')}\n"
        news_summary += "\n"
    
    # Format existing posts with images/URLs
    existing_summary = f"Recent Posts: {len(existing_posts)}\n"
    existing_post_images = []
    existing_post_urls = []
    
    # Collect ALL image URLs from all posts
    for post in existing_posts:
        img_url = post.get('image_url')
        if img_url:
            img_url_str = str(img_url).strip()
            if img_url_str.startswith(('http://', 'https://')):
                existing_post_images.append(img_url_str)
        
        url = post.get('url')
        if url:
            existing_post_urls.append(url)
    
    # Format summary for first 3 posts
    for i, post in enumerate(existing_posts[:3], 1):
        post_text = post.get('post_text', 'N/A')[:100]
        post_type = post.get('post_type', 'unknown')
        existing_summary += f"{i}. [{post_type.upper()}] {post_text}...\n"
        
        img_url = post.get('image_url')
        if img_url:
            existing_summary += f"   Image URL: {img_url}\n"
        else:
            existing_summary += f"   (No image)\n"
        
        url = post.get('url')
        if url:
            existing_summary += f"   Article URL: {url}\n"
        
        existing_summary += "\n"
    
    # Filter news image URLs aggressively to avoid API timeouts
    image_urls = news_content.get('image_urls', [])
    valid_image_urls = []
    
    skip_patterns = [
        'dims4', 'dims/', 'dimensions', 'thumbnail/', 'resize/', 'crop/',
        'quality/', 'format/', 'preview.redd.it', '?url=', '?w=', '?h=',
        '%3A%2F%2F', '%2F', '&w=', '&h=', '&q=', 'cdn.', 'proxy.'
    ]
    
    for url in image_urls:
        if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
            continue
        
        if any(pattern in url.lower() for pattern in skip_patterns):
            continue
        
        if '?' in url or '%' in url:
            continue
        
        is_simple_url = (
            url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or
            ('i.redd.it' in url and '?' not in url and '%' not in url) or
            ('i.imgur.com' in url and '?' not in url and '%' not in url)
        )
        
        if is_simple_url and len(url) < 150:
            valid_image_urls.append(url)
            if len(valid_image_urls) >= 1:
                break
    
    # Build message with image URLs
    message_content = [
        {
            "type": "text",
            "text": f"""Decide what type of LinkedIn post to create based on news content and existing posts.

{news_summary}

{existing_summary}

Guidelines:
- If the last 1-2 posts are images, consider switching to text or url post for variety
- For text and image posts, you can include URLs as strings in the text field
- Make the text content substantial and engaging (not short)
- Choose image_post only if you can create a relevant image_prompt

Return JSON:
{{
    "post_type": "text" | "url" | "image",
    "text": "substantial post text content (can include URLs as strings)",
    "url": "url if post_type is url",
    "title": "title if post_type is url or image",
    "description": "description if post_type is url or image",
    "image_prompt": "prompt for image generation if post_type is image",
    "visibility": "PUBLIC" | "CONNECTIONS"
}}"""
        }
    ]
    
    # Collect safe image URLs to include (news + existing posts)
    all_safe_images = []
    
    if valid_image_urls:
        all_safe_images.extend(valid_image_urls[:1])
    
    for img_url in existing_post_images:
        if not img_url or not isinstance(img_url, str):
            continue
            
        img_url = img_url.strip()
        if not img_url.startswith(('http://', 'https://')):
            continue
        
        is_safe = (
            'supabase.co' in img_url or
            ('?' not in img_url and '%' not in img_url and len(img_url) < 200 and 
             (img_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or
              'i.redd.it' in img_url or 'i.imgur.com' in img_url))
        )
        
        if is_safe:
            all_safe_images.append(img_url)
            if len(all_safe_images) >= 3:
                break
    
    # Add images to message content
    for img_url in all_safe_images:
        message_content.insert(-1, {
            "type": "image_url",
            "image_url": {"url": img_url}
        })
    
    messages = [
        {
            "role": "system",
            "content": "You are a LinkedIn content strategist. Analyze news content and existing posts to decide the best post type. prefer image post if you can create a relevant image_prompt from the news content. or think from yuor end ad best "
        },
        {
            "role": "user",
            "content": message_content
        }
    ]
    
    reply = chat_with_meta_llama(messages, step_name="Step 3: Decide Post Type")
    
    try:
        if isinstance(reply, str):
            raise ValueError("String response received")
        
        if isinstance(reply, dict):
            response_data = reply.get("data", "")
            if not response_data:
                if "choices" in reply:
                    response_data = reply["choices"][0].get("message", {}).get("content", "")
            
            if response_data:
                response_str = str(response_data).strip()
                
                if "```json" in response_str:
                    response_str = re.sub(r'```json\s*', '', response_str)
                    response_str = re.sub(r'```\s*$', '', response_str)
                elif "```" in response_str:
                    response_str = re.sub(r'```\s*', '', response_str)
                    response_str = re.sub(r'```\s*$', '', response_str)
                
                json_match = re.search(r'\{.*"post_type".*\}', response_str, re.DOTALL)
                if json_match:
                    response_str = json_match.group(0)
                
                decision = json.loads(response_str)
                return decision
            else:
                raise ValueError("No data in response")
        else:
            raise ValueError(f"Unexpected reply type: {type(reply)}")
            
    except Exception as e:
        # Default fallback - create unique content from news
        import random
        fallback_text = "Exciting developments in the tech world! 🚀"
        if news_content.get('all_items'):
            item = random.choice(news_content['all_items'][:5])
            title = item.get('title', '')
            url = item.get('url', '')
            summary = item.get('summary', '')[:150] if item.get('summary') else ''
            
            if url and title:
                return {
                    "post_type": "url",
                    "text": f"{title}\n\n{summary}...\n\nWhat are your thoughts? 💭",
                    "url": url,
                    "title": title,
                    "description": summary,
                    "visibility": "PUBLIC"
                }
            elif title:
                fallback_text = f"{title}\n\n{summary}...\n\n#TechNews #AI"
        
        return {
            "post_type": "text",
            "text": fallback_text,
            "visibility": "PUBLIC"
        }

if __name__ == "__main__":
    news = {"all_items": [{"title": "Test", "summary": "Test summary", "url": "https://example.com"}], "image_urls": []}
    posts = []
    decision = decide_post_type(news, posts)
    print(json.dumps(decision, indent=2))
