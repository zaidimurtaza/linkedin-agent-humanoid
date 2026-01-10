"""
Step 4: Execute post creation (generate image if needed, then post to LinkedIn)
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from works.llm.chat import chat_with_image_model, tool_caller_llm
from works.llm.tools import linkedin_tools, image_generation_tools
from works.llm.context import get_llm_context, set_llm_context
from main import LinkedInBot
from db.upload_image import upload_image
import json
import os

def execute_linkedin_tool(bot: LinkedInBot, tool_name: str, **kwargs):
    """Execute LinkedIn tool functions"""
    tool_map = {
        "create_text_post": bot.create_text_post,
        "create_url_post": bot.create_url_post,
        "create_image_post": bot.create_image_post,
        "create_video_post": bot.create_video_post,
        "get_user_info": bot.get_user_info
    }
    func = tool_map.get(tool_name)
    if func:
        return func(**kwargs)
    return None

def add_to_context(step_name: str, action: str, input_data: dict, output_data: dict = None, error: str = None):
    """Add non-LLM action to context"""
    context_entry = f"""
Step: {step_name}
Action: {action}
Input: {json.dumps(input_data, indent=2)}
"""
    if error:
        context_entry += f"Error: {error}\n"
    elif output_data:
        context_entry += f"Output: {json.dumps(output_data, indent=2)}\n"
    context_entry += "---\n"
    set_llm_context(get_llm_context() + context_entry)

def create_post(bot: LinkedInBot, decision: dict):
    """
    Create LinkedIn post based on LLM decision
    
    Returns:
        str: Post URN if successful
    """
    post_type = decision.get("post_type", "text")
    text = decision.get("text", "")
    visibility = decision.get("visibility", "PUBLIC")
    
    print(f"\n📮 Creating {post_type} post...")
    
    if post_type == "image":
        # Generate image first
        image_prompt = decision.get("image_prompt", "Professional LinkedIn post image")
        print(f"🎨 Generating image with prompt: {image_prompt}")
        
        image_result = chat_with_image_model(prompt=image_prompt, step_name="Step 4: Generate Image")
        image_path = "generated_image.png"  # Default path from chat.py
        
        if os.path.exists(image_path):
            # Create image post
            try:
                post_id = bot.create_image_post(
                    text=text,
                    image_path=image_path,
                    title=decision.get("title"),
                    description=decision.get("description"),
                    visibility=visibility
                )
                add_to_context(
                    "Step 4: Create Image Post",
                    "create_image_post",
                    {"text": text[:100] + "...", "image_path": image_path, "title": decision.get("title"), "visibility": visibility},
                    {"post_id": post_id}
                )
            except Exception as e:
                add_to_context(
                    "Step 4: Create Image Post",
                    "create_image_post",
                    {"text": text[:100] + "...", "image_path": image_path},
                    error=str(e)
                )
                raise
            
            # Upload image to Supabase and get public URL
            try:
                print("☁️ Uploading image to Supabase...")
                public_image_url = upload_image(image_path)
                decision["image_url"] = public_image_url
                print(f"✅ Image uploaded to Supabase: {public_image_url}")
                add_to_context(
                    "Step 4: Upload Image",
                    "upload_image",
                    {"image_path": image_path},
                    {"public_url": public_image_url}
                )
            except Exception as e:
                print(f"⚠️ Failed to upload image to Supabase: {e}")
                decision["image_url"] = image_path
                add_to_context(
                    "Step 4: Upload Image",
                    "upload_image",
                    {"image_path": image_path},
                    error=str(e)
                )
            
            return post_id
        else:
            print("⚠️ Image not generated, falling back to text post")
            post_type = "text"
    
    if post_type == "url":
        try:
            post_id = bot.create_url_post(
                text=text,
                url=decision.get("url", ""),
                title=decision.get("title"),
                description=decision.get("description"),
                visibility=visibility
            )
            add_to_context(
                "Step 4: Create URL Post",
                "create_url_post",
                {"text": text[:100] + "...", "url": decision.get("url"), "title": decision.get("title"), "visibility": visibility},
                {"post_id": post_id}
            )
            return post_id
        except Exception as e:
            error_msg = str(e)
            if "DUPLICATE_POST" in error_msg or "422" in error_msg:
                print(f"⚠️ Duplicate URL post detected. Modifying text...")
                text_variation = text + "\n\n#TechNews"
                try:
                    post_id = bot.create_url_post(
                        text=text_variation,
                        url=decision.get("url", ""),
                        title=decision.get("title"),
                        description=decision.get("description"),
                        visibility=visibility
                    )
                    add_to_context(
                        "Step 4: Create URL Post (Retry)",
                        "create_url_post",
                        {"text": text_variation[:100] + "...", "url": decision.get("url"), "visibility": visibility},
                        {"post_id": post_id}
                    )
                    return post_id
                except:
                    add_to_context(
                        "Step 4: Create URL Post",
                        "create_url_post",
                        {"text": text[:100] + "...", "url": decision.get("url")},
                        error=str(e)
                    )
                    print(f"❌ Still failed: {e}")
                    return None
            else:
                add_to_context(
                    "Step 4: Create URL Post",
                    "create_url_post",
                    {"text": text[:100] + "...", "url": decision.get("url")},
                    error=str(e)
                )
                print(f"❌ Error creating URL post: {e}")
                return None
    
    if post_type == "text":
        try:
            post_id = bot.create_text_post(
                text=text,
                visibility=visibility
            )
            add_to_context(
                "Step 4: Create Text Post",
                "create_text_post",
                {"text": text[:100] + "...", "visibility": visibility},
                {"post_id": post_id}
            )
            return post_id
        except Exception as e:
            error_msg = str(e)
            if "DUPLICATE_POST" in error_msg or "422" in error_msg:
                print(f"⚠️ Duplicate post detected. Modifying text slightly...")
                text_variation = text + "\n\n#TechNews #AI"
                try:
                    post_id = bot.create_text_post(
                        text=text_variation,
                        visibility=visibility
                    )
                    add_to_context(
                        "Step 4: Create Text Post (Retry)",
                        "create_text_post",
                        {"text": text_variation[:100] + "...", "visibility": visibility},
                        {"post_id": post_id}
                    )
                    return post_id
                except:
                    add_to_context(
                        "Step 4: Create Text Post",
                        "create_text_post",
                        {"text": text[:100] + "..."},
                        error=str(e)
                    )
                    print(f"❌ Still failed after variation: {e}")
                    return None
            else:
                add_to_context(
                    "Step 4: Create Text Post",
                    "create_text_post",
                    {"text": text[:100] + "..."},
                    error=str(e)
                )
                print(f"❌ Error creating post: {e}")
                return None
    
    return None

if __name__ == "__main__":
    # Example usage
    ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    if ACCESS_TOKEN:
        bot = LinkedInBot(ACCESS_TOKEN)
        decision = {
            "post_type": "text",
            "text": "Test post",
            "visibility": "PUBLIC"
        }
        post_id = create_post(bot, decision)
        print(f"Post created: {post_id}")
