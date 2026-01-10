"""
Step 1: Gather news content on a topic using news tools
LLM calls news tools repeatedly until satisfied with content
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from works.llm.chat import tool_caller_llm
from works.llm.tools import news_tools
from works.news_current_affairs import fetch_reddit, fetch_gnews, dig_deeper_topic, get_world_snapshot
from works.llm.context import get_llm_context, set_llm_context
import json

def execute_news_tool(tool_name: str, **kwargs):
    """Execute news tool functions"""
    tool_map = {
        "fetch_reddit": fetch_reddit,
        "fetch_gnews": fetch_gnews,
        "dig_deeper_topic": dig_deeper_topic,
        "get_world_snapshot": get_world_snapshot
    }
    func = tool_map.get(tool_name)
    if func:
        return func(**kwargs)
    return None

def gather_news_content(topic: str, max_iterations: int = 5):
    """
    LLM gathers news content on a topic, calling news tools until satisfied
    
    Returns:
        dict: Collected news content with items and image URLs
    """
    collected_content = {
        "reddit_items": [],
        "gnews_items": [],
        "image_urls": [],
        "all_items": []
    }
    
    prompt = f"""Research and gather comprehensive news content about: {topic}

You have access to news tools. Call them strategically to gather diverse, relevant content.
Keep calling tools until you have enough quality content (at least 5-10 items from different sources).
Use dig_deeper_topic for deep research, fetch_reddit for Reddit posts, fetch_gnews for news articles."""

    # Format topic for display (handle if it's a list/dict)
    topic_display = topic
    if isinstance(topic, (list, dict)):
        topic_display = "trending topics" if isinstance(topic, list) else str(topic)[:100]
    elif len(str(topic)) > 200:
        topic_display = str(topic)[:200] + "..."
    
    for iteration in range(max_iterations):
        items_before = len(collected_content["all_items"])
        print(f"\n📰 Iteration {iteration + 1}: Gathering news about '{topic_display}'...")
        print(f"   Current items collected: {items_before}")
        
        # LLM decides which tools to call
        print("Calling tool caller")
        response = tool_caller_llm(tools=news_tools, prompt=prompt, step_name="Step 1: Gather News")
        print(f"Responce afte tool call: {response}")
        if isinstance(response, dict) and response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                func_name = tool_call.get("function", {}).get("name")
                try:
                    args = json.loads(tool_call["function"]["arguments"])
                except:
                    args = {}
                
                print(f"  🔧 Calling: {func_name} with {args}")
                result = execute_news_tool(func_name, **args)
                
                if result:
                    # Extract items and image URLs
                    if "reddit_results" in result:
                        items = result.get("reddit_results", [])
                        collected_content["reddit_items"].extend(items)
                        collected_content["all_items"].extend(items)
                        
                        # Extract image URLs
                        for item in items:
                            if item.get("image_url"):
                                collected_content["image_urls"].append(item["image_url"])
                    
                    if "gnews_results" in result:
                        items = result.get("gnews_results", [])
                        collected_content["gnews_items"].extend(items)
                        collected_content["all_items"].extend(items)
                        
                        for item in items:
                            if item.get("image_url"):
                                collected_content["image_urls"].append(item["image_url"])
                    
                    if "items" in result and "reddit_results" not in result and "gnews_results" not in result:
                        items = result.get("items", [])
                        collected_content["all_items"].extend(items)
                        
                        for item in items:
                            if item.get("image_url"):
                                collected_content["image_urls"].append(item["image_url"])
        
        items_after = len(collected_content["all_items"])
        print(f"   Items after this iteration: {items_after}")
        
        # Check if we have enough content
        if items_after >= 1:
            print(f"✅ Collected enough content ({items_after} items) after {iteration + 1} iterations")
            break
        
        # Update prompt with collected content summary (use items_after, not before)
        prompt = f"""You've gathered {items_after} items so far about: {topic_display}
Continue gathering more diverse content. Aim for at least 5-10 quality items."""
    
    # Remove duplicates
    seen_ids = set()
    unique_items = []
    for item in collected_content["all_items"]:
        item_id = item.get("id") or item.get("url", "")
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_items.append(item)
    
    collected_content["all_items"] = unique_items[:20]  # Limit to 20 items
    
    print(f"\n✅ Collected {len(collected_content['all_items'])} unique news items")
    return collected_content

if __name__ == "__main__":
    result = gather_news_content("AI and Machine Learning")
    print(json.dumps(result, indent=2))
