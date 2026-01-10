"""
Flask app for LinkedIn Bot with scheduled workflow execution
"""
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from works.llm.workflow.orchestrator import run_workflow
from works.news_current_affairs import get_trending_topics
import os
from dotenv import load_dotenv
import threading
import traceback
from datetime import datetime

load_dotenv()

app = Flask(__name__)
scheduler = BackgroundScheduler()
workflow_running = False
workflow_lock = threading.Lock()

def execute_workflow():
    """Execute the LinkedIn workflow"""
    global workflow_running
    
    with workflow_lock:
        if workflow_running:
            print(f"[{datetime.now()}] ⚠️ Workflow already running, skipping...")
            return
        
        workflow_running = True
    
    try:
        print(f"\n[{datetime.now()}] 🚀 Starting scheduled workflow...")
        topics = get_trending_topics()
        result = run_workflow(topics)
        
        if result:
            print(f"[{datetime.now()}] ✅ Workflow completed: {result.get('post_urn')}")
        else:
            print(f"[{datetime.now()}] ❌ Workflow failed")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Workflow error: {str(e)}")
        traceback.print_exc()
    finally:
        with workflow_lock:
            workflow_running = False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "workflow_running": workflow_running
    }), 200

@app.route('/start', methods=['POST', 'GET'])
def start():
    """Manually trigger the workflow"""
    global workflow_running
    
    with workflow_lock:
        if workflow_running:
            return jsonify({
                "status": "error",
                "message": "Workflow is already running"
            }), 409
        
        # Start workflow in background thread
        thread = threading.Thread(target=execute_workflow)
        thread.daemon = True
        thread.start()
    
    return jsonify({
        "status": "started",
        "message": "Workflow triggered successfully",
        "timestamp": datetime.now().isoformat()
    }), 200

def start_scheduler():
    """Start the background scheduler"""
    # Schedule workflow to run 4 times a day (every 6 hours)
    # Times: 00:00, 06:00, 12:00, 18:00
    scheduler.add_job(
        func=execute_workflow,
        trigger=CronTrigger(hour='0,6,12,18', minute=0),
        id='linkedin_workflow',
        name='LinkedIn Post Workflow',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Scheduler started - Workflow will run 4 times daily at 00:00, 06:00, 12:00, 18:00")

if __name__ == '__main__':
    # Start scheduler
    start_scheduler()
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Flask app starting on port {port}")
    print(f"📡 Health endpoint: http://localhost:{port}/health")
    print(f"🎯 Start endpoint: http://localhost:{port}/start")
    
    app.run(host='0.0.0.0', port=port, debug=False)
