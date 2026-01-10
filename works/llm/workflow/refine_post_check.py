"""
Step 3.5: Refine and enhance the post decision before execution
Takes decision from step3 and enhances it (better prompts, more descriptive text)
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from works.llm.chat import chat_with_meta_llama
from works.llm.context import get_llm_context
import json
import re

def extract_key_context():
    """Extract important context: step outputs, news items, and journey"""
    context = get_llm_context()
    if not context:
        return "No previous context available."
    
    key_parts = []
    
    # Step 1: Extract news items gathered
    step1_sections = re.findall(r'Step: Step 1: Gather News.*?Output:.*?---', context, re.DOTALL)
    if step1_sections:
        # Extract tool calls to see what news was gathered
        tool_calls = re.findall(r'"name":\s*"([^"]+)".*?"arguments":\s*"([^"]+)"', step1_sections[-1])
        if tool_calls:
            key_parts.append("Step 1 - News Gathering:")
            for tool_name, args in tool_calls[:3]:  # Show first 3 tool calls
                try:
                    args_dict = json.loads(args.replace('\\"', '"'))
                    if 'topic' in args_dict:
                        key_parts.append(f"  - {tool_name}: {args_dict.get('topic', 'N/A')}")
                except:
                    key_parts.append(f"  - {tool_name}: called")
    
    # Step 3: Extract full decision output
    step3_section = re.search(r'Step: Step 3: Decide Post Type.*?Output:.*?({[^}]*"post_type"[^}]*})', context, re.DOTALL)
    if step3_section:
        try:
            decision_json = json.loads(step3_section.group(1))
            key_parts.append("\nStep 3 - Decision:")
            key_parts.append(f"  Post Type: {decision_json.get('post_type', 'N/A')}")
            if decision_json.get('text'):
                text_preview = decision_json['text'][:150] + "..." if len(decision_json['text']) > 150 else decision_json['text']
                key_parts.append(f"  Text: {text_preview}")
            if decision_json.get('image_prompt'):
                prompt_preview = decision_json['image_prompt'][:100] + "..." if len(decision_json['image_prompt']) > 100 else decision_json['image_prompt']
                key_parts.append(f"  Image Prompt: {prompt_preview}")
        except:
            # Fallback: extract post_type
            post_type_match = re.search(r'"post_type":\s*"([^"]+)"', step3_section.group(0))
            if post_type_match:
                key_parts.append(f"\nStep 3 - Decision: {post_type_match.group(1)} post")
    
    # Extract news items from Step 1 input (what topics/news were researched)
    step1_inputs = re.findall(r'Step: Step 1[^\n]*\n.*?Input:.*?"prompt":\s*"([^"]{0,300})', context, re.DOTALL)
    if step1_inputs:
        # Extract topic/news info from prompt
        prompt = step1_inputs[-1]
        if 'Research and gather' in prompt:
            # Try to extract topic
            topic_match = re.search(r'about:\s*([^\n]{0,200})', prompt)
            if topic_match:
                topic_info = topic_match.group(1).replace('\\n', ' ')[:200]
                key_parts.append(f"\nNews Topics Researched: {topic_info}...")
    
    return '\n'.join(key_parts) if key_parts else "Context available."

def refine_post_decision(decision: dict, news_content: dict = None):
    """
    Refine and enhance the post decision from step3
    
    Args:
        decision: Decision dict from step3
        news_content: News content from step1 (optional, for better context)
    
    Returns:
        dict: Enhanced decision with better prompts and more descriptive text
    """
    context_summary = extract_key_context()
    
    # Add news items summary if available
    news_summary = ""
    if news_content and news_content.get('all_items'):
        news_summary = f"\n\nNews Items Gathered ({len(news_content['all_items'])} items):\n"
        for i, item in enumerate(news_content['all_items'][:5], 1):
            news_summary += f"{i}. {item.get('title', 'N/A')[:80]}...\n"
        if len(news_content['all_items']) > 5:
            news_summary += f"... and {len(news_content['all_items']) - 5} more items\n"
    
    # Build enhancement prompt
    messages = [
        {
            "role": "system",
            "content": "You are a LinkedIn content enhancement expert. Your job is to refine and improve post decisions to make them more engaging and effective."
        },
        {
            "role": "user",
            "content": f"""Refine and enhance this LinkedIn post decision. Make it the best possible version.

Workflow Journey & Context:
{context_summary}{news_summary}

Current Decision to Enhance:
{json.dumps(decision, indent=2)}

Enhancement Guidelines:
- For image_post: Create a highly detailed, vivid image_prompt that will generate an engaging visual
- Make the post text substantial, descriptive, and engaging (at least 3-4 sentences, not short)
- Ensure title and description are compelling and informative
- Keep the same post_type unless there's a strong reason to change
- Make URLs in text more natural if included

Return enhanced JSON in this exact format:
{{
    "post_type": "text" | "url" | "image",
    "text": "enhanced substantial post text (make it bigger and more descriptive)",
    "url": "url if post_type is url",
    "title": "enhanced title if post_type is url or image",
    "description": "enhanced description if post_type is url or image",
    "image_prompt": "highly detailed vivid image prompt if post_type is image",
    "visibility": "PUBLIC" | "CONNECTIONS"
}}"""
        }
    ]
    
    reply = chat_with_meta_llama(messages, step_name="Step 3.5: Refine Post Decision")
    
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
                
                # Remove markdown code blocks
                if "```json" in response_str:
                    response_str = re.sub(r'```json\s*', '', response_str)
                    response_str = re.sub(r'```\s*$', '', response_str)
                elif "```" in response_str:
                    response_str = re.sub(r'```\s*', '', response_str)
                    response_str = re.sub(r'```\s*$', '', response_str)
                
                # Extract JSON
                json_match = re.search(r'\{.*"post_type".*\}', response_str, re.DOTALL)
                if json_match:
                    response_str = json_match.group(0)
                
                enhanced_decision = json.loads(response_str)
                print(f"✅ Enhanced decision: {enhanced_decision.get('post_type')} post")
                return enhanced_decision
            else:
                raise ValueError("No data in response")
        else:
            raise ValueError(f"Unexpected reply type: {type(reply)}")
            
    except Exception as e:
        print(f"⚠️ Error refining decision: {e}, using original decision")
        return decision  # Fallback to original

if __name__ == "__main__":
    test_decision = {
        "post_type": "image",
        "text": "AI is changing the world",
        "title": "AI Revolution",
        "description": "Exploring AI",
        "image_prompt": "AI robot",
        "visibility": "PUBLIC"
    }
    enhanced = refine_post_decision(test_decision)
    print(json.dumps(enhanced, indent=2))
