"""
LLM Context Management
"""
import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from db.connection import run_query
import json

llm_context = ""

def set_llm_context(context: str):
    global llm_context
    llm_context = context

def get_llm_context():
    global llm_context
    return llm_context

def save_llm_call(step_name: str, model: str, input_data: dict, output_data: dict = None, 
                  usage: dict = None, time_taken: float = None, is_image: bool = False):
    """Save LLM call to MongoDB"""
    try:
        input_text = json.dumps(input_data, indent=2) if input_data else None
        output_text = None if is_image else (json.dumps(output_data, indent=2) if output_data else None)
        
        call_data = {
            "step_name": step_name,
            "model": model,
            "input_tokens": usage.get("prompt_tokens", 0) if usage else 0,
            "output_tokens": usage.get("completion_tokens", 0) if usage else 0,
            "total_tokens": usage.get("total_tokens", 0) if usage else 0,
            "cost": usage.get("estimated_cost", 0) if usage else 0,
            "time_taken": time_taken,
            "input_text": input_text,
            "output_text": output_text,
            "created_at": datetime.now()
        }
        
        run_query("student", "llm_calls", "insert", data=call_data)
    except Exception as e:
        print(f"⚠️ Failed to save LLM call to DB: {e}")
