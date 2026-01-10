"""
Flask app for LinkedIn Bot with scheduled workflow execution
"""
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from works.llm.workflow.orchestrator import run_workflow
from works.news_current_affairs import get_trending_topics
import os
from dotenv import load_dotenv
import threading
import traceback
import requests
from datetime import datetime

load_dotenv()

app = Flask(__name__)
scheduler = BackgroundScheduler()
workflow_running = False
workflow_lock = threading.Lock()
app_port = None

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

def ping_health_endpoint():
    """Ping health endpoint to keep server awake"""
    global app_port
    try:
        port = app_port or int(os.getenv('PORT', 5000))
        url = f"http://localhost:{port}/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[{datetime.now()}] 💓 Health ping successful")
        else:
            print(f"[{datetime.now()}] ⚠️ Health ping returned status {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️ Health ping failed: {str(e)}")

def health_check():
    """Health check endpoint"""
    request = requests.get("https://linkedin-agent-humanoid.onrender.com/health")
    if request.status_code == 200:
        return "Healthy"
    else:
        return "Unhealthy"
def start_scheduler():
    """Start the background scheduler"""
    global app_port
    
    # Schedule workflow to run 4 times a day (every 6 hours)
    # Times: 00:00, 06:00, 12:00, 18:00
    scheduler.add_job(
        func=execute_workflow,
        trigger=CronTrigger(hour='0,6,12,18', minute=0),
        id='linkedin_workflow',
        name='LinkedIn Post Workflow',
        replace_existing=True
    )
    
    # Schedule health ping every minute to keep server awake
    scheduler.add_job(
        func=ping_health_endpoint,
        trigger=IntervalTrigger(minutes=1),
        id='health_ping',
        name='Health Endpoint Ping',
        replace_existing=True
    )
    scheduler.add_job(
        func=health_check,
        trigger=IntervalTrigger(minutes=1),
        id='health_check',
        name='Health Check',
        replace_existing=True
    )
    scheduler.start()
    print("✅ Scheduler started:")
    print("   - Workflow will run 4 times daily at 00:00, 06:00, 12:00, 18:00")
    print("   - Health endpoint ping every minute to keep server awake")

if __name__ == '__main__':
    # Get port and store globally for health ping
    app_port = int(os.getenv('PORT', 5000))
    
    # Start scheduler
    start_scheduler()
    
    # Run Flask app
    print(f"🚀 Flask app starting on port {app_port}")
    print(f"📡 Health endpoint: http://localhost:{app_port}/health")
    print(f"🎯 Start endpoint: http://localhost:{app_port}/start")
    
    app.run(host='0.0.0.0', port=app_port, debug=False)
