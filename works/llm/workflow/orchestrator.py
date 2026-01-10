"""
Workflow Orchestrator: Runs all steps in sequence
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from works.llm.workflow.step1 import gather_news_content
from works.llm.context import get_llm_context, set_llm_context
from works.llm.workflow.step2 import get_existing_posts
from works.llm.workflow.step3 import decide_post_type
from works.llm.workflow.refine_post_check import refine_post_decision
from works.llm.workflow.step4 import create_post
from works.llm.workflow.step5 import save_post_to_db
from works.news_current_affairs import get_trending_topics
from main import LinkedInBot
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def run_workflow(topic: str, access_token: str = None):
    """
    Run complete workflow:
    1. Gather news content
    2. Get existing posts
    3. Decide post type
    4. Create post
    5. Save to database
    """
    if not access_token:
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    
    if not access_token:
        print("❌ LinkedIn access token required")
        return None
    
    # Reset context at start
    set_llm_context("")
    
    bot = LinkedInBot(access_token)
    
    print("=" * 60)
    print("🚀 Starting LinkedIn Post Workflow")
    print("=" * 60)
    
    # Step 1: Gather news content
    print("\n📰 STEP 1: Gathering news content...")
    news_content = gather_news_content(topic)
    
    # Step 2: Get existing posts
    print("\n📋 STEP 2: Fetching existing posts...")
    existing_posts = get_existing_posts(limit=10)
    
    # Step 3: Decide post type
    print("\n🤔 STEP 3: LLM deciding post type...")
    decision = decide_post_type(news_content, existing_posts)
    
    # Step 3.5: Refine and enhance decision
    print("\n✨ STEP 3.5: Refining and enhancing post decision...")
    decision = refine_post_decision(decision, news_content)
    
    # Step 4: Create post
    print("\n📮 STEP 4: Creating LinkedIn post...")
    post_urn = create_post(bot, decision)
    
    if not post_urn:
        print("❌ Failed to create post")
        return None
    
    # Step 5: Save to database
    print("\n💾 STEP 5: Saving post to database...")
    save_post_to_db(bot, post_urn, decision, news_content)
    
    print("\n" + "=" * 60)
    print("✅ Workflow completed successfully!")
    print(f"📝 Post URN: {post_urn}")
    print("=" * 60)
    
    # Save context to file
    context = get_llm_context()
    # if context:
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     filename = f"llm_context_{timestamp}.txt"
    #     with open(filename, "w", encoding="utf-8") as f:
    #         f.write(f"LinkedIn Bot LLM Context - {datetime.now().isoformat()}\n")
    #         f.write("=" * 60 + "\n\n")
    #         f.write(context)
    #     print(f"📄 Context saved to: {filename}")
    
    return {
        "post_urn": post_urn,
        "decision": decision,
        "news_content": news_content
    }

if __name__ == "__main__":
    # Example usage
    import json
    print("Starting workflow...")
    topics = get_trending_topics()
    print(f"Trending topics: {json.dumps(topics, indent=2) if topics else 'No topics found'}")
    result = run_workflow(topics)
    if result:
        print(f"\n✅ Created post: {result['post_urn']}")
